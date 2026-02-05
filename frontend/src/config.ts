// Конфигурация приложения
// В продакшене эти значения должны быть заменены через переменные окружения

export const config = {
  // API ключ для OpenRouter (LLM)
  OPENROUTER_API_KEY: import.meta.env.VITE_OPENROUTER_API_KEY || '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',
  
  // URL бэкенда
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  
  // API ключ для доступа к бэкенду (опционально, если включена защита)
  API_KEY: import.meta.env.VITE_API_KEY || '',
};

