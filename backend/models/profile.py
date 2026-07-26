"""学情画像模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from database import Base


class LearningProfile(Base):
    """学习画像 — 存储用户的学情画像、能力评估、学习轨迹"""
    __tablename__ = "learning_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # 基本信息
    name = Column(String(100), nullable=False, default="学习者")
    role = Column(String(100), default="业务分析师")        # 岗位类型
    experience = Column(String(50), default="1-3年")         # 工作年限
    ecommerce_exp = Column(Text, default="")                 # 电商/业务经验
    ai_level = Column(String(50), default="基础使用")        # AI经验
    learning_goal = Column(Text, default="")                 # 学习目标

    # 六维能力 (0-100)
    skills_business = Column(Integer, default=50)            # 业务理解能力
    skills_data_analysis = Column(Integer, default=50)       # 数据分析能力
    skills_ai_application = Column(Integer, default=50)      # AI工具应用能力
    skills_decision = Column(Integer, default=50)            # 经营决策能力
    skills_prompt = Column(Integer, default=50)              # Prompt撰写能力
    skills_continuous = Column(Integer, default=50)          # 持续迭代学习能力

    # 评估结果
    stage = Column(String(50), default="初级入门阶段")       # 学习阶段
    score = Column(Integer, default=50)                      # 综合评分
    gaps = Column(Text, default="")                          # 知识缺口
    direction = Column(String(200), default="")              # 推荐方向

    # 能力等级标签
    ai_level_label = Column(String(10), default="L2")
    ai_label = Column(String(50), default="基础使用")
    biz_level = Column(String(10), default="L2")
    biz_label = Column(String(50), default="独立执行")

    # 学习轨迹 (JSON 数组)
    trajectory = Column(JSON, default=list)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "experience": self.experience,
            "ecommerce_exp": self.ecommerce_exp,
            "ai_level": self.ai_level,
            "learning_goal": self.learning_goal,
            "skills": {
                "business": self.skills_business,
                "dataAnalysis": self.skills_data_analysis,
                "aiApplication": self.skills_ai_application,
                "decision": self.skills_decision,
                "prompt": self.skills_prompt,
                "continuous": self.skills_continuous,
            },
            "stage": self.stage,
            "score": self.score,
            "gaps": self.gaps,
            "direction": self.direction,
            "aiLevel_label": self.ai_level_label,
            "aiLabel": self.ai_label,
            "bizLevel": self.biz_level,
            "bizLabel": self.biz_label,
            "trajectory": self.trajectory or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def set_skills(self, skills_dict: dict):
        """批量设置六维能力值"""
        mapping = {
            "business": "skills_business",
            "dataAnalysis": "skills_data_analysis",
            "aiApplication": "skills_ai_application",
            "decision": "skills_decision",
            "prompt": "skills_prompt",
            "continuous": "skills_continuous",
        }
        for key, attr in mapping.items():
            if key in skills_dict:
                setattr(self, attr, skills_dict[key])

    def get_skills_list(self) -> list:
        """返回六维能力列表（用于雷达图）"""
        return [
            self.skills_business or 50,
            self.skills_data_analysis or 50,
            self.skills_ai_application or 50,
            self.skills_decision or 50,
            self.skills_prompt or 50,
            self.skills_continuous or 50,
        ]

    def add_trajectory(self, entry: dict):
        """添加学习轨迹条目"""
        traj = list(self.trajectory or [])
        traj.insert(0, entry)
        self.trajectory = traj
