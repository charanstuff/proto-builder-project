import docker
import tarfile
import io
import os
import time
import concurrent.futures
import json
import subprocess
from proto_builder.core.default.paths import ENTRYPOINT_FILE

from runtime.logger_config import setup_logger

logger = setup_logger(__name__)


class DockerManager:
    DOCKER_IMAGES = {
        "python": "python:3.9-slim",
        "java": "openjdk:11-jre-slim",
        "node": "node:14-slim",
        "reactpython": "react-python:latest",
        "ubuntu": "ubuntu:20.04"
    }

    def __init__(self):
        self.client = docker.from_env()
        self.containers = []

    def run_container(self, image_key, container_name, command="tail -f /dev/null", volumes=None, ports = {"8080/tcp": 8080}, workdir="/workspace", detach=True, labels=None, tag=None):
        if image_key in self.DOCKER_IMAGES:
            image = self.DOCKER_IMAGES[image_key]
        else:
            image = f"{image_key}:{tag}" if (tag and ":" not in image_key) else image_key

        try:
            self.client.images.pull(image)
        except Exception as e:
            logger.error(f"Failed to pull image {image}: {e}")
            raise

        try:
            container = self.client.containers.run(
                image,
                command,
                name=container_name,
                volumes=volumes,
                ports=ports,
                working_dir=workdir,
                detach=detach,
                labels=labels
            )
            self.containers.append(container)
            time.sleep(1)

            # Install ps
            logger.info(f"Installing ps in container {container_name}")
            exit_code, output = container.exec_run("apt-get update")
            print(f"exit_code: {exit_code}")
            exit_code, output = container.exec_run("apt-get install -y procps curl")
            print(f"exit_code: {exit_code}")
            
            if exit_code != 0:
                error_message = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else str(output)
                logger.error(f"ps installation failed: {error_message}")
                raise Exception(f"ps installation failed: {error_message}")
    
            logger.info(f"ps installed successfully in {container_name}")

            return container
        except Exception as e:
            logger.error(f"Failed to run container {container_name}: {e}")
            raise

    

    def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
        """
        Execute a command inside the container directly, redirecting logs.
        """
        if not command_list:
            return (1, "No command provided")
        script = command_list[0]

        if run_dir:
            print(f"run_dir: {run_dir}")
            full_command = f"bash -c 'cd {run_dir} && mkdir -p {run_dir}/logs && chmod +x {run_dir}/{ENTRYPOINT_FILE} && cd {run_dir} && {script} > {run_dir}/logs/run.log 2> {run_dir}/logs/run.err'"
        else:
            full_command = f"bash -c 'mkdir -p logs && chmod +x {ENTRYPOINT_FILE} && {script} > logs/run.log 2> logs/run.err'"

        logger.info(f"Executing command: {full_command}")

        def _exec_direct():
            return container.exec_run(full_command, detach=True)

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_exec_direct)
                exec_result = future.result(timeout=timeout * 60)
        except Exception as e:
            raise Exception(f"Error executing command: {e}")

    # def get_execution_status(self, container):
    #     """
    #     Get the execution status by checking the process list using 'ps'.
    #     """
    #     try:
    #         exit_code, output = container.exec_run("ps")
    #         print(f"exit_code: {exit_code}")
    #         print(f"output: {output}")
    #         if exit_code == 0:
    #             process_list = output.decode("utf-8", errors="replace").splitlines()
    #             # Remove the grep command itself from the process list
    #             process_list = [proc for proc in process_list if "grep npm run serve" not in proc]
    #             if process_list:
    #                 # Check if the server is responsive
    #                 check_code, _ = container.exec_run("curl -sSf http://localhost:8080")
    #                 return 0 if check_code == 0 else None
    #             else:
    #                 return 1 # process not found
    #         else:
    #             logger.error(f"ps command failed: {output}")
    #             return None
    #     except Exception as e:
    #         logger.error(f"Error getting execution status: {e}")
    #         return None

    def execute_local(self, cmd):
        stdout = ""
        stderr = ""
        return_code = 1
        try:
            print(f"Executing command: {' '.join(cmd)}")
            popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = popen.communicate()
            return_code = popen.returncode
            return (return_code, stdout, stderr)
        except Exception as e:
            print(f"Command failed with exception: {e} status: {return_code} stdout: {stdout} stderr: {stderr} ")
            return (1, str(e))

    def get_execution_status(self, container, retries=5, delay=20):
        container_id = container.id
        for attempt in range(retries):
            # Split the command into a list of arguments
            status, stdout, stderr = self.execute_local(["docker", "exec", container_id, "bash", "-c", "'curl -sSf http://localhost:8080'"])
            if status == 0:
                return 0
            time.sleep(delay)
        return 1

    def get_log(self, container, run_dir="/workspace", lines=100):
        exit_code, output = container.exec_run(f"tail -n {lines} /{run_dir}/logs/run.log")
        if exit_code == 0:
            return output.decode("utf-8", errors="replace")
        return f"Error retrieving logs: {output[1].decode()}"

    def copy_code_to_container(self, container, src_path, dest_path):
        """
        Copy the contents of a directory from local src_path into the container at dest_path.
        Instead of copying the entire folder, it copies each item within the folder.
        """
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source path {src_path} does not exist.")

        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Iterate over the contents of src_path and add them individually.
            for item in os.listdir(src_path):
                full_path = os.path.join(src_path, item)
                tar.add(full_path, arcname=item)
        tar_stream.seek(0)
        success = container.put_archive(dest_path, tar_stream.read())
        if not success:
            raise Exception("Failed to copy files to container.")

    def stop_all_containers(self):
        """Stop and remove all containers that were started by this manager."""
        for container in self.containers[:]:
            self.stop_container(container)
        self.containers = []

    def stop_container(self, container):
        """Stop and remove the specified container."""
        try:
            container.stop()
            container.remove()
            # Remove from our list if present.
            if container in self.containers:
                self.containers.remove(container)
        except Exception as e:
            print(f"Error stopping container: {e}")

    def get_containers(self, image_key):
        """
        Return the list of running containers that match the image_key.
        The image_key is looked up in DOCKER_IMAGES first.
        Returns a list of containers or None if none found.
        """
        target_image = self.DOCKER_IMAGES.get(image_key, image_key)
        matching = []
        for container in self.client.containers.list():
            # container.image.tags is a list; check if any tag matches the target image.
            if container.image.tags and any(target_image in tag for tag in container.image.tags):
                matching.append(container)
        return matching if matching else None

def test_success():
    dm = DockerManager()
    container = None
    try:
        container = dm.run_container(
            image_key="node:14",
            container_name="test_success_container",
            command="tail -f /dev/null"
        )
        src_repo = "/tmp/test/helloworld_vue_success"
        dest_dir = "/workspace"
        dm.copy_code_to_container(container, src_repo, dest_dir)

        # Create run.sh in container
        run_sh_content = """#!/bin/bash
        npm install
        npm run serve
        """
        container.exec_run(f"bash -c 'echo \"{run_sh_content}\" > /workspace/run.sh'")
        container.exec_run("chmod +x /workspace/run.sh")

        command_list = ["run.sh"]
        dm.execute(container, command_list, run_dir="/workspace", timeout=5)
        print("Success test finished")

        # Wait for status
        time.sleep(30)
        status = dm.get_execution_status(container)
        print("Final Status:", status)
        num_lines = 100
        print(f"\n\nLast {num_lines} lines of stdout Logs:\n", dm.get_log(container, num_lines))
    finally:
        if container:
            print("Stopping container...")
            dm.stop_container(container)
            print("Done")

def test_failure():
    dm = DockerManager()
    container = None
    try:
        container = dm.run_container(
            image_key="node:14",
 container_name="test_failure_container",
            command="tail -f /dev/null"
        )
        src_repo = "/tmp/test/helloworld_vue_failure"
        dest_dir = "/workspace"
        dm.copy_code_to_container(container, src_repo, dest_dir)

        run_sh_content = """#!/bin/bash
        cd helloworld_vue_failure
        npm install
        npm run serve
        """
        container.exec_run(f"bash -c 'echo \"{run_sh_content}\" > /workspace/run.sh'")
        container.exec_run("chmod +x /workspace/run.sh")

        command_list = ["bash run.sh"]
        dm.execute(container, command_list, run_dir="/workspace", timeout=5)
        print("Failure test finished")

        time.sleep(10)  # Allow time for failure
        #print("Final Status:", dm.get_execution_status(container))
        num_lines = 100
        print(f"\n\nLast {num_lines} lines of stdout Logs:\n", dm.get_log(container, num_lines))
    finally:
        if container:
            print("Stopping container...")
            dm.stop_container(container)
            print("Done")

if __name__ == "__main__":
    print("Running test for success scenario...")
    test_success()
    #print("\nRunning test for failure scenario...")
    #test_failure()
