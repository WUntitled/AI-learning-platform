FROM python:3.11-slim

WORKDIR /app

# 设置环境变量（防止生成 .pyc 文件）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# ★ 修复：复制前端到正确路径（main.py 查找 /app/frontend/）
COPY frontend/ /app/frontend/

# 创建数据目录
RUN mkdir -p /app/backend/data

# 暴露端口
EXPOSE 8000

# ★ 修复：使用 $PORT 环境变量（Railway/Render 自动设置此变量）
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
