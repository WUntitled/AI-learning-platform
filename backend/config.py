"""系统配置管理"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 尝试加载 .env.example
    example_path = Path(__file__).parent / ".env.example"
    if example_path.exists():
        load_dotenv(example_path)


class Settings:
    def __init__(self):
        # 服务配置
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")

        # 数据库
        db_url = os.getenv("DATABASE_URL", "sqlite:///./data/training.db")
        # 确保 SQLite 路径兼容
        if db_url.startswith("sqlite:///./"):
            rel_path = db_url[len("sqlite:///./"):]
            abs_db_dir = Path(__file__).parent / rel_path
            abs_db_dir.parent.mkdir(parents=True, exist_ok=True)
            self.DATABASE_URL = f"sqlite:///{abs_db_dir}"
        else:
            self.DATABASE_URL = db_url

        # LLM 配置
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "simulation")
        self.CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
        self.CLAUDE_API_MODEL: str = os.getenv("CLAUDE_API_MODEL", "claude-sonnet-5-20251001")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_MODEL: str = os.getenv("OPENAI_API_MODEL", "gpt-4o")
        self.DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
        self.DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

        # 知识库
        self.KNOWLEDGE_BASE_URI: str = os.getenv("KNOWLEDGE_BASE_URI", "")

    @property
    def llm_available(self) -> bool:
        """检查是否有可用的 LLM API 配置"""
        if self.LLM_PROVIDER == "claude" and self.CLAUDE_API_KEY:
            return True
        if self.LLM_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return True
        if self.LLM_PROVIDER == "deepseek" and self.DEEPSEEK_API_KEY:
            return True
        if self.LLM_PROVIDER == "simulation":
            return True
        return False


settings = Settings()
