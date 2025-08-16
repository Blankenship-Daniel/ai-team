#!/usr/bin/env python3
"""
AI Team Connect - DEPRECATED - Use 'ai-bridge' instead
Usage: ai-team connect <session1> <session2> "coordination context"

⚠️  DEPRECATION NOTICE: This tool is deprecated. Use 'ai-bridge' instead.
"""

# Show deprecation warning and redirect to new tool
import sys
import subprocess


def show_deprecation_warning():
    """Show deprecation warning with migration guidance"""
    print(
        """⚠️  DEPRECATION WARNING: ai-team-connect is deprecated

🚀 PLEASE USE THE NEW UNIFIED TOOL:
   OLD: ai-team connect team1 team2 "context"
   NEW: ai-bridge connect team1 team2 "context"

✅ Benefits of ai-bridge:
   • Unified interface for all coordination
   • Better error handling and validation
   • Enhanced messaging and status features
   • Consistent with modern tooling

💡 Migration is seamless - same functionality, better UX!
"""
    )


if len(sys.argv) > 1 and sys.argv[1] == "connect":
    show_deprecation_warning()
    print("🔄 Redirecting to ai-bridge...\n")

    # Redirect to new tool with same arguments
    new_args = ["ai-bridge"] + sys.argv[1:]
    try:
        subprocess.run(new_args, check=False)
    except FileNotFoundError:
        print("❌ ai-bridge not found. Please install the unified bridge tools.")
        print("💡 Installation: Copy ai-bridge to your PATH")
    sys.exit(0)

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from security_validator import SecurityValidator
from logging_config import setup_logging

logger = setup_logging(__name__)


class OrchestrationBridge:
    """Handles communication between two orchestrator panes"""

    def __init__(self, session1: str, session2: str, coordination_context: str):
        self.session1 = session1
        self.session2 = session2
        self.coordination_context = coordination_context
        self.orchestrator_pane1 = f"{session1}:0.0"
        self.orchestrator_pane2 = f"{session2}:0.0"

        # Create coordination directory
        self.coord_dir = Path(".ai-coordination")
        self.coord_dir.mkdir(exist_ok=True)
        (self.coord_dir / "messages").mkdir(exist_ok=True)

        logger.info(f"Bridge initialized: {session1} <-> {session2}")

    def validate_sessions(self) -> bool:
        """Validate both tmux sessions exist"""
        for session in [self.session1, self.session2]:
            valid, error = SecurityValidator.validate_session_name(session)
            if not valid:
                print(f"❌ Invalid session name '{session}': {error}")
                return False

            try:
                subprocess.run(["tmux", "has-session", "-t", session], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print(f"❌ Session '{session}' not found")
                return False

        return True

    def create_bridge_context(self):
        """Create coordination context for both orchestrators"""
        bridge_context = {
            "session1": self.session1,
            "session2": self.session2,
            "coordination_context": self.coordination_context,
            "created_at": datetime.now().isoformat(),
            "bridge_id": f"bridge-{int(time.time() * 1000)}",
        }

        with open(self.coord_dir / "bridge_context.json", "w") as f:
            json.dump(bridge_context, f, indent=2)

        return bridge_context

    def inject_coordination_context(self, session: str, peer_session: str):
        """Inject coordination awareness into an orchestrator"""

        coordination_message = f"""
🔗 MULTI-TEAM COORDINATION ESTABLISHED

You are now connected to another AI team for coordination:
- **Your session**: {session}
- **Peer session**: {peer_session}
- **Coordination context**: {self.coordination_context}

**COMMUNICATION PROTOCOL:**
- Use 'send-to-peer' to message the other orchestrator
- Use 'check-peer-messages' to read messages from peer
- Coordinate high-level strategy, then delegate to your agents

**YOUR ROLE AS BRIDGE ORCHESTRATOR:**
1. Coordinate with peer orchestrator on: {self.coordination_context}
2. Break down coordination into tasks for your team
3. Share progress and blockers with peer
4. Resolve conflicts through discussion

**AVAILABLE COMMANDS:**
- send-to-peer "message" - Send message to {peer_session} orchestrator
- check-peer-messages - Read messages from peer orchestrator
- bridge-status - Show coordination status

**EXAMPLE USAGE:**
send-to-peer "Our team is working on user authentication. What's your focus?"
check-peer-messages
bridge-status

Start by introducing your team and asking about their current focus.
"""

        # Send coordination context to orchestrator
        try:
            cmd = ["send-claude-message.sh", f"{session}:0.0", coordination_message]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Injected coordination context into {session}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inject context into {session}: {e}")

    def create_communication_commands(self):
        """Create communication helper commands"""

        # Command for session1 to send to session2
        send_to_peer_1 = f"""#!/bin/bash
# Send message from {self.session1} to {self.session2}
MESSAGE="$1"
MESSAGE_ID="{self.session1}-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${{MESSAGE_ID}}.json << EOF
{{
  "from_session": "{self.session1}",
  "to_session": "{self.session2}",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID"
}}
EOF
echo "✅ Message sent to {self.session2}: $MESSAGE"
tmux send-keys -t "{self.session2}:0.0" "📨 New message from {self.session1}: $(printf \'%q\' "$MESSAGE")" Enter
"""

        # Command for session2 to send to session1
        send_to_peer_2 = f"""#!/bin/bash
# Send message from {self.session2} to {self.session1}
MESSAGE="$1"
MESSAGE_ID="{self.session2}-$(date +%s%N | cut -c1-13)"
cat > .ai-coordination/messages/${{MESSAGE_ID}}.json << EOF
{{
  "from_session": "{self.session2}",
  "to_session": "{self.session1}",
  "message": "$MESSAGE",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "message_id": "$MESSAGE_ID"
}}
EOF
echo "✅ Message sent to {self.session1}: $MESSAGE"
tmux send-keys -t "{self.session1}:0.0" "📨 New message from {self.session2}: $(printf \'%q\' "$MESSAGE")" Enter
"""

        # Check messages command (generic)
        check_messages = """#!/bin/bash
# Check messages for current session
SESSION_NAME=$(tmux display-message -p '#{session_name}')
echo "📨 Messages for $SESSION_NAME:"
for msg in .ai-coordination/messages/*.json; do
    if [ -f "$msg" ]; then
        TO_SESSION=$(jq -r '.to_session' "$msg" 2>/dev/null)
        if [ "$TO_SESSION" = "$SESSION_NAME" ]; then
            FROM=$(jq -r '.from_session' "$msg")
            CONTENT=$(jq -r '.message' "$msg")
            TIME=$(jq -r '.timestamp' "$msg")
            echo "  📩 From $FROM at $TIME: $CONTENT"
        fi
    fi
done
"""

        # Bridge status command
        bridge_status = f"""#!/bin/bash
echo "🔗 Bridge Status:"
echo "  Session 1: {self.session1}"
echo "  Session 2: {self.session2}"
echo "  Context: {self.coordination_context}"
echo "  Coordination Dir: $(pwd)/.ai-coordination"
echo ""
echo "📊 Message Count:"
MSG_COUNT=$(find .ai-coordination/messages -name "*.json" 2>/dev/null | wc -l)
echo "  Total messages: $MSG_COUNT"
"""

        # Write command files
        with open(f"send-to-peer-{self.session1}.sh", "w") as f:
            f.write(send_to_peer_1)
        with open(f"send-to-peer-{self.session2}.sh", "w") as f:
            f.write(send_to_peer_2)
        with open("check-peer-messages.sh", "w") as f:
            f.write(check_messages)
        with open("bridge-status.sh", "w") as f:
            f.write(bridge_status)

        # Make executable
        Path(f"send-to-peer-{self.session1}.sh").chmod(0o755)
        Path(f"send-to-peer-{self.session2}.sh").chmod(0o755)
        Path("check-peer-messages.sh").chmod(0o755)
        Path("bridge-status.sh").chmod(0o755)

    def establish_bridge(self):
        """Main method to establish the coordination bridge"""
        print("🔗 Establishing AI Team Coordination Bridge...")

        # Validate sessions
        if not self.validate_sessions():
            return False

        # Create bridge context
        bridge_context = self.create_bridge_context()
        print(f"✅ Bridge context created: {bridge_context['bridge_id']}")

        # Create communication commands
        self.create_communication_commands()
        print("✅ Communication commands created")

        # Inject coordination context into both orchestrators
        self.inject_coordination_context(self.session1, self.session2)
        self.inject_coordination_context(self.session2, self.session1)
        print("✅ Coordination context injected into both orchestrators")

        print(
            f"""
🎯 COORDINATION ESTABLISHED!

Your AI teams are now connected:
  📱 {self.session1} (Orchestrator pane 0.0)
  📱 {self.session2} (Orchestrator pane 0.0)

🎪 Coordination Context: {self.coordination_context}

🛠️  Communication Commands:
  ./send-to-peer-{self.session1}.sh "message"    # Send from {self.session1} to {self.session2}
  ./send-to-peer-{self.session2}.sh "message"    # Send from {self.session2} to {self.session1}
  ./check-peer-messages.sh                       # Check messages (run from either session)
  ./bridge-status.sh                             # Show bridge status

🚀 Example Usage:
  # From {self.session1}:
  ./send-to-peer-{self.session1}.sh "Our team is handling frontend. What's your focus?"

  # From {self.session2}:
  ./check-peer-messages.sh
  ./send-to-peer-{self.session2}.sh "We're building the API layer. Need frontend requirements."

The orchestrators will now coordinate and delegate tasks to their respective teams!
        """
        )

        return True


def main():
    parser = argparse.ArgumentParser(
        description="Connect two AI team sessions for coordination",
        epilog="""
Examples:
  ai-team connect frontend-team backend-team "Coordinate on user authentication system"
  ai-team connect service-a service-b "Share database schema and API contracts"
  ai-team connect research-team prod-team "Transfer ML model from research to production"
        """,
    )

    parser.add_argument("session1", help="First tmux session name")
    parser.add_argument("session2", help="Second tmux session name")
    parser.add_argument("context", help="What they should coordinate on")

    args = parser.parse_args()

    # Create and establish bridge
    bridge = OrchestrationBridge(args.session1, args.session2, args.context)

    try:
        success = bridge.establish_bridge()
        if success:
            sys.exit(0)
        else:
            print("❌ Failed to establish coordination bridge")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Bridge establishment interrupted")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
