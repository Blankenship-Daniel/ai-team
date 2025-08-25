#!/usr/bin/env python3
"""
Bridge Registry - Multi-bridge coordination management
Supports multiple simultaneous bridges with cleanup
"""

import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class BridgeRegistry:
    """Manages multiple coordination bridges and cleanup"""

    def __init__(self, coord_dir: str = ".ai-coordination"):
        self.coord_dir = Path(coord_dir)
        self.registry_dir = self.coord_dir / "registry"
        self.bridges_dir = self.registry_dir / "bridges"
        self.sessions_dir = self.registry_dir / "sessions"
        self.messages_dir = self.coord_dir / "messages"
        self.cleanup_dir = self.coord_dir / "cleanup"

        # Create directory structure
        self._setup_directories()

    def _setup_directories(self):
        """Create the multi-bridge directory structure"""
        dirs = [
            self.coord_dir,
            self.registry_dir,
            self.bridges_dir,
            self.sessions_dir,
            self.messages_dir,
            self.cleanup_dir,
        ]

        for directory in dirs:
            directory.mkdir(exist_ok=True)

    def create_bridge(self, session1: str, session2: str, context: str) -> str:
        """Create a new bridge between two sessions"""
        bridge_id = f"bridge-{uuid.uuid4().hex[:12]}"

        bridge_config = {
            "bridge_id": bridge_id,
            "session1": session1,
            "session2": session2,
            "coordination_context": context,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "last_activity": datetime.now().isoformat(),
        }

        # Write bridge config
        bridge_file = self.bridges_dir / f"{bridge_id}.json"
        with open(bridge_file, "w") as f:
            json.dump(bridge_config, f, indent=2)

        # Update session mappings
        self._add_session_to_bridge(session1, bridge_id)
        self._add_session_to_bridge(session2, bridge_id)

        # Create message directory for this bridge
        bridge_msg_dir = self.messages_dir / bridge_id
        bridge_msg_dir.mkdir(exist_ok=True)

        # Update active bridges index
        self._update_active_bridges()

        # Update legacy bridge_context.json for backwards compatibility
        self._update_legacy_config(bridge_config)

        print(f"✅ Bridge created: {bridge_id}")
        print(f"   {session1} ↔ {session2}")
        print(f"   Context: {context}")

        return bridge_id

    def _add_session_to_bridge(self, session: str, bridge_id: str):
        """Add a session to a bridge mapping"""
        session_file = self.sessions_dir / f"{session}.json"

        if session_file.exists():
            with open(session_file, "r") as f:
                session_data = json.load(f)
        else:
            session_data = {
                "session_name": session,
                "bridges": [],
                "created_at": datetime.now().isoformat(),
            }

        if bridge_id not in session_data["bridges"]:
            session_data["bridges"].append(bridge_id)
            session_data["last_updated"] = datetime.now().isoformat()

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    def _update_active_bridges(self):
        """Update the active bridges index"""
        active_bridges = []

        for bridge_file in self.bridges_dir.glob("*.json"):
            try:
                with open(bridge_file, "r") as f:
                    bridge_data = json.load(f)

                if bridge_data.get("status") == "active":
                    active_bridges.append(
                        {
                            "bridge_id": bridge_data["bridge_id"],
                            "session1": bridge_data["session1"],
                            "session2": bridge_data["session2"],
                            "context": bridge_data["coordination_context"],
                            "created_at": bridge_data["created_at"],
                            "last_activity": bridge_data.get("last_activity", bridge_data["created_at"]),
                        }
                    )
            except Exception as e:
                print(f"⚠️  Warning: Could not read bridge file {bridge_file}: {e}")

        index_file = self.registry_dir / "active-bridges.json"
        with open(index_file, "w") as f:
            json.dump(
                {
                    "active_bridges": active_bridges,
                    "total_bridges": len(active_bridges),
                    "last_updated": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

    def _update_legacy_config(self, bridge_config: Dict):
        """Update legacy bridge_context.json for backwards compatibility"""
        legacy_file = self.coord_dir / "bridge_context.json"
        with open(legacy_file, "w") as f:
            json.dump(
                {
                    "session1": bridge_config["session1"],
                    "session2": bridge_config["session2"],
                    "coordination_context": bridge_config["coordination_context"],
                    "created_at": bridge_config["created_at"],
                    "bridge_id": bridge_config["bridge_id"],
                    "_note": "Legacy compatibility - use bridge registry for multi-bridge support",
                },
                f,
                indent=2,
            )

    def list_bridges(self) -> List[Dict]:
        """List all active bridges"""
        index_file = self.registry_dir / "active-bridges.json"

        if not index_file.exists():
            self._update_active_bridges()

        with open(index_file, "r") as f:
            data = json.load(f)

        active_bridges: List[Dict] = data.get("active_bridges", [])
        return active_bridges

    def get_session_bridges(self, session: str) -> List[str]:
        """Get all bridges a session participates in"""
        session_file = self.sessions_dir / f"{session}.json"

        if not session_file.exists():
            return []

        with open(session_file, "r") as f:
            session_data = json.load(f)

        bridges: List[str] = session_data.get("bridges", [])
        return bridges

    def find_peer_sessions(self, session: str) -> List[Tuple[str, str]]:
        """Find all peer sessions for a given session"""
        peers = []
        bridges = self.get_session_bridges(session)

        for bridge_id in bridges:
            bridge_file = self.bridges_dir / f"{bridge_id}.json"
            if bridge_file.exists():
                with open(bridge_file, "r") as f:
                    bridge_data = json.load(f)

                if bridge_data["session1"] == session:
                    peers.append((bridge_data["session2"], bridge_id))
                elif bridge_data["session2"] == session:
                    peers.append((bridge_data["session1"], bridge_id))

        return peers

    def cleanup_old_bridges(self, max_age_days: int = 7, dry_run: bool = False) -> Dict[str, Any]:
        """Clean up old bridges and messages"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        cleanup_stats: Dict[str, Any] = {
            "bridges_removed": 0,
            "messages_removed": 0,
            "space_freed": 0,
            "errors": [],
        }

        # Find old bridges
        for bridge_file in self.bridges_dir.glob("*.json"):
            try:
                with open(bridge_file, "r") as f:
                    bridge_data = json.load(f)

                last_activity = datetime.fromisoformat(bridge_data.get("last_activity", bridge_data["created_at"]))

                if last_activity < cutoff_time:
                    bridge_id = bridge_data["bridge_id"]

                    if not dry_run:
                        # Remove bridge config
                        bridge_file.unlink()

                        # Remove message directory
                        msg_dir = self.messages_dir / bridge_id
                        if msg_dir.exists():
                            for msg_file in msg_dir.glob("*.json"):
                                cleanup_stats["space_freed"] += msg_file.stat().st_size
                                msg_file.unlink()
                                cleanup_stats["messages_removed"] += 1
                            msg_dir.rmdir()

                        # Update session mappings
                        self._remove_bridge_from_sessions(bridge_id)

                    cleanup_stats["bridges_removed"] += 1
                    print(f"🗑️  {'Would remove' if dry_run else 'Removed'} old bridge: {bridge_id}")

            except Exception as e:
                cleanup_stats["errors"].append(f"Error processing {bridge_file}: {e}")

        if not dry_run:
            # Update active bridges index
            self._update_active_bridges()

            # Record cleanup
            cleanup_log = self.cleanup_dir / "last-cleanup.json"
            with open(cleanup_log, "w") as f:
                json.dump(
                    {
                        "cleanup_time": datetime.now().isoformat(),
                        "max_age_days": max_age_days,
                        "stats": cleanup_stats,
                    },
                    f,
                    indent=2,
                )

        return cleanup_stats

    def _remove_bridge_from_sessions(self, bridge_id: str):
        """Remove bridge from all session mappings"""
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)

                if bridge_id in session_data.get("bridges", []):
                    session_data["bridges"].remove(bridge_id)
                    session_data["last_updated"] = datetime.now().isoformat()

                    with open(session_file, "w") as f:
                        json.dump(session_data, f, indent=2)

            except Exception as e:
                print(f"⚠️  Warning: Could not update session file {session_file}: {e}")


def show_help():
    """Display comprehensive CLI help with examples"""
    print(
        """🔗 Bridge Registry - Multi-Team Coordination Manager

USAGE:
    bridge_registry.py <command> [options]

COMMANDS:
    create <session1> <session2> "<context>"     Create bridge between sessions
    list                                         List all active bridges
    cleanup [--dry-run] [--max-age-days N]     Clean up old bridges (default: 7 days)
    status <session>                            Show bridges for a session
    help                                        Show this help

PRACTICAL EXAMPLES:
    # 🚀 QUICK START - Connect two teams
    bridge_registry.py create frontend-team backend-team "API coordination"

    # 📋 See all active bridges
    bridge_registry.py list

    # 🔍 Check what bridges a team has
    bridge_registry.py status mobile-team

    # 🧹 Clean up old bridges (safe mode first!)
    bridge_registry.py cleanup --dry-run --max-age-days 3
    bridge_registry.py cleanup --max-age-days 3

COORDINATION WORKFLOW:
    1. 🔗 Create:    bridge_registry.py create team-a team-b "shared context"
    2. 📤 Send:      send-to-peer-team-a.sh "Hello team-b!"
    3. 📥 Check:     check-peer-messages.sh
    4. 📊 Monitor:   bridge_registry.py status team-a
    5. 🧹 Cleanup:   bridge_registry.py cleanup --dry-run

REAL-WORLD USE CASES:
    • Mobile ↔ Web teams coordinating UI consistency
    • Frontend ↔ Backend teams syncing API changes
    • DevOps ↔ Security teams sharing deployment info
    • Research ↔ Production teams transferring models

FILES CREATED:
    .ai-coordination/registry/         Bridge registry and session tracking
    send-to-peer-<session>.sh         Message sending scripts
    check-peer-messages.sh             Message checking script
    bridge-status.sh                   Bridge status script
"""
    )


class BridgeRegistryArgumentParser:
    """Handles CLI argument parsing for bridge registry commands"""
    
    def parse_args(self, args):
        """Parse command line arguments into structured command data"""
        if len(args) < 2 or args[1] in ["help", "--help", "-h"]:
            return {"command": "help"}
        
        command = args[1]
        
        if command == "create" and len(args) >= 5:
            return {
                "command": "create",
                "session1": args[2],
                "session2": args[3], 
                "context": " ".join(args[4:])
            }
        elif command == "list":
            return {"command": "list"}
        elif command == "cleanup":
            dry_run = "--dry-run" in args
            max_age = 7
            if "--max-age-days" in args:
                idx = args.index("--max-age-days")
                if idx + 1 < len(args):
                    max_age = int(args[idx + 1])
            return {
                "command": "cleanup",
                "dry_run": dry_run,
                "max_age": max_age
            }
        elif command == "status" and len(args) >= 3:
            return {
                "command": "status",
                "session": args[2]
            }
        else:
            return {
                "command": "unknown",
                "provided": command
            }


class BridgeRegistryCommandHandler:
    """Handles execution of bridge registry commands"""
    
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, command_data):
        """Execute a parsed command and return result"""
        command = command_data["command"]
        
        if command == "help":
            return self._handle_help()
        elif command == "create":
            return self._handle_create(command_data)
        elif command == "list":
            return self._handle_list()
        elif command == "cleanup":
            return self._handle_cleanup(command_data)
        elif command == "status":
            return self._handle_status(command_data)
        else:
            return self._handle_unknown(command_data)
    
    def _handle_help(self):
        show_help()
        return {"exit_code": 0}
    
    def _handle_create(self, data):
        bridge_id = self.registry.create_bridge(data["session1"], data["session2"], data["context"])
        return {"exit_code": 0, "bridge_id": bridge_id}
    
    def _handle_list(self):
        bridges = self.registry.list_bridges()
        print(f"📋 Active Bridges ({len(bridges)}):")
        for bridge in bridges:
            print(f"  🔗 {bridge['bridge_id']}")
            print(f"     {bridge['session1']} ↔ {bridge['session2']}")
            print(f"     Context: {bridge['context']}")
            print(f"     Created: {bridge['created_at']}")
            print()
        return {"exit_code": 0}
    
    def _handle_cleanup(self, data):
        stats = self.registry.cleanup_old_bridges(data["max_age"], data["dry_run"])
        print(f"🗑️  Cleanup {'(DRY RUN)' if data['dry_run'] else 'COMPLETED'}:")
        print(f"   Bridges removed: {stats['bridges_removed']}")
        print(f"   Messages removed: {stats['messages_removed']}")
        print(f"   Space freed: {stats['space_freed']} bytes")
        if stats["errors"]:
            print(f"   Errors: {len(stats['errors'])}")
        return {"exit_code": 0}
    
    def _handle_status(self, data):
        session = data["session"]
        peers = self.registry.find_peer_sessions(session)
        print(f"📍 Session '{session}' bridges:")
        for peer, bridge_id in peers:
            print(f"   {session} ↔ {peer} (via {bridge_id})")
        return {"exit_code": 0}
    
    def _handle_unknown(self, data):
        print(f"❌ Unknown command: '{data['provided']}'")
        print("\n💡 Try: bridge_registry.py help")
        print('🚀 Quick start: bridge_registry.py create team1 team2 "coordination context"')
        return {"exit_code": 1}


def main():
    """CLI entry point - now follows Command pattern with SRP"""
    parser = BridgeRegistryArgumentParser()
    command_data = parser.parse_args(sys.argv)
    
    registry = BridgeRegistry()
    handler = BridgeRegistryCommandHandler(registry)
    
    result = handler.execute(command_data)
    sys.exit(result.get("exit_code", 0))


if __name__ == "__main__":
    main()
