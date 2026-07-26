"""
Agent引擎 — 多智能体协同执行的核心

职责：
1. 管理Agent生命周期
2. 协调Agent之间的路由与通信
3. 执行辩论审核
4. 生成执行轨迹可视化数据
5. 确保内容合理性与真实性
"""
from __future__ import annotations
import asyncio
import time
from typing import List, Dict, Optional, Callable
from .base import BaseAgent, AgentResult, AgentStatus
from .router import DynamicRouter, RouterContext, RoutingDecision
from .debate import DebateMechanism, DebateResult


class AgentEngine:
    """多智能体协同执行引擎

    支持两种模式：
    1. pipeline模式 — 顺序执行固定Agent链
    2. dynamic模式 — 动态路由决策执行路径
    """

    def __init__(self, llm_service=None):
        self.agents: Dict[int, BaseAgent] = {}
        self.router = DynamicRouter()
        self.debater = DebateMechanism(llm_service=llm_service, use_llm=False)
        self.llm = llm_service
        self.on_agent_status: Optional[Callable] = None  # 状态变更回调

    def register_agent(self, agent: BaseAgent):
        """注册一个Agent到引擎"""
        self.agents[agent.idx] = agent

    def register_agents(self, *agents: BaseAgent):
        """批量注册Agent"""
        for agent in agents:
            self.register_agent(agent)

    def get_agents_info(self) -> list:
        """获取所有Agent信息（用于前端展示）"""
        return [a.get_info() for a in sorted(self.agents.values(), key=lambda x: x.idx)]

    def set_status_callback(self, callback: Callable):
        """设置Agent状态变更回调"""
        self.on_agent_status = callback

    async def _notify_status(self, agent_idx: int, status: AgentStatus, data: dict = None):
        """通知前端Agent状态变更（通过WebSocket/SSE）"""
        if self.on_agent_status:
            await self.on_agent_status({
                "type": "agent_status",
                "agent_idx": agent_idx,
                "status": status.value,
                "data": data or {},
                "timestamp": time.time(),
            })

    async def execute_pipeline(
        self,
        input_data: dict,
        context: dict = None,
        enable_debate: bool = True,
    ) -> List[AgentResult]:
        """按顺序执行所有Agent（pipeline模式）

        每步执行前先经过路由决策判断是否跳过/分支，
        生成内容后经过辩论审核。
        """
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.idx)
        router_ctx = RouterContext()
        results = []

        for i, agent in enumerate(sorted_agents):
            # === 路由决策 ===
            decision = await self.router.decide(
                task=context.get("task", "") if context else "",
                available_agents=[a.get_info() for a in sorted_agents],
                context=router_ctx,
                current_output=results[-1].output if results else None,
            )

            if decision.terminate:
                break

            if decision.skip_reason:
                # 跳过此Agent
                continue

            # === 执行Agent ===
            await self._notify_status(agent.idx, AgentStatus.RUNNING)
            start_time = time.time()

            try:
                result = await agent.process(input_data, context)
                result.execution_time = time.time() - start_time
                router_ctx.add_result(agent.idx, result.output)

                # === 辩论审核（可选）===
                if enable_debate and result.confidence < 0.9:
                    debate_result = await self.debater.debate(result.output, context)
                    result.debate_passed = debate_result.passed
                    result.confidence = debate_result.score
                    if not debate_result.passed:
                        await self._notify_status(
                            agent.idx, AgentStatus.DEBATING,
                            {"debate_issues": debate_result.issues}
                        )

                result.status = AgentStatus.COMPLETED if result.debate_passed else AgentStatus.FAILED
                results.append(result)

                await self._notify_status(
                    agent.idx, result.status,
                    {"output": result.output, "confidence": result.confidence}
                )

            except Exception as e:
                result = AgentResult(
                    agent_name=agent.name,
                    agent_idx=agent.idx,
                    status=AgentStatus.FAILED,
                    error=str(e),
                )
                results.append(result)
                await self._notify_status(agent.idx, AgentStatus.FAILED, {"error": str(e)})

        return results

    async def execute_dynamic(
        self,
        input_data: dict,
        context: dict = None,
        enable_debate: bool = True,
    ) -> List[AgentResult]:
        """动态路由模式执行

        每一步都通过路由决策选择下一个Agent，
        支持分支、循环、条件跳转。
        """
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.idx)
        router_ctx = RouterContext()
        results = []
        max_steps = len(sorted_agents) * 2  # 防止死循环

        for step in range(max_steps):
            # 路由决策：选下一个Agent
            decision = await self.router.decide(
                task=context.get("task", "") if context else "",
                available_agents=[a.get_info() for a in sorted_agents],
                context=router_ctx,
                current_output=results[-1].output if results else None,
            )

            if decision.terminate:
                break

            # 处理并行分支
            if decision.parallel_branch:
                branch_results = await self._execute_parallel(
                    [a for a in sorted_agents if a.idx in decision.parallel_branch],
                    input_data, context
                )
                for br in branch_results:
                    router_ctx.add_result(br.agent_idx, br.output)
                    results.append(br)
                continue

            # 找对应的Agent
            agent = self.agents.get(decision.next_agent_idx)
            if not agent:
                continue

            # 执行单Agent
            await self._notify_status(agent.idx, AgentStatus.RUNNING)
            start_time = time.time()

            try:
                result = await agent.process(input_data, context)
                result.execution_time = time.time() - start_time
                router_ctx.add_result(agent.idx, result.output)

                # 辩论审核
                if enable_debate:
                    debate_result = await self.debater.debate(result.output, context)
                    result.debate_passed = debate_result.passed
                    result.confidence = debate_result.score

                result.status = AgentStatus.COMPLETED if result.debate_passed else AgentStatus.FAILED
                results.append(result)
                await self._notify_status(agent.idx, result.status, {
                    "output": result.output,
                    "confidence": result.confidence,
                })

            except Exception as e:
                result = AgentResult(
                    agent_name=agent.name,
                    agent_idx=agent.idx,
                    status=AgentStatus.FAILED,
                    error=str(e),
                )
                results.append(result)
                await self._notify_status(agent.idx, AgentStatus.FAILED, {"error": str(e)})

            # 小延迟让前端可视化更新
            await asyncio.sleep(0.1)

        return results

    async def _execute_parallel(
        self,
        agents: List[BaseAgent],
        input_data: dict,
        context: dict = None,
    ) -> List[AgentResult]:
        """并行执行多个Agent"""
        async def run_one(agent: BaseAgent) -> AgentResult:
            await self._notify_status(agent.idx, AgentStatus.RUNNING)
            try:
                result = await agent.process(input_data, context)
                await self._notify_status(agent.idx, result.status, {
                    "output": result.output
                })
                return result
            except Exception as e:
                return AgentResult(
                    agent_name=agent.name,
                    agent_idx=agent.idx,
                    status=AgentStatus.FAILED,
                    error=str(e),
                )

        return await asyncio.gather(*[run_one(a) for a in agents])
