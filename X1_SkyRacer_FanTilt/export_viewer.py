import sys, io, json, base64, numpy as np, math; sys.path.insert(0,"tools"); sys.path.insert(0,"."); from geo import load
m=load(sys.argv[1],"m"); P,E=m.build_parts()
def srgb(c): return "#%02x%02x%02x"%tuple(int(round(max(0,min(1,v))*255)) for v in c)
hinges={n:dict(loc=[round(float(v)*1000) for v in h["loc"]],axis=[round(float(v),5) for v in h["axis"]] if "axis" in h else "Y",stowed=float(h["angle"]),parent=h["parent"]) for n,h in m.HINGES.items()}
parts=[]; nv=nt=0
for p in P:
    if p.coll!="main": continue
    R=m.euler_xyz(p.rot); V=np.array([R@v+p.loc for v in p.V])
    q=np.round(V*1000).astype(np.int16)
    groups={}
    for fi,f in enumerate(p.F):
        mn=p.mats[p.M[fi]]; d=m.MATS[mn]
        if d["color"] is None:   # livery texture (body, sponsons): real UVs + the model's livery image
            key=("LIV",1.0,0.32,0.0)
        else:
            key=(srgb(d["color"]),d.get("alpha",1.0),d.get("rough",0.5),d.get("metal",0.0))
        if mn=="Glass": key=("#20262e",0.55,0.08,0.0)
        tris=groups.setdefault(key,[])
        for k in range(1,len(f)-1): tris += [f[0],f[k],f[k+1]]
    gl=[]
    for (col,alpha,rough,metal),idx in groups.items():
        a=np.array(idx,dtype=np.uint16 if len(V)<65535 else np.uint32)
        gl.append(dict(c=col,o=alpha,r=rough,m=metal,u32=a.dtype==np.uint32,i=base64.b64encode(a.tobytes()).decode()))
        nt+=len(idx)//3
    nv+=len(V)
    kind="rotor" if p.name.startswith(("Rotor_","Thruster_Fan")) else "part"
    rec=dict(n=p.name,h=p.parent,k=kind,p=base64.b64encode(q.tobytes()).decode(),g=gl)
    if getattr(p,"park",0.0):          # rotor stow index: turns about its own axis while folding
        rec["pk"]=dict(a=float(p.park),c=[round(float(v)*1000) for v in p.loc],n=[round(float(v),5) for v in R@np.array([0,0,1.0])])
    if p.UV is not None and any(g["c"]=="LIV" for g in gl):
        uv=np.clip(np.array(p.UV,float),0,1); rec["uv"]=base64.b64encode(np.round(uv*65535).astype(np.uint16).tobytes()).decode()
    parts.append(rec)
# engine bay contents from the OPFPLG model (the X1 script only carries the parts outside the bay)
import importlib, contextlib
with contextlib.redirect_stdout(open("/dev/null","w")):
    O=importlib.import_module("x1_opfplg_blender"); _d,objs=O.build(O.PRESET)
for o in objs:
    if o.coll in ("OPFPLG_External","OPFPLG_Radiators") or not o.mesh.f: continue
    vv=[tuple(v) for v in o.mesh.v]
    if o.driver and o.driver_path=="location":          # pistons as at frame 1
        k_=o.driver_index; dk=eval(o.driver.replace("frame","1"),{"cos":math.cos})-o.origin[k_]
        vv=[tuple(c+(dk if i==k_ else 0.0) for i,c in enumerate(v)) for v in vv]
    V=np.array(vv,float); q=np.round(V*1000).astype(np.int16)
    groups={}
    for f,mn in zip(o.mesh.f,o.mesh.m):
        rgb,metal,rough,alpha=O.MATS[mn]
        key=(srgb(rgb),float(alpha),float(rough),float(metal))
        tris=groups.setdefault(key,[])
        for k in range(1,len(f)-1): tris+=[f[0],f[k],f[k+1]]
    gl=[]
    for (col,alpha,rough,metal),idx in groups.items():
        a=np.array(idx,dtype=np.uint16 if len(V)<65535 else np.uint32)
        gl.append(dict(c=col,o=alpha,r=rough,m=metal,u32=a.dtype==np.uint32,i=base64.b64encode(a.tobytes()).decode()))
        nt+=len(idx)//3
    nv+=len(V)
    parts.append(dict(n=o.name,h=None,k="bay",grp=o.coll.replace("OPFPLG_",""),p=base64.b64encode(q.tobytes()).decode(),g=gl))
import io
from PIL import Image
L=m.make_livery(2048,352)[::-1,:,:3]; L=np.round(L*24)/24; buf=io.BytesIO(); Image.fromarray((np.clip(L,0,1)*255).astype(np.uint8)).quantize(16).save(buf,"PNG",optimize=True)
liv="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
meta=dict(livery=liv,rear_tilt_hover=getattr(m,"REAR_TILT_HOVER_DEG",m.LIFT_CANT_R_DEG),rear_tilt_min=getattr(m,"REAR_TILT_MIN_DEG",0),rear_tilt_max=getattr(m,"REAR_TILT_MAX_DEG",0),rear_cant=m.LIFT_CANT_R_DEG,
          pusher_tilt=m.PUSHER_TILT_DEG,wing_inc=m.WING_INCIDENCE_DEG,
          hauler=[m.RULES["folded_width_max"]*1000,m.RULES["folded_height_max"]*1000,m.RULES["length_max"]*1000])
s=json.dumps(dict(meta=meta,hinges=hinges,parts=parts),separators=(",",":"))
open(sys.argv[2],"w").write(s); print("verts",nv,"tris",nt,"json MB %.2f"%(len(s)/1e6))
