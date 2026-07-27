FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 核心：同时加载项目根目录 + backend目录
ENV PYTHONPATH="/app:/app/backend"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p backend/data

EXPOSE 8000

# ⚠️重点改动！启动命令从 backend.main:app → main:app
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}