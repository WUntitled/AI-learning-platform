FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 优先把backend加入搜索路径
ENV PYTHONPATH="/app/backend"

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制全部代码、前端资源
COPY . .

RUN mkdir -p backend/data

EXPOSE 8000

# 核心改动：进入backend目录，直接python运行main.py，和本地启动一模一样
CMD cd backend && python main.py