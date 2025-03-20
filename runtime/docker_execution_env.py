import os
import io
from pathlib import Path
from typing import Optional, Tuple, Union
import sys
import threading
import logging
from dataclasses import dataclass
import tarfile
import subprocess


from proto_builder.core.base_execution_env import BaseExecutionEnv
from proto_builder.core.files_dict import FilesDict  # Adjust or stub as needed
from runtime.backup_docker_manager import DockerManager
from runtime.logger_config import setup_logger
from runtime.config import LOGS_DIR
from proto_builder.core.default.file_store import FileStore

logger = setup_logger(__name__)

class DockerExecutionEnv(BaseExecutionEnv):
    def __init__(self, container: str, docker_manager: DockerManager, workdir: str = "/workspace", path: Union[str, Path, None] = None):
        self.files = FileStore(path)  # Still useful for local staging
        self.workdir = workdir
        self.docker_manager = docker_manager
        self.container = container

    def upload(self, files: FilesDict) -> BaseExecutionEnv:
        """
        Upload files to container:
        1. Stage files locally using FileStore
        2. Create tar archive of files
        3. Copy tar into container
        """

        # Stage files locally first

        logger.info("Files staged in: %s", self.files.working_dir)
        self.files.push(files)
        self.docker_manager.copy_code_to_container(self.container, self.files.working_dir, self.workdir)
        logger.info("Files copied to container of image %s", str(self.container))
        return self
    

    def run(self, command: str, timeout: Optional[int] = 3) -> Tuple[str, str, int]:
        """
        Executes the provided command inside a Docker container.
        This method retrieves the code, builds or pulls the Docker image,
        runs the container, streams logs, and returns stdout, stderr, and exit code.
        """
        logger.info("Starting DockerExecutionEnv run method.")
        command_list = []
        command_list.append(command)
        self.docker_manager.execute(self.container, command_list, run_dir=self.workdir, timeout=timeout)
        status = self.docker_manager.get_execution_status(self.container)
        logger.info("Execution status: %s", status)
        stdout = self.docker_manager.get_log(self.container)
        logger.info("stdout: %s", stdout)
        return status, stdout, "stderr not implemented"

    # def popen(self, command: str) -> subprocess.Popen:
        # """
        # Runs the command in a Docker container using subprocess.Popen.
        # This minimal implementation uses docker run with --rm and mounted volumes.
        # Note: It does not perform code retrieval or image building.
        # """
        # import subprocess
        # docker_cmd = ["docker", "run", "--rm"]
        # volumes = {
        #     os.path.abspath(self.files.working_dir): {
        #         'bind': self.workdir,
        #         'mode': 'rw'
        #     }
        # }
        # for host_dir, binding in volumes.items():
        #     container_bind = binding.get("bind", self.workdir)
        #     mode = binding.get("mode", "rw")
        #     docker_cmd.extend(["-v", f"{host_dir}:{container_bind}:{mode}"])
        # docker_cmd.extend([self.language if self.language else "react-python:latest", "sh", "-c", command])
        # logger.debug("Popen docker command: %s", docker_cmd)
        # return subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def popen(self, command: str) -> subprocess.Popen:
        """
        Runs the command in a Docker container using subprocess.Popen.
        Ensures code is copied to container before executing the command.
        
        Parameters
        ----------
        command : str
            The command to run inside the container
            
        Returns
        -------
        subprocess.Popen
            A process object connected to the command running in the container
        """
        # First ensure code is copied to container
        if not self.files.is_empty():
            logger.info("Copying code to container...")
            self.docker_manager.copy_code_to_container(
                self.container, 
                str(self.files.working_dir), 
                self.workdir
            )
            logger.info("Code copied to container")
        
        docker_cmd = [
            "docker", 
            "exec",
            "-w", self.workdir,  # Set working directory in container
            self.container,      # Use existing container
            "sh", "-c",         # Run command through shell
            command
        ]
        
        logger.debug("Popen docker command: %s", docker_cmd)
        return subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )



    def download(self) -> FilesDict:
        """
        Dummy implementation for download.
        In a full implementation, you might use 'docker cp' to copy files from a container.
        Here, we return an empty FilesDict.
        """
        logger.info("Download called, but not implemented. Returning empty FilesDict.")
        return {}

