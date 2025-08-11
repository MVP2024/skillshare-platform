# Используем официальный образ Python как базовый
FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . /app/

# Открываем порт, на котором будет работать Django
EXPOSE 8000
