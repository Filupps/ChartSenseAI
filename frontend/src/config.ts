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

