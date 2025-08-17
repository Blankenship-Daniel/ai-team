#!/bin/bash
# Send message from ai-team to bsnes via bridge bridge-e846da75db92
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="ai-team-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "ai-team",
  "to_session": "bsnes",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-e846da75db92"
}
EOF

echo "✅ Message sent to bsnes: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "bsnes:0.0" "📨 New message from ai-team: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
