"""
辩论式内容审核机制

核心思想：通过"生成方→质疑方→证据方→裁判方"四轮交叉验证，
降低大模型在垂直领域的幻觉。

流程：
1. 生成方(Generator) — 生成初始内容
2. 质疑方(Challenger) — 对内容提出质疑，找出不准确/不合理的部分
3. 证据方(Evidencer) — 引用证据支持或反驳质疑
4. 裁判方(Judge) — 综合评判，决定内容是否通过审核
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel


class DebateRole(str, Enum):
    GENERATOR = "generator"       # 生成方
    CHALLENGER = "challenger"     # 质疑方
    EVIDENCER = "evidencer"       # 证据方
    JUDGE = "judge"               # 裁判方


class DebateRound(BaseModel):
    """一轮辩论的记录"""
    role: DebateRole
    content: str
    findings: list = []
    confidence: float = 0.0


class DebateResult(BaseModel):
    """辩论最终结果"""
    passed: bool = False                       # 是否通过审核
    final_content: dict = {}                   # 审核后的内容
    issues: list = []                          # 发现的问题
    score: float = 0.0                         # 综合质量评分 (0-1)
    improvement_suggestions: list = []         # 改进建议
    rounds: list[DebateRound] = []             # 辩论轮次记录


class DebateMechanism:
    """辩论审核机制

    使用模拟/LLM驱动的内容审核流程。
    当前实现使用基于规则的模拟审核；
    接入LLM后自动切换为真正的辩论模式。
    """

    def __init__(self, llm_service=None, use_llm: bool = False):
        self.llm = llm_service
        self.use_llm = use_llm

    async def debate(self, content: dict, context: dict = None) -> DebateResult:
        """对生成的内容执行辩论审核

        Args:
            content: 待审核的内容
            context: 审核上下文（画像、岗位等信息）

        Returns:
            DebateResult: 审核结果
        """
        if self.use_llm and self.llm:
            return await self._llm_debate(content, context)
        return self._simulated_debate(content, context)

    def _simulated_debate(self, content: dict, context: dict = None) -> DebateResult:
        """模拟的辩论审核（无LLM时使用）"""
        rounds = []
        issues = []
        passed = True
        score = 1.0
        improvements = []

        # 阶段1: 生成方 - 陈述内容
        rounds.append(DebateRound(
            role=DebateRole.GENERATOR,
            content=f"内容已生成: {len(str(content))}字符",
            confidence=0.9,
        ))

        # 阶段2: 质疑方 - 检查内容合理性
        challenger_findings = self._simulate_challenge(content, context)
        if challenger_findings:
            issues.extend(challenger_findings)
            score -= len(challenger_findings) * 0.1
            rounds.append(DebateRound(
                role=DebateRole.CHALLENGER,
                content=f"发现 {len(challenger_findings)} 个潜在问题",
                findings=challenger_findings,
                confidence=0.7,
            ))
        else:
            rounds.append(DebateRound(
                role=DebateRole.CHALLENGER,
                content="未发现显著问题",
                confidence=0.6,
            ))

        # 阶段3: 证据方 - 引用证据
        evidence = self._simulate_evidence(content, issues)
        rounds.append(DebateRound(
            role=DebateRole.EVIDENCER,
            content=evidence["summary"],
            findings=evidence.get("confirmed_issues", []),
            confidence=evidence.get("confidence", 0.8),
        ))

        # 阶段4: 裁判方 - 综合判决
        if issues:
            verified_issues = [i for i in issues if i.get("verified", False)]
            if verified_issues:
                passed = False
                score = max(0.3, 1.0 - len(verified_issues) * 0.2)
                improvements = [
                    f"修复: {i.get('description', '未知问题')}"
                    for i in verified_issues[:3]
                ]
            else:
                score = max(0.7, 1.0 - len(issues) * 0.05)

        rounds.append(DebateRound(
            role=DebateRole.JUDGE,
            content=f"最终判决: {'通过' if passed else '未通过'} (评分: {score:.2f})",
            confidence=score,
        ))

        return DebateResult(
            passed=passed,
            final_content=content,
            issues=issues,
            score=score,
            improvement_suggestions=improvements,
            rounds=rounds,
        )

    def _simulate_challenge(self, content: dict, context: dict = None) -> list:
        """模拟质疑方的检查逻辑"""
        findings = []

        # 检查空内容
        if not content:
            findings.append({
                "type": "empty_content",
                "severity": "critical",
                "description": "内容为空",
                "verified": True,
            })
            return findings

        # 检查用户输入为空但评分却很高的情况
        if context:
            profile = context.get("profile", {})
            if profile and not any([
                profile.get("name"),
                profile.get("ecommerce_exp"),
                profile.get("learning_goal"),
            ]):
                findings.append({
                    "type": "input_empty",
                    "severity": "high",
                    "description": "用户输入信息为空，但系统生成了内容",
                    "verified": True,
                })

        # 检查分数合理性
        if "skill_scores" in content:
            scores = content["skill_scores"]
            empty_input = context and not context.get("has_input", True)
            if empty_input and any(s > 80 for s in scores if isinstance(s, (int, float))):
                findings.append({
                    "type": "unreasonable_score",
                    "severity": "high",
                    "description": "用户无有效输入但能力评分过高",
                    "verified": True,
                })

        # 检查生成内容的岗位匹配度
        if "role" in content and context and "profile" in context:
            profile_role = context["profile"].get("role", "")
            content_role = content.get("role", "")
            if profile_role and content_role and profile_role != content_role:
                findings.append({
                    "type": "role_mismatch",
                    "severity": "medium",
                    "description": f"内容岗位({content_role})与用户岗位({profile_role})不匹配",
                    "verified": False,
                })

        return findings

    def _simulate_evidence(self, content: dict, issues: list) -> dict:
        """模拟证据方的验证"""
        confirmed = []
        for issue in issues:
            if issue.get("severity") == "critical":
                confirmed.append(issue)
        return {
            "summary": f"验证完成: {len(confirmed)}/{len(issues)} 个问题确认",
            "confirmed_issues": confirmed,
            "confidence": 0.85,
        }

    async def _llm_debate(self, content: dict, context: dict = None) -> DebateResult:
        """基于LLM的正式辩论审核"""
        # 待接入LLM后实现
        return self._simulated_debate(content, context)
