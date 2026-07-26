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
from pathlib import Path

# =====================【新增路径适配代码，必须放在所有import最前面】=====================
# 获取当前main.py文件绝对路径
CURRENT_FILE = Path(__file__).resolve()
# 项目根目录：main.py 的上一级目录（容器内 /app，本地项目根目录）
PROJECT_ROOT = CURRENT_FILE.parent.parent
# 将根目录加入Python搜索路径
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# ======================================================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# 现在可以正常识别根目录 config.py
from .config import settings
from .database import init_db
from .routers.api import api_router
from .routers.profile import router as profile_router
from .routers.course import router as course_router
from .routers.learning import router as learning_router
from .routers.practice import router as practice_router
from .routers.exam import router as exam_router


# 设置控制台编码为UTF-8 (解决Windows GBK编码问题)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"


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
# 每次请求动态计算前端目录，不再启动一次性缓存判断
# ================================================================
def get_frontend_dir() -> Path:
    """获取前端目录路径"""
    return Path(__file__).parent.parent / "frontend"


@app.get("/")
async def root():
    static_dir = get_frontend_dir()
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    # 不存在前端文件，返回API提示JSON
    return {
        "message": "AI辅助业务分析个性化培训系统 API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "/api/v1/system/status"
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """SPA catch-all — 提供前端静态文件，支持前端路由刷新"""
    static_dir = get_frontend_dir()
    index_path = static_dir / "index.html"
    file_path = static_dir / full_path

    # 如果请求的文件存在，直接返回文件
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # 文件不存在，返回index.html（前端SPA路由）
    if index_path.exists():
        return FileResponse(str(index_path))

    return {"message": "Not found", "docs": "/api/docs"}


# 启动时打印前端目录状态
frontend_path = get_frontend_dir()
if frontend_path.exists() and (frontend_path / "index.html").exists():
    print(f"[OK] 前端已加载: {frontend_path}")
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