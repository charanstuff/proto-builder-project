#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "=== Setting up env for proto_builder ==="

# 1. Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv proto_builder_venv
else
    echo "Virtual environment already exists."
fi

# 2. Activate the virtual environment
echo "Activating virtual environment..."
source proto_builder_venv/bin/activate

# 3. Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies from requirements.txt
echo "Installing Python dependencies..."
pip install -r requirements.txt


echo "=== Setup complete! ==="
echo "Activate your virtual environment with: source proto_builder_venv/bin/activate"
