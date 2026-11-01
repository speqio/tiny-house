"""Genera texturas derivadas para el modelo.

- Pintura del casco: recolorea PaintedMetal006 (CC0, ambientCG); las zonas de pintura
  (verde-turquesa) se llevan al tono objetivo y el óxido se conserva.
- Celdas del panel FV: grilla de 6 x 10 celdas monocristalinas (panel de 0,65 x 1,16 m).
- Azulejos de baño de 15 x 15 cm.
Uso: python blender/generate_textures.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "textures", "PaintedMetal006", "PaintedMetal006_1K-JPG_Color.jpg")
OUT = os.path.join(HERE, "textures", "generated")

# tono (0..1), factor de saturación y de brillo para la pintura
TARGETS = {"hull_yellow": (0.125, 1.05, 1.35), "hull_blue": (0.60, 0.85, 0.75)}

hsv = np.asarray(Image.open(SRC).convert("HSV")).astype(np.float32) / 255
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
paint = ((h > 0.33) & (h < 0.62) & (s > 0.2)).astype(np.uint8) * 255
# borde suave entre pintura y óxido
size = paint.shape[::-1]
mask = np.asarray(Image.fromarray(paint).resize((256, 256), Image.BILINEAR).resize(size, Image.BILINEAR)) / 255
# se expande la pintura para dejar un óxido más moderado
mask = np.clip(mask * 2.2, 0, 1)

os.makedirs(OUT, exist_ok=True)
for name, (th, ks, kv) in TARGETS.items():
    nh = np.where(mask > 0.5, th, h)
    ns = np.clip(s * (mask * ks + (1 - mask)), 0, 1)
    nv = np.clip(v * (mask * kv + (1 - mask)), 0, 1)
    img = Image.fromarray((np.stack([nh, ns, nv], -1) * 255).astype(np.uint8), "HSV").convert("RGB")
    img.save(os.path.join(OUT, f"{name}_Color.jpg"), quality=90)
    print(name)

# celdas FV: 6 columnas (lado de 0,65 m) x 10 filas (lado de 1,16 m)
W, H, COLS, ROWS, GAP = 390, 696, 6, 10, 4
pv = Image.new("RGB", (W, H), (205, 210, 215))
d = ImageDraw.Draw(pv)
cw, ch = (W - GAP) / COLS, (H - GAP) / ROWS
for c in range(COLS):
    for r in range(ROWS):
        x0, y0 = GAP + c * cw, GAP + r * ch
        d.rectangle([x0, y0, x0 + cw - GAP, y0 + ch - GAP], fill=(22, 34, 66))
        for k in (1, 2, 3):  # barras colectoras
            bx = x0 + k * (cw - GAP) / 4
            d.line([bx, y0, bx, y0 + ch - GAP], fill=(120, 130, 150), width=1)
pv.save(os.path.join(OUT, "pv_cells_Color.jpg"), quality=92)
print("pv_cells")

# azulejos de baño: 4 x 4 piezas de 15 cm (una repetición = 0,6 m)
N, PX, GROUT = 4, 512, 3
tiles = Image.new("RGB", (PX, PX), (176, 182, 188))
d = ImageDraw.Draw(tiles)
step = PX / N
for i in range(N):
    for j in range(N):
        tone = 238 + ((i * 7 + j * 3) % 5) * 2
        d.rectangle([i * step + GROUT, j * step + GROUT, (i + 1) * step - GROUT, (j + 1) * step - GROUT], fill=(tone, tone, tone + 2))
tiles.save(os.path.join(OUT, "tiles_Color.jpg"), quality=92)
print("tiles")
