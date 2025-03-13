import os
import sys
import threading
import logging
from dataclasses import dataclass
from code_manager import get_code
from docker_manager import DockerManager
from logger_config import setup_logger
from config import DOCKER_IMAGES, DEFAULT_LANGUAGE, EXECUTION_MODE, LOGS_DIR

logger = setup_logger(__name__)

@dataclass
class ExecutionRequest:
    language: str = DEFAULT_LANGUAGE
    source: str = None         # e.g., path to the project (git URL or local directory)
    command: str = None        # command to run inside the container
    workdir: str = "/code"     # working directory inside container
    dest: str = "code_dir"     # destination directory where code is copied/cloned
    mode: str = EXECUTION_MODE

class RuntimeExecutor:
    def __init__(self):
        self.docker_manager = DockerManager()
        logger.debug("RuntimeExecutor initialized.")

    def execute(self, request: ExecutionRequest):
        logger.info("Starting execution of runtime request.")
        logger.debug(f"ExecutionRequest details: {request}")
        # Step 1: Retrieve code (clone or copy)
        try:
            get_code(request.source, request.dest)
            logger.debug(f"Code retrieved successfully from {request.source} to {request.dest}")
        except Exception as e:
            logger.error(f"Failed to get code: {e}", exc_info=True)
            sys.exit(1)

        # Step 2: Determine Docker image to use.
        language_key = request.language.lower() if request.language else DEFAULT_LANGUAGE
        image = DOCKER_IMAGES.get(language_key, DOCKER_IMAGES[DEFAULT_LANGUAGE])
        logger.debug(f"Using image: {image} for language: {language_key}")
        
        # For reactpython, always build the image as part of execution using runtime's Dockerfile.
        if language_key == "reactpython":
            try:
                logger.info("Building react-python image as part of execution.")
                # Use the runtime folder (i.e. directory of this file) as the build context.
                dockerfile_context = os.path.dirname(os.path.abspath(__file__))
                logger.debug(f"Docker build context: {dockerfile_context}")
                self.docker_manager.build_image(dockerfile_context, tag=image)
            except Exception as e:
                logger.error(f"Failed to build image: {e}", exc_info=True)
                sys.exit(1)
        else:
            try:
                self.docker_manager.pull_image(image)
            except Exception as e:
                logger.error(f"Failed to pull Docker image: {e}", exc_info=True)
                sys.exit(1)

        # Set up volume mapping: map host code directory to container's workdir.
        volumes = {
            os.path.abspath(request.dest): {
                'bind': request.workdir,
                'mode': 'rw'
            }
        }
        logger.debug(f"Volume mapping: {volumes}")

        # Set up port mapping (assume container port 5000 to host port 5000).
        ports = {"5000/tcp": 5000}
        logger.debug(f"Port mapping: {ports}")

        # Add a label for cleanup purposes.
        labels = {"runtime_project": "proto-builder"}

        container = None
        try:
            # Step 3: Run container with provided command.
            logger.info("Starting container with provided command.")
            container = self.docker_manager.run_container(
                image=image,
                command=request.command,
                volumes=volumes,
                ports=ports,
                workdir=request.workdir,
                labels=labels
            )

            # Stream container logs in a separate thread.
            logger.info("Starting log streaming thread for container.")
            log_thread = threading.Thread(target=self._stream_logs, args=(container,))
            log_thread.start()

            # Wait for container to finish.
            exit_status = self.docker_manager.wait_for_container(container)
            log_thread.join()

            # Save final logs.
            logs_content = self.docker_manager.get_container_logs(container)
            log_file_path = os.path.join(LOGS_DIR, "execution.log")
            logger.debug(f"Saving final logs to: {log_file_path}")
            with open(log_file_path, "w") as f:
                f.write(logs_content)

            self.docker_manager.cleanup_container(container)

            if exit_status.get("StatusCode", 1) == 0:
                logger.info("Code executed successfully.")
            else:
                logger.error("Code execution failed.")
        except KeyboardInterrupt:
            logger.info("Execution interrupted by user. Saving logs and cleaning up container.")
            try:
                if container:
                    logs_content = self.docker_manager.get_container_logs(container)
                    log_file_path = os.path.join(LOGS_DIR, "execution_interrupt.log")
                    with open(log_file_path, "w") as f:
                        f.write(logs_content)
            except Exception as e:
                logger.error(f"Error saving logs on interruption: {e}", exc_info=True)
            finally:
                if container:
                    try:
                        self.docker_manager.cleanup_container(container)
                    except Exception as e:
                        logger.error(f"Error cleaning up container: {e}", exc_info=True)
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error during container execution: {e}", exc_info=True)
            if container:
                try:
                    self.docker_manager.cleanup_container(container)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up container: {cleanup_error}", exc_info=True)
            sys.exit(1)

    def _stream_logs(self, container):
        logger.info("Streaming container logs:")
        try:
            for line in container.logs(stream=True):
                decoded_line = line.decode("utf-8", errors="replace")
                sys.stdout.write(decoded_line)
                sys.stdout.flush()
                logger.debug(f"Container log: {decoded_line.strip()}")
        except Exception as e:
            logger.error(f"Error streaming container logs: {e}", exc_info=True)

# Example of how to call the interface:
if __name__ == "__main__":
    req = ExecutionRequest(
        language="reactpython",  # defaults to reactpython if not provided
        source="./dummy_helloworld_react_python",  # project directory containing your source code
        command="./build.sh && cd backend && pip install -r requirements.txt && python app.py",
        workdir="/code",
        dest="code_dir",
        mode="local"
    )
    executor = RuntimeExecutor()
    executor.execute(req)
