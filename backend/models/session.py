"""对话和实战会话模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from database import Base


class ChatSession(Base):
    """AI学习助手 — 对话会话"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("learning_profiles.id"), nullable=False)

    # 对话历史 [{role, content, agent?, timestamp}]
    messages = Column(JSON, default=list)

    # 当前对话上下文（用于多Agent路由决策）
    context = Column(JSON, default=dict)

    # 会话主题
    topic = Column(String(200), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "messages": self.messages,
            "context": self.context,
            "topic": self.topic,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PracticeSession(Base):
    """AI陪练助手 — 实战演练会话"""
    __tablename__ = "practice_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("learning_profiles.id"), nullable=False)

    # 实战类型
    scenario_type = Column(String(50))  # 数据理解类, AI分析类, Prompt设计类, 业务决策类
    scenario = Column(JSON, default=dict)       # 场景描述
    user_answer = Column(Text, default="")      # 用户作答
    evaluation = Column(JSON, default=dict)     # 评估结果
    score = Column(Integer, default=0)          # 得分

    status = Column(String(20), default="created")  # created, in_progress, completed

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "scenario_type": self.scenario_type,
            "scenario": self.scenario,
            "user_answer": self.user_answer,
            "evaluation": self.evaluation,
            "score": self.score,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
