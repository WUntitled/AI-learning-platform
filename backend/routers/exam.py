"""
AI考试助手 API

对应考试出题模块和学情更新模块。
包含考试蓝图生成、出题、组卷、评分、学情报告。
"""
from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..database import get_db
from models import Exam, LearningProfile
from services.llm_api import LLMService

router = APIRouter(prefix="/api/v1/exam", tags=["考试助手"])
llm = LLMService()


class ExamCreateRequest(BaseModel):
    profile_id: str
    course_id: Optional[str] = None


class AnswerSubmit(BaseModel):
    exam_id: str
    answers: list[dict]  # [{question_id, answer}]


class ExamResponse(BaseModel):
    id: str
    blueprint: dict
    questions: list
    status: str
    duration: int


# ================================================================
# 考试Agent列表
# ================================================================
EXAM_AGENTS = [
    {"idx": 1, "cn": "考试蓝图 Agent", "en": "Exam Blueprint Agent",
     "desc": "根据学习者画像确定考试目标、能力维度、题型分布、难度比例、总题量和总时长"},
    {"idx": 2, "cn": "出题 Agent", "en": "Question Generator Agent",
     "desc": "依据考试蓝图生成高质量的题目"},
    {"idx": 3, "cn": "答案评分 Agent", "en": "Answer & Scoring Agent",
     "desc": "针对每道题生成标准答案和评分标准"},
    {"idx": 4, "cn": "个性化组卷 Agent", "en": "Personalized Paper Agent",
     "desc": "从候选题中挑选最适合学习者的题目，组成一套试卷"},
    {"idx": 5, "cn": "质量审核 Agent", "en": "Quality Review Agent",
     "desc": "对最终试卷进行质量审核，确保考试内容符合要求"},
]


@router.get("/agents")
async def get_exam_agents():
    """获取考试助手的多智能体列表"""
    return EXAM_AGENTS


@router.post("/create", response_model=ExamResponse)
async def create_exam(request: ExamCreateRequest, db: Session = Depends(get_db)):
    """创建考试（自动执行完整出题流程）

    多Agent流程：
    1. 考试蓝图Agent → 制定考试方案
    2. 出题Agent → 生成各类型题目
    3. 答案评分Agent → 生成参考答案和评分标准
    4. 个性化组卷Agent → 从候选题组卷
    5. 质量审核Agent → 审核并最终确定
    """
    profile = db.query(LearningProfile).filter(
        LearningProfile.id == request.profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="学情画像不存在")

    # 1. 生成考试蓝图
    blueprint = await llm.generate_exam_blueprint(profile.to_dict())

    # 2. 生成题目
    questions = await llm.generate_questions(blueprint, profile.to_dict())

    # 3. 提取答案键
    answer_key = [
        {
            "question_id": q.get("id", f"q_{i}"),
            "correct_answer": q.get("answer", ""),
            "analysis": q.get("analysis", ""),
            "score": q.get("score", 10),
        }
        for i, q in enumerate(questions)
    ]

    # 创建考试记录
    exam = Exam(
        profile_id=profile.id,
        course_id=request.course_id,
        blueprint=blueprint,
        questions=questions,
        answer_key=answer_key,
        status="created",
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    # 添加学习轨迹
    profile.add_trajectory({
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "module": "AI考试助手",
        "content": f"创建考试 - {blueprint.get('objective', '')}",
        "ability": "综合测评",
        "change": 0,
    })
    db.commit()

    return ExamResponse(
        id=exam.id,
        blueprint=exam.blueprint,
        questions=exam.questions,
        status=exam.status,
        duration=exam.blueprint.get("duration_minutes", 60),
    )


@router.post("/submit")
async def submit_exam(submit: AnswerSubmit, db: Session = Depends(get_db)):
    """提交考试答案并自动评分"""
    exam = db.query(Exam).filter(Exam.id == submit.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 记录作答
    exam.answers = submit.answers
    exam.status = "in_progress"

    # 评分
    scoring = await llm.grade_answers(
        exam.questions or [],
        submit.answers,
        exam.answer_key or [],
    )

    # 评分结果
    exam.scoring = scoring
    exam.status = "completed"

    # 更新画像
    profile = db.query(LearningProfile).filter(
        LearningProfile.id == exam.profile_id
    ).first()

    report_data = {"scoring": scoring, "exam": exam.to_dict()}
    profile_data = profile.to_dict() if profile else {}

    # 生成学情报告
    report = await llm.generate_report(report_data, profile_data)
    exam.report = report

    if profile:
        profile.add_trajectory({
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "module": "AI考试助手",
            "content": f"完成考试 - 得分: {scoring.get('percentage', 0)}%",
            "ability": "能力评估",
            "change": scoring.get("percentage", 0) // 10,
        })

        # 根据考试成绩更新能力值
        if report.get("radar"):
            radar_scores = report["radar"].get("scores", [])
            if len(radar_scores) >= 6:
                profile.set_skills({
                    "business": radar_scores[0],
                    "dataAnalysis": radar_scores[1],
                    "aiApplication": radar_scores[2],
                    "decision": radar_scores[3],
                    "prompt": radar_scores[4],
                    "continuous": radar_scores[5],
                })

        # 更新评优
        new_score = scoring.get("percentage", 0)
        profile.score = max(profile.score or 0, new_score)
        db.commit()

    exam.status = "graded"
    db.commit()

    return {
        "exam_id": exam.id,
        "scoring": scoring,
        "report": report,
    }


@router.get("/{exam_id}")
async def get_exam(exam_id: str, db: Session = Depends(get_db)):
    """获取考试详情"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return exam.to_dict()


@router.get("/history/{profile_id}")
async def get_exam_history(profile_id: str, db: Session = Depends(get_db)):
    """获取考试历史"""
    exams = (
        db.query(Exam)
        .filter(Exam.profile_id == profile_id)
        .order_by(Exam.created_at.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "blueprint": e.blueprint,
            "status": e.status,
            "scoring": e.scoring,
            "report": e.report,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in exams
    ]


@router.get("/report/{exam_id}")
async def get_exam_report(exam_id: str, db: Session = Depends(get_db)):
    """获取考试学情报告"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != "graded":
        raise HTTPException(status_code=400, detail="考试尚未完成评分")
    return {
        "report": exam.report,
        "scoring": exam.scoring,
        "exam_id": exam.id,
    }
