"""
AI辅助业务分析个性化培训系统 — 后端入口

启动方式：
  python main.py              # 开发模式
  uvicorn main:app --host 0.0.0.0 --port 8000  # 生产模式

访问地址：
  http://localhost:8000        # 本地访问
  http://<本机IP>:8000         # 局域网设备访问
  http://api/docs              # API文档 (Swagger UI)
"""
import os
import sys

# 设置控制台编码为UTF-8 (解决Windows GBK编码问题)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers.api import api_router
from routers.profile import router as profile_router
from routers.course import router as course_router
from routers.learning import router as learning_router
from routers.practice import router as practice_router
from routers.exam import router as exam_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("[STARTUP] 系统正在启动...")
    init_db()
    print("[OK] 数据库初始化完成")
    print(f"[CONFIG] LLM Provider: {settings.LLM_PROVIDER}")
    if settings.llm_available:
        print("[OK] LLM 服务可用")
    else:
        print("[WARN] LLM 服务未配置，使用模拟模式")
    print(f"[INFO] API 文档: http://localhost:{settings.PORT}/api/docs")
    yield
    print("[SHUTDOWN] 系统关闭")


app = FastAPI(
    title="AI辅助业务分析个性化培训系统",
    description="基于多智能体协同的AI辅助业务分析个性化培训系统后端API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ================================================================
# CORS 配置 — 允许跨设备访问
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境应限制）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# 注册 API 路由
# ================================================================
app.include_router(api_router)
app.include_router(profile_router)
app.include_router(course_router)
app.include_router(learning_router)
app.include_router(practice_router)
app.include_router(exam_router)


# ================================================================
# 静态文件服务（前端SPA）
# ================================================================
# 使用 catch-all 路由提供前端文件，如果前端不存在则返回 API 信息
static_dir = Path(__file__).parent.parent / "frontend"
has_frontend = static_dir.exists() and (static_dir / "index.html").exists()


@app.get("/")
async def root():
    if has_frontend:
        from fastapi.responses import FileResponse
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    return {"message": "AI辅助业务分析个性化培训系统 API", "version": "1.0.0",
            "docs": "/api/docs", "status": "/api/v1/system/status"}


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """SPA catch-all — 提供前端静态文件"""
    if has_frontend:
        from fastapi.responses import FileResponse
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    return {"message": "Not found", "docs": "/api/docs"}


if has_frontend:
    print(f"[OK] 前端已加载: {static_dir}")
else:
    print(f"[INFO] 前端 index.html 不存在，仅API模式运行")


if __name__ == "__main__":
    print(f"""
{'=' * 55}
  AI辅助业务分析个性化培训系统
  基于多智能体协同的AI培训平台
{'=' * 55}
  启动地址: http://{settings.HOST}:{settings.PORT}
  API文档:  http://{settings.HOST}:{settings.PORT}/api/docs
  LLM模式:  {settings.LLM_PROVIDER}
{'=' * 55}
    """)
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )
