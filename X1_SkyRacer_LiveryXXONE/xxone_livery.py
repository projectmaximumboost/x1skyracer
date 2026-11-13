"""XXONE 51 livery for the X1 SkyRacer: black stock-car scheme with red pinstripes and white lettering.

Writes, into <out_dir>:
  xxone_base.b64    2048 x 352 RGBA side-projected paint map for the body and sponsons (no lettering)
  decals.json       every decal: which parts, how it is projected, its box in model mm, and its PNG
  previews of each
Lettering is drawn here in a plain bold italic: no real company's logo, typeface or contingency decals.
Projections (model mm: +x craft left, +y aft, +z up):
  side     faces whose outward normal points sideways; reads correctly from each side
  top      faces pointing up; reads with the nose at the top of the view, seen from above
  top-out  faces pointing up; read from outboard of each side (a centred part reads from the left)
  bottom   faces pointing down; reads with the nose at the top of the view, seen from below
Boxes for left/right parts are given for the left side; the viewer mirrors them for the right.
Usage: python3 -I xxone_decals.py <out_dir>
"""
import base64
import io
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
BLACK, RED, WHITE = (16, 16, 18), (200, 16, 46), (246, 246, 248)
FONT_NUM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_TXT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# ---------------------------------------------------------------- base paint map (no lettering)
W, H, S = 2048, 352, 3
def X(u): return u * W * S
def Y(v): return (1 - v) * H * S
def U(y_mm): return 1.78576e-4 * y_mm + 0.499994          # the body's own side projection
def V(z_mm): return 0.00104871 * z_mm - 0.25989


base = Image.new("RGB", (W * S, H * S), BLACK)
d = ImageDraw.Draw(base)
# red pinstripes along the full length: one at the belt line under the lettering, one above the rocker
d.rectangle([0, Y(V(578)), W * S, Y(V(560))], fill=RED)
d.rectangle([0, Y(V(392)), W * S, Y(V(368))], fill=RED)
base = base.resize((W, H), Image.LANCZOS)
base.save(f"{OUT}/xxone_base_preview.png")
raw = np.flipud(np.asarray(base.convert("RGBA"), dtype=np.uint8)).copy()   # row 0 = keel
open(f"{OUT}/xxone_base.b64", "w").write(base64.b64encode(raw.tobytes()).decode())


# ---------------------------------------------------------------- lettering
def text_img(txt, font, size, fill, stroke=0, stroke_fill=None, italic=0.0):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if italic:
        im = im.transform((int(im.width + italic * im.height), im.height), Image.AFFINE,
                          (1, italic, -italic * im.height, 0, 1, 0), Image.BICUBIC)
    return im


def number51(size=600):
    """White 51 with a red pinstripe outline, as on the reference car."""
    return text_img("51", FONT_NUM, size, WHITE, stroke=int(size * 0.035), stroke_fill=RED, italic=0.12)


def word(txt, size=300):
    return text_img(txt, FONT_TXT, size, WHITE, italic=0.22)


def canvas(w_mm, h_mm, art, margin=0.05, px_per_mm=1.4, max_px=1600, stretch=False):
    k = min(px_per_mm, max_px / max(w_mm, h_mm))
    cw, ch = max(8, int(w_mm * k)), max(8, int(h_mm * k))
    bw, bh = cw * (1 - 2 * margin), ch * (1 - 2 * margin)
    if stretch:
        art = art.resize((max(1, int(bw)), max(1, int(bh))), Image.LANCZOS)
    else:
        f = min(bw / art.width, bh / art.height)
        art = art.resize((max(1, int(art.width * f)), max(1, int(art.height * f))), Image.LANCZOS)
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(art, ((cw - art.width) // 2, (ch - art.height) // 2))
    return out


DECALS = [
    # door number: same place as the Yonder 01 (behind the cockpit, above the sponson), on the body, the rear
    # window, the canopy frame and the flank swoosh; left off the body skin under the canopy glass
    dict(id="num_side", parts="^(Body|Canopy|Canopy_Frame|Flank_Swoosh_[LR])$", proj="side", nmin=0.08,
         box=dict(y=[-710, 196], z=[585, 1155]), art=number51(), margin=0.0, stretch=True, clear_glass=True),
    # roof number: on the engine deck behind the canopy, across the louvres, upright with the nose forward
    # seen from above (turned 90 deg from reading off the left side, 12 Nov 2026)
    dict(id="num_roof", parts="^(Body|Engine_Louvres)$", proj="top", nmin=0.45,
         box=dict(x=[-480, 480], y=[620, 1680]), art=number51(), margin=0.04),
    # XXONE ahead: under the windscreen, above the front wing
    dict(id="xxone_front", parts="^Body$", proj="side", nmin=0.40, box=dict(y=[-2300, -950], z=[583, 770]),
         art=word("XXONE"), margin=0.05),
    # XXONE on the rear quarter, behind the number and below the rear duct
    dict(id="xxone_rear", parts="^(Body|Flank_Swoosh_[LR])$", proj="side", nmin=0.40,
         box=dict(y=[280, 1750], z=[592, 822]), art=word("XXONE"), margin=0.04),
    # ALUMINA on the rear flank between the two red pinstripes, behind the sponson and below the rear duct.
    # The nose is too small to hold it whole (its ends were cut off, leaving a word we must not show).
    dict(id="alumina_rear", parts="^Body$", proj="side", nmin=0.40, box=dict(y=[530, 1420], z=[419, 558]),
         art=word("ALUMINA", 220), margin=0.02),
    # series lettering on the sponsons
    dict(id="x1_sponson", parts="^Sponson_[LR]$", proj="side", nmin=0.40, box=dict(y=[-720, 420], z=[392, 528]),
         art=text_img("X1 RACING", FONT_TXT, 220, WHITE, italic=0.2), margin=0.04),
    # XXONE on top of each front wing (the hood) and each rear wing (the spoiler), read from outboard
    dict(id="xxone_front_wing", parts="^Front_Wing(_Root|_Fillet)?_[LR]$", proj="top-out", nmin=0.50,
         box=dict(x=[590, 1270], y=[-1960, -1040]), art=word("XXONE"), margin=0.05),
    dict(id="xxone_rear_wing", parts="^Rear_Wing(_Stub)?_[LR]$", proj="top-out", nmin=0.50,
         box=dict(x=[655, 1078], y=[670, 1735]), art=word("XXONE"), margin=0.05),
    # 51 under the belly, XXONE under the rear belly, nose-up seen from below
    dict(id="num_belly", parts="^Body$", proj="bottom", nmin=0.55, box=dict(x=[-640, 640], y=[-1800, 380]),
         art=number51(), margin=0.04),
    dict(id="xxone_belly", parts="^Body$", proj="bottom", nmin=0.55, box=dict(x=[-430, 430], y=[930, 1820]),
         art=word("XXONE"), margin=0.05),
]

out = []
for dcl in DECALS:
    b = dcl["box"]
    if dcl["proj"] == "side":
        w, h = b["y"][1] - b["y"][0], b["z"][1] - b["z"][0]
    elif dcl["proj"] == "top-out":
        w, h = b["y"][1] - b["y"][0], b["x"][1] - b["x"][0]
    else:
        w, h = b["x"][1] - b["x"][0], b["y"][1] - b["y"][0]
    img = canvas(w, h, dcl["art"], margin=dcl.get("margin", 0.05), stretch=dcl.get("stretch", False))
    img.save(f"{OUT}/decal_{dcl['id']}.png")
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    out.append(dict(id=dcl["id"], parts=dcl["parts"], proj=dcl["proj"], nmin=dcl["nmin"], box=b,
                    clear_glass=dcl.get("clear_glass", False),
                    png="data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()))
json.dump(out, open(f"{OUT}/decals.json", "w"))
print("ok", len(out), "decals,", sum(len(o["png"]) for o in out) // 1024, "KB")
