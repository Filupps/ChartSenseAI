import re
from typing import Any, Dict, Optional

import pytesseract
from PIL import Image, ImageOps

import cv2
import numpy as np

from app.core.config import settings


class TesseractOCR:
    """OCR для извлечения текста из регионов изображения"""
    
    def __init__(self):
        self.lang = settings.TESSERACT_LANG
        self.psm = settings.TESSERACT_PSM
    
    def extract_text(self, image_region: Image.Image, bbox: Optional[list] = None) -> str:
        """
        Извлечение текста из региона изображения
        
        Args:
            image_region: PIL Image (может быть обрезанное изображение или полное)
            bbox: опциональные координаты [x1, y1, x2, y2] для обрезки
            
        Returns:
            Извлеченный текст
        """
        """
        Важно: OCR применяется только к региону (crop), а не ко всему изображению.
        Для качества применяем:
        - padding bbox, чтобы не обрезать буквы
        - trim border, чтобы толстые рамки не ломали OCR
        - upscale маленьких регионов
        - предобработку (autocontrast + Otsu)
        - fallback psm, если текст пустой
        """
        try:
            if bbox is not None:
                image_region = self._crop_with_padding(image_region, bbox, pad_ratio=0.10, pad_px=6)
                image_region = self._trim_border(image_region, px=5)

            pre = self._preprocess_for_ocr(image_region)

            # основной проход
            text = self._run_tesseract(pre, psm=self.psm)

            # fallback если пусто/почти пусто
            if self._score_text(text) < 3:
                candidates = [
                    self._run_tesseract(pre, psm=7),   # одна строка
                    self._run_tesseract(pre, psm=11),  # sparse text
                ]
                text = max([text, *candidates], key=self._score_text)

            return self._postprocess_text(text)
        except Exception as e:
            print(f"OCR error: {e}")
            return ""

    def _run_tesseract(self, img: Image.Image, psm: int) -> str:
        # OEM 3 = default LSTM/legacy combo, стабильно для смешанного rus+eng
        config = f"--oem 3 --psm {psm} -l {self.lang} -c preserve_interword_spaces=1"
        return pytesseract.image_to_string(img, config=config)

    def _score_text(self, text: str) -> int:
        if not text:
            return 0
        # считаем "полезные" символы
        return len(re.findall(r"[A-Za-zА-Яа-я0-9]", text))

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

    def _trim_border(self, img: Image.Image, px: int) -> Image.Image:
        if img.width <= 2 * px or img.height <= 2 * px:
            return img
        return img.crop((px, px, img.width - px, img.height - px))

    def _preprocess_for_ocr(self, img: Image.Image) -> Image.Image:
        """
        Предобработка под OCR:
        - upscale маленьких регионов
        - grayscale + autocontrast
        - Otsu threshold для контраста
        """
        # upscale до "читабельной" высоты
        target_h = 220
        if img.height < target_h:
            scale = target_h / max(1, img.height)
            new_w = max(1, int(img.width * scale))
            img = img.resize((new_w, target_h), Image.Resampling.LANCZOS)

        img = img.convert("L")
        img = ImageOps.autocontrast(img)

        arr = np.array(img)
        # лёгкое сглаживание от шумов
        arr = cv2.GaussianBlur(arr, (3, 3), 0)
        _, thr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return Image.fromarray(thr)
    
    def _postprocess_text(self, text: str) -> str:
        """
        Постобработка текста для исправления частых ошибок
        
        Args:
            text: исходный текст
            
        Returns:
            Обработанный текст
        """
        if not text:
            return ""
        
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)
        
        # Лёгкие нормализации частых OCR-артефактов
        text = text.replace("|", "l")
        
        # Удаление пробелов в начале и конце
        text = text.strip()
        
        return text
    
    def extract_text_from_regions(
        self, 
        image: Image.Image, 
        text_regions: list[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Извлечение текста из множества регионов
        
        Args:
            image: полное изображение
            text_regions: список регионов с ключами 'bbox' и 'class_name'
            
        Returns:
            Словарь {region_id: text}
        """
        results: Dict[str, Any] = {}
        
        for i, region in enumerate(text_regions):
            bbox = region.get("bbox")
            if bbox:
                text = self.extract_text(image, bbox)
                region_id = f"region_{i}"
                results[region_id] = {
                    "text": text,
                    "bbox": bbox,
                    "class_name": region.get("class_name", ""),
                    "confidence": region.get("confidence", 0.0)
                }
        
        return results


# Глобальный экземпляр OCR
_ocr_instance = None


def get_ocr() -> TesseractOCR:
    """Получить глобальный экземпляр OCR (singleton)"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = TesseractOCR()
    return _ocr_instance



