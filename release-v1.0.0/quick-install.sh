#!/bin/bash
# Quick installation script for Tmux Orchestrator

echo "Installing Tmux Orchestrator..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x create_ai_team.py
chmod +x send-claude-message.sh
chmod +x install.sh

echo "Installation complete!"
echo "Run: python3 create_ai_team.py --help"
