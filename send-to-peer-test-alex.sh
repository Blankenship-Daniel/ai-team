#!/bin/bash
# Send message from test-alex to test-morgan via bridge bridge-542647ec41c0
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="test-alex-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "test-alex",
  "to_session": "test-morgan",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-542647ec41c0"
}
EOF

echo "✅ Message sent to test-morgan: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "test-morgan:0.0" "📨 New message from test-alex: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
