from fastapi import FastAPI
from agents.chatbot import chatbot
from agents.planner import planner
from agents.developer import generate_code
from agents.deployment import deployment
from agents.logger import logger
from agents.modification import mod_handler
from config.settings import config

app = FastAPI()

@app.post("/generate_prototype/")
def generate_prototype(user_input: str):
    idea = chatbot.generate(user_input)
    tasks = planner.generate(idea)
    
    for task_name, task_desc in tasks.items():
        code = generate_code(task_name, task_desc)
        logger.generate(f"Generated code for: {task_name}")

    deployment.deploy()
    
    return {"status": "Success", "mode": config.EXECUTION_MODE, "message": "Prototype deployed!"}

@app.post("/modify/")
def modify_prototype(feature_request: str):
    new_code = mod_handler.request_changes(feature_request)
    deployment.deploy()
    return {"status": "Success", "message": "Feature updated!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
