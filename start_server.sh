#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Source environment variables
source "$HOME/.zprofile"

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the FastAPI server
python "$SCRIPT_DIR/app.py"
