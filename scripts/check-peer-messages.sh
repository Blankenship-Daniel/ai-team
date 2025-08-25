#!/bin/bash
# Check messages for current session
SESSION_NAME=$(tmux display-message -p '#{session_name}')
echo "📨 Messages for $SESSION_NAME:"
for msg in .ai-coordination/messages/*.json; do
    if [ -f "$msg" ]; then
        TO_SESSION=$(jq -r '.to_session' "$msg" 2>/dev/null)
        if [ "$TO_SESSION" = "$SESSION_NAME" ]; then
            FROM=$(jq -r '.from_session' "$msg")
            CONTENT=$(jq -r '.message' "$msg")
            TIME=$(jq -r '.timestamp' "$msg")
            echo "  📩 From $FROM at $TIME: $CONTENT"
        fi
    fi
done
