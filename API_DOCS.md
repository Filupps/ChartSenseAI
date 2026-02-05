# ChartSenseAI API Документация

Полное руководство по использованию API для анализа диаграмм и генерации алгоритмов.

## Базовый URL

```
http://localhost:8000/api
```

## Аутентификация

Если включена защита API (`API_KEY_REQUIRED=true`), добавьте заголовок:

```
X-API-Key: your_api_key
```

## Эндпоинты

### 1. Анализ диаграммы (Диаграмма → Алгоритм)

**POST** `/api/predict`

Загружает изображение диаграммы и получает полный анализ: детекцию элементов, граф и алгоритм.

**Запрос:**
- Content-Type: `multipart/form-data`
- Параметры:
  - `file` (обязательно) - файл изображения (PNG, JPG, JPEG)
  - `X-Session-Id` (опционально) - ID сессии для сохранения в БД

**Пример с curl:**
```bash
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: your_key" \
  -H "X-Session-Id: user-session-123" \
  -F "file=@diagram.png"
```

**Пример с Python:**
```python
import requests

url = "http://localhost:8000/api/predict"
headers = {
    "X-API-Key": "your_key",  # если защита включена
    "X-Session-Id": "user-session-123"
}

with open("diagram.png", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)
    result = response.json()

print(result["algorithm"]["steps"])
```

**Пример с JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/predict', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your_key',
    'X-Session-Id': 'user-session-123'
  },
  body: formData
});

const result = await response.json();
console.log(result.algorithm.steps);
```

**Ответ:**
```json
{
  "bounding_boxes": {
    "all": [...],
    "shapes": [...],
    "arrows": [...],
    "text_regions": [...]
  },
  "shape_texts": {
    "shape_0": {
      "text": "Начало",
      "bbox": [10, 20, 100, 50],
      "class_name": "rectangle",
      "confidence": 0.95
    }
  },
  "graph": {
    "nodes": [...],
    "edges": [...],
    "decisions": [...]
  },
  "algorithm": {
    "steps": [
      "НАЧАЛО",
      "Шаг 1: Действие",
      "ЕСЛИ условие",
      "  [Да]: Действие 1",
      "  [Нет]: Действие 2",
      "КОНЕЦ"
    ],
    "structured": [...]
  },
  "processing_id": 123,
  "session_id": "user-session-123",
  "processing_time_ms": 1250.5
}
```

---

### 2. Сохранение генерации диаграммы

**POST** `/api/diagram-generation`

Сохраняет результат генерации диаграммы из алгоритма в базу данных.

**Запрос:**
```json
{
  "session_id": "user-session-123",
  "input_type": "text",
  "input_text": "Алгоритм авторизации...",
  "input_file_name": null,
  "input_file_content": null,
  "plantuml_code": "@startuml\nstart\n:Действие;\nstop\n@enduml",
  "diagram_url": "https://www.plantuml.com/plantuml/svg/...",
  "llm_model": "openrouter",
  "generation_time_ms": 2500
}
```

**Пример:**
```bash
curl -X POST http://localhost:8000/api/diagram-generation \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key" \
  -d '{
    "session_id": "user-session-123",
    "input_type": "text",
    "input_text": "Алгоритм авторизации",
    "plantuml_code": "@startuml\nstart\nstop\n@enduml",
    "diagram_url": "https://www.plantuml.com/plantuml/svg/...",
    "llm_model": "openrouter",
    "generation_time_ms": 2500
  }'
```

**Ответ:**
```json
{
  "id": 456,
  "status": "saved"
}
```

---

### 3. Сохранение генерации кода

**POST** `/api/code-generation`

Сохраняет сгенерированный код (Python/псевдокод) в базу данных.

**Запрос:**
```json
{
  "processing_id": 123,
  "code_type": "python",
  "generated_code": "def process_algorithm():\n    ...",
  "llm_model": "openrouter",
  "generation_time_ms": 1800
}
```

**Пример:**
```bash
curl -X POST http://localhost:8000/api/code-generation \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key" \
  -d '{
    "processing_id": 123,
    "code_type": "python",
    "generated_code": "def process():\n    pass",
    "llm_model": "openrouter",
    "generation_time_ms": 1800
  }'
```

---

### 4. История сессии

**GET** `/api/session/{session_id}/history`

Получает всю историю обработок для конкретной сессии.

**Пример:**
```bash
curl http://localhost:8000/api/session/user-session-123/history \
  -H "X-API-Key: your_key"
```

**Ответ:**
```json
{
  "session": {
    "id": 1,
    "session_id": "user-session-123",
    "created_at": "2024-01-15T10:30:00"
  },
  "processings": [
    {
      "id": 123,
      "image_filename": "diagram.png",
      "model_version": "yolov8s.pt",
      "processing_time_ms": 1250.5,
      "detected_shapes": 5,
      "detected_arrows": 4,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "generations": [
    {
      "id": 456,
      "input_type": "text",
      "plantuml_code": "@startuml\n...",
      "diagram_url": "https://...",
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
```

---

### 5. Список всех сессий

**GET** `/api/sessions?limit=50`

Получает список всех сессий (по умолчанию 50).

**Пример:**
```bash
curl http://localhost:8000/api/sessions?limit=100 \
  -H "X-API-Key: your_key"
```

---

### 6. Детали обработки

**GET** `/api/processing/{processing_id}`

Получает полные детали конкретной обработки, включая все результаты.

**Пример:**
```bash
curl http://localhost:8000/api/processing/123 \
  -H "X-API-Key: your_key"
```

**Ответ:**
```json
{
  "id": 123,
  "image_filename": "diagram.png",
  "model_version": "yolov8s.pt",
  "processing_time_ms": 1250.5,
  "detected_shapes": 5,
  "detected_arrows": 4,
  "detected_text_regions": 2,
  "detection_result": [...],
  "graph_result": {...},
  "algorithm_result": {...},
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Коды ошибок

- `200` - Успешный запрос
- `400` - Неверный формат запроса (например, не изображение)
- `401` - Требуется API ключ (если защита включена)
- `403` - Неверный API ключ
- `404` - Ресурс не найден
- `500` - Внутренняя ошибка сервера

## Полный пример использования (Python)

```python
import requests
import json

API_URL = "http://localhost:8000/api"
API_KEY = "your_key"  # если защита включена

headers = {
    "X-API-Key": API_KEY,
    "X-Session-Id": "my-session-123"
}

# 1. Загрузить и проанализировать диаграмму
with open("diagram.png", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{API_URL}/predict",
        headers=headers,
        files=files
    )
    result = response.json()

processing_id = result["processing_id"]
algorithm = result["algorithm"]

print("Алгоритм:")
for step in algorithm["steps"]:
    print(f"  {step}")

# 2. Сохранить генерацию кода (если сгенерировали через LLM)
code_data = {
    "processing_id": processing_id,
    "code_type": "python",
    "generated_code": "def process():\n    pass",
    "llm_model": "openrouter",
    "generation_time_ms": 1800
}

response = requests.post(
    f"{API_URL}/code-generation",
    headers=headers,
    json=code_data
)
print(f"Код сохранён: {response.json()}")

# 3. Получить историю сессии
response = requests.get(
    f"{API_URL}/session/my-session-123/history",
    headers=headers
)
history = response.json()
print(f"Всего обработок: {len(history['processings'])}")
```

## Полный пример использования (JavaScript/Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_URL = 'http://localhost:8000/api';
const API_KEY = 'your_key';

const headers = {
  'X-API-Key': API_KEY,
  'X-Session-Id': 'my-session-123'
};

// 1. Загрузить и проанализировать диаграмму
async function analyzeDiagram(imagePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(imagePath));
  
  const response = await axios.post(`${API_URL}/predict`, formData, {
    headers: {
      ...headers,
      ...formData.getHeaders()
    }
  });
  
  return response.data;
}

// Использование
analyzeDiagram('diagram.png')
  .then(result => {
    console.log('Алгоритм:', result.algorithm.steps);
    console.log('Processing ID:', result.processing_id);
  })
  .catch(error => {
    console.error('Ошибка:', error.response?.data || error.message);
  });
```

## Полный пример использования (cURL)

```bash
#!/bin/bash

API_URL="http://localhost:8000/api"
API_KEY="your_key"
SESSION_ID="my-session-123"

# 1. Анализ диаграммы
echo "Анализ диаграммы..."
RESPONSE=$(curl -s -X POST "${API_URL}/predict" \
  -H "X-API-Key: ${API_KEY}" \
  -H "X-Session-Id: ${SESSION_ID}" \
  -F "file=@diagram.png")

PROCESSING_ID=$(echo $RESPONSE | jq -r '.processing_id')
echo "Processing ID: $PROCESSING_ID"

# 2. Получить историю
echo "История сессии..."
curl -s "${API_URL}/session/${SESSION_ID}/history" \
  -H "X-API-Key: ${API_KEY}" | jq '.'
```

---

**Примечание:** Все примеры предполагают, что защита API включена. Если защита отключена (`API_KEY_REQUIRED=false`), просто уберите заголовок `X-API-Key` из запросов.

