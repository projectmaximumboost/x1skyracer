"""Yonder 01 livery for the X1 SkyRacer: base paint map plus decals placed on the parts.

Writes, into <out_dir>:
  yonder_base.b64   2048 x 352 RGBA side-projected paint map for the body and sponsons (no lettering)
  decals.json       every decal: which parts, how it is projected, its box in model mm, and its PNG
  previews of each
Decals are applied by the viewer as overlays with their own projection, so lettering reads correctly
from whichever side, from above or from below. Projections (model mm: +x craft left, +y aft, +z up):
  side     faces whose outward normal points sideways; reads correctly from each side
  top      faces pointing up; reads with the nose at the top of the view, seen from above
  top-out  faces pointing up; reads from outboard of each side, text along the length
  bottom   faces pointing down; reads with the nose at the top of the view, seen from below
Boxes for left/right parts are given for the left side; the viewer mirrors them for the right.
Usage: python3 -I yonder_decals.py <logo.jpg> <out_dir>
"""
import base64
import io
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LOGO, OUT = sys.argv[1], sys.argv[2]
RED, YEL, BLUE, WHITE = (214, 18, 30), (250, 183, 0), (11, 72, 152), (246, 246, 248)
FONT_NUM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_TXT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# ---------------------------------------------------------------- base paint map (no lettering)
W, H, S = 2048, 352, 3
def X(u): return u * W * S
def Y(v): return (1 - v) * H * S
def U(y_mm): return 1.78576e-4 * y_mm + 0.499994          # the body's own side projection
def V(z_mm): return 0.00104871 * z_mm - 0.25989


base = Image.new("RGB", (W * S, H * S), RED)
d = ImageDraw.Draw(base)
def poly(pts, fill): d.polygon([(X(u), Y(v)) for u, v in pts], fill=fill)
SL = 0.035
poly([(0, -0.1), (0.118, -0.1), (0.118 + SL * 1.2, 1.1), (0, 1.1)], WHITE)                 # nose cap
poly([(0.118, -0.1), (0.136, -0.1), (0.136 + SL * 1.2, 1.1), (0.118 + SL * 1.2, 1.1)], YEL)
poly([(0.146, -0.1), (0.158, -0.1), (0.158 + SL * 1.2, 1.1), (0.146 + SL * 1.2, 1.1)], BLUE)
# white band under the windshield, above the front wing: the YONDER wordmark sits on it
b0, b1 = V(575), V(778)
a1 = U(-900)                                               # band ends ahead of the 01
poly([(0, b0 - 0.022), (a1, b0 - 0.022), (a1 + 0.03, b1 + 0.022), (0, b1 + 0.022)], YEL)
poly([(0, b0 - 0.022), (a1, b0 - 0.022), (a1 + 0.03 * 0.0, b0), (0, b0)], BLUE)
poly([(0, b0), (a1, b0), (a1 + 0.03, b1), (0, b1)], WHITE)
poly([(0.905, -0.1), (1.1, -0.1), (1.1, 1.1), (0.905 + SL * 1.2, 1.1)], BLUE)              # tail
poly([(0.885, -0.1), (0.897, -0.1), (0.897 + SL * 1.2, 1.1), (0.885 + SL * 1.2, 1.1)], YEL)
d.rectangle([0, Y(0.115), W * S, H * S], fill=BLUE)                                        # rockers
d.rectangle([0, Y(0.135), W * S, Y(0.115)], fill=YEL)
base = base.resize((W, H), Image.LANCZOS)
base.save(f"{OUT}/yonder_base_preview.png")
raw = np.flipud(np.asarray(base.convert("RGBA"), dtype=np.uint8)).copy()   # row 0 = keel
open(f"{OUT}/yonder_base.b64", "w").write(base64.b64encode(raw.tobytes()).decode())

# ---------------------------------------------------------------- decal art
a = np.asarray(Image.open(LOGO).convert("RGB")).astype(float) / 255


def cut_logo(box):
    x0, y0, x1, y1 = box
    c = a[y0:y1, x0:x1]
    alpha = np.clip((1 - c.min(2)) / 0.85, 0, 1)
    rgb = np.clip(np.where(alpha[..., None] > 1e-3, 1 - (1 - c) / np.maximum(alpha[..., None], 1e-3), 1), 0, 1)
    im = Image.fromarray((np.dstack([rgb, alpha]) * 255).astype(np.uint8), "RGBA")
    return im.crop(im.getbbox())


def plate(im, pad=0.10, bg=WHITE):
    """Logo on a rounded white plate, so the red parts of it read on red paint."""
    p = int(max(im.size) * pad)
    out = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle([0, 0, out.width - 1, out.height - 1], radius=int(p * 1.4), fill=bg + (255,))
    out.alpha_composite(im, (p, p))
    return out


def text_img(txt, font, size, fill, stroke=0, stroke_fill=None, italic=0.0):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if italic:
        im = im.transform((int(im.width + italic * im.height), im.height), Image.AFFINE,
                          (1, italic, -italic * im.height, 0, 1, 0), Image.BICUBIC)
    return im


def number01(size=600):
    num = text_img("01", FONT_NUM, size, WHITE, stroke=int(size * 0.05), stroke_fill=BLUE, italic=0.22)
    shadow = text_img("01", FONT_NUM, size, YEL, stroke=int(size * 0.05), stroke_fill=YEL, italic=0.22)
    off = int(size * 0.06)
    comp = Image.new("RGBA", (num.width + off, num.height + off), (0, 0, 0, 0))
    comp.alpha_composite(shadow, (off, off))
    comp.alpha_composite(num, (0, 0))
    return comp


mark = cut_logo((600, 130, 1240, 615))
word = cut_logo((260, 640, 1580, 890))           # YONDER without the underline
full = cut_logo((260, 130, 1580, 945))           # mark, wordmark and underline


def canvas(w_mm, h_mm, art, margin=0.05, px_per_mm=1.4, max_px=1600, stretch=False):
    k = min(px_per_mm, max_px / max(w_mm, h_mm))
    cw, ch = max(8, int(w_mm * k)), max(8, int(h_mm * k))
    bw, bh = cw * (1 - 2 * margin), ch * (1 - 2 * margin)
    if stretch:                                   # fill the box exactly (used to make the 01 taller)
        art = art.resize((max(1, int(bw)), max(1, int(bh))), Image.LANCZOS)
    else:
        f = min(bw / art.width, bh / art.height)
        art = art.resize((max(1, int(art.width * f)), max(1, int(art.height * f))), Image.LANCZOS)
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    out.alpha_composite(art, ((cw - art.width) // 2, (ch - art.height) // 2))
    return out


DECALS = [
    # car number on each side, on the fuselage and the rear window: above the sponson (z 585 mm). Placed
    # 100 mm further forward than the seat-back limit below, at Mac's call (12 Nov 2026). Originally: never ahead
    # of the plane of the seat back (aft face, y = -824 + 0.4535 (z - 303) mm, about 24 deg), clear of the rear
    # duct. Tallest that fits at this placement: 570 mm, stretched about 6 % taller than the font and wrapping
    # a little over the canopy curve. The canopy top falling away aft and the seat-back plane set the limit.
    dict(id="num_side", parts="^(Body|Canopy|Canopy_Frame|Flank_Swoosh_[LR])$", proj="side",
         nmin=0.08, box=dict(y=[-710, 196], z=[585, 1155]), art=number01(), margin=0.0, stretch=True,
         clear_glass=True),          # not on the body skin under the canopy: only on the glass itself
    # YONDER under the windshield, above the front wing, on the white band
    dict(id="yonder_side", parts="^Body$", proj="side", nmin=0.40, box=dict(y=[-2300, -950], z=[583, 770]),
         art=word, margin=0.06),
    # roof number: on the engine deck behind the canopy, across the louvres, upright with the nose forward
    # seen from above (as on the XXONE 51)
    dict(id="num_roof", parts="^(Body|Engine_Louvres)$", proj="top", nmin=0.45,
         box=dict(x=[-480, 480], y=[620, 1680]), art=number01(), margin=0.04),
    # one Y mark on the flat top of the nose, ahead of the canopy
    dict(id="mark_nose_top", parts="^Body$", proj="top", nmin=0.30, box=dict(x=[-185, 185], y=[-2705, -2432]),
         art=mark.rotate(180), margin=0.03),
    # series lettering on the sponsons
    dict(id="x1_sponson", parts="^Sponson_[LR]$", proj="side", nmin=0.40, box=dict(y=[-720, 420], z=[392, 528]),
         art=text_img("X1 RACING", FONT_TXT, 220, WHITE, italic=0.2), margin=0.04),
    # Y mark on top of each front wing (root, panel and fillet together)
    dict(id="mark_front_wing", parts="^Front_Wing(_Root|_Fillet)?_[LR]$", proj="top", nmin=0.50,
         box=dict(x=[590, 1270], y=[-1960, -1040]), art=plate(mark), margin=0.03),
    # full Yonder logo on top of each rear wing, read from outboard
    dict(id="logo_rear_wing", parts="^Rear_Wing(_Stub)?_[LR]$", proj="top-out", nmin=0.50,
         box=dict(x=[655, 1078], y=[670, 1735]), art=plate(full, pad=0.06), margin=0.03),
    # 01 under the belly
    dict(id="num_belly", parts="^Body$", proj="bottom", nmin=0.55, box=dict(x=[-640, 640], y=[-1800, 380]),
         art=number01(), margin=0.04),
    # Y mark under the belly at the rear
    dict(id="mark_belly", parts="^Body$", proj="bottom", nmin=0.55, box=dict(x=[-430, 430], y=[930, 1820]),
         art=plate(mark), margin=0.04),
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
