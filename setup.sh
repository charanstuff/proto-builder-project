#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "=== Setting up the Sales Outreach AI Agent Backend ==="

# 1. Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
else
    echo "Virtual environment already exists."
fi

# 2. Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies from requirements.txt
echo "Installing Python dependencies..."
pip install -r requirements.txt

# 5. Create project directory structure
echo "Creating project directories..."
mkdir -p app/routes/auth
mkdir -p app/routes/campaigns
mkdir -p app/routes/analytics
mkdir -p app/utils

# 6. Create __init__.py files to mark packages
touch app/__init__.py
touch app/routes/__init__.py
touch app/routes/auth/__init__.py
touch app/routes/campaigns/__init__.py
touch app/routes/analytics/__init__.py

# 7. Create sample files if they don't exist

# app/main.py: Entry point for FastAPI
if [ ! -f "app/main.py" ]; then
cat << 'EOF' > app/main.py
from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="Sales Outreach AI Agent")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sales Outreach AI Agent API"}

# Later: Include additional routers here, e.g.:
# from app.routes.auth import router as auth_router
# app.include_router(auth_router, prefix="/auth")
EOF
fi

# app/config.py: Load configuration from .env
if [ ! -f "app/config.py" ]; then
cat << 'EOF' > app/config.py
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
EOF
fi

# app/models.py: SQLAlchemy setup and base model
if [ ! -f "app/models.py" ]; then
cat << 'EOF' > app/models.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define your models here. For example:
# from sqlalchemy import Column, Integer, String
#
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
EOF
fi

# 8. Create a sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating sample .env file..."
    cat << EOF > .env
# MySQL connection URL: adjust username, password, and database name as needed
DATABASE_URL=mysql+pymysql://root@localhost:3306/agent_db

# Secret key for JWT or encryption
SECRET_KEY=your-secret-key

# LLM provider API key (for LangChain or similar libraries)
LLM_PROVIDER_API_KEY=your-llm-api-key

# Redis URL for Celery
REDIS_URL=redis://localhost:6379/0
EOF
    echo ".env file created. Please review and update it with your actual credentials."
else
    echo ".env file already exists. Skipping creation."
fi

# 9. (Optional) Run Alembic migrations if the alembic directory exists
if [ -d "alembic" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
else
    echo "Alembic directory not found. Skipping migrations."
fi

echo "=== Setup complete! ==="
echo "Activate your virtual environment with: source venv/bin/activate"
echo "Then, start the server with: ./run.sh"
