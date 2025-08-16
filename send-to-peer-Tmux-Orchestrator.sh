#!/bin/bash
# Send message from Tmux-Orchestrator to test-alex via bridge bridge-a07663b020af
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="Tmux-Orchestrator-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "Tmux-Orchestrator",
  "to_session": "test-alex",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-a07663b020af"
}
EOF

echo "✅ Message sent to test-alex: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "test-alex:0.0" "📨 New message from Tmux-Orchestrator: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
