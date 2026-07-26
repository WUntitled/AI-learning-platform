FROM python:3.11-slim

WORKDIR /app

# 设置环境变量（防止生成 .pyc 文件）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 【修正】后端复制到 /app/backend，和本地目录结构保持一致
COPY backend/ /app/backend/

# 复制前端到 /app/frontend
COPY frontend/ /app/frontend/

# 创建数据目录
RUN mkdir -p /app/backend/data

# 暴露端口
EXPOSE 8000

# 启动入口修改：main文件位于 backend 文件夹内
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
