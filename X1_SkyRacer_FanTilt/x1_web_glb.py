"""
X1 SkyRacer -> web GLB (no Blender needed)
=======================================
Writes X1_SkyRacer_FanTilt_web.glb, the model the web viewers and the X1_sim flight simulator load:
  * every part as its own node, rotors / fans / wheels pivoting on their spin axes
  * hinge nodes for the wing / duct fold, so the fold is a real rigid-body motion
  * animations: "Fans" (all 10 fans spinning, loops), "Fold" and "Unfold" (3 s)
  * PBR materials from the Blender palette, livery texture on the body
  * simulator cockpit: Screen_Display keeps its 0..1 UVs (draw instruments on it), and empty nodes mark
    Eye_L / Eye_R (design eye points), Screen_Centre and Stick_Pivot

Run:  python3 x1_web_glb.py      (needs numpy and Pillow; x1_skyracer_blender.py and x1_opfplg_blender.py
                                 next to this file or in the folder above it)
"""
import io
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import x1_skyracer_blender as X1  # noqa: E402

OUT = os.path.join(HERE, "X1_SkyRacer_FanTilt_web.glb")
FOLD_S = 3.0
FAN_REV_S = 0.5          # seconds per revolution in the "Fans" animation

# Blender (x, y, z) -> glTF (x, z, -y): Z-up to Y-up, nose (-Y) to +Z
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)


def quat_from_matrix(R):
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2
    y = math.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2
    z = math.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2
    x = math.copysign(x, R[2, 1] - R[1, 2])
    y = math.copysign(y, R[0, 2] - R[2, 0])
    z = math.copysign(z, R[1, 0] - R[0, 1])
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


def quat_axis_angle(axis, a):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    s = math.sin(a / 2)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, math.cos(a / 2)])


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw,
                     aw * bw - ax * bx - ay * by - az * bz])


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.g = dict(asset=dict(version="2.0", generator="x1_web_glb.py"), scene=0, scenes=[dict(nodes=[])],
                      nodes=[], meshes=[], materials=[], accessors=[], bufferViews=[], buffers=[],
                      animations=[], textures=[], images=[], samplers=[])

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        off = len(self.bin)
        self.bin += data
        bv = dict(buffer=0, byteOffset=off, byteLength=len(data))
        if target:
            bv["target"] = target
        self.g["bufferViews"].append(bv)
        return len(self.g["bufferViews"]) - 1

    def accessor(self, arr, comp, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        bv = self.view(arr.tobytes(), target)
        a = dict(bufferView=bv, componentType=comp, count=int(arr.shape[0]), type=typ)
        if minmax:
            a["min"] = [float(v) for v in arr.min(0)] if arr.ndim > 1 else [float(arr.min())]
            a["max"] = [float(v) for v in arr.max(0)] if arr.ndim > 1 else [float(arr.max())]
        self.g["accessors"].append(a)
        return len(self.g["accessors"]) - 1

    def node(self, **kw):
        self.g["nodes"].append(kw)
        return len(self.g["nodes"]) - 1

    def write(self, path):
        g = {k: v for k, v in self.g.items() if v != []}
        g["buffers"] = [dict(byteLength=len(self.bin))]
        js = json.dumps(g, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        while len(self.bin) % 4:
            self.bin += b"\0"
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin))
        return total


def part_mesh(gb, p, mat_ids, tex_mat):
    """One glTF mesh per part, one primitive per material. Normals: smooth with a crease angle."""
    V = np.array([C @ v for v in p.V], float)
    tris, tmat = [], []
    for fi, f in enumerate(p.F):
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
            tmat.append(p.M[fi])
    T = np.array(tris, int)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    area = np.linalg.norm(fn, axis=1)
    keep = area > 1e-12
    T, fn, area, tmat = T[keep], fn[keep], area[keep], np.array(tmat)[keep]
    fu = fn / area[:, None]
    vn = np.zeros_like(V)
    for c in range(3):
        np.add.at(vn, T[:, c], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]
    cos_lim = math.cos(math.radians(p.split if p.smooth else 0.0))
    prims = []
    for m in sorted(set(tmat.tolist())):
        sel = np.where(tmat == m)[0]
        pos, nor, uvs, idx, seen = [], [], [], [], {}
        textured = tex_mat is not None and p.mats[m] == "Livery" and p.UV is not None
        has_uv = p.UV is not None and (textured or p.mats[m] == "Screen")   # the dash screen keeps its 0..1 UVs
        for t in sel:
            for c in range(3):
                vi = T[t, c]
                smooth = p.smooth and float(vn[vi] @ fu[t]) >= cos_lim
                key = (vi, -1) if smooth else (vi, t)
                j = seen.get(key)
                if j is None:
                    j = seen[key] = len(pos)
                    pos.append(V[vi])
                    nor.append(vn[vi] if smooth else fu[t])
                    if has_uv:
                        u, v = p.UV[vi]
                        uvs.append((u, 1 - v))
                idx.append(j)
        attrs = dict(POSITION=gb.accessor(np.array(pos, np.float32), 5126, "VEC3", 34962, True),
                     NORMAL=gb.accessor(np.array(nor, np.float32), 5126, "VEC3", 34962))
        if has_uv:
            attrs["TEXCOORD_0"] = gb.accessor(np.array(uvs, np.float32), 5126, "VEC2", 34962)
        it = np.array(idx, np.uint32 if len(pos) > 65535 else np.uint16)
        ind = gb.accessor(it, 5125 if it.dtype == np.uint32 else 5123, "SCALAR", 34963)
        prims.append(dict(attributes=attrs, indices=ind, material=tex_mat if textured else mat_ids[p.mats[m]]))
    gb.g["meshes"].append(dict(name=p.name, primitives=prims))
    return len(gb.g["meshes"]) - 1


def main():
    parts, empties = X1.build_parts()
    gb = GLB()

    # materials
    mat_ids = {}
    for name, d in X1.MATS.items():
        if d["color"] is None:
            continue
        base = list(srgb_to_linear(d["color"])) + [d.get("alpha", 1.0)]
        m = dict(name=name, pbrMetallicRoughness=dict(baseColorFactor=[float(c) for c in base],
                                                      metallicFactor=d["metal"], roughnessFactor=d["rough"]))
        if "emit" in d:
            m["emissiveFactor"] = [float(c) for c in srgb_to_linear(d["emit"])]
        if "alpha" in d:
            m["alphaMode"] = "BLEND"
            m["doubleSided"] = True
        gb.g["materials"].append(m)
        mat_ids[name] = len(gb.g["materials"]) - 1
    liv = X1.make_livery(W=2048, H=320)
    buf = io.BytesIO()
    Image.fromarray((np.flipud(liv[..., :3]) * 255).astype(np.uint8)).save(buf, "PNG", optimize=True)
    img_bv = gb.view(buf.getvalue())
    gb.g["images"].append(dict(bufferView=img_bv, mimeType="image/png"))
    gb.g["samplers"].append(dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071))
    gb.g["textures"].append(dict(sampler=0, source=0))
    d = X1.MATS["Livery"]
    gb.g["materials"].append(dict(name="Livery", pbrMetallicRoughness=dict(
        baseColorTexture=dict(index=0), metallicFactor=d["metal"], roughnessFactor=d["rough"])))
    tex_mat = len(gb.g["materials"]) - 1
    for name in X1.MATS:                      # parts that name "Livery" without UVs fall back to white
        mat_ids.setdefault(name, mat_ids["Paint_White"])

    # hinge nodes (rest pose), children wired below
    root = gb.node(name="X1_SkyRacer", children=[])
    gb.g["scenes"][0]["nodes"].append(root)
    hinge_node = {}
    for h in sorted(X1.HINGES, key=lambda k: len(X1.hinge_chain(k))):
        info = X1.HINGES[h]
        parent = info["parent"]
        ploc = X1.HINGES[parent]["loc"] if parent else np.zeros(3)
        n = gb.node(name=h, translation=[float(v) for v in C @ (info["loc"] - ploc)], children=[])
        hinge_node[h] = n
        gb.g["nodes"][hinge_node[parent] if parent else root]["children"].append(n)

    spin_nodes = []                           # (node, rest quaternion, spin sign)
    park_nodes = []                           # (node, rest quaternion, stow index angle)
    spin = {"FL_Upper": 1, "FL_Lower": -1, "FR_Upper": -1, "FR_Lower": 1,
            "RL_Upper": -1, "RL_Lower": 1, "RR_Upper": 1, "RR_Lower": -1}   # +1 = CCW from above
    for p in parts:
        if p.coll != "main" or not p.F:
            continue
        mesh = part_mesh(gb, p, mat_ids, tex_mat)
        q = quat_from_matrix(C @ X1.euler_xyz(p.rot) @ C.T)
        ref = X1.HINGES[p.parent]["loc"] if p.parent else np.zeros(3)
        n = gb.node(name=p.name, mesh=mesh, translation=[float(v) for v in C @ (np.asarray(p.loc) - ref)],
                    rotation=[float(v) for v in q])
        gb.g["nodes"][hinge_node[p.parent] if p.parent else root]["children"].append(n)
        key = p.name.replace("Rotor_", "")
        if p.name.startswith("Rotor_"):
            spin_nodes.append((n, q, spin[key]))
            if getattr(p, "park", 0.0):
                park_nodes.append((n, q, p.park))
        elif p.name.startswith("Thruster_Fan_"):
            spin_nodes.append((n, q, 1 if p.name.endswith("L") else -1))
    # cockpit reference points for simulators: empty nodes (no mesh) at the design eye points, the centre
    # of the dash screen and the stick pivot
    for name, pos in empties.items():
        if name.startswith(("Eye_", "Screen_", "Stick_")):
            n = gb.node(name=name, translation=[float(v) for v in C @ np.asarray(pos, float)])
            gb.g["nodes"][root]["children"].append(n)
    for n in gb.g["nodes"]:
        if n.get("children") == []:
            del n["children"]

    # animations
    def anim(name, channels):
        samplers, chans = [], []
        for node, times, quats in channels:
            ti = gb.accessor(np.array(times, np.float32), 5126, "SCALAR", None, True)
            qo = gb.accessor(np.array(quats, np.float32), 5126, "VEC4")
            samplers.append(dict(input=ti, output=qo, interpolation="LINEAR"))
            chans.append(dict(sampler=len(samplers) - 1, target=dict(node=node, path="rotation")))
        gb.g["animations"].append(dict(name=name, samplers=samplers, channels=chans))

    steps = 8
    fan_t = [FAN_REV_S * k / steps for k in range(steps + 1)]
    up = C @ np.array([0, 0, 1.0])              # part-local spin axis (Blender local Z) in glTF
    anim("Fans", [(n, fan_t, [qmul(q0, quat_axis_angle(up, sgn * 2 * math.pi * k / steps)) for k in range(steps + 1)])
                  for n, q0, sgn in spin_nodes])
    hinge_axis = C @ np.array([0, 1.0, 0])      # Blender rot_y
    fold_t = [FOLD_S * k / 12 for k in range(13)]
    ease = [0.5 - 0.5 * math.cos(math.pi * k / 12) for k in range(13)]
    fold = [(hinge_node[h], fold_t, [quat_axis_angle(C @ np.asarray(X1.HINGES[h]["axis"]) if "axis" in X1.HINGES[h]
                                                     else hinge_axis, X1.HINGES[h]["angle"] * e) for e in ease])
            for h in X1.HINGES]
    # rotors with a stow index turn to it during the first quarter of the fold
    fold += [(n, fold_t, [qmul(q0, quat_axis_angle(up, park * min(1.0, 4 * e))) for e in ease])
             for n, q0, park in park_nodes]
    anim("Fold", fold)
    anim("Unfold", [(n, t, list(reversed(qs))) for n, t, qs in fold])

    size = gb.write(OUT)
    print(f"wrote {OUT}: {size / 1e6:.2f} MB, {len(gb.g['meshes'])} meshes, "
          f"{len(spin_nodes)} spinning fans, {len(X1.HINGES)} hinges")


if __name__ == "__main__":
    main()
