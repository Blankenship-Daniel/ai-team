#!/usr/bin/env python3
"""
Automated Context Keeper - Run this as a daemon to maintain context health
"""

import sys
import time
import signal
from datetime import datetime
from context_manager import get_context_manager
from logging_config import setup_logging

logger = setup_logging(__name__)


class AutoContextKeeper:
    """Daemon process for maintaining context health"""

    def __init__(self):
        self.manager = get_context_manager()
        self.running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        logger.info(f"Received shutdown signal {signum}")
        self.running = False
        self.manager.stop()
        sys.exit(0)

    def run(self):
        """Main daemon loop"""
        logger.info("Starting Auto Context Keeper daemon")

        # Start the context manager
        self.manager.start()

        # Main monitoring loop
        while self.running:
            try:
                # Perform health check
                health = self.manager.check_health()

                # Log status every 5 minutes
                if int(time.time()) % 300 == 0:
                    logger.info(f"Context system health: {health['healthy']}")
                    if not health["healthy"]:
                        logger.warning(f"Issues detected: {health['issues']}")

                # Sleep for a bit
                time.sleep(10)

            except Exception as e:
                logger.error(f"Daemon error: {e}")
                time.sleep(30)  # Back off on errors

        logger.info("Auto Context Keeper daemon stopped")


def main():
    """Entry point for the daemon"""
    keeper = AutoContextKeeper()

    # Check if already running
    import os
    import tempfile

    # Use secure temporary directory
    pid_file = os.path.join(tempfile.gettempdir(), "auto_context_keeper.pid")

    if os.path.exists(pid_file):
        with open(pid_file) as f:
            old_pid = int(f.read())
            try:
                os.kill(old_pid, 0)
                print(f"Auto Context Keeper already running (PID: {old_pid})")
                sys.exit(1)
            except OSError:
                # Process doesn't exist, remove stale PID file
                os.remove(pid_file)

    # Write PID file
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    try:
        keeper.run()
    finally:
        # Clean up PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)


if __name__ == "__main__":
    main()
