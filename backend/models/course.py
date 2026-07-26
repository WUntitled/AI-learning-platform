"""课程模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from database import Base


class Course(Base):
    """个性化课程 — 由AI做课助手生成"""
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("learning_profiles.id"), nullable=False)

    # 课程内容 (JSON)
    skill_tree = Column(JSON, default=dict)           # 技能树与学习路径图
    learning_path = Column(JSON, default=list)        # 学习路径规划
    knowledge_cards = Column(JSON, default=list)      # 技能知识卡
    tasks = Column(JSON, default=list)                # 任务型技能文档
    cases = Column(JSON, default=list)                # 示范案例

    # 课程来源（generated=AI生成, template=模板）
    source = Column(String(20), default="generated")
    status = Column(String(20), default="draft")      # draft, completed

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "skill_tree": self.skill_tree,
            "learning_path": self.learning_path,
            "knowledge_cards": self.knowledge_cards,
            "tasks": self.tasks,
            "cases": self.cases,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
