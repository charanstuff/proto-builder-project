import os
import logging
from pathlib import Path
from termcolor import colored

from proto_builder.core.preprompts_holder import PrepromptsHolder
from proto_builder.applications.cli.cli_agent import CliAgent
from proto_builder.core.default.disk_memory import DiskMemory
from proto_builder.core.default.disk_execution_env import DiskExecutionEnv
from proto_builder.core.default.paths import PREPROMPTS_PATH, memory_path
from proto_builder.core.ai import AI
from proto_builder.core.prompt import Prompt
from proto_builder.core.default.steps import (
    gen_code,
    execute_entrypoint,
    improve_fn,
)
from proto_builder.core.default.file_store import FileStore

def get_preprompts_path(use_custom_preprompts: bool, input_path: Path) -> Path:
    """
    Get the path to the preprompts, using custom ones if specified.

    Parameters
    ----------
    use_custom_preprompts : bool
        Flag indicating whether to use custom preprompts.
    input_path : Path
        The path to the project directory.

    Returns
    -------
    Path
        The path to the directory containing the preprompts.
    """
    original_preprompts_path = PREPROMPTS_PATH
    if not use_custom_preprompts:
        return original_preprompts_path

    custom_preprompts_path = input_path / "preprompts"
    if not custom_preprompts_path.exists():
        custom_preprompts_path.mkdir()

    for file in original_preprompts_path.glob("*"):
        if not (custom_preprompts_path / file.name).exists():
            (custom_preprompts_path / file.name).write_text(file.read_text())
    return custom_preprompts_path

def concatenate_paths(base_path, sub_path):
    # Compute the relative path from base_path to sub_path
    relative_path = os.path.relpath(sub_path, base_path)

    # If the relative path is not in the parent directory, use the original sub_path
    if not relative_path.startswith(".."):
        return sub_path

    # Otherwise, concatenate base_path and sub_path
    return os.path.normpath(os.path.join(base_path, sub_path))

def load_prompt(
    input_repo: DiskMemory,
    improve_mode: bool,
    prompt_file: str,
    image_directory: str,
    entrypoint_prompt_file: str = "",
) -> Prompt:
    """
    Load or request a prompt from the user based on the mode.

    Parameters
    ----------
    input_repo : DiskMemory
        The disk memory object where prompts and other data are stored.
    improve_mode : bool
        Flag indicating whether the application is in improve mode.

    Returns
    -------
    str
        The loaded or inputted prompt.
    """

    if os.path.isdir(prompt_file):
        raise ValueError(
            f"The path to the prompt, {prompt_file}, already exists as a directory. No prompt can be read from it. Please specify a prompt file using --prompt_file"
        )
    prompt_str = input_repo.get(prompt_file)
    if prompt_str:
        print(colored("Using prompt from file:", "green"), prompt_file)
        print(prompt_str)
    else:
        if not improve_mode:
            prompt_str = input(
                "\nWhat application do you want proto-builder to generate?\n"
            )
        else:
            prompt_str = input("\nHow do you want to improve the application?\n")

    if entrypoint_prompt_file == "":
        entrypoint_prompt = ""
    else:
        full_entrypoint_prompt_file = concatenate_paths(
            input_repo.path, entrypoint_prompt_file
        )
        if os.path.isfile(full_entrypoint_prompt_file):
            entrypoint_prompt = input_repo.get(full_entrypoint_prompt_file)

        else:
            raise ValueError("The provided file at --entrypoint-prompt does not exist")

    if image_directory == "":
        return Prompt(prompt_str, entrypoint_prompt=entrypoint_prompt)

    full_image_directory = concatenate_paths(input_repo.path, image_directory)
    if os.path.isdir(full_image_directory):
        if len(os.listdir(full_image_directory)) == 0:
            raise ValueError("The provided --image_directory is empty.")
        image_repo = DiskMemory(full_image_directory)
        return Prompt(
            prompt_str,
            image_repo.get(".").to_dict(),
            entrypoint_prompt=entrypoint_prompt,
        )
    else:
        raise ValueError("The provided --image_directory is not a directory.")



def main():
    """
    Main entry point for the CLI application.
    Demonstrates retrieving preprompts using PrepromptsHolder.
    """
    logging.info("Running proto builder...")
    prompt_file = Path(__file__).parent.parent / "prompt.txt"
    project_path = "."
    path = Path(project_path)
    prompt = load_prompt(
        DiskMemory(path),
        False,
        prompt_file,
        "",
        "",
    )
    # TODO: hacky way to get the project path
    project_path = Path(__file__).parent.parent.parent
    use_custom_preprompts = False
    preprompts_holder = PrepromptsHolder(
        get_preprompts_path(use_custom_preprompts, Path(project_path))
    )
    memory = DiskMemory(memory_path(project_path))
    memory.archive_logs()
    execution_env = DiskExecutionEnv()
    ai = AI(
        model_name="gpt-4o-mini",
        temperature=0.1
    )
    agent = CliAgent.with_default_config(
        memory,
        execution_env,
        ai=ai,
        code_gen_fn=gen_code,
        improve_fn=improve_fn,
        process_code_fn=execute_entrypoint,
        preprompts_holder=preprompts_holder,
    )
    files = FileStore(project_path)
    print("Generating files...")
    files_dict = agent.init(prompt)
    logging.info(f"Generated files:")
    print(files_dict.to_log())
    print("DONE DONE")


if __name__ == "__main__":
    main()