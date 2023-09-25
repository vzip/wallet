FROM python:3.11-bookworm

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /Wallet

# Устанавливаем переменные окружения Python в production mode
ENV PYTHONDONTWRITEBYTECODE 1
# Установка этой переменной обеспечивает мгновенный вывод, что упрощает мониторинг и отладку приложения в контейнере.
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в контейнер
COPY . .

# Запускаем приложение
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
CMD ["sh", "-c", "if [ \"$(nproc)\" -eq 1 ]; then WORKERS=1; else WORKERS=$(($(nproc) * 2 + 1)); fi; exec gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker -t 360 main:app --bind 0.0.0.0:8010"]
