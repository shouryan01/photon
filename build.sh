#!/bin/bash

# Define virtual environment directory
VENV_DIR="venv_build"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Using Python: $(python --version)"

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run PyInstaller
echo "Building executable..."
python -m PyInstaller Photon.spec --clean --noconfirm

# Deactivate virtual environment
deactivate

echo "Build complete. You can find Photon.app in the dist/ folder."

