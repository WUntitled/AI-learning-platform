FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p backend/data

EXPOSE 8000

# 关键改动：使用 python -m uvicorn 模式，自动识别 WORKDIR=/app
CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}