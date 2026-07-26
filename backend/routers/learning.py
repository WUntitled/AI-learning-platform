"""
AI学习助手 API

对应启发式交互答疑模块。
包含多Agent路由、对话管理、学情更新。
"""
from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db
from models import ChatSession, LearningProfile
from services.llm_api import LLMService

router = APIRouter(prefix="/api/v1/learning", tags=["学习助手"])
llm = LLMService()


class ChatMessage(BaseModel):
    role: str = "user"  # user | assistant | system
    content: str
    agent: Optional[str] = None


class ChatRequest(BaseModel):
    profile_id: str
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent_route: Optional[str] = None
    context_updated: bool = False


class SessionResponse(BaseModel):
    id: str
    profile_id: str
    messages: list
    topic: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ================================================================
# 模拟的Agent路由
# ================================================================
AGENT_LIST = [
    {"idx": 1, "cn": "问题路由 Agent", "en": "Question Router Agent",
     "desc": "分析用户问题，路由到最合适的处理Agent"},
    {"idx": 2, "cn": "导学追问 Agent", "en": "Tutoring Agent",
     "desc": "通过追问引导用户深入思考，而不是直接给答案"},
    {"idx": 3, "cn": "知识答疑 Agent", "en": "QA Agent",
     "desc": "解答用户在学习过程中的具体知识点疑问"},
    {"idx": 4, "cn": "案例讲解 Agent", "en": "Case Study Agent",
     "desc": "通过实际业务案例来辅助解释知识点"},
    {"idx": 5, "cn": "学情诊断 Agent", "en": "Diagnosis Agent",
     "desc": "从对话中提取反映用户当前学情的信息"},
    {"idx": 6, "cn": "画像更新 Agent", "en": "Profile Update Agent",
     "desc": "根据新发现的学情信息更新学习画像"},
]


@router.get("/agents")
async def get_learning_agents():
    """获取学习助手的多智能体列表"""
    return AGENT_LIST


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """学习助手对话接口

    多Agent处理流程：
    1. 问题路由 → 判断问题类型
    2. 导学追问 → 引导式提问（可选）
    3. 知识答疑 → 生成回答
    4. 案例讲解 → 补充案例（可选）
    5. 学情诊断 → 提取学情信息
    6. 画像更新 → 更新学习画像
    """
    profile = db.query(LearningProfile).filter(
        LearningProfile.id == request.profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="学情画像不存在")

    # 查找或创建会话
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session = ChatSession(profile_id=profile.id, messages=[])
        db.add(session)

    # 获取当前消息列表
    messages = list(session.messages or [])

    # 从消息历史中提取最近5条作为上下文
    context = {
        "profile": profile.to_dict(),
        "recent_messages": messages[-5:] if messages else [],
        "topic": session.topic or "",
    }

    # 路由判断（模拟）
    agent_route = _route_question(request.message)

    # 添加用户消息
    messages.append({
        "id": str(uuid.uuid4())[:8],
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # 调用LLM生成回复
    reply = await llm.chat_response(messages, context)

    # 添加AI回复
    messages.append({
        "id": str(uuid.uuid4())[:8],
        "role": "assistant",
        "content": reply,
        "agent": agent_route,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # 更新会话
    session.messages = messages
    if not session.topic:
        session.topic = request.message[:50]
    db.commit()
    db.refresh(session)

    return ChatResponse(
        session_id=session.id,
        reply=reply,
        agent_route=agent_route,
        context_updated=True,
    )


@router.get("/sessions/{profile_id}", response_model=list)
async def list_sessions(profile_id: str, db: Session = Depends(get_db)):
    """获取用户的所有对话会话"""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.profile_id == profile_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
        .all()
    )
    return [
        {"id": s.id, "topic": s.topic, "message_count": len(s.messages or []),
         "created_at": s.created_at.isoformat() if s.created_at else None}
        for s in sessions
    ]


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取指定会话的完整消息历史"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return SessionResponse(
        id=session.id,
        profile_id=session.profile_id,
        messages=session.messages or [],
        topic=session.topic or "",
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
    )


@router.post("/analyze/{profile_id}")
async def analyze_learning(profile_id: str, db: Session = Depends(get_db)):
    """分析学习情况并更新画像"""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.profile_id == profile_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(5)
        .all()
    )

    all_messages = []
    for s in sessions:
        all_messages.extend(s.messages or [])

    if not all_messages:
        return {"status": "no_data", "message": "没有足够的对话数据"}

    # 分析会话
    analysis = await llm.analyze_session(all_messages)

    # 更新画像
    profile = db.query(LearningProfile).filter(LearningProfile.id == profile_id).first()
    if profile and analysis.get("profile_update"):
        updates = analysis["profile_update"]
        profile.set_skills(updates)
        profile.add_trajectory({
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "module": "AI学习助手",
            "content": "完成启发式交互学习",
            "ability": "会话分析学情更新",
            "change": 0,
        })
        db.commit()

    return {
        "status": "analyzed",
        "analysis": analysis,
    }


def _route_question(message: str) -> str:
    """模拟问题路由"""
    if "案例" in message or "例子" in message or "场景" in message:
        return "案例讲解Agent"
    if "为什么" in message or "如何" in message or "怎么" in message:
        return "导学追问Agent"
    if "GMV" in message or "数据" in message or "指标" in message:
        return "知识答疑Agent"
    if "Prompt" in message or "提示词" in message:
        return "知识答疑Agent"
    if "不会" in message or "不懂" in message or "难" in message:
        return "导学追问Agent"
    return "知识答疑Agent"
