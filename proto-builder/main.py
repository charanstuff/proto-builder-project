import autogen
from agents.chatbot import chatbot
from agents.planner import planner
from agents.developer import generate_code
from agents.deployment import deployment
from agents.logger import logger
from config.settings import config

# Multi-Agent Group Chat
group_chat = autogen.GroupChat(agents=[chatbot, planner, developer, deployment, logger], messages=[], max_round=20)
chat_manager = autogen.GroupChatManager(groupchat=group_chat)

# Start the Project
def start_project(user_input):
    chat_manager.initiate_chat(chatbot, planner, message=user_input)

if __name__ == "__main__":
    print(f"🚀 Running in {config.EXECUTION_MODE.upper()} mode")
    user_idea = input("Enter your project idea: ")
    start_project(user_idea)
