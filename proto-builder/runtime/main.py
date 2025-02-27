# main.py

import os
import argparse
import logging
import sys
import threading

from logger_config import setup_logger
from config import DOCKER_IMAGES, EXECUTION_MODE, LOGS_DIR
from code_manager import get_code
from docker_manager import DockerManager

logger = setup_logger(__name__)

def stream_logs(container):
    """
    Stream container logs to stdout as they arrive.
    """
    logger.info("Streaming container logs:")
    try:
        for line in container.logs(stream=True):
            sys.stdout.write(line.decode("utf-8", errors="replace"))
            sys.stdout.flush()
    except Exception as e:
        logger.error(f"Error streaming container logs: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Runtime Environment for Code Execution")
    parser.add_argument("--language", type=str, required=True, 
                        help="Programming language of the code (python, java, node, etc)")
    parser.add_argument("--source", type=str, required=True, 
                        help="Source of the code: git URL or local directory path")
    parser.add_argument("--command", type=str, required=True, 
                        help="Command to run inside the container (e.g., 'pip install -r requirements.txt && python app.py')")
    parser.add_argument("--workdir", type=str, default="/code", 
                        help="Working directory inside the container")
    parser.add_argument("--dest", type=str, default="code_dir", 
                        help="Destination directory to copy/clone the code")
    parser.add_argument("--mode", type=str, default=EXECUTION_MODE, 
                        help="Execution mode: local, aws, or server")
    args = parser.parse_args()

    logger.info("Starting runtime environment.")

    # Ensure the logs directory exists
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    container = None
    docker_manager = DockerManager()

    try:
        # Step 1: Get code (clone or copy)
        get_code(args.source, args.dest)

        # Step 2: Determine the Docker image based on language
        image = DOCKER_IMAGES.get(args.language.lower())
        if not image:
            logger.error(f"No Docker image configured for language '{args.language}'.")
            sys.exit(1)

        docker_manager.pull_image(image)

        # Set up volume mapping (host code directory to container's workdir)
        volumes = {
            os.path.abspath(args.dest): {
                'bind': args.workdir,
                'mode': 'rw'
            }
        }
        # Also, set up port mapping if needed (e.g., mapping container port 5000 to host port 5000)
        ports = {"5000/tcp": 5000}

        # Step 3: Run container with the specified command and port mapping
        container = docker_manager.run_container(
            image=image,
            command=args.command,
            volumes=volumes,
            ports=ports,
            workdir=args.workdir
        )
        
        # Start streaming container logs in real time
        log_thread = threading.Thread(target=stream_logs, args=(container,))
        log_thread.start()

        # Wait for container execution to complete
        exit_status = docker_manager.wait_for_container(container)
        log_thread.join()  # Ensure log streaming is complete

        # Retrieve and save the final logs into the logs directory
        logs_content = docker_manager.get_container_logs(container)
        log_file_path = os.path.join(LOGS_DIR, "execution.log")
        with open(log_file_path, "w") as f:
            f.write(logs_content)

        docker_manager.cleanup_container(container)

        if exit_status.get("StatusCode", 1) == 0:
            logger.info("Code executed successfully.")
        else:
            logger.error("Code execution failed.")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user. Saving logs and cleaning up container.")
        try:
            if container:
                # Get whatever logs are available
                logs_content = docker_manager.get_container_logs(container)
                log_file_path = os.path.join(LOGS_DIR, "execution_interrupt.log")
                with open(log_file_path, "w") as f:
                    f.write(logs_content)
        except Exception as e:
            logger.error(f"Error saving logs on interruption: {str(e)}")
        finally:
            if container:
                try:
                    docker_manager.cleanup_container(container)
                except Exception as e:
                    logger.error(f"Error cleaning up container: {str(e)}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during container execution: {str(e)}")
        if container:
            try:
                docker_manager.cleanup_container(container)
            except Exception as e:
                logger.error(f"Error cleaning up container: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
