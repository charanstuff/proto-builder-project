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
from runtime.docker_manager import DockerManager
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
        # # Get and prepare Docker image
        # image = self.docker_manager.get_image()
        # # Setup container configuration
        # container_config = self._get_container_config(command)
        # logger.info("command:", str(container_config["command"]))
        # container = self.docker_manager.run_container(image=container_config["image"], command=container_config["command"], volumes=container_config["volumes"], ports=container_config["ports"], workdir=container_config["workdir"], labels=container_config["labels"])
        # return self._handle_container_output(container)
        command_list = []
        command_list.append(command)
        return self.docker_manager.execute(self.container, command_list, run_dir=self.workdir, timeout=timeout)
        

    def _get_container_config(self, command: str) -> dict:
        """Prepares container configuration including volumes, ports, and labels."""
        volumes = {
            os.path.abspath(self.files.working_dir): {
                'bind': self.workdir,
                'mode': 'rw'
            }
        }
        logger.debug("Volume mapping: %s", volumes)
        
        return {
            'image': self.image,
            'command': command,
            'volumes': volumes,
            'ports': {"5000/tcp": 5000},
            'workdir': self.workdir,
            'labels': {"runtime_project": "proto-builder"}
        }

    def _handle_container_output(self, container) -> Tuple[str, str, int]:
        """Handles container output streaming, logging and cleanup."""
        stdout_accum = []
        try:
            # Stream logs and accumulate stdout
            log_thread = threading.Thread(
                target=self._stream_container_logs,
                args=(container, stdout_accum)
            )
            log_thread.start()
            
            exit_status = self.docker_manager.wait_for_container(container)
            log_thread.join()

            # Save and process final logs
            logs_content = self._save_container_logs(container)
            # todo: cleanup container
            #self.docker_manager.cleanup_container(container)
            
            stdout_combined = "".join(stdout_accum)
            return (stdout_combined, logs_content, exit_status.get("StatusCode", 1))
        except Exception as e:
            logger.error("Error handling container output: %s", e, exc_info=True)
            try:
                self.docker_manager.cleanup_container(container)
            except Exception as cleanup_error:
                logger.error("Error cleaning up container: %s", cleanup_error, exc_info=True)
            return ("", str(e), 1)

    def _stream_container_logs(self, container, stdout_accum: list):
        """Streams and accumulates container logs."""
        try:
            for line in container.logs(stream=True):
                decoded_line = line.decode("utf-8", errors="replace")
                stdout_accum.append(decoded_line)
                sys.stdout.write(decoded_line)
                sys.stdout.flush()
        except Exception as e:
            logger.error("Error streaming container logs: %s", e, exc_info=True)

    def _save_container_logs(self, container) -> str:
        """Saves container logs to file and returns log content."""
        logs_content = self.docker_manager.get_container_logs(container)
        log_file_path = os.path.join(LOGS_DIR, "execution.log")
        logger.debug("Saving final logs to: %s", log_file_path)
        with open(log_file_path, "w") as f:
            f.write(logs_content)
        return logs_content

    def popen(self, command: str) -> subprocess.Popen:
        """
        Runs the command in a Docker container using subprocess.Popen.
        This minimal implementation uses docker run with --rm and mounted volumes.
        Note: It does not perform code retrieval or image building.
        """
        import subprocess
        docker_cmd = ["docker", "run", "--rm"]
        volumes = {
            os.path.abspath(self.files.working_dir): {
                'bind': self.workdir,
                'mode': 'rw'
            }
        }
        for host_dir, binding in volumes.items():
            container_bind = binding.get("bind", self.workdir)
            mode = binding.get("mode", "rw")
            docker_cmd.extend(["-v", f"{host_dir}:{container_bind}:{mode}"])
        docker_cmd.extend([self.language if self.language else "react-python:latest", "sh", "-c", command])
        logger.debug("Popen docker command: %s", docker_cmd)
        return subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)



    def download(self) -> FilesDict:
        """
        Dummy implementation for download.
        In a full implementation, you might use 'docker cp' to copy files from a container.
        Here, we return an empty FilesDict.
        """
        logger.info("Download called, but not implemented. Returning empty FilesDict.")
        return {}

