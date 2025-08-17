#!/bin/bash
# Send message from bsnes-plus to snes-modder
MESSAGE="$1"
MESSAGE_ID="bsnes-plus-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${MESSAGE_ID}.json << EOF
{
  "from_session": "bsnes-plus",
  "to_session": "snes-modder",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID"
}
EOF
echo "✅ Message sent to snes-modder: $MESSAGE"
tmux send-keys -t "snes-modder:0.0" "📨 New message from bsnes-plus: $(printf '%q' "$MESSAGE")" Enter
