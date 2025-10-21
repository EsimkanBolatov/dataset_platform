# 1. Используем официальный образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию
WORKDIR /app

# 3. Копируем файл зависимостей
COPY requirements.txt .

# Слой 1: Устанавливаем системные зависимости для компиляции
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc

# Слой 2: Устанавливаем "тяжёлый" PyTorch с увеличенным таймаутом
RUN pip install --timeout 600 torch \
  --index-url https://download.pytorch.org/whl/cpu \
  --trusted-host download.pytorch.org

# Слой 3: Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt \
  --trusted-host pypi.org \
  --trusted-host files.pythonhosted.org

# Слой 4: Очищаем систему от ненужных пакетов
RUN apt-get purge -y build-essential gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# 5. Копируем весь код нашего приложения
COPY ./app /app/app

# 6. Указываем команду для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]





