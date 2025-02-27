# docker_manager.py

import docker
import logging
import os

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    def pull_image(self, image):
        logger.info(f"Checking for Docker image: {image}")
        try:
            # Try to get the image locally
            self.client.images.get(image)
            logger.info(f"Image {image} found locally. Skipping pull.")
        except docker.errors.ImageNotFound:
            logger.info(f"Image {image} not found locally. Pulling from repository.")
            try:
                self.client.images.pull(image)
                logger.info(f"Image {image} pulled successfully.")
            except Exception as e:
                logger.error(f"Error pulling image {image}: {str(e)}")
                raise

    def run_container(self, image, command, volumes=None, ports=None, workdir="/code", detach=False):
        """
        Runs a Docker container.
        
        Parameters:
          image: Docker image to use.
          command: Command to run inside the container.
          volumes: A dict mapping host directories to container directories.
          workdir: The working directory inside the container.
          detach: Whether to run in detached mode (default is False for our run-and-capture pattern).
        """
        if isinstance(command, str):
            command = ["sh", "-c", command]
            logger.debug(f"Wrapped command for shell execution: {command}")
        try:
            container = self.client.containers.run(
                image,
                command=command,
                volumes=volumes,
                ports=ports,         # Pass the port mapping here
                working_dir=workdir,
                detach=True,
                tty=True  # Allocate a pseudo-TTY
            )
            logger.info(f"Container {container.id} started.")
            return container
        except Exception as e:
            logger.error(f"Error running container: {str(e)}")
            raise

    def wait_for_container(self, container):
        logger.info(f"Waiting for container {container.id} to finish.")
        try:
            exit_status = container.wait()  # Returns a dict like {"StatusCode": 0}
            logger.info(f"Container {container.id} finished with status: {exit_status}")
            return exit_status
        except Exception as e:
            logger.error(f"Error waiting for container: {str(e)}")
            raise

    def get_container_logs(self, container):
        logger.info(f"Fetching logs for container {container.id}")
        try:
            logs = container.logs(stream=False).decode("utf-8")
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            raise

    def cleanup_container(self, container):
        logger.info(f"Cleaning up container {container.id}")
        try:
            container.remove(force=True)
            logger.info(f"Container {container.id} removed.")
        except Exception as e:
            logger.error(f"Error removing container: {str(e)}")
