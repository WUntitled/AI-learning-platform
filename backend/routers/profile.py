"""
学情画像 API

对应 AI做课助手的学情画像构建模块。
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from models import LearningProfile, User
from services.llm_api import LLMService

router = APIRouter(prefix="/api/v1/profile", tags=["学情画像"])
llm = LLMService()


# ================================================================
# Pydantic Schemas
# ================================================================
class ProfileInput(BaseModel):
    name: str = "学习者"
    role: str = "业务分析师"
    experience: str = "1-3年"
    ecommerce_exp: str = ""
    ai_level: str = "基础使用"
    learning_goal: str = ""
    skills: Optional[dict] = None
    profile_id: Optional[str] = None  # 编辑已有画像时传入


class ProfileResponse(BaseModel):
    id: str
    name: str
    role: str
    experience: str
    ecommerce_exp: str
    ai_level: str
    learning_goal: str
    skills: dict
    stage: str
    score: int
    gaps: str
    direction: str
    aiLevel_label: str
    aiLabel: str
    bizLevel: str
    bizLabel: str
    trajectory: list
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SkillsUpdateInput(BaseModel):
    profile_id: str
    skills: dict


# ================================================================
# API Endpoints
# ================================================================

@router.post("/diagnose", response_model=ProfileResponse)
async def create_or_update_profile(input_data: ProfileInput, db: Session = Depends(get_db)):
    """创建或更新学情画像

    1. 收集用户输入信息
    2. LLM生成六维能力评估
    3. 生成学情诊断报告
    4. 存入数据库
    """
    # 查找或创建用户
    user = db.query(User).filter(User.name == input_data.name).first()
    if not user:
        user = User(name=input_data.name)
        db.add(user)
        db.commit()

    # 如果是编辑已有画像
    if input_data.profile_id:
        profile = db.query(LearningProfile).filter(
            LearningProfile.id == input_data.profile_id
        ).first()
        if not profile:
            raise HTTPException(status_code=404, detail="画像不存在")
    else:
        profile = LearningProfile(user_id=user.id)
        db.add(profile)

    # 更新基本信息
    profile.name = input_data.name
    profile.role = input_data.role
    profile.experience = input_data.experience
    profile.ecommerce_exp = input_data.ecommerce_exp
    profile.ai_level = input_data.ai_level
    profile.learning_goal = input_data.learning_goal

    # 如果有前端传入的能力值，直接使用
    if input_data.skills:
        profile.set_skills(input_data.skills)
        # 根据能力值计算阶段和评分
        skills_list = profile.get_skills_list()
        avg_score = sum(skills_list) / len(skills_list)
        profile.score = max(15, int(avg_score))

        if avg_score >= 80:
            profile.stage = "高级进阶阶段"
        elif avg_score >= 55:
            profile.stage = "中级成长阶段"
        else:
            profile.stage = "初级入门阶段"

        profile.gaps = " · ".join(
            ["业务理解能力", "数据分析能力", "AI工具应用能力",
             "经营决策能力", "Prompt撰写能力", "持续迭代能力"][:3]
        )
    else:
        # 调用LLM生成能力评估
        profile_input = {
            "name": input_data.name,
            "role": input_data.role,
            "experience": input_data.experience,
            "ecommerce_exp": input_data.ecommerce_exp,
            "ai_level": input_data.ai_level,
            "learning_goal": input_data.learning_goal,
        }
        diagnosis = await llm.generate_diagnosis(profile_input)
        profile.set_skills(diagnosis.get("skills", {}))
        profile.stage = diagnosis.get("stage", "初级入门阶段")
        profile.score = diagnosis.get("score", 50)
        profile.gaps = diagnosis.get("gaps", "")
        profile.direction = diagnosis.get("direction", "")
        profile.ai_level_label = diagnosis.get("aiLevel_label", "L2")
        profile.ai_label = diagnosis.get("aiLabel", "基础使用")
        profile.biz_level = diagnosis.get("bizLevel", "L2")
        profile.biz_label = diagnosis.get("bizLabel", "独立执行")

    # 添加学习轨迹
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    profile.add_trajectory({
        "date": now_str,
        "module": "AI做课助手",
        "content": "完成学情画像创建",
        "ability": "能力初始评估",
        "change": 0,
    })

    db.commit()
    db.refresh(profile)

    return profile.to_dict()


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """获取指定学情画像"""
    profile = db.query(LearningProfile).filter(LearningProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")
    return profile.to_dict()


@router.get("/", response_model=list)
async def list_profiles(db: Session = Depends(get_db)):
    """获取所有学情画像列表"""
    profiles = db.query(LearningProfile).order_by(LearningProfile.updated_at.desc()).all()
    return [p.to_dict() for p in profiles]


@router.put("/{profile_id}/trajectory")
async def add_trajectory(profile_id: str, entry: dict, db: Session = Depends(get_db)):
    """添加学习轨迹条目"""
    profile = db.query(LearningProfile).filter(LearningProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")
    profile.add_trajectory(entry)
    db.commit()
    return {"status": "ok"}


@router.put("/{profile_id}/skills")
async def update_skills(profile_id: str, data: SkillsUpdateInput, db: Session = Depends(get_db)):
    """更新能力值并重新计算画像"""
    profile = db.query(LearningProfile).filter(LearningProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")
    profile.set_skills(data.skills)
    # 重新计算评分
    skills_list = profile.get_skills_list()
    avg = sum(skills_list) / len(skills_list)
    profile.score = max(15, int(avg))
    db.commit()
    db.refresh(profile)
    return profile.to_dict()


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    """删除学情画像"""
    profile = db.query(LearningProfile).filter(LearningProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")
    db.delete(profile)
    db.commit()
    return {"status": "deleted"}
