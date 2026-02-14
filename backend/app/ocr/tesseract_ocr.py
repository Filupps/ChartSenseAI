import re
from typing import Any, Dict, List, Optional

import pytesseract
from PIL import Image, ImageOps

import cv2
import numpy as np

from app.core.config import settings


class TesseractOCR:
    """OCR для извлечения текста из регионов изображения"""

    _KEEP_SHORT = frozenset(
        "и в к с а о у я на по из до за не ни но да ну от об во ко со же ли бы "
        "if or no do is it on at to by up we he me my us so an am".split()
    )

    def __init__(self):
        self.lang = settings.TESSERACT_LANG
        self.psm = settings.TESSERACT_PSM

    def extract_text(self, image_region: Image.Image, bbox: Optional[list] = None, class_name: str = "") -> str:
        try:
            if bbox is not None:
                image_region = self._crop_with_padding(image_region, bbox, pad_ratio=0.08, pad_px=4)
                image_region = self._trim_shape_border(image_region, class_name)

            variants = self._make_preprocessing_variants(image_region)

            best_text = ""
            best_score = 0

            for pre in variants:
                text = self._run_tesseract(pre, psm=self.psm)
                score = self._score_text(text)

                if score < 3:
                    for fallback_psm in (7, 11, 13):
                        t = self._run_tesseract(pre, psm=fallback_psm)
                        s = self._score_text(t)
                        if s > score:
                            text, score = t, s

                if score > best_score:
                    best_text, best_score = text, score

            return self._postprocess_text(best_text)
        except Exception as e:
            print(f"OCR error: {e}")
            return ""

    def _run_tesseract(self, img: Image.Image, psm: int) -> str:
        config = f"--oem 3 --psm {psm} -l {self.lang} -c preserve_interword_spaces=1"
        return pytesseract.image_to_string(img, config=config)

    def _score_text(self, text: str) -> int:
        if not text:
            return 0
        alnum = len(re.findall(r"[A-Za-zА-Яа-яёЁ0-9]", text))
        junk = len(re.findall(r"[|~^<>\[\]{}©®™#\\_=+]", text))
        return max(0, alnum - junk)

    def _crop_with_padding(self, image: Image.Image, bbox: list, pad_ratio: float, pad_px: int) -> Image.Image:
        x1, y1, x2, y2 = map(int, bbox)
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        pad_x = int(w * pad_ratio) + pad_px
        pad_y = int(h * pad_ratio) + pad_px

        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(image.width, x2 + pad_x)
        y2 = min(image.height, y2 + pad_y)
        return image.crop((x1, y1, x2, y2))

    def _trim_shape_border(self, img: Image.Image, class_name: str = "") -> Image.Image:
        w, h = img.size
        if w < 12 or h < 12:
            return img

        cn = class_name.lower()

        if "circle" in cn or "ellipse" in cn:
            trim = 0.18
            cx, cy = w / 2, h / 2
            rx, ry = w * (0.5 - trim), h * (0.5 - trim)
            x1 = max(0, int(cx - rx))
            y1 = max(0, int(cy - ry))
            x2 = min(w, int(cx + rx))
            y2 = min(h, int(cy + ry))
            if x2 - x1 > 10 and y2 - y1 > 10:
                return img.crop((x1, y1, x2, y2))
            return img

        if "diamond" in cn:
            trim_x = max(8, int(w * 0.15))
            trim_y = max(8, int(h * 0.15))
        elif "text" in cn:
            trim_x = 2
            trim_y = 2
        else:
            trim_x = max(3, int(w * 0.04))
            trim_y = max(3, int(h * 0.04))

        if w > 2 * trim_x and h > 2 * trim_y:
            return img.crop((trim_x, trim_y, w - trim_x, h - trim_y))
        return img

    def _ensure_black_on_white(self, thr: np.ndarray) -> np.ndarray:
        if np.mean(thr) < 127:
            return cv2.bitwise_not(thr)
        return thr

    def _make_preprocessing_variants(self, img: Image.Image) -> List[Image.Image]:
        variants = [
            self._preprocess_otsu(img),
            self._preprocess_adaptive(img),
        ]
        return variants

    def _upscale(self, img: Image.Image) -> Image.Image:
        target_h = 300
        if img.height < target_h:
            scale = target_h / max(1, img.height)
            new_w = max(1, int(img.width * scale))
            img = img.resize((new_w, target_h), Image.Resampling.LANCZOS)
        return img

    def _add_white_border(self, arr: np.ndarray, px: int = 12) -> np.ndarray:
        return cv2.copyMakeBorder(arr, px, px, px, px, cv2.BORDER_CONSTANT, value=255)

    def _preprocess_otsu(self, img: Image.Image) -> Image.Image:
        img = self._upscale(img)
        gray = np.array(img.convert("L"))

        pil_gray = ImageOps.autocontrast(Image.fromarray(gray), cutoff=1)
        gray = np.array(pil_gray)

        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        thr = self._ensure_black_on_white(thr)
        thr = self._add_white_border(thr)
        return Image.fromarray(thr)

    def _preprocess_adaptive(self, img: Image.Image) -> Image.Image:
        img = self._upscale(img)
        gray = np.array(img.convert("L"))

        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        block_size = max(15, (min(gray.shape) // 10) | 1)
        thr = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 8
        )

        thr = self._ensure_black_on_white(thr)
        thr = self._add_white_border(thr)
        return Image.fromarray(thr)

    def _postprocess_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text).strip()

        text = text.replace("|", "l")
        text = text.replace("}", ")")
        text = text.replace("{", "(")

        text = re.sub(r'[~^<>\[\]©®™#\\=+]+', '', text)

        text = re.sub(r'^\s*[\-_.:;,!?/\\|*`\'\"]+\s*', '', text)
        text = re.sub(r'\s*[\-_.:;,!?/\\|*`\'\"]+\s*$', '', text)

        text = re.sub(r'\s+', ' ', text).strip()

        words = text.split()
        while words and len(words[0]) <= 2 and words[0].lower() not in self._KEEP_SHORT:
            words.pop(0)
        while words and len(words[-1]) <= 2 and words[-1].lower() not in self._KEEP_SHORT:
            words.pop()

        return ' '.join(words)

    def extract_text_from_regions(
        self,
        image: Image.Image,
        text_regions: list[Dict[str, Any]]
    ) -> Dict[str, str]:
        results: Dict[str, Any] = {}
        for i, region in enumerate(text_regions):
            bbox = region.get("bbox")
            if bbox:
                text = self.extract_text(image, bbox, class_name=region.get("class_name", ""))
                region_id = f"region_{i}"
                results[region_id] = {
                    "text": text,
                    "bbox": bbox,
                    "class_name": region.get("class_name", ""),
                    "confidence": region.get("confidence", 0.0)
                }
        return results


_ocr_instance = None


def get_ocr() -> TesseractOCR:
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = TesseractOCR()
    return _ocr_instance
