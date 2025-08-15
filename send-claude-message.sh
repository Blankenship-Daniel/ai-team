#!/bin/bash

# Send message to Claude agent in tmux window/pane
# Usage: send-claude-message.sh <session:window> <message>
# Note: Includes 1-second delay to ensure prompt is fully typed before submission

if [ $# -lt 2 ]; then
    echo "Usage: $0 <session:window> <message>"
    echo "Example: $0 agentic-seek:3 'Hello Claude!'"
    exit 1
fi

WINDOW="$1"
shift  # Remove first argument, rest is the message
MESSAGE="$*"

# Send the message
tmux send-keys -t "$WINDOW" "$MESSAGE"

# Wait 1 second for prompt to be fully typed before submitting
sleep 1

# Send Enter to submit
tmux send-keys -t "$WINDOW" Enter

echo "Message sent to $WINDOW: $MESSAGE"