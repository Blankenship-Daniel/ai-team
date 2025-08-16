# 🔗 User Migration Guide - Legacy to Unified Bridge Tools

## WELCOME TO THE NEW UNIFIED BRIDGE SYSTEM! 🚀

Your team coordination just got **massively** easier with our new unified tools.

## QUICK MIGRATION REFERENCE

### If you used `ai-team connect`
```bash
# ❌ OLD (still works with helpful warning)
ai-team connect frontend backend "API coordination"

# ✅ NEW (streamlined interface)
ai-bridge connect frontend backend "API coordination"
```

### If you used `bridge_registry.py`
```bash
# ❌ OLD (verbose but still works)
bridge_registry.py create frontend backend "API coordination"

# ✅ NEW (same power, simpler interface)
ai-bridge create frontend backend "API coordination"
```

### If you used `send-to-peer-*.sh` scripts
```bash
# ❌ OLD (hardcoded scripts)
send-to-peer-backend.sh "message"

# ✅ NEW (universal command)
ai-bridge send backend "message"
```

## COMPLETE UNIFIED COMMAND REFERENCE

### 🔗 Bridge Creation (Choose Your Style!)
```bash
ai-bridge connect team1 team2 "context"    # Friendly style
ai-bridge create team1 team2 "context"     # Power-user style
# Both do exactly the same thing!
```

### 📤 Send Messages
```bash
ai-bridge send backend "Frontend ready for review"
ai-bridge send mobile "Please sync with web styles"
```

### 📥 Check Messages
```bash
ai-bridge messages                          # All messages
ai-bridge messages frontend                 # Messages for specific team
```

### 📊 Monitor Bridges
```bash
ai-bridge list                              # All active bridges
ai-bridge status frontend                   # Bridges for specific team
```

### 🧹 Maintenance
```bash
ai-bridge cleanup                           # Safe cleanup with defaults
ai-bridge cleanup --dry-run                # Preview what will be cleaned
ai-bridge cleanup --days 5                 # Custom age limit
```

### 📖 Help & Info
```bash
ai-bridge help                              # Comprehensive help
ai-bridge                                   # Quick help
```

## STEP-BY-STEP MIGRATION WALKTHROUGH

### Step 1: Try the New Command
```bash
# Start simple - get help
ai-bridge help

# Create your first bridge with new syntax
ai-bridge connect your-team peer-team "coordination context"
```

### Step 2: Test Messaging
```bash
# Send a test message
ai-bridge send peer-team "Testing new unified tools!"

# Check for responses
ai-bridge messages
```

### Step 3: Explore Advanced Features
```bash
# See all your team's bridges
ai-bridge status your-team

# List all system bridges
ai-bridge list

# Try maintenance features
ai-bridge cleanup --dry-run
```

### Step 4: Update Your Workflows
Replace old commands in your scripts and documentation:
- `ai-team connect` → `ai-bridge connect`
- `bridge_registry.py create` → `ai-bridge create`
- `send-to-peer-*.sh` → `ai-bridge send`

## MIGRATION SAFETY FEATURES

### ✅ Zero Breaking Changes
- All old commands still work
- Existing bridges continue functioning
- No data loss or corruption

### ✅ Helpful Warnings
- Deprecated commands show migration guidance
- Auto-redirection preserves functionality
- Clear benefits explained for each change

### ✅ Gradual Transition
- Use old and new commands side-by-side
- Migrate at your own pace
- Team members can adopt independently

## REAL-WORLD MIGRATION SCENARIOS

### Scenario 1: Frontend-Backend Coordination
```bash
# OLD workflow
ai-team connect frontend backend "API development"
send-to-peer-backend.sh "New endpoints ready"
bridge_registry.py status frontend

# NEW workflow
ai-bridge connect frontend backend "API development"
ai-bridge send backend "New endpoints ready"
ai-bridge status frontend
```

### Scenario 2: Multi-Team Project
```bash
# OLD: Multiple scattered commands
bridge_registry.py create mobile web "UI consistency"
bridge_registry.py create backend database "Schema changes"
send-to-peer-web.sh "Mobile styles updated"
send-to-peer-database.sh "Schema migration ready"

# NEW: Unified interface
ai-bridge create mobile web "UI consistency"
ai-bridge create backend database "Schema changes"
ai-bridge send web "Mobile styles updated"
ai-bridge send database "Schema migration ready"
```

### Scenario 3: Daily Coordination
```bash
# OLD: Mixed tools
check-peer-messages.sh
bridge_registry.py list
send-to-peer-backend.sh "Daily standup at 10am"

# NEW: Single tool
ai-bridge messages
ai-bridge list
ai-bridge send backend "Daily standup at 10am"
```

## BENEFITS OF UNIFIED SYSTEM

### 🚀 Simpler Interface
- One command to learn instead of multiple tools
- Consistent syntax across all operations
- Intuitive verbs (`connect`, `send`, `messages`)

### 🔧 Better Error Handling
- Clear error messages with suggestions
- Automatic validation and safety checks
- Helpful guidance when things go wrong

### 📈 Enhanced Features
- Dynamic bridge discovery
- Multi-bridge support
- Better status and monitoring
- Improved cleanup and maintenance

### 🛠️ Easier Maintenance
- Single codebase to update
- Consistent documentation
- Unified installation process

## TROUBLESHOOTING MIGRATION

### Problem: "ai-bridge command not found"
**Solution:**
```bash
# Make sure ai-bridge is executable
chmod +x ai-bridge

# Check if it's in your PATH or run with ./
./ai-bridge help
```

### Problem: "Old commands show warnings"
**Solution:** This is expected! The warnings help you migrate:
```bash
# Follow the guidance in the warning
# Example: Use ai-bridge connect instead of ai-team connect
```

### Problem: "Can't find my existing bridges"
**Solution:** All bridges are preserved:
```bash
# List all existing bridges
ai-bridge list

# Check specific team status
ai-bridge status your-team-name
```

## MIGRATION TIMELINE

### ✅ NOW: Both Systems Work
- Use `ai-bridge` for new coordination
- Old commands still function with helpful warnings
- No pressure to migrate immediately

### 📅 RECOMMENDED: 30 Days
- Gradually replace old commands in scripts
- Update team documentation
- Train team members on new interface

### 🎯 FUTURE: Unified Experience
- Old wrappers may be removed eventually
- `ai-bridge` becomes the standard interface
- Simplified installation and maintenance

## NEED HELP?

### 📖 Quick Reference
```bash
ai-bridge help                              # Full help
ai-bridge                                   # Quick commands
```

### 📋 Documentation
- `BRIDGE_MIGRATION_FINAL.md` - Technical details
- `ORCHESTRATOR_GUIDE.md` - Complete system guide

### 🤝 Team Support
Ask your team members who have already migrated - the new system is intuitive and powerful!

---

**Welcome to faster, simpler team coordination with ai-bridge!** 🎉
