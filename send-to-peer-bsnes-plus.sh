#!/bin/bash
# Send message from bsnes-plus to snes-modder via bridge bridge-f8c006c6e7e6
MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <message>"
    exit 1
fi

MESSAGE_ID="bsnes-plus-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "bsnes-plus",
  "to_session": "snes-modder",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID",
  "bridge_id": "bridge-f8c006c6e7e6"
}
EOF

echo "✅ Message sent to snes-modder: $MESSAGE"
# Notify peer session about new message
tmux send-keys -t "snes-modder:0.0" "📨 New message from bsnes-plus: $(printf '%q' "$MESSAGE")" Enter 2>/dev/null || true
