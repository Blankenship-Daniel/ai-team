#!/bin/bash

# Technical Debt Management Demo - Sam leads the cleanup crusade
# Shows how the team prioritizes and tackles technical debt

set -e

echo "🧹 Technical Debt Management Demo"
echo "=================================="
echo ""
echo "This demo shows how the team handles technical debt:"
echo "• Sam identifies and prioritizes debt items"
echo "• Alex ensures fixes follow best practices"
echo "• Morgan balances cleanup with shipping features"
echo ""

# Setup paths
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CREATE_TEAM="$SCRIPT_DIR/create_ai_team.py"
SEND_MSG="$SCRIPT_DIR/send-claude-message.sh"

SESSION="demo-debt"

# Create a "legacy" project with technical debt
PROJECT_DIR="/tmp/legacy_project"
rm -rf "$PROJECT_DIR" 2>/dev/null || true
mkdir -p "$PROJECT_DIR/src"
mkdir -p "$PROJECT_DIR/tests"

# Create files with various technical debt issues
cat > "$PROJECT_DIR/src/user_manager.py" << 'EOF'
# User management module - legacy code from 2019
import json
import os

# TODO: Replace with proper database
USER_FILE = "/tmp/users.json"

class UserManager:
    def __init__(self):
        # FIXME: This crashes if file doesn't exist
        self.users = json.load(open(USER_FILE))

    def add_user(self, name, email):
        # HACK: Using timestamp as ID
        import time
        id = str(int(time.time()))
        self.users[id] = {"name": name, "email": email}
        # TODO: Add validation
        # TODO: Check for duplicates
        self.save()
        return id

    def save(self):
        # WARNING: No error handling!
        json.dump(self.users, open(USER_FILE, 'w'))

    # Deprecated: Use get_user instead
    def findUser(self, id):
        return self.users.get(id)

    def get_user(self, id):
        # TODO: Add caching
        return self.users.get(id)
EOF

cat > "$PROJECT_DIR/src/api.py" << 'EOF'
# API endpoints - needs major refactoring
from flask import Flask, request
import sys
sys.path.append('/tmp/legacy_project/src')  # HACK: Fix imports
from user_manager import UserManager

app = Flask(__name__)
um = UserManager()  # Global instance - not thread safe!

@app.route('/api/v1/user/<id>')  # Old endpoint
@app.route('/api/v2/users/<id>') # New endpoint
def get_user(id):
    # TODO: Migrate all clients to v2
    user = um.findUser(id)  # Using deprecated method!
    if user:
        return user
    return {"error": "Not found"}, 404

# Copy-pasted from another project
@app.route('/health')
def health():
    # TODO: Actually check system health
    return {"status": "ok"}

# Dead code - remove after Q4 2023
def old_auth_check():
    pass
EOF

cat > "$PROJECT_DIR/README.md" << 'EOF'
# Legacy User System

## Known Issues (Technical Debt)
- No tests (0% coverage)
- Using JSON file instead of database
- No input validation
- Deprecated methods still in use
- Global state issues
- No error handling
- Hardcoded paths
- Mixed API versions
- Dead code present
- No logging
- Not thread-safe
- No authentication

## Priority: ??? (Needs team discussion)
EOF

echo "📁 Created legacy project at: $PROJECT_DIR"
echo ""

# Kill existing session
tmux kill-session -t $SESSION 2>/dev/null || true

echo "🚀 Creating AI team for debt management..."
python3 "$CREATE_TEAM" --session "$SESSION" --observe-only --yes

sleep 3

echo ""
echo "📤 Sending technical debt analysis request..."
echo ""

# Create the debt analysis request
DEBT_MSG="Team, we've inherited a legacy project with significant technical debt. I need your help to:

1. Review the code in $PROJECT_DIR
2. Identify and prioritize technical debt items
3. Create an action plan

The main files are:
- $PROJECT_DIR/src/user_manager.py
- $PROJECT_DIR/src/api.py
- $PROJECT_DIR/README.md (lists known issues)

Sam, please lead the technical debt analysis.
Alex, ensure our fixes follow best practices.
Morgan, help us balance cleanup with feature delivery.

Let's create a pragmatic plan that improves the code while keeping the system running."

# Send to orchestrator
if [ -f "$SEND_MSG" ]; then
    "$SEND_MSG" "$SESSION:0.0" "$DEBT_MSG"
    echo "✅ Technical debt analysis request sent!"
else
    echo "⚠️  send-claude-message.sh not found. Please manually send the request."
fi

echo ""
echo "🎯 Demo is running! What to expect:"
echo ""
echo "1. Attach to watch: tmux attach -t $SESSION"
echo "2. Sam will identify all debt items and prioritize them"
echo "3. Alex will insist on proper architecture for fixes"
echo "4. Morgan will push for incremental improvements"
echo "5. The team will debate and create a balanced plan"
echo ""
echo "💡 This shows how different perspectives create better debt management!"
echo ""
echo "To clean up:"
echo "  tmux kill-session -t $SESSION"
echo "  rm -rf $PROJECT_DIR"
