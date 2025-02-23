import traceback
import autogen
import os
import re
import subprocess
from xml.etree import ElementTree as ET
from pydantic import BaseModel, Field
from typing import List, Dict
from create_project import parse_developer_xml, create_project_from_data

from config.settings import config
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

class FileEntry(BaseModel):
    path: str = Field(..., description="Relative file path")
    content: str = Field(..., description="File content (may be enclosed in <code>...</code> tags)")

class DeveloperOutputXML(BaseModel):
    project_structure: List[str] = Field(..., description="List of directories to create, from <dir> elements.")
    setup: str = Field(..., description="Installation instructions, prerequisites, and initial setup steps.")
    files: Dict[str, str] = Field(..., description="Mapping of file paths to file content (with <code> tags).")
    run_deploy_steps: str = Field(..., description="Steps on how to run the project.")
    misc_content: str = Field("", description="Any miscellaneous additional information.")
    project_creation_command: str = Field("", description="Command (e.g., 'vue create my-project') if available; otherwise empty.")

# Determine if the model supports system messages.
supports_system_message = config.OPENAI_MODEL not in ["o1-mini"]

llm_config = {
    "api_key": config.OPENAI_API_KEY,
    "model": config.OPENAI_MODEL
}

if supports_system_message:
    llm_config["system_message"] = """You are a skilled Developer Agent. 
Instructions:
- Follow the detailed plan and produce complete, functional code that can be run locally.
- Comment extensively and follow best practices.
    
OUTPUT FORMAT: A single valid XML with the structure:

<developer_output>
  <project_structure>
    <dir>...</dir>
    <dir>...</dir>
  </project_structure>
  <setup>...</setup>
  <files>
    <file>
      <path>path/to/file/from/project/root/directory.js</path>
      <content><![CDATA[<code>...</code>]]></content>
    </file>
    ...
  </files>
  <run_deploy_steps>...</run_deploy_steps>
  <misc_content>...</misc_content>
  <project_creation_command>...</project_creation_command>
</developer_output>

NO markdown. NO backticks. Just XML.
"""

developer = autogen.AssistantAgent("Developer", llm_config=llm_config)

if not supports_system_message:
    developer._oai_system_message = ""
    def patched_generate_reply(messages, sender=None):
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages
        )
        return {"content": response.choices[0].message.content.strip()}
    developer.generate_reply = patched_generate_reply



def generate_code(task_name, task_description):
    """
    Requests the Developer agent to output valid XML with the specified structure.
    Returns the raw XML string or an error message if something fails.
    """
    try:
        # System message is already set if supports_system_message is True.
        if not supports_system_message:
            # Provide fallback instructions in the user prompt if system not supported
            instructions = """
- Follow the detailed plan and produce complete, functional code that can be run locally.
- Comment extensively and follow best practices.
    
OUTPUT FORMAT: A single valid XML with the structure:

<developer_output>
  <project_structure>
    <dir>...</dir>
    <dir>...</dir>
  </project_structure>
  <setup>...</setup>
  <files>
    <file>
      <path>path/to/file/from/project/root/directory.js</path>
      <content><![CDATA[<code>...</code>]]></content>
    </file>
    ...
  </files>
  <run_deploy_steps>...</run_deploy_steps>
  <misc_content>...</misc_content>
  <project_creation_command>...</project_creation_command>
</developer_output>

NO markdown. NO backticks. Just XML.
"""
            full_prompt = f"{instructions}\n\nTask: {task_description}"
        else:
            full_prompt = task_description

        response = developer.generate_reply(messages=[{"role": "user", "content": full_prompt}])
        raw_xml = response["content"]

        # (Optionally) remove any triple backticks if the LLM added them:
        raw_xml = re.sub(r"^```(xml)?", "", raw_xml.strip())
        raw_xml = re.sub(r"```$", "", raw_xml.strip())

        return raw_xml
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
        return f"Error: {str(e)}\nStack Trace:\n{stack_trace}"

def create_project_from_output(dev_output: DeveloperOutputXML):
    """
    Creates the project structure and files based on the DeveloperOutputXML model.
    If "project_creation_command" is provided, executes it.
    Otherwise, we create directories from dev_output.project_structure,
    then create files from dev_output.files,
    removing <code> tags from the content.
    """
    if dev_output.project_creation_command.strip():
        print("Executing project creation command:")
        print(dev_output.project_creation_command)
        try:
            subprocess.run(dev_output.project_creation_command, shell=True, check=True)
        except Exception as cmd_err:
            print(f"Failed to execute project creation command: {cmd_err}")
    else:
        for directory in dev_output.project_structure:
            try:
                if directory.strip():
                    os.makedirs(directory.strip(), exist_ok=True)
                    print(f"Created directory: {directory.strip()}")
            except Exception as dir_err:
                print(f"Failed to create directory '{directory.strip()}': {dir_err}")

    for path, content in dev_output.files.items():
        # Remove <code>...</code> tags if present
        cleaned = re.sub(r"</?code>", "", content).strip()
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w") as f:
            f.write(cleaned)
        print(f"Created file: {path}")

    # Print setup / run info
    print("\n--- Setup Instructions ---")
    print(dev_output.setup)
    print("\n--- Run Instructions ---")
    print(dev_output.run_deploy_steps)
    if dev_output.misc_content.strip():
        print("\n--- Miscellaneous Info ---")
        print(dev_output.misc_content)

def simulate_project_creation(task_description):
    """
    Example usage: requests the Developer agent for an XML output, 
    parses it, then (optionally) calls create_project_from_output.
    """
    print("Bulding project based on the idea")
    raw_xml = generate_code("test", task_description)
    with open("raw_xml.txt", "w") as f: 
        f.write(raw_xml)
    try:
        
        data = parse_developer_xml(raw_xml)
        # Print the parsed model
        print("\nParsed DeveloperOutputXML object:")
        print(data)
        create_project_from_data(data)
    except Exception as e:
        print(f"Error parsing the LLM's XML: {e}")
