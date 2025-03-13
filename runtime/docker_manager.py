# import docker
# import tarfile
# import io
# import os
# import time
# import concurrent.futures
# import threading
# import sys

# from runtime.logger_config import setup_logger

# logger = setup_logger(__name__)


# class DockerManager:
#     # A mapping of keys to Docker image names.
#     DOCKER_IMAGES = {
#         "python": "python:3.9-slim",
#         "java": "openjdk:11-jre-slim",
#         "node": "node:14-slim",
#         "reactpython": "react-python:latest",  # default image for reactpython
#         "ubuntu": "ubuntu:20.04"
#     }
#     def __init__(self):
#         print("Initializing DockerManager")
#         self.client = docker.from_env()
#         self.containers = []  # Track containers started by DockerManager

#     def run_container(self, image_key, container_name, command="tail -f /dev/null", volumes=None, ports=None, workdir="/workspace", detach=True, labels=None, tag=None):
#         """
#         Run a docker container indefinitely.
#         - image_key: key to DOCKER_IMAGES or an image name.
#         - If tag is provided and image_key is not in DOCKER_IMAGES, then image becomes image_key:tag.
#         Returns the container object.
#         """
#         # Determine the image to use.
#         if image_key in self.DOCKER_IMAGES:
#             image = self.DOCKER_IMAGES[image_key]
#         else:
#             # If image_key already contains a colon (e.g., ubuntu:20.04), use as is.
#             if ":" not in image_key and tag is not None:
#                 image = f"{image_key}:{tag}"
#             else:
#                 image = image_key

#         # Pull the image to be sure it is available.
#         try:
#             self.client.images.pull(image)
#         except Exception as e:
#             print(f"Failed to pull image {image}: {e}")
#             raise

#         try:
#             container = self.client.containers.run(
#                 image,
#                 command,
#                 name=container_name,
#                 volumes=volumes,
#                 ports=ports,
#                 working_dir=workdir,
#                 detach=detach,
#                 labels=labels
#             )
#             self.containers.append(container)
#             # Give container a moment to start
#             time.sleep(1)
#             return container
#         except Exception as e:
#             print(f"Failed to run container {container_name}: {e}")
#             raise

#     def stop_container(self, container):
#         """Stop and remove the specified container."""
#         try:
#             container.stop()
#             container.remove()
#             # Remove from our list if present.
#             if container in self.containers:
#                 self.containers.remove(container)
#         except Exception as e:
#             print(f"Error stopping container: {e}")

#     def get_containers(self, image_key):
#         """
#         Return the list of running containers that match the image_key.
#         The image_key is looked up in DOCKER_IMAGES first.
#         Returns a list of containers or None if none found.
#         """
#         target_image = self.DOCKER_IMAGES.get(image_key, image_key)
#         matching = []
#         for container in self.client.containers.list():
#             # container.image.tags is a list; check if any tag matches the target image.
#             if container.image.tags and any(target_image in tag for tag in container.image.tags):
#                 matching.append(container)
#         return matching if matching else None

#     # def copy_code_to_container(self, container, src_path, dest_path="/workspace"):
#     #     """
#     #     Copy a directory from local src_path into the container at dest_path.
#     #     This is done by tarring the source directory and using put_archive.
#     #     """
#     #     # todo: check if container is running
#     #     # # check if container is running
#     #     # if not container.status == "running":
#     #     #     raise Exception("Container is not running.")

#     #     if not os.path.exists(src_path):
#     #         raise FileNotFoundError(f"Source path {src_path} does not exist.")

#     #     # Create a tar archive of the directory in memory.
#     #     tar_stream = io.BytesIO()
#     #     with tarfile.open(fileobj=tar_stream, mode='w') as tar:
#     #         # arcname ensures that the files are placed directly into dest_path
#     #         tar.add(src_path, arcname=os.path.basename(src_path))
#     #     tar_stream.seek(0)
#     #     # Put the archive into the container. Note: dest_path must exist in the container.
#     #     success = container.put_archive(dest_path, tar_stream.read())
#     #     if not success:
#     #         raise Exception("Failed to copy files to container.")

#     def copy_code_to_container(self, container, src_path, dest_path):
#         """
#         Copy the contents of a directory from local src_path into the container at dest_path.
#         Instead of copying the entire folder, it copies each item within the folder.
#         """
#         if not os.path.exists(src_path):
#             raise FileNotFoundError(f"Source path {src_path} does not exist.")

#         tar_stream = io.BytesIO()
#         with tarfile.open(fileobj=tar_stream, mode='w') as tar:
#             # Iterate over the contents of src_path and add them individually.
#             for item in os.listdir(src_path):
#                 full_path = os.path.join(src_path, item)
#                 tar.add(full_path, arcname=item)
#         tar_stream.seek(0)
#         success = container.put_archive(dest_path, tar_stream.read())
#         if not success:
#             raise Exception("Failed to copy files to container.")

#     # def execute(self, container, command_list, timeout=3, log_lines=20, port_mapping=None):
#     #     """
#     #     Execute a list of commands inside the container sequentially.
#     #     timeout: per command timeout in minutes (default 3 minutes).
#     #     Returns a tuple (status, error_logs) where:
#     #       - status 0: success.
#     #       - status 1: failure (non-zero exit code) with error_logs.
#     #       - status 2: timeout.
#     #     If all commands succeed, container logs are written to a file and the last 'log_lines'
#     #     lines are returned.
#     #     The port_mapping parameter is accepted but not used since ports are usually bound at container run.
#     #     """
#     #     total_timeout = timeout * 60  # convert minutes to seconds

#     #     def _exec_command(cmd):
#     #         # Execute a single command in the container.
#     #         # Using demux=True to get (stdout, stderr) separately.
#     #         exec_result = container.exec_run(cmd, demux=True)
#     #         # exec_run returns a tuple (exit_code, (stdout, stderr))
#     #         return exec_result.exit_code, exec_result.output

#     #     with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
#     #         for cmd in command_list:
#     #             future = executor.submit(_exec_command, cmd)
#     #             try:
#     #                 exit_code, output = future.result(timeout=total_timeout)
#     #             except concurrent.futures.TimeoutError:
#     #                 return (2, f"Timeout executing command: {cmd}")

#     #             # If command failed, process error logs.
#     #             if exit_code != 0:
#     #                 stderr = ""
#     #                 if output is not None and isinstance(output, tuple) and output[1]:
#     #                     stderr = output[1].decode("utf-8", errors="replace")
#     #                 # Get the last log_lines lines from stderr.
#     #                 error_log_lines = stderr.splitlines()[-log_lines:]
#     #                 return (1, "\n".join(error_log_lines))

#     #     # If all commands succeeded, fetch container logs.
#     #     try:
#     #         logs = container.logs().decode("utf-8", errors="replace")
#     #         # Write full logs to a file.
#     #         with open("execution_logs.txt", "w") as f:
#     #             f.write(logs)
#     #         # Get the last log_lines from the logs.
#     #         log_lines_content = "\n".join(logs.splitlines()[-log_lines:])
#     #         return (0, log_lines_content)
#     #     except Exception as e:
#     #         return (1, f"Failed to retrieve logs: {e}")

#     def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
#         """
#         Execute a list of commands inside the container sequentially.
#         - run_dir: if provided, the commands will be executed in this directory.
#         - timeout: per command timeout in minutes (default 3 minutes).
#         Returns a tuple (status, error_logs) where:
#           - status 0: success.
#           - status 1: failure (non-zero exit code) with error_logs.
#           - status 2: timeout.
#         If all commands succeed, container logs are written to a file and the last 'log_lines'
#         lines are returned.
#         """
#         total_timeout = timeout * 60  # Convert minutes to seconds

#         def _exec_command(cmd):
#             # If run_dir is provided, prefix the command with cd
#             if run_dir:
#                 cmd = f"bash -c 'cd {run_dir} && {cmd}'"
#             return container.exec_run(cmd, demux=True)

#         logger.info(f"Executing commands: {command_list}")
#         with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
#             for cmd in command_list:
#                 logger.info(f"Executing command: {cmd} in {run_dir}")
#                 future = executor.submit(_exec_command, cmd)
#                 try:
#                     exec_result = future.result(timeout=total_timeout)
#                     exit_code = exec_result.exit_code
#                     output = exec_result.output
#                 except concurrent.futures.TimeoutError:
#                     return (2, f"Timeout executing command: {cmd}")

#                 if exit_code != 0:
#                     stderr = ""
#                     if output is not None and isinstance(output, tuple) and output[1]:
#                         stderr = output[1].decode("utf-8", errors="replace")
#                     error_log_lines = stderr.splitlines()[-log_lines:]
#                     return (1, "\n".join(error_log_lines))

#         try:
#             logs = container.logs().decode("utf-8", errors="replace")
#             with open("execution_logs.txt", "w") as f:
#                 f.write(logs)
#             log_lines_content = "\n".join(logs.splitlines()[-log_lines:])
#             return (0, log_lines_content)
#         except Exception as e:
#             return (1, f"Failed to retrieve logs: {e}")

#     # def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
#     #     """
#     #     Execute a list of commands inside the container in a detached way.
#     #     The commands are run sequentially in a separate daemon thread.
        
#     #     As the command(s) produce output, the logs are streamed live both to stdout 
#     #     (i.e. where this DockerManager code is running) and to a log file at:
#     #          run_dir/logs/execute.log
#     #     (if run_dir is provided).
        
#     #     This prevents the execute function from hanging when running long-lived processes
#     #     (e.g., 'npm run serve').
        
#     #     Returns (0, "Detached execution started") immediately.
#     #     """
#     #     def _run_commands():
#     #         # If a run_dir is provided, ensure that the logs directory exists on the host.
#     #         log_file_path = None
#     #         if run_dir:
#     #             logs_dir = os.path.join(run_dir, "logs")
#     #             os.makedirs(logs_dir, exist_ok=True)
#     #             log_file_path = os.path.join(logs_dir, "execute.log")
#     #         for cmd in command_list:
#     #             logger.info(f"Executing command: {cmd} in {run_dir}. Log file: {log_file_path}" )
#     #             # If run_dir is provided, change directory in the container before running the command.
#     #             if run_dir:
#     #                 full_cmd = f"bash -c 'cd {run_dir} && {cmd}'"
#     #             else:
#     #                 full_cmd = cmd
#     #             try:
#     #                 # Use stream=True and demux=True to get output as it is produced.
#     #                 stream = container.exec_run(full_cmd, stream=True, demux=True)
#     #                 for chunk in stream:
#     #                     # Each chunk is a tuple (stdout, stderr); decode and combine them.
#     #                     output = ""
#     #                     if chunk[0]:
#     #                         output += chunk[0].decode("utf-8", errors="replace")
#     #                     if chunk[1]:
#     #                         output += chunk[1].decode("utf-8", errors="replace")
#     #                     logger.info(f"Output: {output}")
#     #                     # Append output to the log file.
#     #                     if log_file_path:
#     #                         with open(log_file_path, "a") as lf:
#     #                             lf.write(output)
#     #                     # Also print output to the console.
#     #                     sys.stdout.write(output)
#     #                     sys.stdout.flush()
#     #             except Exception as e:
#     #                 error_msg = f"Exception while executing command '{cmd}': {e}\n"
#     #                 if log_file_path:
#     #                     with open(log_file_path, "a") as lf:
#     #                         lf.write(error_msg)
#     #                 sys.stdout.write(error_msg)
#     #                 sys.stdout.flush()
#     #                 break  # Stop execution if a command fails.

#     #     # Start the execution in a detached (daemon) thread.
#     #     thread = threading.Thread(target=_run_commands, daemon=True)
#     #     thread.start()

#     #     return (0, "Detached execution started")

#     # def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
#     #     """
#     #     Execute a list of commands inside the container in a detached way.
        
#     #     If run_dir is provided, the commands are modified to:
#     #       - Create a logs directory inside run_dir on the container,
#     #       - Change directory into run_dir,
#     #       - Execute the command while piping its output through tee to write
#     #         all output to {run_dir}/logs/execute.log.
        
#     #     The output is streamed live from the container back to stdout on your localhost.
#     #     This function starts a separate daemon thread so that long-running commands
#     #     (e.g. "npm run serve") do not block execution.
        
#     #     Returns immediately with (0, "Detached execution started").
#     #     """
#     #     def _run_commands():
#     #         for cmd in command_list:
#     #             if run_dir:
#     #                 # Wrap the command to create logs folder, change directory, and pipe output to tee.
#     #                 full_cmd = f"bash -c 'mkdir -p {run_dir}/logs && cd {run_dir} && {cmd} | tee {run_dir}/logs/execute.log'"
#     #             else:
#     #                 full_cmd = cmd
#     #             try:
#     #                 # Start the command execution with streaming output.
#     #                 stream = container.exec_run(full_cmd, stream=True, demux=True)
#     #                 for chunk in stream:
#     #                     output = ""
#     #                     if chunk[0]:
#     #                         output += chunk[0].decode("utf-8", errors="replace")
#     #                     if chunk[1]:
#     #                         output += chunk[1].decode("utf-8", errors="replace")
#     #                     sys.stdout.write(output)
#     #                     sys.stdout.flush()
#     #             except Exception as e:
#     #                 error_msg = f"Exception while executing command '{cmd}': {e}\n"
#     #                 sys.stdout.write(error_msg)
#     #                 sys.stdout.flush()
#     #                 break

#     #     # Start detached execution in a daemon thread.
#     #     thread = threading.Thread(target=_run_commands, daemon=True)
#     #     thread.start()
#     #     return (0, "Detached execution started")

#     def stop_all_containers(self):
#         """Stop and remove all containers that were started by this manager."""
#         for container in self.containers[:]:
#             self.stop_container(container)
#         self.containers = []


# # -------------------- Tests --------------------

# def test_success():
#     """
#     Test 1: Run a Node.js container, copy the helloworld_vue_success project,
#     install dependencies, build the project with webpack, and record success.
#     """
#     dm = DockerManager()
#     container = None
#     try:
#         # Use the Node image so that npm and node are available.
#         container = dm.run_container(
#             image_key="node:14",
#             container_name="test_success_container",
#             command="tail -f /dev/null"
#         )
#         # Copy the helloworld_vue_success project into /workspace inside the container.
#         src_repo = "/tmp/test/helloworld_vue_success"
#         dest_dir = "/workspace"
#         dm.copy_code_to_container(container, src_repo, dest_dir)

#         # Execute commands: install npm dependencies and build using webpack.
#         command_list = [
#             "bash -c 'cd /workspace/helloworld_vue_success && npm install && npx webpack --config webpack.config.js'"
#         ]
#         status, logs = dm.execute(container, command_list, timeout=5)
#         print("Test Success:")
#         print("Status:", status)
#         print("Logs:")
#         print(logs)
#     except Exception as e:
#         print("Test Success encountered an exception:", e)
#     finally:
#         if container:
#             dm.stop_container(container)

# def test_failure():
#     """
#     Test 2: Run a Node.js container, copy the helloworld_vue_failure project,
#     install dependencies, attempt to build using webpack (which should fail),
#     and record the error logs.
#     """
#     dm = DockerManager()
#     container = None
#     try:
#         container = dm.run_container(
#             image_key="node:14",
#             container_name="test_failure_container",
#             command="tail -f /dev/null"
#         )
#         # Copy the helloworld_vue_failure project into /workspace inside the container.
#         src_repo = "/tmp/test/helloworld_vue_failure"
#         dest_dir = "/workspace"
#         dm.copy_code_to_container(container, src_repo, dest_dir)

#         # Execute commands: install npm dependencies and attempt to build.
#         # The failure project is designed with an intentional error in the template.
#         command_list = [
#             "bash -c 'cd /workspace/helloworld_vue_failure && npm install && npx webpack --config webpack.config.js'"
#         ]
#         status, logs = dm.execute(container, command_list, timeout=5)
#         print("Test Failure:")
#         print("Status:", status)
#         print("Logs:")
#         print(logs)
#     except Exception as e:
#         print("Test Failure encountered an exception:", e)
#     finally:
#         if container:
#             dm.stop_container(container)


# if __name__ == "__main__":
#     print("Running test for success scenario...")
#     test_success()
#     print("\nRunning test for failure scenario...")
#     test_failure()


# ----------- New Docker Manager ------------

import docker
import tarfile
import io
import os
import time
import concurrent.futures
import json
#from runtime.logger_config import setup_logger
import logging
import subprocess

logger = logging.getLogger(__name__)

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

    def run_container(self, image_key, container_name, command="tail -f /dev/null", volumes=None, ports=None, workdir="/workspace", detach=True, labels=None, tag=None):
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
            exit_code, output = container.exec_run("apt-get install -y procps")
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

    # def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
    #     total_timeout = timeout * 60
    #     command_str = " && ".join(command_list)
    #     # Wrap command in quotes and use -x for executable
    #     pm2_command = (
    #         f'pm2 start --name vue-app --output /workspace/logs/run.log '
    #         f'--error /workspace/logs/run.err -x -- "{command_str}"'
    #     )
    #     if run_dir:
    #         pm2_command = f"bash -c 'cd {run_dir} && {pm2_command}'"

    #     logger.info(f"Executing PM2 command: {pm2_command}")

    #     def _exec_pm2():
    #         return container.exec_run(pm2_command, demux=True, environment={"PM2_HOME": "/tmp/pm2"})

    #     try:
    #         with concurrent.futures.ThreadPoolExecutor() as executor:
    #             future = executor.submit(_exec_pm2)
    #             exec_result = future.result(timeout=total_timeout)
    #             exit_code = exec_result.exit_code
    #             output = exec_result.output

    #             if exit_code != 0:
    #                 stderr = output[1].decode("utf-8", errors="replace") if output[1] else ""
    #                 return (1, stderr)
    #             return (0, "PM2 process started successfully")
    #     except concurrent.futures.TimeoutError:
    #         return (2, "Timeout starting PM2 process")
    #     except Exception as e:
    #         return (1, str(e))

    # def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
    #     """
    #     Execute a command inside the container via PM2 in a detached way.
        
    #     This version assumes that command_list contains one command—the script to run
    #     (e.g. "run.sh"). It changes into run_dir (if provided) and then tells PM2 to start
    #     that script. PM2 will stream the logs into {run_dir}/logs/run.log inside the container.
        
    #     Returns (0, "PM2 process started successfully") if PM2 starts the process.
    #     """
    #     # For now, assume only one command is provided, which is the script filename.
    #     if not command_list:
    #         return (1, "No command provided")
    #     script = command_list[0]

    #     if run_dir:
    #         pm2_command = (
    #             f"bash -c 'cd {run_dir} && mkdir -p logs && "
    #             f"pm2 start {script} --name vue-app --output {run_dir}/logs/run.log "
    #             f"--error {run_dir}/logs/run.err -x'"
    #         )
    #     else:
    #         pm2_command = f"pm2 start {script} --name vue-app --output logs/run.log --error logs/run.err -x"

    #     logger.info(f"Executing PM2 command: {pm2_command}")

    #     def _exec_pm2():
    #         return container.exec_run(pm2_command, demux=True, environment={"PM2_HOME": "/tmp/pm2"})

    #     try:
    #         with concurrent.futures.ThreadPoolExecutor() as executor:
    #             future = executor.submit(_exec_pm2)
    #             exec_result = future.result(timeout=timeout * 60)
    #             exit_code = exec_result.exit_code
    #             output = exec_result.output

    #             if exit_code != 0:
    #                 stderr = (
    #                     output[1].decode("utf-8", errors="replace") if output[1] else ""
    #                 )
    #                 return (1, stderr)
    #             return (0, "PM2 process started successfully")
    #     except concurrent.futures.TimeoutError:
    #         return (2, "Timeout starting PM2 process")
    #     except Exception as e:
    #         return (1, str(e))

    def execute(self, container, command_list, run_dir=None, timeout=3, log_lines=20, port_mapping=None):
        """
        Execute a command inside the container directly, redirecting logs.
        """
        if not command_list:
            return (1, "No command provided")
        script = command_list[0]

        if run_dir:
            print(f"run_dir: {run_dir}")
            full_command = f"bash -c 'cd {run_dir} && mkdir -p {run_dir}/logs && chmod +x {run_dir}/{script} && {run_dir}/{script} > {run_dir}/logs/run.log 2> {run_dir}/logs/run.err'"
        else:
            full_command = f"bash -c 'mkdir -p logs && chmod +x {script} && {script} > logs/run.log 2> logs/run.err'"

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

    def get_execution_status(self, container, retries=3, delay=5):
        container_id = container.id
        for attempt in range(retries):
            # Split the command into a list of arguments
            status, stdout, stderr = self.execute_local(["docker", "exec", container_id, "bash", "-c", "curl -sSf http://localhost:8080"])
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
