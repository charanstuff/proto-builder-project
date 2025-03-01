import os
import autogen
from agents.chatbot import generate_chatbot_response  # Ensure this function is used
from agents.planner import planner
from agents.developer import simulate_project_creation
from agents.deployment import deployment
from agents.logger import generate_log_entry
from config.settings import config

# Ensure "projects" directory exists in test mode
if config.EXECUTION_MODE == "test":
    os.makedirs("projects", exist_ok=True)

def terminal_chat():
    """Interactive terminal chatbot for ProtoBot."""
    print("🛠️ Proto Agent: Hello, welcome to ProtoBot, let's discuss your idea and prototype it.")

    while True:
        user_input = input("Me: ")

        if user_input.lower() in ["exit", "quit"]:
            print("🛠️ Proto Agent: Goodbye! Exiting ProtoBot.")
            break

        # Process user input using the chatbot function
        print("🛠️ Proto Agent: Let me analyze your idea...")

        # Ensure that system messages are not passed for models like `o1-mini`
        response = generate_chatbot_response(user_input)  # Use updated function

        if not response:
            print("🛠️ Proto Agent: Error processing response. Please try again.")
            continue

        idea = response.strip()  # Ensure clean text output

        # Generate tasks
        print("🛠️ Proto Agent: Breaking down tasks...")
        response = planner.generate_reply(messages=[{"role": "user", "content": idea}])
        print(response)

        if "content" in response:
            tasks = response["content"]
        else:
            print("🛠️ Proto Agent: Error in task breakdown. Please try again.")
            continue

        print(response["content"])

        print(f"🛠️ Proto Agent: Working on the idea...")
        simulate_project_creation(response["content"])
        generate_log_entry("Developer", f"Generated code for idea")

        print("🛠️ Proto Agent: Running your prototype locally...")
        deployment.deploy()

        print("✅ Proto Agent: Your prototype is ready! Check the 'projects/' folder.")

if __name__ == "__main__":
    print(f"🚀 Running ProtoBot in {config.EXECUTION_MODE.upper()} mode")
    terminal_chat()
