#!/bin/bash
# Send message from bsnes to ai-team via bridge bridge-e846da75db92
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="bsnes-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "bsnes",
  "to_session": "ai-team",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-e846da75db92"
}
EOF

echo "✅ Message sent to ai-team: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "ai-team:0.0" "📨 New message from bsnes: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
