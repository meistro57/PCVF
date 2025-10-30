#!/bin/bash

# Install script for Podcast Video Factory
# This script sets up a virtual environment and installs required dependencies

set -e

echo "Checking Python version..."
python3 --version

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Verifying installation..."
python -c "import faster_whisper, requests, websocket, openai, pysrt; print('All required packages installed successfully!')"

echo "Installation complete. To activate the virtual environment in the future, run: source venv/bin/activate"