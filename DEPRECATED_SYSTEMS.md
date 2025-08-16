# ⚠️ DEPRECATED SYSTEMS - EMERGENCY CONSOLIDATION
*Legacy systems deprecated during architectural chaos cleanup*

## 🚨 DEPRECATION NOTICE

The following systems have been **DEPRECATED** as of $(date +%Y-%m-%d) due to architectural violations and redundancy:

### ❌ **ai-team-connect.py** (DEPRECATED)
**Reason**: Single-bridge legacy system incompatible with multi-bridge architecture
**Replacement**: `bridge_registry.py` with unified multi-bridge support
**Migration Path**: Use `bridge_registry.py create` instead of `ai-team connect`

```bash
# OLD (DEPRECATED):
python3 ai-team-connect.py connect team1 team2 "context"

# NEW (RECOMMENDED):
python3 bridge_registry.py create team1 team2 "context"
```

### ❌ **Legacy send-to-peer-* Scripts** (DEPRECATED)
**Reason**: Hardcoded session pairs violate DRY principle and dynamic routing
**Replacement**: Unified dynamic routing via bridge registry
**Scripts Deprecated**:
- `send-to-peer-snes-modder.sh`
- `send-to-peer-test-backend.sh`
- `send-to-peer-test-frontend.sh`
- `send-to-peer-test-fix1.sh`
- `send-to-peer-test-fix2.sh`
- `send-to-peer-bsnes.sh`

```bash
# OLD (DEPRECATED):
./send-to-peer-snes-modder.sh "message"

# NEW (RECOMMENDED):
./send-to-peer.sh snes-modder "message"  # Dynamic routing
```

### ❌ **bridge_context.json** (LEGACY COMPATIBILITY ONLY)
**Reason**: Single-bridge context incompatible with multi-bridge registry
**Replacement**: `.ai-coordination/registry/` with proper multi-bridge support
**Status**: Maintained for backward compatibility only

## 🔄 **MIGRATION GUIDE**

### For Users
1. **Stop using** `ai-team-connect.py` immediately
2. **Migrate** to `bridge_registry.py` commands
3. **Update scripts** to use dynamic routing instead of hardcoded peer scripts

### For Developers
1. **Remove dependencies** on deprecated systems
2. **Update documentation** to reference new bridge registry
3. **Test compatibility** with new unified system

## 📅 **DEPRECATION TIMELINE**

- **Immediate**: Mark systems as deprecated, add warnings
- **Week 1**: Update all documentation and examples
- **Week 2**: Remove deprecated scripts, keep stubs with migration messages
- **Week 3**: Complete removal of deprecated code
- **Week 4**: Clean up any remaining references

## ⚠️ **BREAKING CHANGES**

### Command Line Interface
```bash
# BREAKING: ai-team-connect.py commands will fail
# MIGRATION: Use bridge_registry.py equivalent commands

# BREAKING: Hardcoded send-to-peer-* scripts will be removed
# MIGRATION: Use dynamic send-to-peer.sh with session argument
```

### File Structure
```bash
# DEPRECATED: .ai-coordination/bridge_context.json (single bridge)
# REPLACEMENT: .ai-coordination/registry/ (multi-bridge support)
```

## 🛠️ **EMERGENCY CONSOLIDATION PLAN**

### Phase 1: Deprecation Warnings ✅
- Add deprecation warnings to all legacy systems
- Update documentation with migration paths
- Create this deprecation notice

### Phase 2: Unified Dynamic Routing
- Create unified `send-to-peer.sh` with dynamic routing
- Update `check-peer-messages.sh` for multi-bridge support
- Consolidate bridge status checking

### Phase 3: Legacy System Removal
- Replace deprecated scripts with migration stubs
- Remove legacy code while maintaining compatibility layers
- Update install.sh to only install modern systems

### Phase 4: Clean Architecture Verification
- Verify SOLID principles compliance
- Run comprehensive tests on unified system
- Document clean architecture patterns

---

## 📞 **SUPPORT**

If you encounter issues during migration:
1. Check the **ORCHESTRATOR_GUIDE.md** for updated commands
2. Use `bridge_registry.py help` for comprehensive examples
3. Report migration issues immediately for emergency fixes

---

*This deprecation notice is part of the systematic technical debt cleanup initiative.*
