#!/bin/bash
# Activate the virtual environment
source venv/bin/activate

echo "Starting the FastAPI application with Uvicorn..."
# Start the application in reload mode for development
uvicorn app.main:app --reload

