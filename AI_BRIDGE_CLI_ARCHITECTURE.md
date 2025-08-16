# 🎯 AI-BRIDGE UNIFIED CLI ARCHITECTURE

## ARCHITECTURAL CONSISTENCY REQUIREMENTS

### CLI Pattern Analysis
Current project follows **subcommand pattern** established by:
- `ai-team` (main script with subcommands)
- `bridge_registry.py` (direct command pattern)
- Consistent with Unix CLI conventions

### UNIFIED CLI STRUCTURE
```bash
ai-bridge <subcommand> [options] [arguments]

SUBCOMMANDS:
  connect/create <session1> <session2> "<context>"   # Create bridge
  list                                               # List active bridges
  status <session>                                   # Show session bridges
  cleanup [--dry-run] [--max-age-days N]           # Clean old bridges
  help                                              # Show help
```

---

## 🔧 CLI IMPLEMENTATION ARCHITECTURE

### 1. WRAPPER SCRIPT PATTERN
**Create**: `ai-bridge` (bash wrapper script)
```bash
#!/bin/bash
# AI Bridge - Unified bridge management CLI
# Routes commands to bridge_registry.py with consistent error handling

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_REGISTRY="$SCRIPT_DIR/bridge_registry.py"

# Color codes for consistent output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Error handling function
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Validation function
validate_dependencies() {
    command -v python3 >/dev/null 2>&1 || error_exit "python3 not found"
    command -v tmux >/dev/null 2>&1 || error_exit "tmux not found"
    command -v jq >/dev/null 2>&1 || error_exit "jq not found (required for messaging)"
    [ -f "$BRIDGE_REGISTRY" ] || error_exit "bridge_registry.py not found"
}

# Route commands
case "${1:-help}" in
    "connect"|"create")
        validate_dependencies
        shift
        python3 "$BRIDGE_REGISTRY" create "$@"
        ;;
    "list")
        validate_dependencies
        python3 "$BRIDGE_REGISTRY" list
        ;;
    "status")
        validate_dependencies
        shift
        python3 "$BRIDGE_REGISTRY" status "$@"
        ;;
    "cleanup")
        validate_dependencies
        shift
        python3 "$BRIDGE_REGISTRY" cleanup "$@"
        ;;
    "help"|"--help"|"-h"|"")
        python3 "$BRIDGE_REGISTRY" help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo -e "${BLUE}💡 Try: ai-bridge help${NC}"
        exit 1
        ;;
esac
```

### 2. ERROR HANDLING CONSISTENCY
**Pattern**: Follow existing SecurityValidator and ai-team patterns
```bash
# Consistent error messages
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Consistent success messages
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Consistent warning messages
warn_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}
```

### 3. ARGUMENT VALIDATION
**Pattern**: SecurityValidator integration for all inputs
```python
# In bridge_registry.py enhanced create_bridge method:
def create_bridge_with_validation(self, session1: str, session2: str, context: str):
    # 1. Security validation
    valid, error = SecurityValidator.validate_session_name(session1)
    if not valid:
        raise ValueError(f"Invalid session1: {error}")

    valid, error = SecurityValidator.validate_session_name(session2)
    if not valid:
        raise ValueError(f"Invalid session2: {error}")

    # 2. Context validation
    if not context or len(context) > 500:
        raise ValueError("Context must be 1-500 characters")

    # 3. Proceed with creation
    return self.create_bridge(session1, session2, context)
```

---

## 📦 INSTALL.SH INTEGRATION REQUIREMENTS

### 1. UPDATE REQUIRED_FILES
```bash
REQUIRED_FILES=("create_ai_team.py" "bridge_registry.py" "tmux_utils.py"
                "security_validator.py" "logging_config.py" "unified_context_manager.py"
                "send-claude-message.sh" "schedule_with_note.sh" "check-peer-messages.sh"
                "ai-team" "ai-bridge")
```

### 2. AI-BRIDGE INSTALLATION SECTION
Insert after ai-team installation (around line 140):
```bash
# Copy the unified bridge CLI
cp "$SOURCE_DIR/ai-bridge" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/ai-bridge"
echo -e "${GREEN}✓ Installed ai-bridge command${NC}"
```

### 3. DEPENDENCY VALIDATION ENHANCEMENT
Update jq check (from INSTALL_SH_BRIDGE_UPDATES.md):
```bash
# Enhanced dependency check
echo -e "${BLUE}🔍 Checking bridge dependencies...${NC}"
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'jq' required for bridge messaging${NC}"
    echo "Install: brew install jq (macOS) or apt install jq (Ubuntu)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
else
    echo -e "${GREEN}✓ jq found${NC}"
fi
```

### 4. INSTALLATION TESTING
```bash
# Test ai-bridge functionality
echo -e "${BLUE}🧪 Testing ai-bridge command...${NC}"
if "$INSTALL_DIR/ai-bridge" help >/dev/null 2>&1; then
    echo -e "${GREEN}✓ ai-bridge functional${NC}"
else
    echo -e "${RED}❌ ai-bridge test failed${NC}"
    exit 1
fi
```

### 5. USAGE DOCUMENTATION UPDATE
```bash
echo "Usage:"
echo -e "  ${BLUE}ai-team${NC}                                           # Create default team"
echo -e "  ${BLUE}ai-bridge connect team1 team2 \"context\"${NC}          # Connect teams"
echo -e "  ${BLUE}ai-bridge list${NC}                                    # List bridges"
echo -e "  ${BLUE}ai-bridge status team1${NC}                          # Check team bridges"
echo -e "  ${BLUE}ai-bridge cleanup${NC}                               # Clean old bridges"
```

---

## 🎯 ARCHITECTURAL BENEFITS

### 1. **Consistency**
- Follows established CLI patterns from ai-team
- Consistent error handling and messaging
- Unified dependency validation

### 2. **Maintainability**
- Single entry point for all bridge operations
- Clear separation between wrapper (bash) and logic (Python)
- Centralized error handling

### 3. **User Experience**
- Intuitive subcommand structure
- Helpful error messages with suggestions
- Consistent visual feedback (colors, emojis)

### 4. **Extensibility**
- Easy to add new subcommands
- Validation layer prevents breaking changes
- Modular architecture supports testing

---

## ✅ VALIDATION CHECKLIST

**CLI Architecture**:
- [ ] ai-bridge wrapper script created
- [ ] Subcommand routing implemented
- [ ] Error handling follows project patterns
- [ ] SecurityValidator integration complete
- [ ] Help system consistent with existing tools

**Installation Integration**:
- [ ] REQUIRED_FILES updated with ai-bridge
- [ ] ai-bridge installation and chmod +x
- [ ] Dependency validation (jq) functional
- [ ] Installation testing includes ai-bridge
- [ ] Usage documentation updated

**User Experience**:
- [ ] `ai-bridge help` shows comprehensive help
- [ ] Error messages include helpful suggestions
- [ ] Success/warning messages use consistent formatting
- [ ] All subcommands tested end-to-end

**Backward Compatibility**:
- [ ] `ai-team connect` still routes to bridge system
- [ ] Existing bridge_context.json compatibility maintained
- [ ] Legacy send-to-peer scripts continue working
- [ ] No breaking changes for existing users

This unified CLI architecture provides a clean, maintainable interface while preserving all existing functionality and following established project patterns.
