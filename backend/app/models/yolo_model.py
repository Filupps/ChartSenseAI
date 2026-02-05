from ultralytics import YOLO
from PIL import Image
import torch
from typing import List, Dict, Any
from pathlib import Path
from app.core.config import settings


class YOLOModel:
    """YOLO модель для детекции элементов диаграммы"""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f" YOLO Model initializing on device: {self.device.upper()}")
        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели YOLO из папки models в корне проекта"""
        model_path = Path(settings.MODEL_PATH)
        fallback_path = Path(settings.MODEL_FALLBACK)
        models_dir = Path(settings.MODELS_DIR)
        
        # Создаем папку models если её нет
        models_dir.mkdir(exist_ok=True)
        
        print(f" Models directory: {models_dir}")
        
        # Пробуем загрузить кастомную модель
        if model_path.exists():
            # Проверяем, что файл не пустой
            if model_path.stat().st_size > 1000:  # Минимум 1KB
                try:
                    print(f" Loading custom model: {model_path.name}")
                    self.model = YOLO(str(model_path))
                    print(f" Model loaded successfully")
                except Exception as e:
                    print(f"  Failed to load custom model: {e}")
                    print(f"   Switching to fallback model...")
                    self.model = None
            else:
                print(f" Custom model file is empty or corrupted: {model_path.name}")
                print(f"   File size: {model_path.stat().st_size} bytes")
                print(f"   Switching to fallback model...")
        
        
        if self.model is None:
            if fallback_path.exists() and fallback_path.stat().st_size > 1000:
                print(f" Loading fallback model: {fallback_path.name}")
                self.model = YOLO(str(fallback_path))
            else:
                # Скачиваем и сохраняем в папку models
                model_name = fallback_path.name  
                print(f"  Downloading {model_name} to {models_dir}...")
                self.model = YOLO(model_name)
                
                # Копируем загруженную модель в папку models
                import shutil
                downloaded_model = Path.home() / ".ultralytics" / "weights" / model_name
                if downloaded_model.exists():
                    shutil.copy(downloaded_model, fallback_path)
                    print(f" Model saved to: {fallback_path}")
        
        # Перемещаем модель на нужное устройство
        self.model.to(self.device)
        print(f" Model loaded successfully on {self.device.upper()}")
    
    def predict(self, image: Image.Image, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Предсказание bounding boxes для элементов диаграммы
        
        Args:
            image: PIL Image
            conf_threshold: порог уверенности
            
        Returns:
            List of dicts with keys: 'bbox', 'class', 'confidence', 'class_name'
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Инференс
        results = self.model(image, conf=conf_threshold, device=self.device)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                # Получаем координаты bbox (xyxy format)
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                class_name = self.model.names[class_id]
                
                detections.append({
                    "bbox": bbox,  # [x1, y1, x2, y2]
                    "class": class_id,
                    "confidence": confidence,
                    "class_name": class_name
                })
        
        return detections
    
    def get_text_regions(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует детекции, оставляя только текстовые регионы
        
        Args:
            detections: список детекций от predict()
            
        Returns:
            Отфильтрованные детекции с текстовыми элементами
        """
    
        text_classes = ["text", "label", "text_region", "text_box"]
        
        text_regions = []
        for det in detections:
            if det["class_name"].lower() in text_classes:
                text_regions.append(det)
        
        return text_regions
    
    def get_shape_elements(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует детекции, оставляя только элементы формы (прямоугольники, ромбы, круги)
        
        Args:
            detections: список детекций от predict()
            
        Returns:
            Отфильтрованные детекции с элементами формы
        """
        # Классы элементов диаграммы
        shape_classes = ["rectangle", "diamond", "circle", "ellipse", "process", "decision", "start", "end"]
        
        shape_elements = []
        for det in detections:
            class_name = det["class_name"].lower()
            if any(shape in class_name for shape in shape_classes):
                shape_elements.append(det)
        
        return shape_elements
    
    def get_arrows(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует детекции, оставляя только стрелки
        
        Args:
            detections: список детекций от predict()
            
        Returns:
            Отфильтрованные детекции со стрелками
        """
        arrow_classes = ["arrow", "line", "connection", "edge"]
        
        arrows = []
        for det in detections:
            class_name = det["class_name"].lower()
            if any(arrow in class_name for arrow in arrow_classes):
                arrows.append(det)
        
        return arrows


# Глобальный экземпляр модели
_yolo_model = None


def get_yolo_model() -> YOLOModel:
    """Получить глобальный экземпляр модели YOLO (singleton)"""
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLOModel()
    return _yolo_model


def get_model_info() -> Dict[str, Any]:
    """Получить информацию о загруженной модели"""
    global _yolo_model
    if _yolo_model is None or _yolo_model.model is None:
        return {"model_name": "not_loaded", "device": "unknown"}
    
    model_path = Path(settings.MODEL_PATH)
    fallback_path = Path(settings.MODEL_FALLBACK)
    
    if model_path.exists() and model_path.stat().st_size > 1000:
        model_name = model_path.name
    else:
        model_name = fallback_path.name
    
    return {
        "model_name": model_name,
        "device": _yolo_model.device
    }

