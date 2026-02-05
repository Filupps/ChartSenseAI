from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List
import os

# Определяем корень проекта 
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


class Settings(BaseSettings):
    """
    Настройки приложения.
    Значения ниже — это DEFAULT-ы (используются если нет .env файла).
    Реальные значения загружаются из .env автоматически!
    """
    # Database settings (переопределяются из .env)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "1234"  
    DB_NAME: str = "ChartSenseAI"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Model settings - абсолютные пути от корня проекта
    MODEL_PATH: str = str(MODELS_DIR / "yolov8n_diagrams.pt")
    MODEL_FALLBACK: str = str(MODELS_DIR / "yolov8s.pt")  
    MODELS_DIR: str = str(MODELS_DIR)
    
    # OCR settings
    TESSERACT_LANG: str = "rus+eng"
    TESSERACT_PSM: int = 6
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # API Security (опционально)
    API_KEY_REQUIRED: bool = False  # Включить защиту API ключом
    API_KEY: str = ""  # Апи ключ (если пусто - защита отключена)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
