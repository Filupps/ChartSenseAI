FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем весь исходный код проекта в рабочую директорию
COPY . .

# Определяем аргументы сборки для переменных окружения 
ARG VITE_API_BASE_URL=http://localhost:8000/api
ARG VITE_OPENROUTER_API_KEY

# Устанавливаем переменные окружения из аргументов сборки
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_OPENROUTER_API_KEY=$VITE_OPENROUTER_API_KEY

# Выполняем сборку приложения
RUN npm run build

# Второй этап: production
FROM nginx:alpine

# Копируем собранные файлы из этапа сборки в nginx директорию для статики
COPY --from=build /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]