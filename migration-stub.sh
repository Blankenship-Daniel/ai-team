#!/bin/bash
# Migration stub template for deprecated send-to-peer-* scripts
# This script provides migration guidance for legacy hardcoded scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Extract target session from script name
SCRIPT_NAME="$(basename "$0")"
TARGET_SESSION="${SCRIPT_NAME#send-to-peer-}"
TARGET_SESSION="${TARGET_SESSION%.sh}"

echo -e "${RED}⚠️  DEPRECATED SCRIPT WARNING${NC}"
echo "================================================"
echo ""
echo -e "${YELLOW}Script '$SCRIPT_NAME' is deprecated!${NC}"
echo ""
echo -e "${BLUE}🚀 PLEASE USE THE NEW UNIFIED TOOL:${NC}"
echo -e "   ${RED}OLD:${NC} ./$SCRIPT_NAME \"message\""
echo -e "   ${GREEN}NEW:${NC} ./send-to-peer.sh $TARGET_SESSION \"message\""
echo ""
echo -e "${GREEN}✅ Benefits of unified tool:${NC}"
echo "   • Dynamic bridge discovery (no hardcoded sessions)"
echo "   • Multi-bridge support"
echo "   • Better error handling and validation"
echo "   • Consistent interface across all peer communication"
echo ""
echo -e "${BLUE}🔄 Auto-migration (if message provided):${NC}"

# If message provided, auto-migrate to new tool
if [ $# -gt 0 ]; then
    MESSAGE="$1"
    echo "   Redirecting to: ./send-to-peer.sh $TARGET_SESSION \"$MESSAGE\""
    echo ""

    # Check if new tool exists
    if [ -f "./send-to-peer.sh" ]; then
        echo -e "${GREEN}🚀 Executing unified tool...${NC}"
        ./send-to-peer.sh "$TARGET_SESSION" "$MESSAGE"
    else
        echo -e "${RED}❌ Error: Unified tool ./send-to-peer.sh not found${NC}"
        echo "Please ensure you have the latest unified bridge tools installed."
        exit 1
    fi
else
    echo ""
    echo -e "${YELLOW}💡 No message provided - showing help only${NC}"
    echo -e "${BLUE}Usage:${NC} ./send-to-peer.sh $TARGET_SESSION \"your message here\""
    echo ""
    echo -e "${BLUE}📋 Bridge Management:${NC}"
    echo "   ai-bridge list                    # View active bridges"
    echo "   ai-bridge status <session>       # Check session bridges"
    echo "   ai-bridge create <s1> <s2> \"ctx\" # Create new bridge"
fi

echo ""
echo -e "${YELLOW}📚 Migration guide: DEPRECATED_SYSTEMS.md${NC}"
echo -e "${BLUE}🔗 Full documentation: ORCHESTRATOR_GUIDE.md${NC}"
echo ""
