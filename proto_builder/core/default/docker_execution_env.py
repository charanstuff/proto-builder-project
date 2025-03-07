import os
import sys
import threading
import logging
from dataclasses import dataclass
from subprocess import Popen
from typing import Optional, Tuple

from base_execution_env import BaseExecutionEnv
from proto_builder.core.files_dict import FilesDict  # Adjust or stub as needed
from code_manager import get_code
from docker_manager import DockerManager
from logger_config import setup_logger
from config import DOCKER_IMAGES, DEFAULT_LANGUAGE, EXECUTION_MODE, LOGS_DIR

logger = setup_logger(__name__)

@dataclass
class DockerExecutionRequest:
    language: str = DEFAULT_LANGUAGE
    source: str = None         # e.g., path to the project (git URL or local directory)
    command: str = None        # command to run inside the container
    workdir: str = "/code"     # working directory inside container
    dest: str = "code_dir"     # destination directory where code is copied/cloned
    mode: str = EXECUTION_MODE

class DockerExecutionEnv(BaseExecutionEnv):
    def __init__(self, request: DockerExecutionRequest):
        self.request = request
        self.docker_manager = DockerManager()
        logger.debug("DockerExecutionEnv initialized with request: %s", request)

    def run(self, command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """
        Executes the provided command inside a Docker container.
        This method retrieves the code, builds or pulls the Docker image,
        runs the container, streams logs, and returns stdout, stderr, and exit code.
        """
        logger.info("Starting DockerExecutionEnv run method.")
        # Retrieve code
        try:
            get_code(self.request.source, self.request.dest)
            logger.debug("Code retrieved successfully from %s to %s", self.request.source, self.request.dest)
        except Exception as e:
            logger.error("Failed to get code: %s", e, exc_info=True)
            return ("", str(e), 1)
        
        # Determine image to use.
        language_key = self.request.language.lower() if self.request.language else DEFAULT_LANGUAGE
        image = DOCKER_IMAGES.get(language_key, DOCKER_IMAGES[DEFAULT_LANGUAGE])
        logger.debug("Using image: %s for language: %s", image, language_key)
        
        # For reactpython, build the image using the runtime’s Dockerfile.
        if language_key == "reactpython":
            try:
                logger.info("Building react-python image as part of execution.")
                # Use the runtime folder (i.e. directory of this file) as the build context.
                dockerfile_context = os.path.dirname(os.path.abspath(__file__))
                logger.debug("Docker build context: %s", dockerfile_context)
                self.docker_manager.build_image(dockerfile_context, tag=image)
            except Exception as e:
                logger.error("Failed to build image: %s", e, exc_info=True)
                return ("", str(e), 1)
        else:
            try:
                self.docker_manager.pull_image(image)
            except Exception as e:
                logger.error("Failed to pull Docker image: %s", e, exc_info=True)
                return ("", str(e), 1)
        
        # Setup volume mapping.
        volumes = {
            os.path.abspath(self.request.dest): {
                'bind': self.request.workdir,
                'mode': 'rw'
            }
        }
        logger.debug("Volume mapping: %s", volumes)
        # Setup port mapping.
        ports = {"5000/tcp": 5000}
        logger.debug("Port mapping: %s", ports)
        # Label for cleanup.
        labels = {"runtime_project": "proto-builder"}
        
        container = None
        stdout_accum = []
        try:
            logger.info("Starting container with provided command.")
            container = self.docker_manager.run_container(
                image=image,
                command=command,
                volumes=volumes,
                ports=ports,
                workdir=self.request.workdir,
                labels=labels
            )

            # Stream logs and accumulate stdout.
            def stream_logs():
                try:
                    for line in container.logs(stream=True):
                        decoded_line = line.decode("utf-8", errors="replace")
                        stdout_accum.append(decoded_line)
                        sys.stdout.write(decoded_line)
                        sys.stdout.flush()
                except Exception as e:
                    logger.error("Error streaming container logs: %s", e, exc_info=True)
            
            log_thread = threading.Thread(target=stream_logs)
            log_thread.start()
            exit_status = self.docker_manager.wait_for_container(container)
            log_thread.join()
            
            # Save final logs.
            logs_content = self.docker_manager.get_container_logs(container)
            log_file_path = os.path.join(LOGS_DIR, "execution.log")
            logger.debug("Saving final logs to: %s", log_file_path)
            with open(log_file_path, "w") as f:
                f.write(logs_content)
            self.docker_manager.cleanup_container(container)
            
            stdout_combined = "".join(stdout_accum)
            return (stdout_combined, logs_content, exit_status.get("StatusCode", 1))
        except Exception as e:
            logger.error("Error during container execution: %s", e, exc_info=True)
            if container:
                try:
                    self.docker_manager.cleanup_container(container)
                except Exception as cleanup_error:
                    logger.error("Error cleaning up container: %s", cleanup_error, exc_info=True)
            return ("", str(e), 1)

    def popen(self, command: str) -> Popen:
        """
        Runs the command in a Docker container using subprocess.Popen.
        This minimal implementation uses docker run with --rm and mounted volumes.
        Note: It does not perform code retrieval or image building.
        """
        import subprocess
        docker_cmd = ["docker", "run", "--rm"]
        volumes = {
            os.path.abspath(self.request.dest): {
                'bind': self.request.workdir,
                'mode': 'rw'
            }
        }
        for host_dir, binding in volumes.items():
            container_bind = binding.get("bind", self.request.workdir)
            mode = binding.get("mode", "rw")
            docker_cmd.extend(["-v", f"{host_dir}:{container_bind}:{mode}"])
        docker_cmd.extend([self.request.language if self.request.language else "react-python:latest", "sh", "-c", command])
        logger.debug("Popen docker command: %s", docker_cmd)
        return subprocess.Popen(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def upload(self, files: FilesDict) -> BaseExecutionEnv:
        """
        Dummy implementation for upload.
        In a full implementation, you might use 'docker cp' to copy files into a running container.
        Here, we assume files are made available via mounted volumes.
        """
        logger.info("Upload called, but not implemented. Returning self.")
        return self

    def download(self) -> FilesDict:
        """
        Dummy implementation for download.
        In a full implementation, you might use 'docker cp' to copy files from a container.
        Here, we return an empty FilesDict.
        """
        logger.info("Download called, but not implemented. Returning empty FilesDict.")
        return {}

