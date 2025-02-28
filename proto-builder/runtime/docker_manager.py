import docker
import logging
import os
import sys

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    def build_image(self, path, tag):
        logger.info(f"Building Docker image with tag: {tag} from path: {path}")
        try:
            image, build_logs = self.client.images.build(
                path=path,
                tag=tag,
                dockerfile="Dockerfile",
                rm=True
            )
            # Stream build logs for image building
            for chunk in build_logs:
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

    def run_container(self, image, command, volumes=None, ports=None, workdir="/code", detach=False, labels=None):
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
