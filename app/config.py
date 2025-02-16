import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://username:password@localhost:3306/agent_db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
LLM_PROVIDER_API_KEY = os.getenv("LLM_PROVIDER_API_KEY", "your-llm-api-key")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class Settings:
    database_url: str = DATABASE_URL
    secret_key: str = SECRET_KEY
    llm_provider_api_key: str = LLM_PROVIDER_API_KEY
    redis_url: str = REDIS_URL

settings = Settings()
