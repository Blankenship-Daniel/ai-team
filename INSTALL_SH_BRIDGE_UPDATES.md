# 🔧 INSTALL.SH UPDATES FOR BRIDGE CONSOLIDATION

## CRITICAL CHANGES REQUIRED

### 1. UPDATE REQUIRED_FILES ARRAY
**BEFORE** (Line 84):
```bash
REQUIRED_FILES=("create_ai_team.py" "ai-team-connect.py" "tmux_utils.py" "security_validator.py" "logging_config.py" "unified_context_manager.py" "send-claude-message.sh" "schedule_with_note.sh" "ai-team")
```

**AFTER** (Updated):
```bash
REQUIRED_FILES=("create_ai_team.py" "bridge_registry.py" "tmux_utils.py" "security_validator.py" "logging_config.py" "unified_context_manager.py" "send-claude-message.sh" "schedule_with_note.sh" "check-peer-messages.sh" "ai-team")
```

### 2. REMOVE AI-TEAM-CONNECT.PY INSTALLATION
**BEFORE** (Lines 101-103):
```bash
# Copy connect script
cp "$SOURCE_DIR/ai-team-connect.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied ai-team-connect.py${NC}"
```

**AFTER** (Replace with):
```bash
# Copy bridge registry
cp "$SOURCE_DIR/bridge_registry.py" "$INSTALL_DIR/"
echo -e "${GREEN}✓ Copied bridge_registry.py${NC}"

# Copy peer communication tools
cp "$SOURCE_DIR/check-peer-messages.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/check-peer-messages.sh"
echo -e "${GREEN}✓ Copied check-peer-messages.sh${NC}"
```

### 3. UPDATE INSTALLATION SUMMARY
**BEFORE** (Lines 156-158):
```bash
echo "  • create_ai_team.py (main script)"
echo "  • ai-team-connect.py (multi-team coordination)"
echo "  • tmux_utils.py (tmux management)"
```

**AFTER** (Updated):
```bash
echo "  • create_ai_team.py (main script)"
echo "  • bridge_registry.py (multi-bridge coordination)"
echo "  • tmux_utils.py (tmux management)"
echo "  • check-peer-messages.sh (peer communication)"
```

### 4. UPDATE USAGE INSTRUCTIONS
**BEFORE** (Line 170):
```bash
echo -e "  ${BLUE}ai-team connect session1 session2 \"context\"${NC}     # Connect two teams"
```

**AFTER** (Updated):
```bash
echo -e "  ${BLUE}ai-team connect session1 session2 \"context\"${NC}     # Connect two teams (via bridge registry)"
```

## ADDITIONAL ARCHITECTURAL REQUIREMENTS

### 5. ADD DEPENDENCY VALIDATION
Insert after line 45 (Claude CLI check):
```bash
# Check if jq is available (required for bridge messaging)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'jq' command not found${NC}"
    echo "Bridge messaging requires jq for JSON processing"
    echo "Install: brew install jq (macOS) or apt install jq (Ubuntu)"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ jq found${NC}"
fi
```

### 6. ADD BRIDGE SYSTEM VERIFICATION
Insert after line 149 (Installation test):
```bash
# Test bridge registry functionality
echo -e "${BLUE}🧪 Testing bridge registry...${NC}"
if python3 "$INSTALL_DIR/bridge_registry.py" help >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Bridge registry functional${NC}"
else
    echo -e "${YELLOW}⚠️  Bridge registry test failed${NC}"
fi
```

### 7. UPDATE AI-TEAM WRAPPER SCRIPT
The `ai-team` wrapper script needs to route `connect` commands to bridge_registry.py:
```bash
# Add to ai-team script (around line where connect is handled):
if [[ "$1" == "connect" ]]; then
    shift
    exec python3 "$(dirname "$0")/bridge_registry.py" create "$@"
fi
```

## VALIDATION CHECKLIST

**Pre-deployment validation**:
- [ ] All REQUIRED_FILES exist in source directory
- [ ] bridge_registry.py help command works
- [ ] check-peer-messages.sh is executable
- [ ] jq dependency check functions correctly
- [ ] ai-team connect routes to bridge_registry.py
- [ ] Installation completes without errors
- [ ] Bridge creation works end-to-end

**Post-deployment validation**:
- [ ] `ai-team connect team1 team2 "context"` works
- [ ] Generated send-to-peer scripts function
- [ ] check-peer-messages.sh finds messages correctly
- [ ] Legacy bridge_context.json compatibility maintained
- [ ] No broken file references in installation

## ARCHITECTURAL NOTES

This installation update completes the bridge consolidation by:
1. **Eliminating dual systems** - Only bridge_registry.py installed
2. **Maintaining compatibility** - ai-team connect still works via routing
3. **Adding validation** - Proper dependency checking
4. **Improving UX** - Single, consistent bridge interface

The result is a clean, maintainable installation that reflects the unified bridge architecture while preserving all existing functionality.
