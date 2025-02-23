# import autogen
# from config.settings import config

# # Determine if the model supports system messages.
# supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

# llm_config = {
#     "api_key": config.OPENAI_API_KEY,
#     "model": config.OPENAI_MODEL
# }

# # Only add the system message if supported.
# if supports_system_message:
#     llm_config["system_message"] = (
#         "You are a meticulous Planner Agent whose goal is to convert the user’s idea into a structured, step-by-step plan. "
#         "Analyze the provided idea details and split them into clear, manageable subtasks.\n\n"
#         "Instructions:\n"
#         "- Break down the idea: Divide the overall concept into discrete modules (e.g., user interface, backend logic, integrations, etc.).\n"
#         "- Specify steps: For each module, list the specific tasks needed to implement it. Include dependencies and expected outcomes.\n"
#         "- Use clear, numbered steps or bullet points: This makes it easy for the Developer Agent to follow.\n"
#         "- Provide examples and reference tactics: For example, \"Write a function to handle user authentication. (Hint: Consider using token-based authentication.)\"\n"
#         "- Validate the plan: Ensure that all aspects of the user’s requirements are covered and that the tasks can be completed in sequence.\n\n"
#         "Example Output:\n"
#         "Based on the user’s input, here’s a breakdown of the project:\n"
#         "1. User Interface:\n"
#         "   - Design wireframes for the landing page, dashboard, and settings page.\n"
#         "   - Gather feedback on the initial designs.\n"
#         "2. Backend Development:\n"
#         "   - Set up the server environment.\n"
#         "   - Develop API endpoints for user management, data retrieval, and updates.\n"
#         "3. Integration & Testing:\n"
#         "   - Integrate frontend and backend components.\n"
#         "   - Write unit tests for each module.\n"
#         "4. Deployment:\n"
#         "   - Prepare deployment scripts and environments.\n\n"
#         "Make sure every subtask is self-contained and includes any necessary details."
#     )

# # Create the Planner Agent.
# planner = autogen.AssistantAgent("Planner", llm_config=llm_config)

# # For models that do NOT support system messages, clear the stored system message.
# if not supports_system_message:
#     planner._oai_system_message = ""

# def generate_plan(user_idea):
#     """
#     Generates a step-by-step plan from the user's idea.
#     For models that do not support system messages (e.g., o1-mini), the instructions are embedded in the prompt.
#     """
#     if not supports_system_message:
#         instructions = (
#             "You are a meticulous Planner Agent whose goal is to convert the user's idea into a structured, step-by-step plan. "
#             "Break down the idea into clear, manageable subtasks with numbered steps or bullet points. "
#             "Now, based on the following idea, generate a detailed plan:"
#         )
#         full_prompt = f"{instructions}\n\nUser Idea: {user_idea}"
#     else:
#         full_prompt = user_idea

#     response = planner.generate_reply(messages=[{"role": "user", "content": full_prompt}])
#     return response["content"]

import traceback
import os
import autogen
from config.settings import config
import openai

from openai import OpenAI

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
)

supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

llm_config = {
    "api_key": config.OPENAI_API_KEY,
    "model": config.OPENAI_MODEL
}

if supports_system_message:
    llm_config["system_message"] = """You are a meticulous Planner Agent whose goal is to convert the user’s idea into a structured, step-by-step plan. Analyze the provided idea details and split them into clear, manageable subtasks.

Instructions:
- Break down the idea: Divide the overall concept into discrete modules (e.g., user interface, backend logic, integrations, etc.).
- Specify steps: For each module, list the specific tasks needed to implement it. Include dependencies and expected outcomes.
- Use clear, numbered steps or bullet points: This makes it easy for the Developer Agent to follow.
- Provide examples and reference tactics: For example, "Write a function to handle user authentication. (Hint: Consider using token-based authentication.)"
- Validate the plan: Ensure that all aspects of the user’s requirements are covered and that the tasks can be completed in sequence.

Example Output:
Based on the user’s input, here’s a breakdown of the project:
1. User Interface:
   - Design wireframes for the landing page, dashboard, and settings page.
   - Gather feedback on the initial designs.
2. Backend Development:
   - Set up the server environment.
   - Develop API endpoints for user management, data retrieval, and updates.
3. Integration & Testing:
   - Integrate frontend and backend components.
   - Write unit tests for each module.
4. Deployment:
   - Prepare deployment scripts and environments.

Make sure every subtask is self-contained and includes any necessary details."""
    
planner = autogen.AssistantAgent("Planner", llm_config=llm_config)

if not supports_system_message:
    planner._oai_system_message = ""
    def patched_generate_reply(messages, sender=None):
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages
        )
        return {"content": response.choices[0].message.content.strip()}
    planner.generate_reply = patched_generate_reply

def generate_plan(user_idea):
    """
    Generates a detailed plan from the user's idea.
    If the model does not support system messages, the elaborate instructions are embedded into the prompt.
    If an error occurs, the full exception and stack trace are returned.
    """
    try:
        if not supports_system_message:
            instructions = """You are a meticulous Planner Agent whose goal is to convert the user’s idea into a structured, step-by-step plan. Analyze the provided idea details and split them into clear, manageable subtasks.

Instructions:
- It's important that the plan is only for the MVP - nothing more, nothing less. DON'T PROVIDE TIPS.
- Break down the idea: Divide the overall concept into discrete modules but to the point where it is easy for the Developer Agent to follow. (e.g., user interface, backend logic, etc).
- Specify steps: For each module, list the specific tasks needed to implement it. Include dependencies and expected outcomes.
- Use clear, numbered steps or bullet points: This makes it easy for the Developer Agent to follow.
- Do not include any miscellaneous information in the output. EG: "Here is the plan for the project..." OR "Let me know if you have any questions..."
 etc.
 - Do not provide any enhancements or next steps.
 - Make it as concise and to the point as possible.
Example Input:
I need to build a crawler that crawls the web for scientific papers and saves them to a database. I want to be able to search for papers by title, author, or keywords. There should be a UI where I can see the papers and their details.

Example Output:
1. Implement a Web Crawler:
   - Using Python web scraping libraries (e.g., Scrapy, BeautifulSoup)

2. Set up a Database:
   - SQL database (e.g., PostgreSQL) for structured data storage
   - Create all tables needed

3. Set up a Search Functionality:
   - Add Search by title implementation
   - Add Search by author implementation 
   - Add Search by keywords implementation

4. Create a User Interface:
   - Use a frontend framework (e.g., React, Vue.js) to create this. 
   - Create a paper listing view
   - Create a paper detail view
   - Create a search interface
   - Make the UI responsive

6. Deployment:
   - Create Local deployment steps
   - Create Docker container

Make sure every subtask is self-contained and includes any necessary details."""
            full_prompt = f"{instructions}\n\nUser Idea: {user_idea}"
        else:
            full_prompt = user_idea

        response = planner.generate_reply(messages=[{"role": "user", "content": full_prompt}])
        return response["content"]
    except Exception as e: 
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return f"Error: {str(e)}\nStack Trace:\n{stack_trace}"
