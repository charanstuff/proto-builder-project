# main.py

import argparse
from docker_execution_env import DockerExecutionEnv
from docker_manager import DockerManager
from config import DOCKER_IMAGES, DEFAULT_IMAGE_KEY

def main():
    parser = argparse.ArgumentParser(description="Runtime Environment Interface")
    parser.add_argument("--language", type=str, default=DEFAULT_IMAGE_KEY, help=f"Programming language (default: {DEFAULT_IMAGE_KEY})")
    parser.add_argument("--source", type=str, required=True, help="Source of the code (git URL or local directory)")
    parser.add_argument("--command", type=str, required=True, help="Command to run inside the container")
    parser.add_argument("--workdir", type=str, default="/workspace", help="Working directory inside container")
    parser.add_argument("--dest", type=str, default="code_dir", help="Destination directory for code")
    parser.add_argument("--mode", type=str, default="local", help="Execution mode")
    
    args = parser.parse_args()
    
    # Get the appropriate Docker image based on language
    image = DOCKER_IMAGES.get(args.language.lower(), DOCKER_IMAGES[DEFAULT_IMAGE_KEY])
    
    # Initialize Docker manager
    docker_manager = DockerManager()
    
    # Initialize the Docker execution environment
    env = DockerExecutionEnv(
        image=image,
        docker_manager=docker_manager,
        path=args.dest
    )
    
    # Run the command and get the results
    stdout, stderr, exit_code = env.run(args.command)
    
    # Print the results
    if stdout:
        print("Output:", stdout)
    if stderr:
        print("Errors:", stderr)
    return exit_code

if __name__ == "__main__":
    main()
