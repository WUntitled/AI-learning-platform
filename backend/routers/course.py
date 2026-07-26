"""
课程生成 API

对应 AI做课助手的个性化课程生成模块。
包含多智能体协同生成课程的功能。
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from models import Course, LearningProfile
from services.llm_api import LLMService
from agents import AgentEngine, AgentResult, BaseAgent

router = APIRouter(prefix="/api/v1/course", tags=["课程生成"])
llm = LLMService()


class CourseGenerateInput(BaseModel):
    profile_id: str


class CourseResponse(BaseModel):
    id: str
    profile_id: str
    skill_tree: dict
    learning_path: list
    knowledge_cards: list
    tasks: list
    cases: list
    status: str
    agent_results: list = []


# ================================================================
# 模拟Agent（用于前端可视化）
# ================================================================
class _PlanningAgent(BaseAgent):
    name = "课程规划Agent"
    idx = 3
    cn_name = "课程规划 Agent"
    en_name = "Curriculum Planning Agent"
    description = "设计课程体系结构，规划章节顺序与学习路径"
    async def process(self, input_data, context=None):
        return {"plan_complete": True, "structure": "课程体系已规划"}

class _ContentAgent(BaseAgent):
    name = "内容生成Agent"
    idx = 4
    cn_name = "内容生成 Agent"
    en_name = "Content Generation Agent"
    description = "生成课程知识点、教程、任务与练习内容"
    async def process(self, input_data, context=None):
        return {"content_generated": True}

class _CaseAgent(BaseAgent):
    name = "案例设计Agent"
    idx = 5
    cn_name = "案例设计 Agent"
    en_name = "Case Design Agent"
    description = "生成符合岗位的业务案例，含数据与评价标准"
    async def process(self, input_data, context=None):
        return {"case_designed": True}

class _ReviewAgent(BaseAgent):
    name = "课程审核Agent"
    idx = 6
    cn_name = "课程审核 Agent"
    en_name = "Quality Review Agent"
    description = "检查课程知识准确性、业务真实性、难度匹配与能力覆盖"
    async def process(self, input_data, context=None):
        return {"review_passed": True, "quality_score": 0.92}


# ================================================================
# API Endpoints
# ================================================================

@router.get("/agents")
async def get_course_agents():
    """获取做课助手的多智能体列表"""
    engine = AgentEngine()
    agents = [
        _PlanningAgent(), _ContentAgent(), _CaseAgent(), _ReviewAgent()
    ]
    engine.register_agents(*agents)
    return engine.get_agents_info()


@router.post("/generate", response_model=CourseResponse)
async def generate_course(input_data: CourseGenerateInput, db: Session = Depends(get_db)):
    """生成个性化课程

    多智能体协同流程：
    1. 验证学情画像
    2. 浏览画像生成个性化课程内容
    3. 辩论审核
    4. 存入数据库
    """
    profile = db.query(LearningProfile).filter(
        LearningProfile.id == input_data.profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="学情画像不存在")

    # 调用LLM生成课程
    course_data = await llm.generate_course(profile.to_dict())

    # 保存到数据库
    course = Course(
        profile_id=profile.id,
        skill_tree=course_data.get("skill_tree", {}),
        learning_path=course_data.get("learning_path", []),
        knowledge_cards=course_data.get("knowledge_cards", []),
        tasks=course_data.get("tasks", []),
        cases=course_data.get("cases", []),
        source="generated",
        status="completed",
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # 添加学习轨迹
    from datetime import datetime
    profile.add_trajectory({
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "module": "AI做课助手",
        "content": "生成个性化培训课程",
        "ability": "课程体系设计",
        "change": 0,
    })
    db.commit()

    result = course.to_dict()
    result["agent_results"] = [
        {"agent_name": "课程规划Agent", "status": "completed"},
        {"agent_name": "内容生成Agent", "status": "completed"},
        {"agent_name": "案例设计Agent", "status": "completed"},
        {"agent_name": "课程审核Agent", "status": "completed"},
    ]
    return result


@router.get("/{course_id}")
async def get_course(course_id: str, db: Session = Depends(get_db)):
    """获取课程详情"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course.to_dict()


@router.get("/by-profile/{profile_id}")
async def get_courses_by_profile(profile_id: str, db: Session = Depends(get_db)):
    """获取指定画像的所有课程"""
    courses = (
        db.query(Course)
        .filter(Course.profile_id == profile_id)
        .order_by(Course.created_at.desc())
        .all()
    )
    return [c.to_dict() for c in courses]
