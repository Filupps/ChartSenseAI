from PIL import Image
from typing import Dict, Any
import numpy as np
from app.models.yolo_model import get_yolo_model
from app.ocr.tesseract_ocr import get_ocr
from app.graph.builder import build_graph_from_detections
from app.algo.generator import generate_algorithm_from_graph


def convert_to_json_serializable(obj):
    """Конвертирует numpy типы в JSON-совместимые"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj


async def process_diagram(image: Image.Image) -> Dict[str, Any]:
    """
    Главная функция обработки диаграммы
    
    Пайплайн (ПРАВИЛЬНЫЙ):
    1. YOLO → детекция элементов
    2. OCR → применяется к каждому shape element (rectangle/diamond/circle)
    3. OCR → также к text_region (если есть отдельные метки)
    4. Graph → построение графа с улучшенными эвристиками
    5. Algorithm → генерация алгоритма
    
    Args:
        image: PIL Image
        
    Returns:
        JSON с результатами
    """
    
    # Шаг 1: YOLO детекция
    print("YOLO детекция")
    yolo_model = get_yolo_model()
    detections = yolo_model.predict(image)
    
    # Разделяем детекции на категории
    text_regions_detections = yolo_model.get_text_regions(detections)
    shape_elements = yolo_model.get_shape_elements(detections)
    arrows = yolo_model.get_arrows(detections)
    
    print(f"   Found: {len(shape_elements)} shapes, {len(arrows)} arrows, {len(text_regions_detections)} text regions")
    
    # Шаг 2: OCR для SHAPE ELEMENTS 
    print("OCR")
    ocr = get_ocr()
    
    # OCR для каждого shape element (rectangle/diamond/circle)
    shape_texts = {}
    for i, shape in enumerate(shape_elements):
        bbox = shape.get("bbox")
        if bbox:
            text = ocr.extract_text(image, bbox)
            shape_id = f"shape_{i}"
            shape_texts[shape_id] = {
                "text": text,
                "bbox": bbox,
                "class_name": shape.get("class_name", ""),
                "confidence": shape.get("confidence", 0.0)
            }
            if text:
                print(f"   Shape {i} ({shape['class_name']}): '{text}'")
    
    # Шаг 3: OCR для отдельных text_region 
    print(" OCR для отдельных text_region")
    text_regions = ocr.extract_text_from_regions(image, text_regions_detections)
    
    # Шаг 4: Построение графа с эвристиками
    print(" Построение графа с эвристиками")
    graph = build_graph_from_detections(shape_elements, arrows, shape_texts, text_regions)
    
    # Шаг 5: Генерация алгоритма
    print(" Генерация алгоритма")
    algorithm = generate_algorithm_from_graph(graph)
    
    print("Пайплайн успешно выполнен")
    
    # Формируем результат
    result = {
        "bounding_boxes": {
            "all": detections,
            "shapes": shape_elements,
            "arrows": arrows,
            "text_regions": text_regions_detections
        },
        "shape_texts": shape_texts,
        "text_regions": text_regions,
        "graph": graph,
        "algorithm": algorithm
    }
    
    # Конвертируем numpy типы в JSON-совместимые
    return convert_to_json_serializable(result)

