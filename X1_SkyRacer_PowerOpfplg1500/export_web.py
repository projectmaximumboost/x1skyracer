"""Export the OPFPLG model for the web viewer (JSON + float32/uint32 buffer) and as a GLB with animation."""
import sys, json, math, struct, base64, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x1_opfplg_blender as m

def tris(mesh):
    out = {}
    for f, mat in zip(mesh.f, mesh.m):
        t = out.setdefault(mat, [])
        for k in range(1, len(f) - 1):
            t += [f[0], f[k], f[k + 1]]
    return out

def gather():
    d, objs = m.build()
    report, ok = m.fit_report(d, objs)
    objs = objs + [o for o in m.reference_objects() if o.display != "EMPTY"]
    return d, objs, report, ok

def to_three(v):   # blender (x, y, z) -> three / glTF (x, z, -y)
    return (v[0], v[2], -v[1])

def export_viewer(d, objs, report, ok, out_json, out_bin):
    buf = bytearray()
    items = []
    for o in objs:
        V = np.array([to_three(v) for v in o.mesh.v], dtype=np.float32)
        if o.driver and o.driver_path == "rotation_euler":
            piv = np.array(to_three(o.origin), dtype=np.float32)
        else:
            piv = (V.min(0) + V.max(0)) / 2
        V = V - piv
        it = dict(name=o.name, coll=o.coll, pivot=[round(float(c), 5) for c in piv], pos=[len(buf), len(V)], groups=[])
        buf += V.astype('<f4').tobytes()
        if o.mesh.e:
            e = np.array(o.mesh.e, dtype='<u4').ravel()
            it["edges"] = [len(buf), len(e)]
            buf += e.tobytes()
        for mat, idx in tris(o.mesh).items():
            a = np.array(idx, dtype='<u4')
            it["groups"].append([mat, len(buf), len(a)])
            buf += a.tobytes()
        if o.driver:
            it["driver"] = dict(expr=o.driver, path=o.driver_path)
        if o.motion:
            it["motion"] = [o.motion[0], round(o.motion[1], 6)]
        items.append(it)
    mats = {k: dict(rgb=list(v[0]), metal=v[1], rough=v[2], alpha=v[3]) for k, v in m.MATS.items()}
    P = d["perf"]
    c = m.CYCLE
    man = dict(materials=mats, objects=items, report=report, fits=ok,
               design={k: d[k] for k in ("B", "S", "disp", "m_move", "F_cont", "F_pk", "Lm", "r_mo", "r_ho", "zc", "y_T", "z_T",
                                         "Vb_idc", "Vb_odc", "A_eff", "END", "pitch", "clear", "skirt_engaged", "blk_face", "flange_r", "r_hi", "Rb")},
               cyl_y=d["cyl_y"], mass=d["mass"], perf={k: v for k, v in P.items()},
               cycle={k: v for k, v in c.items() if k != "motion"}, motion=c["motion"], acc=d["acc"], env=m.ENV,
               trace=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trace.json'))))
    json.dump(man, open(out_json, 'w'))
    open(out_bin, 'wb').write(bytes(buf))
    return len(buf)

def export_glb(d, objs, path):
    bin_ = bytearray()
    views, accs, meshes, nodes, materials, mat_ix = [], [], [], [], [], {}
    def pad():
        while len(bin_) % 4: bin_.append(0)
    def add_view(data, target=None):
        pad(); off = len(bin_); bin_.extend(data)
        v = dict(buffer=0, byteOffset=off, byteLength=len(data))
        if target: v["target"] = target
        views.append(v); return len(views) - 1
    def add_acc(arr, ctype, typ, target=None, minmax=False):
        vi = add_view(arr.tobytes(), target)
        a = dict(bufferView=vi, componentType=ctype, count=int(arr.shape[0]), type=typ)
        if minmax:
            a["min"] = [float(x) for x in np.atleast_2d(arr).min(0)] if arr.ndim > 1 else [float(arr.min())]
            a["max"] = [float(x) for x in np.atleast_2d(arr).max(0)] if arr.ndim > 1 else [float(arr.max())]
        accs.append(a); return len(accs) - 1
    def mat(name):
        if name not in mat_ix:
            rgb, metal, rough, alpha = m.MATS[name]
            lin = [((c_ + 0.055) / 1.055) ** 2.4 if c_ > 0.04045 else c_ / 12.92 for c_ in rgb]
            md = dict(name="OPF_" + name, doubleSided=True,
                      pbrMetallicRoughness=dict(baseColorFactor=lin + [alpha], metallicFactor=metal, roughnessFactor=max(rough, 0.15)))
            if alpha < 1: md["alphaMode"] = "BLEND"
            materials.append(md); mat_ix[name] = len(materials) - 1
        return mat_ix[name]
    samplers, channels = [], []
    N = 96
    times = np.array([k / N for k in range(N + 1)], dtype='<f4')          # 1 s loop = one engine cycle (slow motion)
    t_acc = None
    for o in objs:
        if o.display == "WIRE" or not o.mesh.f:
            continue
        V = np.array([to_three(v) for v in o.mesh.v], dtype='<f4')
        piv = np.array(to_three(o.origin), dtype='<f4') if (o.driver or o.motion) else (V.min(0) + V.max(0)) / 2
        V = (V - piv).astype('<f4')
        pa = add_acc(V, 5126, "VEC3", 34962, minmax=True)
        prims = []
        for mn, idx in tris(o.mesh).items():
            ia = add_acc(np.array(idx, dtype='<u4'), 5125, "SCALAR", 34963)
            prims.append(dict(attributes=dict(POSITION=pa), indices=ia, material=mat(mn)))
        meshes.append(dict(name=o.name, primitives=prims))
        nodes.append(dict(name=o.name, mesh=len(meshes) - 1, translation=[float(x) for x in piv]))
        if o.driver or o.motion:
            if t_acc is None:
                t_acc = add_acc(times, 5126, "SCALAR", minmax=True)
            ni = len(nodes) - 1
            if o.motion:
                vals = np.array([[piv[0] + m.piston_x(o.motion[0], o.motion[1], 1 + 24.0 * k / N), piv[1], piv[2]] for k in range(N + 1)], dtype='<f4')
                oa = add_acc(vals, 5126, "VEC3")
                samplers.append(dict(input=t_acc, output=oa, interpolation="LINEAR"))
                channels.append(dict(sampler=len(samplers) - 1, target=dict(node=ni, path="translation")))
            else:
                q = []
                for k in range(N + 1):
                    a = eval(o.driver, {"frame": 1 + 24.0 * k / N})
                    q.append([math.sin(a / 2), 0.0, 0.0, math.cos(a / 2)])
                oa = add_acc(np.array(q, dtype='<f4'), 5126, "VEC4")
                samplers.append(dict(input=t_acc, output=oa, interpolation="LINEAR"))
                channels.append(dict(sampler=len(samplers) - 1, target=dict(node=ni, path="rotation")))
    root = dict(name="X1_OPFPLG_1500hp", children=list(range(len(nodes))))
    nodes.append(root)
    g = dict(asset=dict(version="2.0", generator="x1_opfplg export_web.py"), scene=0, scenes=[dict(nodes=[len(nodes) - 1])],
             nodes=nodes, meshes=meshes, materials=materials, accessors=accs, bufferViews=views, buffers=[dict(byteLength=0)],
             animations=[dict(name="engine_cycle", samplers=samplers, channels=channels)])
    pad(); g["buffers"][0]["byteLength"] = len(bin_)
    js = json.dumps(g, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(bin_), 0x004E4942)); f.write(bin_)

if __name__ == "__main__":
    d, objs, report, ok = gather()
    os.makedirs(os.path.join(HERE, 'viewer'), exist_ok=True)
    binp = os.path.join(HERE, 'opf_model.bin')
    n = export_viewer(d, objs, report, ok, os.path.join(HERE, 'viewer', 'opf_model.json'), binp)
    with open(binp, 'rb') as f_, open(os.path.join(HERE, 'viewer', 'opf_model.b64.txt'), 'w') as g_:
        g_.write(base64.b64encode(f_.read()).decode())
    os.remove(binp)
    glb = os.path.join(HERE, 'X1_OPFPLG_1500hp.glb')
    export_glb(d, objs, glb)
    th = [2 * math.pi * k / 400 for k in range(400)]
    x = [m.piston_travel(t) for t in th]
    print("viewer buffer", n, "glb", os.path.getsize(glb), "travel min/max mm", round(min(x) * 1e3, 2), round(max(x) * 1e3, 2), "stroke", m.CYCLE["stroke"])
