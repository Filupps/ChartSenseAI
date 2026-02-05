# ChartSenseAI

Интеллектуальный сервис для анализа блок-схем и диаграмм с автоматическим извлечением алгоритмов и генерацией кода.

## Что это?

ChartSenseAI — это веб-приложение, которое:
- **Распознаёт элементы** на изображениях диаграмм (блоки, стрелки, текст) с помощью YOLO
- **Извлекает текст** из блоков с помощью OCR (Tesseract)
- **Строит граф** связей между элементами
- **Генерирует алгоритм** в текстовом виде
- **Создаёт код** (псевдокод или Python) через LLM
- **Генерирует диаграммы** из описания алгоритма (обратный процесс)

## Основные возможности

### 1. Диаграмма → Алгоритм
- Загрузите изображение блок-схемы
- Система автоматически распознаёт все элементы
- Получите структурированный алгоритм с ветвлениями
- **Редактируйте алгоритм** прямо в интерфейсе (добавление, удаление, изменение шагов)
- Скачайте результат в JSON или сгенерируйте код (Python/псевдокод)

### 2. Алгоритм → Диаграмма
- Опишите алгоритм текстом или прикрепите JSON/Python файл
- LLM сгенерирует PlantUML код
- Получите визуальную диаграмму (SVG/PNG)

## Технологии

**Backend:**
- FastAPI — REST API
- YOLOv8 (Ultralytics) — детекция элементов
- Tesseract OCR — распознавание текста
- PyTorch — нейронные сети
- MySQL — база данных для хранения истории
- SQLAlchemy — ORM

**Frontend:**
- React + TypeScript
- Vite — сборка
- Axios — HTTP запросы
- Unbounded font — дизайн

**LLM:**
- OpenRouter API — генерация кода и диаграмм

##  Требования

- Python 3.10+
- Node.js 20+
- MySQL 8.0+
- Tesseract OCR (с русским языком)
- CUDA (опционально, для GPU ускорения)

##  Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ChartSenseAI
```

### 2. Настройка Backend

```bash
# Создайте виртуальное окружение
cd backend
python -m venv venv

# Активируйте (Windows)
venv\Scripts\activate
# Или (Linux/Mac)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

**Настройте переменные окружения:**

Скопируйте `env.example` в `.env` и заполните:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=ваш_пароль
DB_NAME=ChartSenseAI
```

**Создайте базу данных:**

```sql
CREATE DATABASE ChartSenseAI CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Настройка Frontend

```bash
cd frontend
npm install
```

**Настройте переменные окружения:**

Скопируйте `env.example` в `.env`:

```env
VITE_OPENROUTER_API_KEY=ваш_ключ_openrouter
VITE_API_BASE_URL=http://localhost:8000/api
```

### 4. Запуск

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Откройте браузер: `http://localhost:5173`

##  Docker 

### Запуск через Docker Compose

```bash
# Из корня проекта
cd docker
docker-compose up -d
```

Сервисы будут доступны:
- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- MySQL: `localhost:3306`

### Остановка

```bash
docker-compose down
```

##  Структура проекта

```
ChartSenseAI/
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── api/         # API эндпоинты
│   │   ├── models/      # логика работы YOLO моделью
│   │   ├── ocr/         # Tesseract OCR
│   │   ├── graph/       # Построение графа
│   │   ├── algo/        # Генерация алгоритма
│   │   ├── db/          # База данных
│   │   └── services/    # Бизнес-логика
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/            # React приложение
│   ├── src/
│   │   ├── components/ # React компоненты
│   │   ├── api.ts       # API клиент
│   │   ├── config.ts    # Конфигурация
│   │   └── styles/      # CSS стили
│   ├── Dockerfile
│   └── nginx.conf
│
├── docker/
│   └── docker-compose.yml
│
└── models/              # YOLO модели
```

## Конфигурация

### Backend

Все настройки в `backend/.env`:
- `DB_*` — параметры MySQL
- `MODEL_PATH` — путь к кастомной модели
- `TESSERACT_LANG` — языки OCR (по умолчанию `rus+eng`)

### Frontend

Все настройки в `frontend/.env`:
- `VITE_OPENROUTER_API_KEY` — ключ для LLM
- `VITE_API_BASE_URL` — URL бэкенда

## База данных

Система автоматически создаёт таблицы при первом запуске:

- `sessions` — сессии пользователей
- `processings` — результаты анализа диаграмм
- `diagram_generations` — сгенерированные диаграммы
- `code_generations` — сгенерированный код

## API Endpoints

- `POST /api/predict` — загрузка и анализ диаграммы
- `POST /api/diagram-generation` — сохранение генерации диаграммы
- `POST /api/code-generation` — сохранение генерации кода
- `GET /api/session/{id}/history` — история сессии
- `GET /api/sessions` — список всех сессий

 **Подробная документация API с примерами:** см. [API_DOCS.md](API_DOCS.md)

##  Особенности

- **Автоматическое определение устройства** (CUDA/CPU)
- **Умное построение графа** с эвристиками для связывания элементов
- **Обработка ветвлений** (if/else) в алгоритмах
- **Редактирование алгоритма** в интерфейсе
- **Красивый UI** с эффектом liquid glass
- **История обработок** в базе данных

##  Автор

Воробьев Филипп, 2026

---

**Приятного использования**

