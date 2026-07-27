"""
主API路由 — 系统总入口

将所有子路由聚合到同一前缀下：
- /api/v1/profile  — 学情画像
- /api/v1/course   — 课程生成
- /api/v1/learning — 学习助手
- /api/v1/practice — 陪练助手
- /api/v1/exam     — 考试助手
- /api/v1/system   — 系统信息
"""
from fastapi import APIRouter
from config import settings

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/system/status")
async def system_status():
    """获取系统状态"""
    return {
        "status": "running",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_available": settings.llm_available,
        "knowledge_base_connected": bool(settings.KNOWLEDGE_BASE_URI),
    }
