// Конфигурация приложения

export const config = {
  // API ключ для OpenRouter (LLM)
  OPENROUTER_API_KEY: import.meta.env.VITE_OPENROUTER_API_KEY,
  
  // URL бэкенда
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  
  // API ключ для доступа к бэкенду (опционально, если включена защита)
  API_KEY: import.meta.env.VITE_API_KEY || '',
};

