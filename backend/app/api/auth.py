from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Проверяет API ключ, если защита включена.
    Если API_KEY_REQUIRED=False, всегда возвращает True.
    """
    if not settings.API_KEY_REQUIRED:
        return True
    
    if not settings.API_KEY:
        # Защита включена, но ключ не задан - ошибка конфигурации
        raise HTTPException(
            status_code=500,
            detail="API key protection is enabled but API_KEY is not set in configuration"
        )
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header."
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

