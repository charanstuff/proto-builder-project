
# import traceback
# import autogen
# import os
# from config.settings import config
# from openai import OpenAI
# from pydantic import BaseModel, Field

# client = OpenAI(
#     api_key = os.getenv("OPENAI_API_KEY"),
# )

# # Define the structured output schema using Pydantic.
# # Define the structured output schema using Pydantic.
# class DeveloperOutput(BaseModel):
#     project_structure: str = Field(..., description="A description of the project directory structure.")
#     setup: str = Field(..., description="Installation instructions, prerequisites, and initial setup steps.")
#     files: str = Field(..., description="A summary of the key files and their contents in the project.")
#     run_deploy_steps: str = Field(..., description="Detailed steps on how to run and deploy the project.")



# # Determine if the model supports system messages.
# supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

# llm_config = {
#     "api_key": config.OPENAI_API_KEY,  # Retained for autogen config (not used in our patched call)
#     "model": config.OPENAI_MODEL
# }

# if supports_system_message:
#     llm_config["system_message"] = """You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. Write clean, modular, and well-documented code for each task.

# Instructions:
# - Follow the detailed plan: Implement the subtasks in sequence, ensuring each module is functional.
# - Comment extensively: Explain what each function or code block does and why it’s structured that way.
# - Structure your code: Use functions, classes, or modules appropriately to keep the code modular.
# - Provide examples and test cases: For example, include code snippets that verify functionality.
# - Adhere to best practices: Use proper error handling, input validation, and coding conventions.
# - If external tools are needed (e.g., for API calls or calculations), clearly annotate those sections.
# """

# developer = autogen.AssistantAgent("Developer", llm_config=llm_config)

# if not supports_system_message:
#     # Clear the internal system message.
#     developer._oai_system_message = ""
#     # Patch generate_reply to call the new ChatCompletion endpoint.
#     def patched_generate_reply(messages, sender=None):
#         response = client.chat.completions.create(
#             model=config.OPENAI_MODEL,
#             messages=messages
#         )
#         return {"content": response.choices[0].message.content.strip()}
#     developer.generate_reply = patched_generate_reply

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
#     Generates code and either saves it locally (test mode) or returns it for deployment.
#     If an error occurs during code generation, a detailed error message and stack trace are returned.
#     """
#     try:
#         if not supports_system_message:
#             instructions = """You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. Write clean, modular, and well-documented code for that does a list of tasks.

# Instructions:
# - Follow the detailed plan: Implement the list of tasks in any sequence as you deem fit, ensuring each module is functional.
# - Ensure the complete code is functional and can be run locally.
# - Comment extensively: Explain what each function or code block does and why it’s structured that way.
# - Structure your code: Use functions, classes, or modules appropriately to keep the code modular.
# - Provide examples and test cases: For example, include code snippets that verify functionality.
# - Adhere to best practices: Use proper error handling, input validation, and coding conventions.
# - If external tools are needed (e.g., for API calls or calculations), clearly annotate those sections.

# Now, generate code for the following task:"""
#             full_prompt = f"{instructions}\n\nTask: list {task_description}"
#         else:
#             full_prompt = task_description

#         response = developer.generate_reply(messages=[{"role": "user", "content": full_prompt}])
#         code = response["content"]

#         if config.EXECUTION_MODE == "test":
#             return save_code_locally(task_name, code)
#         return code
#     except Exception as e:
#         stack_trace = traceback.format_exc()
#         print(stack_trace)
#         return f"Error: {str(e)}\nStack Trace:\n{stack_trace}"

import traceback
import autogen
import os
from config.settings import config
from openai import OpenAI
from pydantic import BaseModel, Field
import json

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
)

# Define the structured output schema using Pydantic.
class DeveloperOutput(BaseModel):
    project_structure: str = Field(..., description="A description of the project directory structure.")
    setup: str = Field(..., description="Installation instructions, prerequisites, and initial setup steps.")
    files: str = Field(..., description="A summary of the key files and their contents in the project.")
    run_deploy_steps: str = Field(..., description="Detailed steps on how to run and deploy the project.")
    misc_content: str = Field("", description="Any miscellaneous additional information.")

# Determine if the model supports system messages.
supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

llm_config = {
    "api_key": config.OPENAI_API_KEY,  # Retained for autogen config (not used in our patched call)
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

Your output MUST be a valid JSON object with exactly the following keys:
  "project_structure", "setup", "files", "run_deploy_steps", and "misc_content".
Do not output any extra text outside of the JSON.
"""

developer = autogen.AssistantAgent("Developer", llm_config=llm_config)

if not supports_system_message:
    # Clear the internal system message.
    developer._oai_system_message = ""
    # Patch generate_reply to call the new ChatCompletion endpoint.
    def patched_generate_reply(messages, sender=None):
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages
        )
        return {"content": response.choices[0].message.content.strip()}
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
    """
    Generates code and either saves it locally (test mode) or returns it for deployment.
    If an error occurs during code generation, a detailed error message and stack trace are returned.
    The output MUST be a valid JSON object following the DeveloperOutput schema.
    """
    try:
        # Always use a structured prompt to enforce JSON output.
        instructions = """You are a skilled Developer Agent assigned to build a fully functional prototype based on the detailed plan. Write clean, modular, and well-documented code for a list of tasks.

Instructions:
- Follow the detailed plan and produce complete, functional code that can be run locally.
- Comment extensively and follow best practices.
- Your output MUST be a valid JSON object with exactly the following keys:
    "project_structure": a string describing the directory structure,
    "setup": a string with installation instructions, prerequisites, and setup steps,
    "files": a string summarizing the key files and their contents,
    "run_deploy_steps": a string describing the steps to run and deploy the project,
    "misc_content": a string containing any miscellaneous additional information.
Do not include any text outside of the JSON.
"""
        full_prompt = f"{instructions}\n\nTask: list {task_description}"
        
        response = developer.generate_reply(messages=[{"role": "user", "content": full_prompt}])
        code_str = response["content"]
        
        with open("code_str.txt", "w") as f:
            f.write(code_str)

        try:
            parsed = json.loads(code_str)
            # Validate the parsed JSON against the DeveloperOutput model.
            validated = DeveloperOutput.parse_obj(parsed)
            # If misc_content is present, print it.
            if validated.misc_content:
                print("Miscellaneous Information:")
                print(validated.misc_content)
            # Convert back to pretty-printed JSON string.
            code_str = validated.json(indent=2)
        except Exception as parse_err:
            raise ValueError(f"Failed to parse/validate JSON output. Output received: {code_str}\nError: {parse_err}")
        
        if config.EXECUTION_MODE == "test":
            return save_code_locally(task_name, code_str)
        return code_str
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return f"Error: {str(e)}\nStack Trace:\n{stack_trace}"
