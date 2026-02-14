import cv2
import os
import numpy as np
from tqdm import tqdm

IMG_DIR = "images"
OUT_DIR = "images_tiled"

TILE = 1024
OVERLAP = 0.25
STEP = int(TILE * (1 - OVERLAP))

os.makedirs(OUT_DIR, exist_ok=True)

for img_name in tqdm(os.listdir(IMG_DIR)):
    if not img_name.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    img = cv2.imread(os.path.join(IMG_DIR, img_name))
    h, w = img.shape[:2]

    for y in range(0, h, STEP):
        for x in range(0, w, STEP):
            tile = img[y:y+TILE, x:x+TILE]

            # padding если меньше TILE
            pad_h = TILE - tile.shape[0]
            pad_w = TILE - tile.shape[1]

            if pad_h > 0 or pad_w > 0:
                tile = cv2.copyMakeBorder(
                    tile,
                    0, pad_h,
                    0, pad_w,
                    cv2.BORDER_CONSTANT,
                    value=(255, 255, 255)  # белый фон
                )

            out_name = f"{os.path.splitext(img_name)[0]}_{x}_{y}.jpg"
            cv2.imwrite(os.path.join(OUT_DIR, out_name), tile)
