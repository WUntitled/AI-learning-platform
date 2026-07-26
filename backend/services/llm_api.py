"""
LLM API 服务

统一对外接口，根据配置自动选择：
- simulation --使用 SimulationGenerator 生成模拟内容
- claude --调用 Anthropic Claude API
- openai --调用 OpenAI API
- deepseek --调用 DeepSeek API
"""
from __future__ import annotations
import json
import httpx
from typing import Optional, AsyncGenerator, Any
from config import settings
from .llm_service import SimulationGenerator


class LLMService:
    """LLM 服务统一入口"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.simulator = SimulationGenerator()

    @property
    def provider_name(self) -> str:
        return self.provider

    def is_available(self) -> bool:
        """检查当前配置是否可用"""
        return settings.llm_available

    # ================================================================
    # 学情画像相关
    # ================================================================
    async def generate_skills(self, profile_input: dict) -> dict:
        """生成六维能力评估"""
        if self.provider == "simulation":
            return self.simulator.generate_skills(profile_input)

        # 真实LLM模式
        prompt = self._build_skills_prompt(profile_input)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self.simulator.generate_skills(profile_input))

    async def generate_diagnosis(self, profile_input: dict) -> dict:
        """生成学情诊断"""
        skills = await self.generate_skills(profile_input)
        return {
            "stage": skills.get("stage", "初级入门阶段"),
            "score": skills.get("score", 50),
            "gaps": skills.get("gaps", ""),
            "direction": skills.get("direction", ""),
            "skills": {k: v for k, v in skills.items()
                      if k in ("business", "dataAnalysis", "aiApplication",
                               "decision", "prompt", "continuous")},
            "aiLevel_label": skills.get("aiLevel_label", "L2"),
            "aiLabel": skills.get("aiLabel", "基础使用"),
            "bizLevel": skills.get("bizLevel", "L2"),
            "bizLabel": skills.get("bizLabel", "独立执行"),
        }

    # ================================================================
    # 课程相关
    # ================================================================
    async def generate_course(self, profile: dict) -> dict:
        """生成个性化课程"""
        if self.provider == "simulation":
            return self.simulator.generate_course(profile)

        prompt = self._build_course_prompt(profile)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self.simulator.generate_course(profile))

    # ================================================================
    # 考试相关
    # ================================================================
    async def generate_exam_blueprint(self, profile: dict) -> dict:
        """生成考试蓝图"""
        if self.provider == "simulation":
            return self.simulator.generate_exam_blueprint(profile)

        prompt = self._build_exam_blueprint_prompt(profile)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self.simulator.generate_exam_blueprint(profile))

    async def generate_questions(self, blueprint: dict, profile: dict = None) -> list:
        """生成考题"""
        if self.provider == "simulation":
            return self.simulator.generate_questions(blueprint, profile)

        prompt = self._build_questions_prompt(blueprint, profile)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self.simulator.generate_questions(blueprint, profile))

    async def grade_answers(self, questions: list, answers: list, answer_key: list) -> dict:
        """评卷评分"""
        if self.provider == "simulation":
            return self._simulate_grading(questions, answers, answer_key)

        prompt = self._build_grading_prompt(questions, answers, answer_key)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self._simulate_grading(questions, answers, answer_key))

    async def generate_report(self, exam_data: dict, profile: dict) -> dict:
        """生成学情报告"""
        if self.provider == "simulation":
            return self._simulate_report(exam_data, profile)

        prompt = self._build_report_prompt(exam_data, profile)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self._simulate_report(exam_data, profile))

    # ================================================================
    # 实战相关
    # ================================================================
    async def generate_scenario(self, scenario_type: str, profile: dict = None) -> dict:
        """生成实战场景"""
        if self.provider == "simulation":
            return self.simulator.generate_scenario(scenario_type, profile)

        prompt = self._build_scenario_prompt(scenario_type, profile)
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self.simulator.generate_scenario(scenario_type, profile))

    async def evaluate_practice(self, scenario: dict, user_answer: str, profile: dict = None) -> dict:
        """评估实战演练答案"""
        if self.provider == "simulation":
            return self._simulate_evaluate(scenario, user_answer)

        prompt = f"评估以下实战回答，给出评分和改进建议。\n场景：{json.dumps(scenario, ensure_ascii=False)}\n回答：{user_answer}"
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self._simulate_evaluate(scenario, user_answer))

    # ================================================================
    # 学习助手相关
    # ================================================================
    async def chat_response(self, messages: list, context: dict = None) -> str:
        """学习助手对话回复"""
        if self.provider == "simulation":
            return self._simulate_chat(messages, context)

        response = await self._call_llm(self._build_chat_prompt(messages, context))
        return response or self._simulate_chat(messages, context)

    async def analyze_session(self, messages: list) -> dict:
        """分析对话会话，提取学情信息"""
        if self.provider == "simulation":
            return self._simulate_session_analysis(messages)

        prompt = f"分析以下对话，提取用户学情信息。对话：{json.dumps(messages[-10:], ensure_ascii=False)}"
        response = await self._call_llm(prompt)
        return self._parse_json_response(response, self._simulate_session_analysis(messages))

    # ================================================================
    # 内部辅助方法
    # ================================================================

    def _simulate_grading(self, questions: list, answers: list, answer_key: list) -> dict:
        """模拟评分"""
        total_score = 0
        max_score = 0
        details = []

        for i, q in enumerate(questions):
            q_score = q.get("score", 10)
            max_score += q_score
            user_answer = ""
            for a in answers:
                if a.get("question_id") == q.get("id"):
                    user_answer = a.get("answer", "")
                    break

            # 模拟评分：检查答案中是否包含关键词
            correct = q.get("answer", "")
            is_correct = False
            if correct and user_answer:
                is_correct = correct[0].upper() in user_answer.upper()
            elif user_answer and len(user_answer) > 20:
                is_correct = True

            score = q_score if is_correct else 0
            total_score += score

            details.append({
                "question_id": q.get("id", f"q_{i}"),
                "question": q.get("stem", "")[:50],
                "correct_answer": correct,
                "user_answer": user_answer[:100],
                "score": score,
                "max_score": q_score,
                "is_correct": is_correct,
            })

        percentage = round((total_score / max_score * 100), 1) if max_score > 0 else 0
        return {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "details": details,
            "passed": percentage >= 60,
        }

    def _simulate_report(self, exam_data: dict, profile: dict) -> dict:
        """模拟生成学情报告"""
        scoring = exam_data.get("scoring", {})
        percentage = scoring.get("percentage", 0)
        details = scoring.get("details", [])

        # 分维度正确率
        dim_scores = {}
        for d in details:
            q = d.get("question", "")
            if "GMV" in q or "转化" in q or "漏斗" in q:
                dim = "业务理解"
            elif "AI" in q or "Prompt" in q:
                dim = "AI工具应用"
            elif "数据" in q or "点击" in q or "ROI" in q:
                dim = "数据分析"
            else:
                dim = "经营决策"

            if dim not in dim_scores:
                dim_scores[dim] = {"correct": 0, "total": 0}
            dim_scores[dim]["total"] += 1
            if d.get("is_correct", False):
                dim_scores[dim]["correct"] += 1

        # 六维能力更新
        old_skills = profile.get("skills", {}) if profile else {}
        growth_rate = min(15, max(0, (percentage - 50) // 5))
        new_skills = {
            "business": min(95, (old_skills.get("business", 50) or 50) + (5 if dim_scores.get("业务理解", {}).get("correct", 0) > 0 else 0)),
            "dataAnalysis": min(95, (old_skills.get("dataAnalysis", 50) or 50) + (5 if dim_scores.get("数据分析", {}).get("correct", 0) > 0 else 0)),
            "aiApplication": min(95, (old_skills.get("aiApplication", 50) or 50) + (5 if dim_scores.get("AI工具应用", {}).get("correct", 0) > 0 else 0)),
            "decision": min(95, (old_skills.get("decision", 50) or 50) + (5 if dim_scores.get("经营决策", {}).get("correct", 0) > 0 else 0)),
            "prompt": min(95, (old_skills.get("prompt", 50) or 50) + growth_rate // 2),
            "continuous": min(95, (old_skills.get("continuous", 50) or 50) + growth_rate),
        }

        return {
            "radar": {
                "dimensions": ["业务理解能力", "数据分析能力", "AI工具应用能力", "经营决策能力", "Prompt撰写能力", "持续迭代能力"],
                "scores": [new_skills["business"], new_skills["dataAnalysis"],
                          new_skills["aiApplication"], new_skills["decision"],
                          new_skills["prompt"], new_skills["continuous"]],
            },
            "heatmap": {
                "y_labels": ["商品分析", "用户分析", "渠道分析", "活动分析"],
                "x_labels": ["Excel", "SQL", "AI工具", "BI系统"],
                "data": [[random_between(20, 80) for _ in range(4)] for _ in range(4)],
            },
            "trend": {
                "labels": ["培训前", "阶段一", "阶段二", "阶段三", "本次"],
                "skill_scores": [max(0, new_skills["dataAnalysis"] - 30 + i * 8) for i in range(5)],
                "efficiency": [max(0, 90 - i * 12 + random_between(-5, 5)) for i in range(5)],
            },
            "suggestions": _generate_suggestions(new_skills, percentage),
            "summary": {
                "total_score": percentage,
                "passed": percentage >= 60,
                "skill_change": growth_rate,
                "weak_dimensions": [k for k, v in new_skills.items() if v < 55],
            },
        }

    def _simulate_evaluate(self, scenario: dict, user_answer: str) -> dict:
        """模拟实战评估"""
        if not user_answer or len(user_answer.strip()) < 10:
            return {
                "score": random.randint(10, 30),
                "feedback": "回答过于简短，请更详细地展开分析。",
                "dimensions": [
                    {"name": "分析完整性", "score": random.randint(10, 30)},
                    {"name": "逻辑清晰度", "score": random.randint(10, 30)},
                    {"name": "数据支撑", "score": random.randint(10, 30)},
                    {"name": "创新思维", "score": random.randint(10, 30)},
                ],
                "suggestions": ["请参考题目中的数据和提示，给出更完整的分析"],
            }

        return {
            "score": random.randint(55, 95),
            "feedback": "你的分析较为完整，逻辑清晰。建议在数据支撑和量化分析方面进一步加强。",
            "dimensions": [
                {"name": "分析完整性", "score": random.randint(60, 90)},
                {"name": "逻辑清晰度", "score": random.randint(60, 90)},
                {"name": "数据支撑", "score": random.randint(50, 85)},
                {"name": "创新思维", "score": random.randint(50, 85)},
            ],
            "suggestions": [
                "可以尝试使用更多定量分析来支撑结论",
                "考虑从多维度进行归因，避免单一角度",
            ],
        }

    def _simulate_chat(self, messages: list, context: dict = None) -> str:
        """模拟对话回复"""
        if not messages:
            return "您好！我是AI学习助手，有什么可以帮助您的吗？"

        last_msg = messages[-1].get("content", "") if messages else ""

        if "你好" in last_msg or "hello" in last_msg.lower():
            return "您好！欢迎来到AI辅助业务分析培训系统。我是您的学习助手，可以帮您解答关于电商业务分析、AI工具使用、数据分析方法等方面的问题。请问今天有什么可以帮助您的？"

        if "GMV" in last_msg:
            return "GMV（商品交易总额）是电商最核心的指标，计算公式为：\n\n**GMV = 访客数 × 转化率 × 客单价**\n\n当GMV出现波动时，建议从以下四个维度进行拆解分析：\n1. **流量维度** — 访客数的变化趋势\n2. **转化维度** — 转化率的升降原因\n3. **价格维度** — 客单价的变动\n4. **售后维度** — 退款率的影响\n\n需要我详细解释某个维度的分析方法吗？"

        if "Prompt" in last_msg or "prompt" in last_msg.lower():
            return "Prompt（提示词）的质量直接影响AI输出的效果。一个高质量的Prompt应包含以下要素：\n\n**1. 角色设定** — 告诉AI它应该扮演什么角色\n**2. 任务描述** — 清晰说明要完成什么任务\n**3. 约束条件** — 明确限制和边界\n**4. 输出格式** — 指定答案的组织形式\n\n例如：'你是一名电商数据分析师（角色），请分析这份月度销售数据（任务），从GMV趋势和品类表现两个维度进行（约束），以表格形式呈现（格式）。'"

        if "数据分析" in last_msg or "分析" in last_msg:
            return "在电商数据分析中，常用的分析方法包括：\n\n1. **对比分析** — 同比、环比、与目标对比\n2. **归因分析** — 找出影响业务指标的关键因素\n3. **漏斗分析** — 追踪用户在各环节的转化率\n4. **分群分析** — 对不同用户群体进行差异化分析\n\n每种方法都有其适用场景。您想深入了解哪一种？"

        if "考试" in last_msg or "测试" in last_msg:
            return "我建议您先通过AI考试助手完成一次能力测评，这样可以更准确地了解自己的知识掌握情况。当然，如果您有具体的问题需要解答，也可以直接问我！"

        if "实战" in last_msg or "练习" in last_msg:
            return "实战是巩固知识最好的方式！我建议您前往AI陪练助手模块，那里有针对不同场景的实战演练题，包括数据理解、AI分析、Prompt设计和业务决策四种类型。"

        # 默认回复
        return f"这是一个很好的问题！关于「{last_msg[:30]}」，我建议从以下几个方面来理解：\n\n首先，需要明确这个问题的业务背景。在电商业务分析中，每个问题都需要结合实际业务场景来具体分析。\n\n其次，可以尝试使用AI工具辅助分析。一个好的Prompt可以帮助AI更好地理解和回答您的问题。\n\n最后，建议您将理论知识应用到实际工作中，通过学习、思考、实践、复盘的循环来持续提升能力。\n\n如果您需要更详细的解答，请告诉我具体想了解哪个方面？"

    def _simulate_session_analysis(self, messages: list) -> dict:
        """模拟会话分析"""
        return {
            "topics_discussed": ["GMV分析", "Prompt设计", "数据分析方法"],
            "knowledge_gaps": ["高级归因分析", "AI工具深度应用"],
            "engagement_level": "high" if len(messages) > 6 else "medium",
            "suggested_focus": "建议加强归因分析和经营决策方面的学习",
            "profile_update": {
                "prompt": 55,
                "continuous": 60,
            },
        }

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """调用真实的LLM API"""
        if self.provider == "claude":
            return await self._call_claude(prompt)
        elif self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "deepseek":
            return await self._call_deepseek(prompt)
        return None

    async def _call_claude(self, prompt: str) -> Optional[str]:
        """调用 Claude API"""
        if not settings.CLAUDE_API_KEY:
            return None
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.CLAUDE_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": settings.CLAUDE_API_MODEL,
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("content", [{}])[0].get("text", "")
            except Exception:
                return None
        return None

    async def _call_openai(self, prompt: str) -> Optional[str]:
        """调用 OpenAI API"""
        if not settings.OPENAI_API_KEY:
            return None
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.OPENAI_API_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4096,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                return None
        return None

    async def _call_deepseek(self, prompt: str) -> Optional[str]:
        """调用 DeepSeek API"""
        if not settings.DEEPSEEK_API_KEY:
            return None
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    settings.DEEPSEEK_API_BASE + "/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4096,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                return None
        return None

    @staticmethod
    def _parse_json_response(response: Optional[str], fallback: Any) -> Any:
        """解析LLM返回的JSON，失败时使用fallback"""
        if not response:
            return fallback
        try:
            # 尝试从markdown代码块中提取JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return fallback

    @staticmethod
    def _build_skills_prompt(profile: dict) -> str:
        return f"根据以下学习者信息，评估其六维能力（业务理解、数据分析、AI应用、经营决策、Prompt撰写、持续迭代），输出JSON格式的能力值(0-100)和学习阶段。输入：{json.dumps(profile, ensure_ascii=False)}"

    @staticmethod
    def _build_course_prompt(profile: dict) -> str:
        return f"根据以下学习者画像，生成个性化培训课程内容。输出JSON格式的技能树、学习路径、知识卡、实战任务和案例。画像：{json.dumps(profile, ensure_ascii=False)}"

    @staticmethod
    def _build_exam_blueprint_prompt(profile: dict) -> str:
        return f"根据以下学习者画像，生成考试蓝图。输出JSON格式。画像：{json.dumps(profile, ensure_ascii=False)}"

    @staticmethod
    def _build_questions_prompt(blueprint: dict, profile: dict) -> str:
        return f"根据以下考试蓝图生成试题，输出JSON数组。蓝图：{json.dumps(blueprint, ensure_ascii=False)}"

    @staticmethod
    def _build_grading_prompt(questions: list, answers: list, answer_key: list) -> str:
        return f"评阅以下试卷。题目：{json.dumps(questions, ensure_ascii=False)}\n用户答案：{json.dumps(answers, ensure_ascii=False)}"

    @staticmethod
    def _build_report_prompt(exam_data: dict, profile: dict) -> str:
        return f"生成学情报告。考试数据：{json.dumps(exam_data, ensure_ascii=False)}\n画像：{json.dumps(profile, ensure_ascii=False)}"

    @staticmethod
    def _build_scenario_prompt(scenario_type: str, profile: dict) -> str:
        return f"生成{scenario_type}实战演练场景。画像：{json.dumps(profile, ensure_ascii=False)}"

    @staticmethod
    def _build_chat_prompt(messages: list, context: dict) -> str:
        return f"你是一个AI辅助业务分析培训系统的学习助手。对话历史：{json.dumps(messages[-10:], ensure_ascii=False)}"


def random_between(low: int, high: int) -> int:
    """生成范围内的随机数（文件级辅助函数）"""
    import random
    return random.randint(low, high)


def _generate_suggestions(skills: dict, score: float) -> list:
    """根据能力短板生成培训建议"""
    suggestions = []
    if skills.get("dataAnalysis", 50) < 55:
        suggestions.append("加强数据分析能力训练，重点学习对比分析和归因分析方法")
    if skills.get("aiApplication", 50) < 55:
        suggestions.append("建议多练习Prompt撰写，提高AI工具的应用熟练度")
    if skills.get("decision", 50) < 55:
        suggestions.append("加强经营决策训练，学习数据驱动的决策方法论")
    if skills.get("business", 50) < 55:
        suggestions.append("建议深入理解电商业务指标体系，打好业务基础")
    if skills.get("prompt", 50) < 55:
        suggestions.append("建议系统学习Prompt工程，这是人机协同的关键能力")
    if not suggestions:
        suggestions.append("整体能力均衡，建议挑战更高难度的课程和实战任务")

    if score < 60:
        suggestions.append("建议从基础课程开始，夯实核心概念和方法")
    elif score < 80:
        suggestions.append("整体基础较好，建议在薄弱维度进行重点突破")

    return suggestions
