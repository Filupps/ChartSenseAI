FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.10 python3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости для OpenCV и Tesseract
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*

# Зависимости Python (CUDA 11.8)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

