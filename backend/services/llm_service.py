"""
LLM服务抽象层

支持多种LLM提供商和模拟模式：
- simulation: 内置模拟数据（无需API Key）
- claude: Anthropic Claude API
- openai: OpenAI API
- deepseek: DeepSeek API

模拟模式下生成的内容会考虑用户画像，确保合理性。
"""
from __future__ import annotations
import json
import random
import httpx
from typing import Optional, AsyncGenerator, Any
from config import settings


class SimulationGenerator:
    """模拟内容生成器 — 根据用户画像生成合理的培训内容"""

    @staticmethod
    def _get_role_info(role: str) -> dict:
        """根据岗位获取对应的能力模板"""
        templates = {
            "电商运营": {
                "skills": {"business": 70, "dataAnalysis": 65, "aiApplication": 55,
                          "decision": 60, "prompt": 50, "continuous": 60},
                "direction": "AI辅助电商运营分析",
                "gaps": ["数据分析", "AI工具应用", "Prompt撰写"],
                "course_emphasis": "电商数据分析与AI运营优化",
            },
            "业务分析师": {
                "skills": {"business": 65, "dataAnalysis": 70, "aiApplication": 60,
                          "decision": 65, "prompt": 55, "continuous": 60},
                "direction": "AI辅助业务分析决策",
                "gaps": ["AI工具应用", "经营决策", "Prompt撰写"],
                "course_emphasis": "AI辅助业务分析方法论",
            },
            "产品经理": {
                "skills": {"business": 60, "dataAnalysis": 55, "aiApplication": 65,
                          "decision": 55, "prompt": 60, "continuous": 65},
                "direction": "AI辅助产品分析",
                "gaps": ["数据分析", "经营决策"],
                "course_emphasis": "AI辅助产品数据分析",
            },
        }
        return templates.get(role, templates["业务分析师"])

    @staticmethod
    def _adjust_skills_for_experience(skills: dict, experience: str) -> dict:
        """根据工作年限调整能力值"""
        exp_multipliers = {
            "1年以下": 0.7,
            "1-3年": 0.85,
            "3-5年": 1.0,
            "5年以上": 1.1,
        }
        mult = exp_multipliers.get(experience, 0.85)
        return {k: min(95, int(v * mult * random.uniform(0.9, 1.1)))
                for k, v in skills.items()}

    @staticmethod
    def _adjust_skills_for_ai(skills: dict, ai_level: str) -> dict:
        """根据AI经验水平调整AI相关能力"""
        ai_bonus = {"未使用": 0.6, "基础使用": 0.85, "熟练使用": 1.0}
        mult = ai_bonus.get(ai_level, 0.85)
        adjusted = dict(skills)
        adjusted["aiApplication"] = min(95, int(adjusted["aiApplication"] * mult))
        adjusted["prompt"] = min(95, int(adjusted["prompt"] * mult * 0.9))
        return adjusted

    @staticmethod
    def _compute_stage_and_score(skills: dict) -> tuple:
        """根据能力值计算学习阶段和综合评分"""
        avg = sum(skills.values()) / len(skills)
        if avg >= 80:
            return "高级进阶阶段", int(avg), 3
        elif avg >= 60:
            return "中级成长阶段", int(avg), 2
        else:
            return "初级入门阶段", max(35, int(avg)), 1

    @staticmethod
    def _get_gaps(skills: dict) -> str:
        """找出能力短板"""
        dims = [
            ("业务理解能力", skills.get("business", 50)),
            ("数据分析能力", skills.get("dataAnalysis", 50)),
            ("AI工具应用能力", skills.get("aiApplication", 50)),
            ("经营决策能力", skills.get("decision", 50)),
            ("Prompt撰写能力", skills.get("prompt", 50)),
            ("持续迭代能力", skills.get("continuous", 50)),
        ]
        gaps = [d[0] for d in dims if d[1] < 60]
        if not gaps:
            gaps = ["数据分析"]
        return " · ".join(gaps[:3])

    # ================================================================
    # 内容生成方法
    # ================================================================

    @classmethod
    def generate_skills(cls, profile: dict = None) -> dict:
        """生成六维能力值（确保输入为空时分数合理）"""
        if not profile or not profile.get("name"):
            # 无有效输入 → 低分
            return {
                "business": random.randint(15, 30),
                "dataAnalysis": random.randint(10, 25),
                "aiApplication": random.randint(10, 25),
                "decision": random.randint(15, 30),
                "prompt": random.randint(5, 20),
                "continuous": random.randint(20, 35),
                "stage": "未评估",
                "score": random.randint(15, 25),
                "gaps": "业务理解能力 · 数据分析能力 · AI工具应用能力 · 经营决策能力 · Prompt撰写能力",
                "direction": "请先完善个人学习信息",
            }

        role = profile.get("role", "业务分析师")
        experience = profile.get("experience", "1-3年")
        ai_level = profile.get("ai_level", "基础使用")

        # 基础能力
        template = cls._get_role_info(role)
        skills = template["skills"].copy()

        # 应用经验调整
        skills = cls._adjust_skills_for_experience(skills, experience)
        skills = cls._adjust_skills_for_ai(skills, ai_level)

        # 确保AI经验低的人AI相关能力低
        if ai_level == "未使用":
            skills["aiApplication"] = min(skills["aiApplication"], 30)
            skills["prompt"] = min(skills["prompt"], 20)

        # 计算阶段和评分
        stage, score, level = cls._compute_stage_and_score(skills)
        gaps = cls._get_gaps(skills)

        # 综合考核 — 如果有任何输入缺失，降低整体置信度
        input_penalty = 0
        if not profile.get("ecommerce_exp"):
            input_penalty += 5
        if not profile.get("learning_goal"):
            input_penalty += 5

        adjusted_score = max(15, score - input_penalty)

        # 确保低输入的用户分数不会异常高
        has_real_input = bool(profile.get("ecommerce_exp") or profile.get("learning_goal"))
        if not has_real_input:
            adjusted_score = min(adjusted_score, 35)
            skills = {k: min(v, 40) for k, v in skills.items()}
            stage = "初级入门阶段"

        return {
            **skills,
            "stage": stage,
            "score": adjusted_score,
            "gaps": gaps,
            "direction": template["direction"],
            "aiLevel_label": f"L{level}",
            "aiLabel": ai_level if ai_level != "基础使用" else ("基础使用" if level >= 2 else "初学"),
            "bizLevel": f"L{max(1, level - 1)}",
            "bizLabel": "独立执行" if level >= 2 else "初学",
        }

    @classmethod
    def generate_course(cls, profile: dict = None) -> dict:
        """生成个性化培训课程内容"""
        if not profile or not profile.get("name"):
            return cls._default_course("业务分析师")

        role = profile.get("role", "业务分析师")
        stage = profile.get("stage", "初级入门阶段")
        skills = {
            "business": profile.get("skills", {}).get("business", 50),
            "dataAnalysis": profile.get("skills", {}).get("dataAnalysis", 50),
            "aiApplication": profile.get("skills", {}).get("aiApplication", 50),
            "decision": profile.get("skills", {}).get("decision", 50),
            "prompt": profile.get("skills", {}).get("prompt", 50),
        }

        course_data = cls._default_course(role)

        # 根据能力水平调整课程深度
        avg_skill = sum(skills.values()) / len(skills) if skills else 50
        if avg_skill < 40:
            # 入门级 — 更基础的内容
            course_data["skill_tree"]["children"] = [
                {"name": "电商业务基础概念", "level": "入门"},
                {"name": "AI工具入门", "level": "入门"},
                {"name": "数据基础认知", "level": "入门"},
                {"name": "业务分析思维入门", "level": "入门"},
                {"name": "案例观摩", "level": "入门"},
            ]
            course_data["learning_path"] = [
                {"phase": "阶段一", "title": "电商业务基础", "desc": "掌握电商核心指标与业务分析基本概念",
                 "skills": ["GMV/UV/转化率概念", "电商经营模式", "数据分析基础"]},
                {"phase": "阶段二", "title": "AI工具认知", "desc": "了解AI能做什么，学会简单的AI工具使用",
                 "skills": ["AI基础认知", "Prompt基本写法", "AI对话技巧"]},
                {"phase": "阶段三", "title": "数据分析入门", "desc": "学会阅读销售报表、商品分析报告等基本报表",
                 "skills": ["报表阅读", "指标理解", "趋势判断"]},
            ]
        elif avg_skill >= 70:
            # 高级 — 更深度的内容
            course_data["skill_tree"]["children"] = [
                {"name": "高级数据分析与建模", "level": "高级"},
                {"name": "AI辅助经营决策", "level": "高级"},
                {"name": "Prompt高阶工程", "level": "核心"},
                {"name": "多维度归因分析", "level": "高级"},
                {"name": "企业级案例分析", "level": "高级"},
            ]
            course_data["learning_path"] = [
                {"phase": "阶段一", "title": "高级数据方法", "desc": "掌握多维归因、漏斗分析、用户画像建模",
                 "skills": ["多维归因", "漏斗分析", "用户画像建模"]},
                {"phase": "阶段二", "title": "AI深度应用", "desc": "系统化Prompt工程，AI协同分析复杂业务",
                 "skills": ["Prompt系统工程", "AI协同分析", "自动化报告"]},
                {"phase": "阶段三", "title": "经营决策优化", "desc": "基于数据驱动的ROI优化与经营策略制定",
                 "skills": ["ROI深度优化", "预算智能分配", "经营战略制定"]},
                {"phase": "阶段四", "title": "案例实战", "desc": "完整的企业级业务分析项目实战",
                 "skills": ["全流程分析", "高阶决策", "项目管理"]},
            ]

        # 根据Prompt能力调整相关内容
        if skills.get("prompt", 50) < 40:
            course_data["knowledge_cards"] = [{
                "title": "Prompt基础写法",
                "concept": "Prompt是用户向AI描述任务的指令文本。一个好的Prompt需要清晰、具体、结构化。",
                "formula": "角色 + 任务 + 要求 + 输出格式 = 高质量Prompt",
                "bizExp": "例如：'你是一个电商数据分析师，分析这份销售报表的GMV下降原因，从流量、转化、客单价三个维度给出归因分析。'",
                "mistake": '常见错误：指令模糊（"帮我分析一下"）、缺少约束条件、未指定输出格式。'
            }]

        return course_data

    @classmethod
    def _default_course(cls, role: str) -> dict:
        """默认课程模板"""
        return {
            "skill_tree": {
                "root": "AI辅助业务分析能力体系",
                "children": [
                    {"name": "电商业务基础知识", "level": "入门"},
                    {"name": "数据分析与归因方法", "level": "进阶"},
                    {"name": "Prompt工程与设计", "level": "核心"},
                    {"name": "AI辅助经营决策", "level": "进阶"},
                    {"name": "业务案例实战分析", "level": "高级"},
                ],
            },
            "learning_path": [
                {"phase": "阶段一", "title": "业务分析基础",
                 "desc": "掌握电商核心指标、经营分析框架与数据采集方法",
                 "skills": ["GMV指标体系", "电商经营分析", "数据采集与清洗"]},
                {"phase": "阶段二", "title": "AI工具应用",
                 "desc": "学习Prompt工程设计方法，掌握AI辅助分析工具",
                 "skills": ["Prompt工程", "AI协同分析", "工具应用实践"]},
                {"phase": "阶段三", "title": "数据分析实践",
                 "desc": "运用对比分析、归因分析等方法解决真实业务问题",
                 "skills": ["对比分析", "归因分析", "漏斗分析", "留存分析"]},
                {"phase": "阶段四", "title": "经营决策训练",
                 "desc": "基于数据驱动的经营决策方法，提升ROI与经营效率",
                 "skills": ["ROI优化", "预算分配", "经营诊断", "策略制定"]},
            ],
            "knowledge_cards": [
                {
                    "title": "GMV下降原因分析框架",
                    "concept": "GMV是电商最核心的经营指标。当GMV下降时，需要从流量、转化、客单价、退款四个维度进行系统性诊断。",
                    "formula": "GMV = 访客数 × 转化率 × 客单价",
                    "bizExp": f"假设某{role}发现上月的GMV同比下降15%，拆解发现：访客数▲3.6%，转化率▼34%（从3.8%降至2.5%），客单价▼7.7%。核心问题在转化率。",
                    "mistake": "常见错误：只看GMV绝对值下降就归因于流量不足，应先从公式拆解再诊断。"
                },
                {
                    "title": "归因分析模型",
                    "concept": "归因分析用于确定导致业务变化的关键因素。通过对比分析、贡献度计算等方法找出问题根源。",
                    "formula": "贡献度 = (因素变化量 / 总变化量) × 100%",
                    "bizExp": "某活动ROI从3.2降至2.1，归因发现：广告精准度下降贡献度52%，竞争加剧贡献度28%，季节性因素20%。",
                    "mistake": "避免只关注一个维度，要综合考虑内外部因素的交互影响。"
                },
            ],
            "tasks": [
                {
                    "title": f"{role}的ROI下降分析实战",
                    "bg": "某品牌618大促营销预算增加20%，但ROI从3.2降至2.1，GMV同比下降15%。需要从多个维度进行归因分析。",
                    "goal": "使用AI辅助分析工具，从流量、转化、客单价、退款四个维度进行归因诊断，输出分析报告和改进建议。",
                    "skills": ["业务理解能力", "数据分析能力", "AI应用能力", "经营决策能力"],
                    "steps": [
                        "收集并整理相关业务数据（流量、转化、客单价、退款率等）",
                        "使用AI工具进行数据拆解和归因分析",
                        "基于分析结果生成诊断报告",
                        "提出针对性的改进建议和行动计划",
                    ],
                    "evaluation": [
                        "数据拆解是否正确完整（30分）",
                        "归因分析逻辑是否清晰（30分）",
                        "改进建议是否具体可行（25分）",
                        "报告结构是否规范（15分）",
                    ],
                },
            ],
            "cases": [
                {
                    "title": "某电商品牌GMV下滑诊断案例",
                    "steps": [
                        {"label": "问题发现", "desc": "GMV连续3周同比下降，从5%扩大至15%，触发经营预警。运营团队立即启动诊断流程。"},
                        {"label": "数据拆解", "desc": "拆解GMV=访客数(▲3.6%)×转化率(▼34%)×客单价(▼7.7%)，转化率下降34%是核心因素。"},
                        {"label": "归因分析", "desc": "广告精度下降，点击率从12%降至8%，高意向用户占比从45%降至28%，退款率升至8.3%。"},
                        {"label": "解决方案", "desc": "优化人群定向模型，暂停低效渠道投放，设置ROI预警阈值。预期转化率回升至3.2%以上。"},
                    ],
                },
            ],
        }

    @classmethod
    def generate_exam_blueprint(cls, profile: dict) -> dict:
        """生成考试蓝图"""
        if not profile or not profile.get("name"):
            return {"objective": "基础测评", "dimensions": [], "difficulty": "easy",
                    "total": 5, "duration": 30, "distribution": {}}

        stage = profile.get("stage", "初级入门阶段")
        score = profile.get("score", 50)

        difficulty = "easy"
        if score >= 70:
            difficulty = "hard"
        elif score >= 50:
            difficulty = "medium"

        total = 10
        duration = 60
        if difficulty == "easy":
            total, duration = 8, 45
        elif difficulty == "hard":
            total, duration = 12, 90

        # 调整题型分布：客观题+主观题
        obj_count = max(2, total * 3 // 5)  # 60%客观题
        subj_count = total - obj_count      # 40%主观题
        return {
            "objective": f"评估{profile.get('role', '业务分析师')}的AI辅助业务分析能力",
            "dimensions": ["业务理解", "数据分析", "AI工具应用", "经营决策"],
            "difficulty": difficulty,
            "total_questions": total,
            "duration_minutes": duration,
            "distribution": {
                "基础知识题": {"count": max(1, obj_count // 4), "difficulty": difficulty},
                "AI工具使用题": {"count": max(1, obj_count // 4), "difficulty": difficulty},
                "数据分析题": {"count": max(1, obj_count // 4), "difficulty": difficulty},
                "业务案例分析题": {"count": max(1, subj_count // 2 + obj_count % 2), "difficulty": difficulty},
                "经营决策题": {"count": max(1, subj_count // 2), "difficulty": difficulty},
            },
        }

    @classmethod
    def generate_questions(cls, blueprint: dict, profile: dict = None) -> list:
        """根据蓝图生成考试题目"""
        questions = []
        dist = blueprint.get("distribution", {})
        role = profile.get("role", "业务分析师") if profile else "业务分析师"

        for qtype, config in dist.items():
            for i in range(config.get("count", 1)):
                q = cls._make_question(qtype, config.get("difficulty", "medium"), role, len(questions) + 1)
                if q:
                    questions.append(q)

        # 打乱顺序
        random.shuffle(questions)
        # 重新编号
        for i, q in enumerate(questions):
            q["number"] = i + 1

        return questions

    @classmethod
    def _make_question(cls, qtype: str, difficulty: str, role: str, num: int) -> Optional[dict]:
        """生成一道题目"""
        pool = {
            "基础知识题": [
                {
                    "stem": f"电商GMV的完整计算公式是什么？以下哪个选项正确？",
                    "options": [
                        "A. GMV = 访客数 × 转化率",
                        "B. GMV = 访客数 × 转化率 × 客单价",
                        "C. GMV = 访客数 + 转化率 + 客单价",
                        "D. GMV = 销售额 × 利润率",
                    ],
                    "answer": "B",
                    "analysis": "GMV = 访客数 × 转化率 × 客单价，这是电商最核心的经营指标公式。",
                    "question_type": "objective",
                },
                {
                    "stem": "在电商数据分析中，什么是'漏斗分析'？",
                    "options": [
                        "A. 一种流量分配方法",
                        "B. 分析用户从进入网站到完成转化的每一步流失情况",
                        "C. 价格比较策略",
                        "D. 库存管理方法",
                    ],
                    "answer": "B",
                    "analysis": "漏斗分析追踪用户在每个环节的行为转化，找出流失关键节点。",
                    "question_type": "objective",
                },
                {
                    "stem": "以下哪个指标最能反映电商平台的用户粘性？",
                    "options": [
                        "A. 客单价",
                        "B. 复购率",
                        "C. GMV",
                        "D. 退款率",
                    ],
                    "answer": "B",
                    "analysis": "复购率反映了用户对平台的忠诚度和持续使用意愿。",
                    "question_type": "objective",
                },
                {
                    "stem": "什么是A/B测试？在电商场景中如何使用？",
                    "options": [
                        "A. 两种商品的价格比较",
                        "B. 同时运行两个版本比较效果差异的试验方法",
                        "C. 库存A和仓库B的物流比较",
                        "D. 两种广告渠道的投放",
                    ],
                    "answer": "B",
                    "analysis": "A/B测试是随机分流对比试验，用于验证页面改动、算法优化等方案的效果。",
                    "question_type": "objective",
                },
            ],
            "AI工具使用题": [
                {
                    "stem": f"作为一名{role}，你需要AI帮助你分析季度销售数据，以下哪个Prompt最有效？",
                    "options": [
                        "A. '帮我分析一下销售数据'",
                        "B. '你是一名电商数据分析师。请分析这份季度销售数据，从GMV趋势、品类表现、渠道贡献三个维度进行归因，指出关键问题并给出建议'",
                        "C. '分析数据'",
                        "D. '告诉我销售情况怎么样'",
                    ],
                    "answer": "B",
                    "analysis": "好的Prompt应包含角色设定、具体任务、分析维度和输出要求。",
                    "question_type": "objective",
                },
                {
                    "stem": "在使用AI进行业务分析时，以下哪种做法最能提高分析质量？",
                    "options": [
                        "A. 一次性给出所有数据，让AI自己决定分析什么",
                        "B. 将复杂问题拆解为多个子任务，分步向AI提问",
                        "C. 使用最简单的提问方式",
                        "D. 完全不使用AI，自己手动分析",
                    ],
                    "answer": "B",
                    "analysis": "将复杂业务问题拆解为多个子任务，分步与AI协作，能获得更有深度的分析结果。",
                    "question_type": "objective",
                },
                {
                    "stem": "AI在电商数据分析中不能完成以下哪项任务？",
                    "options": [
                        "A. 从大量数据中识别趋势和模式",
                        "B. 生成数据可视化报告",
                        "C. 制定完全准确且无需人工审核的经营决策",
                        "D. 快速汇总和分析多维度指标",
                    ],
                    "answer": "C",
                    "analysis": "AI提供决策建议，但最终决策需要人工审核和判断，不能完全依赖AI。",
                    "question_type": "objective",
                },
            ],
            "数据分析题": [
                {
                    "stem": "某店铺上月GMV 100万，本月GMV 85万，同比变化是多少？",
                    "options": [
                        "A. 增长15%",
                        "B. 下降15%",
                        "C. 下降17.6%",
                        "D. 增长17.6%",
                    ],
                    "answer": "B",
                    "analysis": "(85-100)/100 = -15%，即同比下降15%。",
                    "question_type": "objective",
                },
                {
                    "stem": "某品牌广告投放数据：曝光100000次，点击3000次，转化90单。点击率和转化率分别是？",
                    "options": [
                        "A. 点击率3%，转化率3%",
                        "B. 点击率0.3%，转化率3%",
                        "C. 点击率3%，转化率0.3%",
                        "D. 点击率0.3%，转化率0.3%",
                    ],
                    "answer": "A",
                    "analysis": "点击率 = 3000/100000 = 3%，转化率 = 90/3000 = 3%。",
                    "question_type": "objective",
                },
            ],
            "业务案例分析题": [
                {
                    "stem": f"你是一个{role}，发现某款商品连续3个月GMV下滑，你应该优先分析哪个维度的数据？",
                    "options": [
                        "A. 只分析价格变化",
                        "B. 从流量、转化率、客单价、退款率四个维度系统性分析",
                        "C. 只看竞品价格",
                        "D. 等待下个月数据再决定",
                    ],
                    "answer": "B",
                    "analysis": "GMV下滑应系统性地从流量、转化、客单价、退款四个维度拆解分析，找出核心原因。",
                    "question_type": "objective",
                },
                {
                    "stem": "618大促期间，A渠道ROI为4.5（花费10万，GMV45万），B渠道ROI为1.8（花费50万，GMV90万），以下说法正确的是？",
                    "options": [
                        "A. A渠道效果好，应该把所有预算转到A渠道",
                        "B. B渠道虽然ROI低，但贡献了更多GMV绝对值，应该寻找优化B渠道的方法",
                        "C. B渠道效果太差，应该立即停止",
                        "D. ROI不重要，只看GMV总额",
                    ],
                    "answer": "B",
                    "analysis": "ROI和GMV需要综合权衡。B渠道虽然ROI较低，但贡献了更多GMV，应该优化而非放弃。",
                    "question_type": "objective",
                },
            ],
            "经营决策题": [
                {
                    "stem": "当月GMV目标为200万，目前完成120万，还剩15天。根据历史数据，日均GMV为5万，以下哪项决策最合理？",
                    "options": [
                        "A. 制定冲刺计划：加大营销投入，预计日均GMV提升至6-7万",
                        "B. 放弃目标，等待下个月",
                        "C. 降价50%清仓",
                        "D. 不做任何调整",
                    ],
                    "answer": "A",
                    "analysis": "按当前进度15天×5万=75万，总共195万缺口5万。适当加大营销投入可弥补缺口，是合理决策。",
                    "question_type": "objective",
                },
                {
                    "stem": "某商品毛利率为25%，退货率为15%，广告ROI为2.5。以下哪个指标对利润影响最大？",
                    "options": [
                        "A. 毛利率",
                        "B. 退货率",
                        "C. 广告ROI",
                        "D. 三者都很重要，需要综合优化",
                    ],
                    "answer": "D",
                    "analysis": "毛利率、退货率、广告ROI三者共同决定最终利润，需要系统性优化而非只关注单一指标。",
                    "question_type": "objective",
                },
            ],
        }

        # Add subjective questions pool
        subjective_pool = {
            "业务案例分析题": [
                {
                    "stem": f"你是一个{role}，请分析以下场景并给出你的诊断：某电商品牌上个月的GMV为500万，环比下降20%。从流量、转化率、客单价和退款率四个维度分析可能的原因，并给出具体的改进建议。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["是否从四个维度全面分析", "分析逻辑是否清晰", "建议是否具体可行"],
                    "reference_answer": "应系统性拆解GMV=访客数×转化率×客单价，对比各维度数据变化找出核心问题维度，再进行归因分析，最后给出针对性建议。"
                },
                {
                    "stem": f"作为{role}，某电商平台发现新用户首单转化率持续偏低（从12%降至7%），请分析可能的原因，并设计一个A/B测试方案来验证你的假设。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["原因假设是否合理全面", "A/B测试方案设计是否科学", "是否考虑了样本量和置信度"],
                    "reference_answer": "应从流量质量、落地页体验、新客权益、注册流程等方面分析原因。A/B测试应设定单一变量、明确核心指标、计算所需样本量。"
                },
                {
                    "stem": f"作为{role}，请设计一个用户流失预警方案。你需要说明：哪些指标可以作为流失预警信号？如何设定预警阈值？当预警触发后应采取什么措施？",
                    "question_type": "subjective",
                    "evaluation_criteria": ["预警指标选择是否合理", "阈值设定是否有依据", "应对措施是否可执行"],
                    "reference_answer": "预警指标可包括：登录频次下降、购买间隔拉长、客单价降低等。阈值应基于历史数据分布设定，措施应分级应对。"
                },
                {
                    "stem": f"作为{role}，某店铺在618大促期间的销售额未达预期（目标800万，实际完成520万）。请从活动策划、流量引入、转化优化、售后服务四个阶段进行复盘，找出关键问题点并提出改进方案。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["复盘结构是否完整", "问题诊断是否准确", "改进方案是否可落地"],
                    "reference_answer": "应从活动前中后全链路复盘，对比各环节数据与预期差距，找出核心漏斗瓶颈。重点分析引流效率、页面转化、库存备货、售后体验。"
                },
                {
                    "stem": f"你是一家电商平台的{role}，商品A的月销量从3000件下降到1200件，但搜索曝光量并未明显减少。请分析可能的原因，并制定一个完整的诊断和优化方案。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["指标体系是否完整", "原因分析是否深入", "优化方案是否有优先级"],
                    "reference_answer": "应从点击率、转化率、评价评分、竞品价格、流量质量等维度拆解。对比同期数据，进行品类市场份额分析，再制定分阶段优化策略。"
                },
            ],
            "经营决策题": [
                {
                    "stem": f"你是某电商平台的{role}，有三个营销渠道可供选择：\nA渠道：ROI 3.5，但触达用户量少（月均5万）\nB渠道：ROI 2.8，触达用户量中等（月均20万）\nC渠道：ROI 1.6，触达用户量最大（月均80万）\n总预算100万，你会如何分配？请详细说明你的决策逻辑。\n\n同时请分析：如果目标是'最大化GMV'和'最大化ROI'，两种策略有何不同？",
                    "question_type": "subjective",
                    "evaluation_criteria": ["是否理解不同目标下的策略差异", "预算分配方案是否有逻辑支撑", "是否考虑了渠道间的协同效应"],
                    "reference_answer": "最大化GMV应优先ROI高的渠道并逐步扩展到规模渠道；最大化ROI应集中预算在高效渠道。两种目标需要平衡，可采取组合策略。"
                },
                {
                    "stem": f"作为{role}，请为以下情况制定经营策略：\n- 某品类GMV连续两月下滑，但行业整体增长了8%\n- 该品类是平台核心品类（占比35% GMV）\n- 竞品近期加大促销力度，折扣率从8折降至6折\n- 你的营销预算剩余20%\n\n请分析当前局势并提出具体的应对策略。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["局势分析是否全面", "应对策略是否对症下药", "预算分配是否合理", "是否有数据支撑决策"],
                    "reference_answer": "应从行业对比、竞品分析、自身问题诊断三个维度分析。策略应聚焦差异化竞争、精细化运营和预算优化。"
                },
                {
                    "stem": f"你是一个{role}，你的团队有A和B两个项目可选：\n项目A：确定性高，预计投入30万，ROI稳定在3.0\n项目B：创新性强，预计投入50万，ROI可能达到5.0但风险较大（40%失败率）\n你只能在两个项目中选一个。请分析你的决策逻辑，并说明经营决策中如何平衡风险与收益。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["是否量化分析了风险和收益", "决策逻辑是否清晰", "是否考虑了公司的整体战略"],
                    "reference_answer": "应根据公司发展阶段和风险承受能力决策。成熟期可偏好稳健项目A，成长期可尝试创新项目B。也可考虑缩小B的试点规模来平衡风险。"
                },
                {
                    "stem": f"作为{role}，你发现某商品类目的季度GMV同比增长了30%，但利润率却下降了5个百分点。请分析可能导致'增收不增利'的原因，并制定一个利润优化方案。",
                    "question_type": "subjective",
                    "evaluation_criteria": ["原因分析是否全面", "利润优化方案是否具体", "是否考虑了长期竞争影响"],
                    "reference_answer": "应从成本结构、折扣力度、退货率、流量成本、品类结构调整等方面分析。优化方案可包括精细化定价、SKU优化、成本控制和会员运营。"
                },
            ],
        }

        # 业务案例分析题和经营决策题中，约一半为主观题
        use_subjective = False
        if qtype in ("业务案例分析题", "经营决策题") and num % 2 == 0:
            use_subjective = True

        if use_subjective and qtype in subjective_pool:
            sp = subjective_pool[qtype]
            q = random.choice(sp).copy()
            q.update({
                "id": f"q_{num}",
                "type": qtype,
                "sub_type": "主观题",
                "difficulty": difficulty,
                "score": cls._question_score(qtype, difficulty) + 5,
            })
            return q

        questions_pool = pool.get(qtype, [])
        if not questions_pool:
            return None

        q = random.choice(questions_pool).copy()
        q.update({
            "id": f"q_{num}",
            "type": qtype,
            "difficulty": difficulty,
            "score": cls._question_score(qtype, difficulty),
        })
        return q

    @staticmethod
    def _question_score(qtype: str, difficulty: str) -> int:
        base = {"基础知识题": 10, "AI工具使用题": 15, "数据分析题": 20,
                "业务案例分析题": 25, "经营决策题": 30}.get(qtype, 10)
        diff_mult = {"easy": 0.8, "medium": 1.0, "hard": 1.2}.get(difficulty, 1.0)
        return int(base * diff_mult)

    @classmethod
    def generate_scenario(cls, scenario_type: str, profile: dict = None) -> dict:
        """生成实战演练场景"""
        role = profile.get("role", "业务分析师") if profile else "业务分析师"

        scenarios = {
            "数据理解类": {
                "title": "阅读销售报表",
                "description": f"作为{role}，请阅读以下月度销售报表数据，分析关键趋势和问题。",
                "data": {
                    "monthly_gmv": [120, 135, 128, 142, 138, 155, 150, 148, 162, 158, 170, 165],
                    "conversion_rate": [3.2, 3.5, 3.1, 3.8, 3.6, 4.0, 3.9, 3.7, 4.1, 3.9, 4.2, 4.0],
                    "avg_order_value": [298, 305, 290, 312, 308, 325, 318, 310, 330, 322, 340, 335],
                    "return_rate": [8.5, 7.8, 9.2, 7.5, 8.0, 7.2, 7.8, 8.5, 7.0, 7.5, 6.8, 7.2],
                },
                "questions": [
                    "过去12个月的GMV整体趋势如何？哪个季度表现最好？",
                    "哪个月份的转化率最高？哪个月份最低？可能的原因是什么？",
                    "退货率的变化趋势如何？是否存在需要关注的异常？",
                    "结合所有指标，给出你的综合分析和建议。",
                ],
            },
            "AI分析类": {
                "title": "AI辅助分析GMV波动原因",
                "description": f"作为{role}，使用AI工具分析某品牌Q2的GMV波动原因。",
                "data": {
                    "scenario": "某品牌Q2 GMV数据显示：4月GMV为300万，5月为260万（下降13.3%），6月为285万（环比增长9.6%）",
                    "channels": {"天猫旗舰店": "4月180万→5月140万→6月155万",
                                "京东自营": "4月80万→5月75万→6月80万",
                                "抖音小店": "4月40万→5月45万→6月50万"},
                    "marketing_spend": {"4月": "45万", "5月": "50万", "6月": "48万"},
                },
                "questions": [
                    "5月GMV下降的主要渠道是哪个？可能的原因有哪些？",
                    "6月GMV回升的关键驱动因素是什么？",
                    "各渠道的ROI分别是多少？哪个渠道效率最高？",
                    "请使用AI工具生成一份Q2经营诊断报告。",
                ],
            },
            "Prompt设计类": {
                "title": "设计AI分析Prompt",
                "description": f"作为{role}，需要设计一个Prompt让AI帮助分析用户行为数据。",
                "data": {
                    "task": "分析不同渠道的用户转化路径",
                    "data_available": ["各渠道流量数据", "用户行为日志", "转化漏斗数据", "用户画像标签"],
                    "requirements": ["输出渠道转化效率对比", "识别高价值用户渠道来源",
                                    "给出渠道投放优化建议", "数据可视化要求"],
                },
                "questions": [
                    "请设计一个完整的Prompt，让AI完成渠道转化分析任务。",
                    "你的Prompt中包含了哪些关键要素？为什么这样设计？",
                    "如果AI的第一次输出不够理想，你会如何优化Prompt？",
                ],
            },
            "业务决策类": {
                "title": "经营决策：广告预算分配",
                "description": f"作为{role}，需要根据数据做出广告预算分配决策。",
                "data": {
                    "total_budget": "100万/月",
                    "channels": {
                        "搜索广告": {"roi": 3.2, "monthly_cap": "40万", "trend": "稳定"},
                        "信息流": {"roi": 2.8, "monthly_cap": "35万", "trend": "上升"},
                        "KOL合作": {"roi": 4.5, "monthly_cap": "25万", "trend": "波动大"},
                        "品牌广告": {"roi": 1.5, "monthly_cap": "20万", "trend": "长期价值"},
                    },
                    "constraints": ["KOL合作每月最多25万", "品牌广告不低于10万", "总预算不可超支"],
                },
                "questions": [
                    "根据ROI数据，你会如何分配100万预算？列出具体分配方案。",
                    "为什么品牌广告ROI最低但还要保留预算？",
                    "如果KOL合作ROI持续下滑，你会如何调整策略？",
                    "AI给出了预算方案，你是否完全采纳？为什么？",
                ],
            },
        }

        scenario = scenarios.get(scenario_type, scenarios["数据理解类"])
        return scenario
