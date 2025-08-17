#!/bin/bash
# Send message from snes-modder to bsnes-plus
MESSAGE="$1"
MESSAGE_ID="snes-modder-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "snes-modder",
  "to_session": "bsnes-plus",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID"
}
EOF
echo "✅ Message sent to bsnes-plus: $MESSAGE"
tmux send-keys -t "bsnes-plus:0.0" "📨 New message from snes-modder: $(printf '%q' "$MESSAGE")" Enter
