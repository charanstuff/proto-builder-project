import autogen
import git
import os
import subprocess
from config.settings import config

class DeploymentAgent:
    def __init__(self):
        self.repo = git.Repo("path_to_repo") if config.EXECUTION_MODE == "prod" else None

    def push_to_github(self):
        if config.EXECUTION_MODE == "prod":
            self.repo.git.checkout("-b", "feature_branch")
            self.repo.git.add(".")
            self.repo.git.commit("-m", "Auto-generated prototype")
            self.repo.git.push("origin", "feature_branch")
            print("✅ Code pushed to GitHub on feature branch.")

    def deploy_to_ec2(self):
        if config.EXECUTION_MODE == "prod":
            print("🚀 Deploying to EC2...")
            # Implement actual EC2 deployment logic here

    def run_locally(self):
        """Runs the generated prototype locally (for test mode)."""
        print("🛠️ Running locally...")
        for file in os.listdir("projects"):
            if file.endswith(".py"):
                print(f"▶️ Running {file} ...")
                subprocess.run(["python", f"projects/{file}"], check=True)

    def deploy(self):
        if config.EXECUTION_MODE == "prod":
            self.push_to_github()
            self.deploy_to_ec2()
        else:
            self.run_locally()

deployment = DeploymentAgent()
