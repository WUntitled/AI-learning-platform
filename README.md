# AI辅助业务分析个性化培训系统

**基于多智能体协同的AI培训平台**

面向企业内部业务岗位员工的AI辅助业务分析技能培训系统。系统采用多智能体协同架构，通过AI做课助手、AI学习助手、AI陪练助手、AI考试助手四大模块，实现学情画像构建、个性化课程生成、启发式交互学习、实战演练和智能评估的完整培训闭环。

---

## 目录

- [技术架构](#技术架构)
- [功能模块](#功能模块)
- [快速启动](#快速启动)
- [跨设备访问](#跨设备访问)
- [LLM配置](#llm配置)
- [知识库接入](#知识库接入)
- [Docker部署](#docker部署)
- [生产部署](#生产部署)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

---

## 技术架构

```
┌──────────────────────────────────────────────────────┐
│                    用户交互层                          │
│  (React SPA: 主面板 / 做课 / 学习 / 陪练 / 考试)      │
├──────────────────────────────────────────────────────┤
│  任务编排与智能路由层  (动态路由引擎)                   │
├──────────────────────────────────────────────────────┤
│  多智能体协同层  (6+6+5+5 Agent 群)                   │
├──────────────────────────────────────────────────────┤
│  企业知识与数据支撑层  (知识库预留接口)                 │
├──────────────────────────────────────────────────────┤
│  质量控制与安全治理层  (辩论审核机制)                   │
├──────────────────────────────────────────────────────┤
│  学情反馈与评估层  (六维雷达 / 热力图 / 趋势)          │
└──────────────────────────────────────────────────────┘
```

| 层级 | 技术 |
|------|------|
| 后端框架 | Python FastAPI + Uvicorn |
| 数据库 | SQLite (通过 SQLAlchemy ORM) |
| 前端 | 原生 JavaScript SPA (无构建步骤) |
| LLM | 模拟模式 / Claude API / OpenAI API / DeepSeek API |
| 部署 | 裸机启动 / Docker |

---

## 功能模块

### 1. AI做课助手 📚
- **学情画像构建**: 收集学习者信息（岗位、经验、AI背景等），生成六维能力雷达图
- **个性化课程生成**: 多Agent协同生成技能树、学习路径、知识卡、实战任务和案例
- **Agent可视化**: 6个Agent的执行流程实时展示

### 2. AI学习助手 💬
- **启发式交互**: 自然语言问答，支持多轮对话
- **多Agent路由**: 根据问题类型自动路由到最合适的Agent（路由/导学/答疑/案例/诊断/更新）
- **学情追踪**: 从对话中提取学情信息，实时更新画像

### 3. AI陪练助手 ⚡
- **4类实战场景**: 数据理解类、AI分析类、Prompt设计类、业务决策类
- **AI评估**: 多维度的回答评估（完整性、逻辑性、数据支撑、创新性）
- **历史记录**: 练习记录与得分追踪

### 4. AI考试助手 📝
- **智能出题**: 5种题型（基础知识、AI工具、数据分析、案例分析、经营决策）
- **自动评分**: 自动批改并生成详细评分报告
- **学情报告**: 六维雷达图、知识热力图、阶段趋势、培训建议

---

## 快速启动

### 前置条件

- Python 3.10 或更高版本
- pip（Python包管理器）

### Windows 一键启动

```bash
# 双击 start.bat，或命令行运行：
cd backend
start.bat
```

### 手动启动

```bash
# 1. 进入backend目录
cd backend

# 2. （推荐）创建虚拟环境
python -m venv venv

# Windows激活：
venv\Scripts\activate
# Mac/Linux激活：
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建配置（可选，系统会自动使用默认值）
copy .env.example .env

# 5. 启动系统
python main.py
```

### 访问系统

启动后，终端会显示如下信息：

```
=======================================================
  AI辅助业务分析个性化培训系统
  基于多智能体协同的AI培训平台
=======================================================
  启动地址: http://0.0.0.0:8000
  API文档:  http://0.0.0.0:8000/api/docs
  LLM模式:  simulation
=======================================================
```

- **主界面**: http://localhost:8000/
- **API文档**: http://localhost:8000/api/docs (Swagger UI)
- **API文档(Redoc)**: http://localhost:8000/api/redoc

---

## 跨设备访问

### 局域网访问

1. 在启动系统的电脑上，查看本机局域网IP：
   ```bash
   # Windows
   ipconfig
   # Mac/Linux
   ifconfig
   ```

2. 同一局域网内的其他设备（手机、平板、其他电脑）打开浏览器访问：
   ```
   http://<本机IP>:8000
   ```
   例如 `http://192.168.1.100:8000`

3. **确保防火墙允许 8000 端口**：
   - Windows: 系统会弹出防火墙提示，点击"允许访问"
   - 或手动添加防火墙规则

### 公网访问（生产部署）

#### 方式一：使用内网穿透（推荐测试用）

```bash
# 使用 ngrok（免费）
ngrok http 8000
# 会生成一个公网URL，如 https://abc123.ngrok.io
```

#### 方式二：云服务器部署

1. 购买云服务器（阿里云、腾讯云、AWS等）
2. SSH登录服务器
3. 安装 Python 3.10+
4. 上传项目文件
5. 按快速启动步骤运行
6. **安全组放行 8000 端口**

#### 方式三：使用反向代理（生产推荐）

安装 Nginx 或 Caddy 作为反向代理，配置 SSL 证书：

```nginx
# Nginx 配置示例
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

---

## LLM配置

系统默认使用**模拟模式**，无需API Key即可运行所有功能。
接入真实LLM后，生成的内容质量会显著提升。

### 配置方法

编辑 `backend/.env` 文件：

```env
# LLM 服务配置
# 可选值: simulation | claude | openai | deepseek
LLM_PROVIDER=simulation

# Claude API（任选其一）
# LLM_PROVIDER=claude
# CLAUDE_API_KEY=sk-ant-xxxxx
# CLAUDE_API_MODEL=claude-sonnet-5-20251001

# OpenAI API
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxxxx
# OPENAI_API_MODEL=gpt-4o

# DeepSeek API（国产，性价比高）
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=sk-xxxxx
# DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

### 提供商对比

| 提供商 | 优势 | 适用场景 |
|--------|------|---------|
| 模拟模式 | 无需API Key，零成本 | 演示、开发、测试 |
| Claude | 中文能力强，推理出色 | 正式使用 |
| OpenAI | 生态成熟 | 已有API Key |
| DeepSeek | 性价比高，国内访问快 | 国内用户 |

---

## 知识库接入

系统预留了知识库接口（`backend/knowledge_base/`），支持接入以下知识库：

| 知识库 | 用途 | 接入方式 |
|--------|------|---------|
| 岗位技能与能力标准库 | 个性化知识生成基础 | REST API |
| 题库知识库 | 考试出题数据源 | REST API |
| 企业业务案例库 | 实战和案例教学 | REST API |

接入方法请参阅 `backend/knowledge_base/README.md`。

---

## Docker部署

### 前提

安装了 Docker 和 Docker Compose

### 构建和启动

```bash
# 在项目根目录执行
docker-compose up -d --build
```

### 访问

```
http://localhost:8000
```

### 停止

```bash
docker-compose down
```

---

## 生产部署

对于生产环境，建议：

1. **配置HTTPS**: 使用 Nginx + Let's Encrypt 配置 SSL
2. **更换数据库**: SQLite -> PostgreSQL/MySQL（编辑 `backend/.env` 中的 `DATABASE_URL`）
3. **环境变量**: 使用强密码替换 `SECRET_KEY`
4. **进程管理**: 使用 `systemd` 或 `supervisor` 管理进程
5. **日志**: 配置日志轮转
6. **监控**: 添加健康检查端点

### systemd 服务配置示例

```ini
[Unit]
Description=AI Training System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/training-system/backend
ExecStart=/opt/training-system/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
```

---

## 常见问题

### Q: 启动报错 "No module named ..."
A: 确保已安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

### Q: 其他设备无法访问
A: 检查：
1. 启动时主机IP是否为 `0.0.0.0`（默认）
2. 防火墙是否放行8000端口
3. 是否在同一局域网

### Q: 前端页面空白/加载异常
A: 打开浏览器开发者工具(F12)查看Console错误，确认API可访问。

### Q: 如何修改端口？
A: 编辑 `backend/.env`，修改 `PORT=8000` 为其他端口。

### Q: 数据存储在哪里？
A: SQLite数据库文件存储在 `backend/data/training.db`。重置只需删除该文件。

### Q: 如何重置所有数据？
A: 删除 `backend/data/` 目录中的 `.db` 文件，重启系统即可。

---

## 项目结构

```
project/
├── start.bat                    # Windows 一键启动脚本
├── docker-compose.yml           # Docker 编排
├── Dockerfile.backend           # Docker 构建文件
├── README.md                    # 本文件
├── .gitignore
│
├── backend/                     # 后端
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   ├── requirements.txt         # Python 依赖
│   ├── .env.example             # 配置模板
│   ├── start.bat                # 后端启动脚本
│   │
│   ├── models/                  # 数据模型
│   │   ├── user.py              # 用户
│   │   ├── profile.py           # 学情画像
│   │   ├── course.py            # 课程
│   │   ├── exam.py              # 考试
│   │   └── session.py           # 会话
│   │
│   ├── agents/                  # 多智能体
│   │   ├── base.py              # Agent基类
│   │   ├── engine.py            # 引擎
│   │   ├── router.py            # 动态路由
│   │   ├── debate.py            # 辩论审核
│   │   └── .../                 # 各模块Agent
│   │
│   ├── services/                # 服务层
│   │   ├── llm_service.py       # 内容生成器
│   │   └── llm_api.py           # LLM API封装
│   │
│   ├── routers/                 # API路由
│   │   ├── api.py               # 主路由
│   │   ├── profile.py           # 学情画像
│   │   ├── course.py            # 课程
│   │   ├── learning.py          # 学习助手
│   │   ├── practice.py          # 陪练助手
│   │   └── exam.py              # 考试助手
│   │
│   └── knowledge_base/          # 知识库接口
│       ├── __init__.py
│       └── README.md
│
└── frontend/                    # 前端 SPA
    ├── index.html               # 主页面
    ├── css/
    │   └── style.css            # 全局样式
    └── js/
        ├── app.js               # 路由 & 主逻辑
        ├── api.js               # API客户端
        ├── components.js        # 共享组件
        ├── charts/
        │   └── radar.js         # 雷达图
        └── pages/
            ├── dashboard.js     # 主面板
            ├── course.js        # AI做课助手
            ├── learning.js      # AI学习助手
            ├── practice.js      # AI陪练助手
            ├── exam.js          # AI考试助手
            └── report.js        # 学情报告
```

---

## License

MIT License

Copyright (c) 2026
