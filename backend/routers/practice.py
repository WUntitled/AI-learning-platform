"""
AI陪练助手 API

对应实战题演练模块。
包含场景生成、用户作答评估、学情更新。
"""
from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from models import PracticeSession, LearningProfile
from services.llm_api import LLMService

router = APIRouter(prefix="/api/v1/practice", tags=["陪练助手"])
llm = LLMService()


class ScenarioRequest(BaseModel):
    profile_id: str
    scenario_type: str  # 数据理解类, AI分析类, Prompt设计类, 业务决策类


class AnswerSubmit(BaseModel):
    session_id: str
    answer: str


class QuestionAnswer(BaseModel):
    question_index: int
    answer: str


class PracticeSubmit(BaseModel):
    session_id: str
    answers: list[QuestionAnswer]


SCENARIO_TYPES = ["数据理解类", "AI分析类", "Prompt设计类", "业务决策类"]


@router.get("/types")
async def get_scenario_types():
    """获取实战题类型列表"""
    return {"types": SCENARIO_TYPES}


@router.post("/scenario")
async def generate_scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    """生成实战演练场景"""
    if request.scenario_type not in SCENARIO_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的实战类型，可选: {SCENARIO_TYPES}")

    profile = db.query(LearningProfile).filter(
        LearningProfile.id == request.profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="学情画像不存在")

    # 生成场景
    scenario = await llm.generate_scenario(
        request.scenario_type, profile.to_dict()
    )

    # 创建实战会话
    session = PracticeSession(
        profile_id=profile.id,
        scenario_type=request.scenario_type,
        scenario=scenario,
        status="created",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "scenario": scenario,
        "profile": {
            "name": profile.name,
            "role": profile.role,
            "stage": profile.stage,
        },
    }


@router.post("/submit")
async def submit_practice(submit: PracticeSubmit, db: Session = Depends(get_db)):
    """提交实战演练答案并获取评估"""
    session = db.query(PracticeSession).filter(
        PracticeSession.id == submit.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="实战会话不存在")

    # 整理回答
    answers_text = "\n".join([
        f"Q{a.question_index + 1}: {a.answer}"
        for a in submit.answers
    ])

    # 获取画像
    profile = db.query(LearningProfile).filter(
        LearningProfile.id == session.profile_id
    ).first()

    # 评估
    evaluation = await llm.evaluate_practice(
        session.scenario or {}, answers_text,
        profile.to_dict() if profile else None
    )

    # 更新会话
    session.user_answer = answers_text
    session.evaluation = evaluation
    session.score = evaluation.get("score", 0)
    session.status = "completed"
    db.commit()

    # 更新画像轨迹
    if profile:
        profile.add_trajectory({
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "module": "AI陪练助手",
            "content": f"完成{session.scenario_type}实战演练",
            "ability": f"{session.scenario_type}实战",
            "change": evaluation.get("score", 0) // 10,
        })
        db.commit()

    return {
        "session_id": session.id,
        "score": session.score,
        "evaluation": evaluation,
    }


@router.get("/history/{profile_id}")
async def get_practice_history(profile_id: str, db: Session = Depends(get_db)):
    """获取实战演练历史"""
    sessions = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.profile_id == profile_id,
            PracticeSession.status == "completed",
        )
        .order_by(PracticeSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "scenario_type": s.scenario_type,
            "scenario_title": s.scenario.get("title", "") if s.scenario else "",
            "score": s.score,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/session/{session_id}")
async def get_practice_session(session_id: str, db: Session = Depends(get_db)):
    """获取实战会话详情"""
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="实战会话不存在")
    return session.to_dict()
