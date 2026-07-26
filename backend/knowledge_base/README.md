# 知识库接入说明

本系统预留了知识库接口，用于接入企业知识库系统。

## 需要接入的知识库

| 知识库名称 | 用途 | 优先级 |
|-----------|------|--------|
| **业务分析岗位技能与能力标准库** | 含初级、中级、高级能力标准、每项技能的评价证据，是个性化领域技能知识生成的基础 | 高 |
| **题库知识库** | 含分技能、分难度试题和标准答案 | 高 |
| **企业业务案例库** | 含真实的电商/业务场景案例，用于实战和案例教学 | 中 |

## 接入方式

### 方式一：通过配置文件

在 `backend/.env` 中设置：

```env
KNOWLEDGE_BASE_URI=http://your-knowledge-base-server:8080/api
```

### 方式二：通过代码集成

编辑 `backend/knowledge_base/__init__.py`，实现 `KnowledgeBaseClient` 类：

```python
class KnowledgeBaseClient:
    """知识库客户端 — 接入外部知识库服务"""

    def __init__(self, base_uri: str):
        self.base_uri = base_uri
        self.client = httpx.AsyncClient(base_url=base_uri)

    async def query_skill_standards(self, role: str, level: str) -> dict:
        """查询岗位技能与能力标准"""
        resp = await self.client.get("/skills", params={"role": role, "level": level})
        return resp.json()

    async def query_questions(self, skill: str, difficulty: str, count: int) -> list:
        """查询题库"""
        resp = await self.client.get("/questions", params={
            "skill": skill, "difficulty": difficulty, "count": count
        })
        return resp.json()

    async def query_cases(self, scenario: str) -> list:
        """查询业务案例"""
        resp = await self.client.get("/cases", params={"scenario": scenario})
        return resp.json()
```

## 标准接口定义

知识库服务需实现以下 RESTful API：

### 1. 技能标准查询
```
GET /api/skills?role={role}&level={level}
Response: {
    "skills": [
        {"name": "数据分析能力", "level": "中级", "description": "..."},
        ...
    ],
    "evidence": [...]
}
```

### 2. 题目查询
```
GET /api/questions?skill={skill}&difficulty={difficulty}&count={count}
Response: {
    "questions": [
        {"type": "选择题", "stem": "...", "options": [...], "answer": "...", "analysis": "..."},
        ...
    ]
}
```

### 3. 案例查询
```
GET /api/cases?scenario={scenario}
Response: {
    "cases": [
        {"title": "...", "background": "...", "data": {...}, "steps": [...]},
        ...
    ]
}
```

## 当前状态

系统目前使用 **模拟数据模式**，配置知识库后会自动切换到真实数据。
