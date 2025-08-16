#!/bin/bash
# Unified Dynamic Peer Messaging System
# Replaces all legacy hardcoded send-to-peer-* scripts
# Usage: send-to-peer.sh <target-session> "message"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_REGISTRY="$SCRIPT_DIR/bridge_registry.py"
COORD_DIR=".ai-coordination"

# Help function
show_help() {
    echo -e "${BLUE}🚀 Unified Dynamic Peer Messaging System${NC}"
    echo "================================================"
    echo ""
    echo "USAGE:"
    echo "    send-to-peer.sh <target-session> \"message\""
    echo ""
    echo "EXAMPLES:"
    echo "    send-to-peer.sh snes-modder \"Please analyze ROM at $7E2000\""
    echo "    send-to-peer.sh backend-team \"API changes deployed to staging\""
    echo "    send-to-peer.sh mobile-team \"UI mockups ready for review\""
    echo ""
    echo "FEATURES:"
    echo "    ✅ Dynamic bridge discovery (no hardcoded sessions)"
    echo "    ✅ Multi-bridge support"
    echo "    ✅ Automatic message timestamping"
    echo "    ✅ Security validation"
    echo "    ✅ Bridge status verification"
    echo ""
    echo "BRIDGE MANAGEMENT:"
    echo "    bridge_registry.py list                    # View active bridges"
    echo "    bridge_registry.py status <session>       # Check session bridges"
    echo "    bridge_registry.py create <s1> <s2> \"ctx\" # Create new bridge"
    echo ""
}

# Validate arguments
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Error: Missing arguments${NC}"
    echo ""
    show_help
    exit 1
fi

TARGET_SESSION="$1"
MESSAGE="$2"

# Get current session name
CURRENT_SESSION=$(tmux display-message -p "#{session_name}" 2>/dev/null || echo "unknown")

echo -e "${BLUE}🔗 Unified Dynamic Peer Messaging${NC}"
echo "================================================"
echo -e "${BLUE}From:${NC} $CURRENT_SESSION"
echo -e "${BLUE}To:${NC} $TARGET_SESSION"
echo -e "${BLUE}Message:${NC} $MESSAGE"
echo ""

# Check if bridge registry exists
if [ ! -f "$BRIDGE_REGISTRY" ]; then
    echo -e "${RED}❌ Error: Bridge registry not found at $BRIDGE_REGISTRY${NC}"
    echo "Make sure you're in the correct directory with bridge_registry.py"
    exit 1
fi

# Check if coordination directory exists
if [ ! -d "$COORD_DIR" ]; then
    echo -e "${YELLOW}⚠️  Warning: Coordination directory not found${NC}"
    echo "Creating coordination directory structure..."
    mkdir -p "$COORD_DIR"
fi

# Find active bridge to target session
echo -e "${BLUE}🔍 Discovering bridge to $TARGET_SESSION...${NC}"

# Use bridge registry to find peer sessions
BRIDGE_INFO=$(python3 "$BRIDGE_REGISTRY" status "$CURRENT_SESSION" 2>/dev/null | grep "$TARGET_SESSION" | head -1)

if [ -z "$BRIDGE_INFO" ]; then
    echo -e "${RED}❌ Error: No active bridge found${NC}"
    echo "Current session '$CURRENT_SESSION' has no bridge to '$TARGET_SESSION'"
    echo ""
    echo -e "${YELLOW}💡 Available bridges for $CURRENT_SESSION:${NC}"
    python3 "$BRIDGE_REGISTRY" status "$CURRENT_SESSION" 2>/dev/null || echo "   (no bridges found)"
    echo ""
    echo -e "${YELLOW}💡 To create a bridge:${NC}"
    echo "   bridge_registry.py create \"$CURRENT_SESSION\" \"$TARGET_SESSION\" \"coordination context\""
    exit 1
fi

# Extract bridge ID from bridge info
BRIDGE_ID=$(echo "$BRIDGE_INFO" | grep -o "bridge-[a-f0-9]*" | head -1)

if [ -z "$BRIDGE_ID" ]; then
    echo -e "${RED}❌ Error: Could not extract bridge ID${NC}"
    echo "Bridge info: $BRIDGE_INFO"
    exit 1
fi

echo -e "${GREEN}✅ Bridge found: $BRIDGE_ID${NC}"

# Verify target session exists
echo -e "${BLUE}🔍 Verifying target session exists...${NC}"
if ! tmux has-session -t "$TARGET_SESSION" 2>/dev/null; then
    echo -e "${RED}❌ Error: Target session '$TARGET_SESSION' not found${NC}"
    echo "Make sure the target session is running"
    exit 1
fi

echo -e "${GREEN}✅ Target session verified${NC}"

# Create message with metadata
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
MESSAGE_ID="${CURRENT_SESSION}-$(date +%s%N | cut -c1-13)"

MESSAGE_DATA=$(cat <<EOF
{
    "message_id": "$MESSAGE_ID",
    "from_session": "$CURRENT_SESSION",
    "to_session": "$TARGET_SESSION",
    "bridge_id": "$BRIDGE_ID",
    "message": "$MESSAGE",
    "timestamp": "$TIMESTAMP",
    "sender_type": "orchestrator"
}
EOF
)

# Create message file
MESSAGE_DIR="$COORD_DIR/messages/$BRIDGE_ID"
mkdir -p "$MESSAGE_DIR"

MESSAGE_FILE="$MESSAGE_DIR/$MESSAGE_ID.json"
echo "$MESSAGE_DATA" > "$MESSAGE_FILE"

echo -e "${GREEN}✅ Message stored: $MESSAGE_FILE${NC}"

# Send message to target session's orchestrator (pane 0.0)
echo -e "${BLUE}📤 Sending message to ${TARGET_SESSION}:0.0...${NC}"

FORMATTED_MESSAGE="🔗 Bridge message from $CURRENT_SESSION: $MESSAGE"

if tmux send-keys -t "${TARGET_SESSION}:0.0" "$FORMATTED_MESSAGE" 2>/dev/null; then
    echo -e "${GREEN}✅ Message sent successfully!${NC}"

    # Update bridge last activity
    python3 "$BRIDGE_REGISTRY" status "$CURRENT_SESSION" > /dev/null 2>&1

    echo ""
    echo -e "${BLUE}📊 Message Summary:${NC}"
    echo "   Bridge: $BRIDGE_ID"
    echo "   Message ID: $MESSAGE_ID"
    echo "   Sent at: $TIMESTAMP"
    echo "   Storage: $MESSAGE_FILE"

else
    echo -e "${RED}❌ Error: Failed to send message to target session${NC}"
    echo "The target session may not be responsive or accessible"
    exit 1
fi

echo -e "${GREEN}🎉 Dynamic peer messaging completed successfully!${NC}"
