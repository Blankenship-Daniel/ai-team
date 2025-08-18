#!/bin/bash

# Code Review Workflow Demo - Three perspectives on code quality
# Shows how agents with different priorities review the same code

set -e

echo "🔍 Code Review Workflow Demo"
echo "============================="
echo ""
echo "This demo shows how three agents review code differently:"
echo "• Alex focuses on architecture and best practices"
echo "• Morgan focuses on whether it works and ships"
echo "• Sam focuses on cleanup opportunities"
echo ""

# Setup paths
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CREATE_TEAM="$SCRIPT_DIR/create_ai_team.py"
SEND_MSG="$SCRIPT_DIR/send-claude-message.sh"

SESSION="demo-review"

# Create sample code for review
SAMPLE_CODE="/tmp/sample_api.py"
cat > "$SAMPLE_CODE" << 'EOF'
# Quick API endpoint - needs review
from flask import Flask, request
import json

app = Flask(__name__)

# TODO: Move to database later
users = {}

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    # Quick validation
    if not data.get('name'):
        return {'error': 'Missing name'}, 400

    id = len(users) + 1
    users[id] = {
        'id': id,
        'name': data['name'],
        'email': data.get('email', '')  # Optional
    }
    return users[id], 201

@app.route('/user/<int:id>')
def get_user(id):
    if id in users:
        return users[id]
    return {'error': 'Not found'}, 404

# TODO: Add update and delete
# TODO: Add authentication
# TODO: Add proper error handling

if __name__ == '__main__':
    app.run(debug=True)  # FIXME: Don't use debug in production!
EOF

echo "📝 Sample code created at: $SAMPLE_CODE"
echo ""

# Kill existing session
tmux kill-session -t $SESSION 2>/dev/null || true

echo "🚀 Creating AI team for code review..."
python3 "$CREATE_TEAM" --session "$SESSION" --observe-only --yes

sleep 3

echo ""
echo "📤 Sending code review request to orchestrator..."
echo ""

# Create the review request message
REVIEW_MSG="Team, I need you to review this Flask API code and provide your perspectives:

\`\`\`python
$(cat "$SAMPLE_CODE")
\`\`\`

Please each provide your review focusing on your expertise:
- Alex: Architecture and best practices
- Morgan: Does it work? Can we ship it?
- Sam: What technical debt and cleanup opportunities do you see?

After individual reviews, discuss and agree on priority fixes."

# Send to orchestrator using the send script
if [ -f "$SEND_MSG" ]; then
    "$SEND_MSG" "$SESSION:0.0" "$REVIEW_MSG"
    echo "✅ Code review request sent!"
else
    echo "⚠️  send-claude-message.sh not found. Please manually send the review request."
fi

echo ""
echo "🎬 Demo is running! Next steps:"
echo ""
echo "1. Attach to see the review: tmux attach -t $SESSION"
echo "2. Watch as each agent provides their perspective:"
echo "   • Alex will critique the lack of proper architecture"
echo "   • Morgan will say it's good enough for MVP"
echo "   • Sam will identify all the TODOs and cleanup needs"
echo "3. The orchestrator will help them prioritize fixes"
echo ""
echo "💡 This demonstrates how different perspectives lead to better code!"
echo ""
echo "To clean up:"
echo "  tmux kill-session -t $SESSION"
echo "  rm $SAMPLE_CODE"
