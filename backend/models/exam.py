"""考试模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from database import Base


class Exam(Base):
    """考试 — 包含考试蓝图、题目、作答、评分和报告"""
    __tablename__ = "exams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("learning_profiles.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=True)

    # 考试蓝图
    blueprint = Column(JSON, default=dict)

    # 题目列表
    questions = Column(JSON, default=list)

    # 用户作答记录
    answers = Column(JSON, default=list)

    # 标准答案和评分标准
    answer_key = Column(JSON, default=list)

    # 评分结果
    scoring = Column(JSON, default=dict)

    # 学情报告
    report = Column(JSON, default=dict)

    # 状态: created, in_progress, completed, graded
    status = Column(String(20), default="created")

    # 考试用时（秒）
    duration = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "course_id": self.course_id,
            "blueprint": self.blueprint,
            "questions": self.questions,
            "answers": self.answers,
            "answer_key": self.answer_key,
            "scoring": self.scoring,
            "report": self.report,
            "status": self.status,
            "duration": self.duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExamQuestion(Base):
    """独立的题库表（扩展用）"""
    __tablename__ = "exam_questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_type = Column(String(30))       # 基础知识题, AI工具使用题, 数据分析题, 业务案例分析题, 经营决策题
    difficulty = Column(String(10))          # easy, medium, hard
    skill_dimension = Column(String(30))     # 对应的能力维度
    content = Column(JSON, default=dict)     # 题目内容
    answer = Column(Text, default="")        # 标准答案
    scoring_criteria = Column(JSON, default=dict)  # 评分标准
    created_at = Column(DateTime, default=datetime.utcnow)
