# 🔗 Bridge System Migration Guide

## EMERGENCY CONSOLIDATION COMPLETE ✅

The bridge system has been consolidated into **ONE UNIFIED INTERFACE** to eliminate user confusion and maintenance hell.

## NEW UNIFIED COMMAND: `ai-bridge`

**Single command replaces all bridge tools:**

```bash
# ✅ NEW UNIFIED INTERFACE
ai-bridge connect team1 team2 "context"     # Create bridge
ai-bridge send team2 "message"              # Send message
ai-bridge messages                           # Check messages
ai-bridge list                               # List bridges
ai-bridge status team1                       # Team status
ai-bridge cleanup                            # Maintenance
```

## MIGRATION FROM OLD TOOLS

### Replace `ai-team connect`
```bash
# ❌ OLD (deprecated)
ai-team connect frontend backend "API coordination"

# ✅ NEW
ai-bridge connect frontend backend "API coordination"
```

### Replace `bridge_registry.py`
```bash
# ❌ OLD (still works but verbose)
bridge_registry.py create frontend backend "API coordination"

# ✅ NEW (streamlined)
ai-bridge connect frontend backend "API coordination"
```

### Replace scattered `send-to-peer-*.sh`
```bash
# ❌ OLD (confusing per-session scripts)
send-to-peer-backend.sh "message"

# ✅ NEW (universal command)
ai-bridge send backend "message"
```

## BACKWARDS COMPATIBILITY

- `bridge_registry.py` **still works** (powers the new system)
- `ai-team-connect.py` shows **deprecation warning**
- Old `send-to-peer-*.sh` scripts **redirect to new system**

## USER TRANSITION STRATEGY

1. **Immediate**: Use `ai-bridge` for all new coordination
2. **Gradual**: Old commands show migration hints
3. **Seamless**: No breaking changes to existing bridges

## INSTALLATION INTEGRATION

For `install.sh`:
```bash
# Install unified interface
cp ai-bridge /usr/local/bin/
chmod +x /usr/local/bin/ai-bridge

# Set up deprecation warnings
echo "⚠️  ai-team connect is deprecated. Use: ai-bridge connect" > ~/.ai-team-deprecated
```

## DELIVERY IMPACT: ZERO DISRUPTION

- ✅ Existing bridges continue working
- ✅ Old commands show helpful migration messages
- ✅ New users get simple, consistent interface
- ✅ Zero breaking changes

## ARCHITECTURAL CLEANUP ACHIEVED

**Before:** Chaos
- `ai-team-connect.py` (10KB, single-bridge)
- `bridge_registry.py` (14KB, multi-bridge)
- `send-to-peer-*.sh` (scattered scripts)

**After:** Clean
- `ai-bridge` (unified interface)
- `bridge_registry.py` (backend engine)
- Clear deprecation path

## SUCCESS METRICS

- **User Confusion**: Eliminated (one command)
- **Maintenance Hell**: Solved (unified codebase)
- **Installation Complexity**: Reduced (single tool)
- **Backwards Compatibility**: Preserved (zero breakage)

This is **pragmatic architecture cleanup** that enables delivery without disruption! 🚀
