"""
Agent基类体系

所有智能体继承自 BaseAgent，实现 process 方法。
AgentResult 承载执行结果与决策信息。
"""
from __future__ import annotations
import uuid
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEBATING = "debating"


class AgentResult(BaseModel):
    """Agent执行结果"""
    agent_name: str
    agent_idx: int
    status: AgentStatus = AgentStatus.COMPLETED
    output: dict = {}
    confidence: float = 1.0               # 置信度 0-1
    routing_hint: str = ""                # 路由提示：推荐下一个agent
    routing_decision: dict = {}           # 路由决策信息
    debate_passed: bool = True            # 是否通过辩论审核
    error: Optional[str] = None
    token_usage: dict = {}                # token使用情况（接入LLM时用）
    execution_time: float = 0.0           # 执行耗时(秒)


class BaseAgent:
    """所有Agent的基类

    子类需设置:
    - name: Agent名称
    - idx: Agent序号
    - description: Agent描述
    - input_schema: 输入格式描述
    - output_schema: 输出格式描述

    子类需实现:
    - async def process(self, input_data: dict, context: dict = None) -> AgentResult:
    """

    name: str = "base_agent"
    idx: int = 0
    description: str = ""
    input_schema: dict = {}
    output_schema: dict = {}

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self._id = str(uuid.uuid4())[:8]

    async def process(self, input_data: dict, context: dict = None) -> AgentResult:
        """处理输入并返回结果 — 子类必须实现"""
        raise NotImplementedError

    def get_info(self) -> dict:
        """获取Agent信息（用于前端展示）"""
        return {
            "idx": self.idx,
            "name": self.name,
            "cn_name": self.cn_name if hasattr(self, 'cn_name') else self.name,
            "en_name": self.en_name if hasattr(self, 'en_name') else self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "status": AgentStatus.IDLE,
        }

    async def validate_input(self, input_data: dict) -> bool:
        """验证输入是否满足基本要求"""
        return bool(input_data)
