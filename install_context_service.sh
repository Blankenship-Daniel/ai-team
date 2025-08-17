#!/bin/bash
"""
Installation script for Context Keeper service
Makes the system maintainable across environments
"""

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="tmux-context-keeper"
INSTALL_DIR="$HOME/.local/bin"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Installing Tmux Context Keeper service..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$SERVICE_DIR"

# Copy main scripts
cp "$SCRIPT_DIR/auto_context_keeper.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/context_manager.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/logging_config.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/auto_context_keeper.py"

# Create systemd service file
cat > "$SERVICE_DIR/$SERVICE_NAME.service" << EOF
[Unit]
Description=Tmux Context Keeper
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/auto_context_keeper.py
Restart=always
RestartSec=30
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$INSTALL_DIR:$SCRIPT_DIR

[Install]
WantedBy=default.target
EOF

# Create management script
cat > "$INSTALL_DIR/context-keeper-ctl" << 'EOF'
#!/bin/bash
SERVICE_NAME="tmux-context-keeper"

case "${1:-}" in
    start)
        systemctl --user start "$SERVICE_NAME"
        echo "Context keeper started"
        ;;
    stop)
        systemctl --user stop "$SERVICE_NAME"
        echo "Context keeper stopped"
        ;;
    restart)
        systemctl --user restart "$SERVICE_NAME"
        echo "Context keeper restarted"
        ;;
    status)
        systemctl --user status "$SERVICE_NAME"
        ;;
    enable)
        systemctl --user enable "$SERVICE_NAME"
        echo "Context keeper enabled for auto-start"
        ;;
    disable)
        systemctl --user disable "$SERVICE_NAME"
        echo "Context keeper disabled"
        ;;
    logs)
        journalctl --user -u "$SERVICE_NAME" -f
        ;;
    health)
        python3 -c "
from context_manager import get_context_manager
import json
health = get_context_manager().check_health()
print(json.dumps(health, indent=2))
"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|health}"
        exit 1
        ;;
esac
EOF

chmod +x "$INSTALL_DIR/context-keeper-ctl"

# Reload systemd and enable service
systemctl --user daemon-reload

echo "✓ Context Keeper service installed successfully!"
echo ""
echo "Usage:"
echo "  context-keeper-ctl start    # Start the service"
echo "  context-keeper-ctl enable   # Enable auto-start"
echo "  context-keeper-ctl status   # Check status"
echo "  context-keeper-ctl health   # Health check"
echo "  context-keeper-ctl logs     # View logs"
echo ""
echo "To start now: context-keeper-ctl start"
echo "To enable auto-start: context-keeper-ctl enable"
