# import autogen
# import os
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
#         "You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. "
#         "Write clean, modular, and well-documented code for each task.\n\n"
#         "Instructions:\n"
#         "- Follow the detailed plan: Implement the subtasks in sequence, ensuring each module is functional.\n"
#         "- Comment extensively: Explain what each function or code block does and why it’s structured that way.\n"
#         "- Structure your code: Use functions, classes, or modules appropriately to keep the code modular.\n"
#         "- Provide examples and test cases, including code snippets that verify functionality.\n"
#         "- Adhere to best practices: Use proper error handling, input validation, and coding conventions.\n"
#         "- If external tools are needed (e.g., for API calls or calculations), clearly annotate those sections."
#     )

# developer = autogen.AssistantAgent("Developer", llm_config=llm_config)

# # For models like o1-mini, clear the internal system message by setting it to an empty list.
# if not supports_system_message:
#     developer._oai_system_message = []

# def save_code_locally(task_name, code):
#     """Saves generated code to the 'projects' directory in test mode."""
#     if config.EXECUTION_MODE == "test":
#         file_path = f"projects/{task_name}.py"
#         with open(file_path, "w") as f:
#             f.write(code)
#         print(f"✅ Code saved locally: {file_path}")
#     return code

# def generate_code(task_name, task_description):
#     """
#     Generates code for the given task.
#     If the model does not support system messages, embed developer instructions in the prompt.
#     """
#     if not supports_system_message:
#         instructions = (
#             "You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. "
#             "Write clean, modular, and well-documented code for each task.\n\n"
#             "Instructions:\n"
#             "- Follow the detailed plan and implement the subtasks sequentially.\n"
#             "- Comment extensively on what each function or code block does.\n"
#             "- Structure your code using functions, classes, or modules appropriately.\n"
#             "- Provide examples and test cases to verify functionality.\n"
#             "- Use proper error handling, input validation, and coding conventions.\n"
#             "- Clearly annotate sections requiring external tools if needed.\n\n"
#             "Now, generate code for the following task:"
#         )
#         full_prompt = f"{instructions}\n\nTask: {task_description}"
#     else:
#         full_prompt = task_description

#     response = developer.generate_reply(messages=[{"role": "user", "content": full_prompt}])
#     code = response["content"]

#     if config.EXECUTION_MODE == "test":
#         return save_code_locally(task_name, code)
#     return code
import autogen
import os
from config.settings import config
import openai

supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

llm_config = {
    "api_key": config.OPENAI_API_KEY,
    "model": config.OPENAI_MODEL
}

if supports_system_message:
    llm_config["system_message"] = """You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. Write clean, modular, and well-documented code for each task.

Instructions:
- Follow the detailed plan: Implement the subtasks in sequence, ensuring each module is functional.
- Comment extensively: Explain what each function or code block does and why it’s structured that way.
- Structure your code: Use functions, classes, or modules appropriately to keep the code modular.
- Provide examples and test cases: For example, include code snippets that verify functionality.
- Adhere to best practices: Use proper error handling, input validation, and coding conventions.
- If external tools are needed (e.g., for API calls or calculations), clearly annotate those sections.
"""
    
developer = autogen.AssistantAgent("Developer", llm_config=llm_config)

if not supports_system_message:
    developer._oai_system_message = ""
    def patched_generate_reply(messages, sender=None):
        response = openai.ChatCompletion.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            api_key=config.OPENAI_API_KEY
        )
        return {"content": response.choices[0].message["content"]}
    developer.generate_reply = patched_generate_reply

def save_code_locally(task_name, code):
    """Saves generated code to the 'projects' directory in test mode."""
    if config.EXECUTION_MODE == "test":
        file_path = f"projects/{task_name}.py"
        with open(file_path, "w") as f:
            f.write(code)
        print(f"✅ Code saved locally: {file_path}")
    return code

def generate_code(task_name, task_description):
    """Generates code and either saves it locally (test mode) or returns it for deployment."""
    if not supports_system_message:
        instructions = """You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. Write clean, modular, and well-documented code for each task.

Instructions:
- Follow the detailed plan: Implement the subtasks in sequence, ensuring each module is functional.
- Comment extensively: Explain what each function or code block does and why it’s structured that way.
- Structure your code: Use functions, classes, or modules appropriately to keep the code modular.
- Provide examples and test cases: For example, include code snippets that verify functionality.
- Adhere to best practices: Use proper error handling, input validation, and coding conventions.
- If external tools are needed (e.g., for API calls or calculations), clearly annotate those sections.

Now, generate code for the following task:"""
        full_prompt = f"{instructions}\n\nTask: {task_description}"
    else:
        full_prompt = task_description

    response = developer.generate_reply(messages=[{"role": "user", "content": full_prompt}])
    code = response["content"]

    if config.EXECUTION_MODE == "test":
        return save_code_locally(task_name, code)
    return code
