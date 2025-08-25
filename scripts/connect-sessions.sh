#!/bin/bash
# connect-sessions.sh - Connect existing tmux sessions for multi-team coordination

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}🔗 AI Team Session Connector${NC}"
echo "=================================="

# Check if coordination directory exists
COORD_DIR=".ai-coordination"
if [ ! -d "$COORD_DIR" ]; then
    echo -e "${YELLOW}Creating coordination directory...${NC}"
    mkdir -p "$COORD_DIR"/{messages,team_status}
    echo "[]" > "$COORD_DIR/work_queue.json"
fi

# List available tmux sessions
echo -e "\n📋 Available tmux sessions:"
tmux list-sessions -F "#{session_name}" | nl -v0 -s": "

echo ""
read -p "Enter name for Team 1 session: " TEAM1_SESSION
read -p "Enter name for Team 2 session: " TEAM2_SESSION

# Verify sessions exist
if ! tmux has-session -t "$TEAM1_SESSION" 2>/dev/null; then
    echo "❌ Session '$TEAM1_SESSION' not found!"
    exit 1
fi

if ! tmux has-session -t "$TEAM2_SESSION" 2>/dev/null; then
    echo "❌ Session '$TEAM2_SESSION' not found!"
    exit 1
fi

# Register both teams
echo -e "\n${YELLOW}Registering teams in coordination system...${NC}"

# Create team registration for Team 1
cat > "$COORD_DIR/team_status/${TEAM1_SESSION}-team.json" << EOF
{
  "team_name": "${TEAM1_SESSION}-team",
  "session_name": "$TEAM1_SESSION",
  "orchestrator_pane": "0.0",
  "registered_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "last_seen": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "status": "active",
  "capabilities": ["general_development"],
  "current_work": []
}
EOF

# Create team registration for Team 2
cat > "$COORD_DIR/team_status/${TEAM2_SESSION}-team.json" << EOF
{
  "team_name": "${TEAM2_SESSION}-team",
  "session_name": "$TEAM2_SESSION",
  "orchestrator_pane": "0.0",
  "registered_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "last_seen": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "status": "active",
  "capabilities": ["general_development"],
  "current_work": []
}
EOF

# Create coordination helper scripts for each session
cat > "team-coord-${TEAM1_SESSION}.sh" << EOF
#!/bin/bash
# Quick coordination commands for ${TEAM1_SESSION}

TEAM_NAME="${TEAM1_SESSION}-team"
OTHER_TEAM="${TEAM2_SESSION}-team"

case "\$1" in
    "send")
        # Send message to other team
        MESSAGE_ID="\${TEAM_NAME}-\$(date +%s%S)"
        cat > ".ai-coordination/messages/\${MESSAGE_ID}.json" << MSGEOF
{
  "from_team": "\$TEAM_NAME",
  "to_team": "\$OTHER_TEAM",
  "message_type": "message",
  "content": "\$2",
  "priority": "normal",
  "timestamp": "\$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "message_id": "\$MESSAGE_ID"
}
MSGEOF
        echo "✅ Message sent to \$OTHER_TEAM: \$2"
        ;;
    "read")
        # Read messages for this team
        echo "📨 Messages for \$TEAM_NAME:"
        for msg in .ai-coordination/messages/*.json; do
            if [ -f "\$msg" ]; then
                RECIPIENT=\$(jq -r '.to_team' "\$msg" 2>/dev/null)
                if [ "\$RECIPIENT" = "\$TEAM_NAME" ]; then
                    FROM=\$(jq -r '.from_team' "\$msg")
                    CONTENT=\$(jq -r '.content' "\$msg")
                    TIME=\$(jq -r '.timestamp' "\$msg")
                    echo "  📩 From \$FROM at \$TIME: \$CONTENT"
                fi
            fi
        done
        ;;
    "status")
        # Show coordination status
        echo "🎯 Coordination Status:"
        echo "  Team: \$TEAM_NAME"
        echo "  Other Team: \$OTHER_TEAM"
        echo "  Coordination Dir: \$(pwd)/.ai-coordination"
        echo ""
        echo "📊 Work Queue:"
        if [ -f ".ai-coordination/work_queue.json" ]; then
            jq -r '.[] | "  - [\(.status)] \(.title)"' .ai-coordination/work_queue.json 2>/dev/null || echo "  (empty)"
        else
            echo "  (no work queue)"
        fi
        ;;
    *)
        echo "Usage: \$0 {send|read|status} [message]"
        echo ""
        echo "Examples:"
        echo "  \$0 send \"Hey other team, how's the API coming?\""
        echo "  \$0 read"
        echo "  \$0 status"
        ;;
esac
EOF

# Create coordination helper for Team 2
cat > "team-coord-${TEAM2_SESSION}.sh" << EOF
#!/bin/bash
# Quick coordination commands for ${TEAM2_SESSION}

TEAM_NAME="${TEAM2_SESSION}-team"
OTHER_TEAM="${TEAM1_SESSION}-team"

case "\$1" in
    "send")
        # Send message to other team
        MESSAGE_ID="\${TEAM_NAME}-\$(date +%s%S)"
        cat > ".ai-coordination/messages/\${MESSAGE_ID}.json" << MSGEOF
{
  "from_team": "\$TEAM_NAME",
  "to_team": "\$OTHER_TEAM",
  "message_type": "message",
  "content": "\$2",
  "priority": "normal",
  "timestamp": "\$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
  "message_id": "\$MESSAGE_ID"
}
MSGEOF
        echo "✅ Message sent to \$OTHER_TEAM: \$2"
        ;;
    "read")
        # Read messages for this team
        echo "📨 Messages for \$TEAM_NAME:"
        for msg in .ai-coordination/messages/*.json; do
            if [ -f "\$msg" ]; then
                RECIPIENT=\$(jq -r '.to_team' "\$msg" 2>/dev/null)
                if [ "\$RECIPIENT" = "\$TEAM_NAME" ]; then
                    FROM=\$(jq -r '.from_team' "\$msg")
                    CONTENT=\$(jq -r '.content' "\$msg")
                    TIME=\$(jq -r '.timestamp' "\$msg")
                    echo "  📩 From \$FROM at \$TIME: \$CONTENT"
                fi
            fi
        done
        ;;
    "status")
        # Show coordination status
        echo "🎯 Coordination Status:"
        echo "  Team: \$TEAM_NAME"
        echo "  Other Team: \$OTHER_TEAM"
        echo "  Coordination Dir: \$(pwd)/.ai-coordination"
        echo ""
        echo "📊 Work Queue:"
        if [ -f ".ai-coordination/work_queue.json" ]; then
            jq -r '.[] | "  - [\(.status)] \(.title)"' .ai-coordination/work_queue.json 2>/dev/null || echo "  (empty)"
        else
            echo "  (no work queue)"
        fi
        ;;
    *)
        echo "Usage: \$0 {send|read|status} [message]"
        echo ""
        echo "Examples:"
        echo "  \$0 send \"API endpoints are ready for testing!\""
        echo "  \$0 read"
        echo "  \$0 status"
        ;;
esac
EOF

chmod +x "team-coord-${TEAM1_SESSION}.sh"
chmod +x "team-coord-${TEAM2_SESSION}.sh"

# Add sample work item
cat > "$COORD_DIR/work_queue.json" << EOF
[
  {
    "item_id": "work-$(date +%s%S)",
    "title": "Coordinate between teams",
    "description": "Test the multi-team coordination system",
    "assigned_team": null,
    "status": "pending",
    "priority": "normal",
    "created_by": "connect-sessions-script",
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
    "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%SZ")",
    "dependencies": []
  }
]
EOF

echo -e "\n${GREEN}✅ Sessions connected successfully!${NC}"
echo ""
echo "🎯 Your teams are now coordinated:"
echo "  📱 Team 1: ${TEAM1_SESSION}-team"
echo "  📱 Team 2: ${TEAM2_SESSION}-team"
echo ""
echo "🛠️  Quick commands created:"
echo "  ./team-coord-${TEAM1_SESSION}.sh send \"message\""
echo "  ./team-coord-${TEAM1_SESSION}.sh read"
echo "  ./team-coord-${TEAM1_SESSION}.sh status"
echo ""
echo "  ./team-coord-${TEAM2_SESSION}.sh send \"message\""
echo "  ./team-coord-${TEAM2_SESSION}.sh read"
echo "  ./team-coord-${TEAM2_SESSION}.sh status"
echo ""
echo "🔗 Example usage:"
echo "  # From session 1:"
echo "  ./team-coord-${TEAM1_SESSION}.sh send \"Hey team 2, how's the backend coming?\""
echo ""
echo "  # From session 2:"
echo "  ./team-coord-${TEAM2_SESSION}.sh read"
echo "  ./team-coord-${TEAM2_SESSION}.sh send \"API is ready! Need the frontend endpoints.\""
echo ""
echo "📁 Coordination files in: .ai-coordination/"
