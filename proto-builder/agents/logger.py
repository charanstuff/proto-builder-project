# import autogen
# from config.settings import config

# # Determine if the model supports system messages.
# supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

# llm_config = {
#     "api_key": config.OPENAI_API_KEY,
#     "model": config.OPENAI_MODEL
# }

# # Only add a system message if the model supports it.
# if supports_system_message:
#     llm_config["system_message"] = (
#         "You are a Logger Agent responsible for capturing and reporting all interactions between agents in a clear, concise, and human-readable manner.\n\n"
#         "Instructions:\n"
#         "- Log every interaction and reasoning step from each agent.\n"
#         "- Provide concise messages and bullet points summarizing actions, decisions, and any notable reasoning.\n"
#         "- Format logs in a well-structured, human-readable way using headers, bullet points, or short paragraphs.\n"
#         "- Include timestamps or sequence markers where applicable to trace the flow of operations.\n"
#         "- Clearly indicate which agent the log entry pertains to, and provide context about the interaction.\n"
#         "- Use accessible language and avoid overly technical jargon unless necessary for clarity.\n"
#         "- Your logs should serve as a clear and informative summary of the agents’ interactions for debugging and review purposes.\n\n"
#         "Example Output:\n"
#         "[12:01] Chatbot: Asked the user to describe the app's core functionality.\n"
#         "[12:02] Planner: Broke down the idea into UI, Backend, and Deployment subtasks.\n"
#         "[12:03] Developer: Started coding the authentication module with detailed comments."
#     )

# logger = autogen.AssistantAgent("Logger", llm_config=llm_config)

# # For models like o1-mini, clear the internal system message by setting it to an empty list.
# if not supports_system_message:
#     logger._oai_system_message = []

# def generate_log_entry(agent_name, log_message):
#     """
#     Generates a log entry for the specified agent and event.
#     For models that do not support system messages, embed instructions in the prompt.
#     """
#     if not supports_system_message:
#         instructions = (
#             "You are a Logger Agent responsible for capturing and reporting all interactions in a clear and concise manner.\n\n"
#             "Instructions:\n"
#             "- Log every interaction and reasoning step from each agent.\n"
#             "- Provide concise messages and bullet points summarizing actions and decisions.\n"
#             "- Format logs using headers, bullet points, or short paragraphs.\n"
#             "- Include timestamps or sequence markers to trace operations.\n"
#             "- Clearly indicate which agent the log entry pertains to.\n"
#             "- Avoid overly technical jargon unless necessary.\n\n"
#             "Now, generate a log entry for the following event:"
#         )
#         full_prompt = f"{instructions}\n\nAgent: {agent_name}\nEvent: {log_message}"
#     else:
#         full_prompt = f"Agent: {agent_name}\nEvent: {log_message}"

#     response = logger.generate_reply(messages=[{"role": "user", "content": full_prompt}])
#     return response["content"]
import os
import traceback
import autogen
from config.settings import config
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
    llm_config["system_message"] = """You are a Logger Agent responsible for capturing and reporting all interactions between agents in a clear, concise, and human-readable manner.

Instructions:
- Log every interaction and reasoning step from each agent.
- Provide concise messages and bullet points summarizing actions, decisions, and any notable reasoning.
- Format logs in a well-structured, human-readable way using headers, bullet points, or short paragraphs.
- Include timestamps or sequence markers where applicable to trace the flow of operations.
- Clearly indicate which agent the log entry pertains to, and provide context about the interaction.
- Use accessible language and avoid overly technical jargon unless it is necessary for clarity.
- Your logs should serve as a clear and informative summary of the agents’ interactions for debugging and review purposes.

Example Output:
[12:01] Chatbot: Asked the user to describe the app's core functionality.
[12:02] Planner: Broke down the idea into UI, Backend, and Deployment subtasks.
[12:03] Developer: Started coding the authentication module with detailed comments.
"""
    
logger = autogen.AssistantAgent("Logger", llm_config=llm_config)

if not supports_system_message:
    logger._oai_system_message = ""
    def patched_generate_reply(messages, sender=None):
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages
        )
        return {"content": response.choices[0].message.content.strip()}
    logger.generate_reply = patched_generate_reply

def generate_log_entry(agent_name, log_message):
    """Generates a log entry for the specified event.
    
    If an error occurs during log generation, a detailed error message with stack trace is returned.
    """
    try:
        if not supports_system_message:
            instructions = """You are a Logger Agent responsible for capturing and reporting all interactions between agents in a clear, concise, and human-readable manner.

Instructions:
- Log every interaction and reasoning step from each agent.
- Provide concise messages and bullet points summarizing actions, decisions, and any notable reasoning.
- Format logs in a well-structured, human-readable way using headers, bullet points, or short paragraphs.
- Include timestamps or sequence markers where applicable to trace the flow of operations.
- Clearly indicate which agent the log entry pertains to, and provide context about the interaction.
- Use accessible language and avoid overly technical jargon unless it is necessary for clarity.
- Your logs should serve as a clear and informative summary of the agents’ interactions for debugging and review purposes.

Example Output:
[12:01] Chatbot: Asked the user to describe the app's core functionality.
[12:02] Planner: Broke down the idea into UI, Backend, and Deployment subtasks.
[12:03] Developer: Started coding the authentication module with detailed comments.

Now, generate a log entry for the following event:"""
            full_prompt = f"{instructions}\n\nAgent: {agent_name}\nEvent: {log_message}"
        else:
            full_prompt = f"Agent: {agent_name}\nEvent: {log_message}"
    
        response = logger.generate_reply(messages=[{"role": "user", "content": full_prompt}])
        return response["content"]
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return f"Error: {str(e)}\nStack Trace:\n{stack_trace}"
