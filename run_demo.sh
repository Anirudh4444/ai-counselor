#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Source environment variables
source "$HOME/.zprofile"

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the python script
python "$SCRIPT_DIR/gemini_demo.py"
