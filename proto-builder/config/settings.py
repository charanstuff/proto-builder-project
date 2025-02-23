import os

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO = "your-repo-name"
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

    # Execution Mode: "test" (local) or "prod" (GitHub + EC2)
    EXECUTION_MODE = os.getenv("EXECUTION_MODE", "test")  # Default to "test"
    OPENAI_MODEL = "o1-mini"

    # Ensure the "projects" directory exists in test mode
    if EXECUTION_MODE == "test":
        os.makedirs("projects", exist_ok=True)

config = Config()
