#!/bin/bash
# Send message from test-morgan to test-alex via bridge bridge-542647ec41c0
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="test-morgan-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "test-morgan",
  "to_session": "test-alex",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-542647ec41c0"
}
EOF

echo "✅ Message sent to test-alex: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "test-alex:0.0" "📨 New message from test-morgan: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
