#!/bin/bash
set -e

# Determine OS type
OS_TYPE=$(uname)
echo "Detected OS: $OS_TYPE"

# Install and start required services based on OS
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "Running on macOS..."
    # Check for Homebrew
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew not found. Please install Homebrew (https://brew.sh) and try again."
        exit 1
    fi

    # Install MySQL and Redis if they are not already installed
    if ! brew ls --versions mysql >/dev/null; then
        echo "Installing MySQL..."
        brew install mysql
    fi
    if ! brew ls --versions redis >/dev/null; then
        echo "Installing Redis..."
        brew install redis
    fi

    echo "Starting MySQL and Redis services..."
    brew services start mysql
    brew services start redis

elif [[ "$OS_TYPE" == "Linux" ]]; then
    echo "Running on Linux..."
    # Update package lists
    sudo apt-get update

    # Install MySQL and Redis if not installed (assumes apt-get is available)
    if ! dpkg -l | grep -q mysql-server; then
        echo "Installing MySQL server..."
        sudo apt-get install -y mysql-server
    fi
    if ! dpkg -l | grep -q redis-server; then
        echo "Installing Redis server..."
        sudo apt-get install -y redis-server
    fi

    echo "Starting MySQL and Redis services..."
    sudo service mysql start
    sudo service redis-server start

else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

# Give a short pause to ensure services are up
echo "Waiting for services to start..."
sleep 5

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A celery_app.celery worker --loglevel=info &
CELERY_PID=$!

# Optionally, wait a few seconds for the worker to initialize
sleep 5

# Start FastAPI application using your run.sh script
echo "Starting FastAPI application..."
./run.sh

# (Optional) When you want to shut everything down, you can kill the Celery worker:
# kill $CELERY_PID

