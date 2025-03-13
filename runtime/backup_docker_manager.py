import docker
import os
import sys
from typing import Tuple, Union
from runtime.logger_config import setup_logger
from runtime.config import DOCKER_IMAGES, DEFAULT_IMAGE_KEY, EXECUTION_MODE, LOGS_DIR

logger = setup_logger(__name__)

class DockerManager:
    def __init__(self, image_key: str = DEFAULT_IMAGE_KEY):
        logger.info("Initializing DockerManager")
        self.client = docker.from_env()
        logger.info(f"Docker client: {self.client}")
        self.image_key = image_key

    def build_image(self, path, tag):
        logger.info(f"Building Docker image with tag: {tag} from path: {path}")
        try:
            image, build_logs = self.client.images.build(
                path=path,
                tag=tag,
                dockerfile="Dockerfile",
                rm=True
            )
            logger.info("Build call returned, processing build logs.")
            # Stream build logs for image building
            for chunk in build_logs:
                logger.info("chunk: %s", chunk)
                if 'stream' in chunk:
                    for line in chunk['stream'].splitlines():
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()
                        logger.info(line)
            logger.info(f"Image {tag} built successfully.")
            return image
        except Exception as e:
            logger.error(f"Error building image: {e}")
            raise

    
    
    def get_image(self) -> Union[str, Tuple[str, str, int]]:
        """Prepares the Docker image by either building or pulling it."""
        image = DOCKER_IMAGES.get(self.image_key, DOCKER_IMAGES[DEFAULT_IMAGE_KEY])
        logger.debug("Using image: %s for language: %s", image, self.image_key)

        if self.image_key == "reactpython":
            logger.info("Building react-python image as part of execution.")
            dockerfile_context = os.path.dirname(os.path.abspath(__file__))
            logger.debug("Docker build context: %s", dockerfile_context)
            self.build_image(dockerfile_context, tag=image)
        else:
            self.pull_image(image)
        return image

    def pull_image(self, image):
        logger.info(f"Checking for Docker image: {image}")
        try:
            self.client.images.get(image)
            logger.info(f"Image {image} found locally. Skipping pull.")
        except docker.errors.ImageNotFound:
            logger.info(f"Image {image} not found locally. Pulling from repository.")
            try:
                self.client.images.pull(image)
                logger.info(f"Image {image} pulled successfully.")
            except Exception as e:
                logger.error(f"Error pulling image {image}: {e}")
                raise

    def run_container(self, image, command, volumes=None, ports=None, workdir="/workspace", detach=False, labels=None):
        logger.info(f"Running container with image {image} and command: {command}")
        if isinstance(command, str):
            command = ["sh", "-c", command]
            logger.debug(f"Wrapped command for shell execution: {command}")
        try:
            container = self.client.containers.run(
                image,
                command=command,
                volumes=volumes,
                ports=ports,
                working_dir=workdir,
                detach=True,
                tty=False,
                labels=labels
            )
            logger.info(f"Container {container.id} started.")
            return container
        except Exception as e:
            logger.error(f"Error running container: {e}")
            raise

    def wait_for_container(self, container):
        logger.info(f"Waiting for container {container.id} to finish.")
        try:
            exit_status = container.wait()  # Returns dict, e.g. {"StatusCode": 0}
            logger.info(f"Container {container.id} finished with status: {exit_status}")
            return exit_status
        except Exception as e:
            logger.error(f"Error waiting for container: {e}")
            raise

    def get_container_logs(self, container):
        logger.info(f"Fetching logs for container {container.id}")
        try:
            logs = container.logs(stream=False).decode("utf-8", errors="replace")
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            raise

    def cleanup_container(self, container):
        logger.info(f"Cleaning up container {container.id}")
        try:
            container.remove(force=True)
            logger.info(f"Container {container.id} removed.")
        except Exception as e:
            logger.error(f"Error removing container: {e}")

    def copy_to_container(self, container, path: str, data: bytes) -> bool:
        """
        Copy data into a container at specified path.
        
        Args:
            container: Docker container object
            path: Destination path in container
            data: Tar archive as bytes to copy into container
            
        Returns:
            bool: True if copy successful, False otherwise
        """
        try:
            container.put_archive(path, data)
            return True
        except Exception as e:
            logger.error("Failed to copy to container: %s", e)
            return False
