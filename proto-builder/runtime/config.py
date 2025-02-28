# config.py

DOCKER_IMAGES = {
    "python": "python:3.9-slim",
    "java": "openjdk:11-jre-slim",
    "node": "node:14-slim",
    "reactpython": "react-python:latest"  # default image for reactpython
}

DEFAULT_LANGUAGE = "reactpython"
EXECUTION_MODE = "local"
LOGS_DIR = "logs"
