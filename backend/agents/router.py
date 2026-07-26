"""
动态路由引擎

核心思想：不再使用固定Agent链，而是根据上下文动态决定下一个调用的Agent。

路由策略：
1. 上下文感知 — 根据当前状态和历史选择最佳路径
2. 条件分支 — 基于中间结果判断走哪条分支
3. 并行路由 — 可并行执行的Agent分发
4. 自适应调整 — 根据用户反馈动态调整路由
"""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel


class RoutingDecision(BaseModel):
    """路由决策"""
    next_agent_idx: int                     # 下一个执行的Agent序号
    next_agent_name: str                    # Agent名称
    confidence: float = 0.8                 # 决策置信度
    reasoning: str = ""                     # 决策理由
    parallel_branch: List[int] = []         # 并行分支的Agent列表（可选）
    terminate: bool = False                 # 是否终止流程
    feedback_needed: bool = False           # 是否需要用户反馈后再继续
    skip_reason: str = ""                   # 跳过某个Agent的原因


class RouterContext:
    """路由上下文 — 存储当前流程状态"""
    def __init__(self):
        self.completed_agents: List[int] = []
        self.current_agent: Optional[int] = None
        self.intermediate_results: dict = {}
        self.agent_outputs: dict = {}
        self.user_feedback: List[dict] = []
        self.loop_count: int = 0
        self.branch_path: List[str] = []

    def add_result(self, agent_idx: int, output: dict):
        """记录Agent执行结果"""
        self.completed_agents.append(agent_idx)
        self.agent_outputs[agent_idx] = output
        self.intermediate_results.update(output)

    def get_output(self, agent_idx: int) -> Optional[dict]:
        """获取指定Agent的输出"""
        return self.agent_outputs.get(agent_idx)

    def to_dict(self) -> dict:
        return {
            "completed_agents": self.completed_agents,
            "current_agent": self.current_agent,
            "branch_path": self.branch_path,
            "loop_count": self.loop_count,
        }


class DynamicRouter:
    """动态路由实现

    根据上下文、Agent之间的关联关系、以及中间结果来动态决策流程。
    """

    def __init__(self):
        self.routing_rules: dict = {}

    def register_rules(self, module: str, rules: dict):
        """注册模块的路由规则"""
        self.routing_rules[module] = rules

    async def decide(
        self,
        task: str,
        available_agents: List[dict],
        context: RouterContext,
        current_output: Optional[dict] = None,
    ) -> RoutingDecision:
        """核心路由决策方法

        根据当前上下文和输出，决定下一步该执行哪个Agent。
        """
        completed = context.completed_agents

        # ===== 策略1: 无已完成Agent → 从第一个开始 =====
        if not completed:
            first = available_agents[0]
            return RoutingDecision(
                next_agent_idx=first["idx"],
                next_agent_name=first["name"],
                reasoning="流程起始，从第一个Agent开始执行",
            )

        # ===== 策略2: 检查是否需要跳过某些Agent =====
        skip_decision = self._check_skip_conditions(completed, available_agents, context)
        if skip_decision:
            return skip_decision

        # ===== 策略3: 查找下一个未完成的Agent =====
        for agent in available_agents:
            if agent["idx"] not in completed:
                return RoutingDecision(
                    next_agent_idx=agent["idx"],
                    next_agent_name=agent["name"],
                    reasoning=f"顺序执行至下一个Agent: {agent['name']}",
                )

        # ===== 策略4: 检查是否需要循环/重试 =====
        if current_output and context.loop_count < 2:
            quality = current_output.get("quality_score", 1.0)
            if quality < 0.5:
                context.loop_count += 1
                return RoutingDecision(
                    next_agent_idx=available_agents[-2]["idx"],
                    next_agent_name=available_agents[-2]["name"],
                    reasoning=f"质量得分{quality}低于阈值，重试上一Agent",
                )

        # ===== 策略5: 所有Agent完成 =====
        return RoutingDecision(
            next_agent_idx=-1,
            next_agent_name="",
            terminate=True,
            reasoning="所有Agent已完成执行",
        )

    def _check_skip_conditions(
        self,
        completed: List[int],
        available_agents: List[dict],
        context: RouterContext,
    ) -> Optional[RoutingDecision]:
        """检查是否需要跳过某些Agent"""
        # 如果某个Agent的输出表明不需要后续处理
        for idx in completed:
            output = context.get_output(idx)
            if output and output.get("skip_next", False):
                skip_idx = idx + 1
                for agent in available_agents:
                    if agent["idx"] == skip_idx:
                        return RoutingDecision(
                            next_agent_idx=skip_idx + 1 if skip_idx + 1 < len(available_agents) else -1,
                            next_agent_name=agent["name"],
                            skip_reason=output.get("skip_reason", ""),
                            reasoning=f"Agent {idx} 输出指示跳过 {agent['name']}",
                        )
        return None

    def get_parallel_branches(
        self,
        agent_idx: int,
        available_agents: List[dict],
        context: RouterContext,
    ) -> List[int]:
        """判断当前Agent是否可以并行执行后续分支"""
        # 识别可并行的场景
        if agent_idx == 4:  # 内容生成后可并行评估
            return [a["idx"] for a in available_agents if a["idx"] in [5, 6]]
        return []
