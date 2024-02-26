#!/bin/sh

# Запуск миграций Alembic
alembic upgrade head

# Запуск приложения
if [ "$(nproc)" -eq 1 ]; then
    WORKERS=1
else
    WORKERS=$(($(nproc) * 2 + 1))
fi

exec gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker -t 360 main:app --bind 0.0.0.0:8010
