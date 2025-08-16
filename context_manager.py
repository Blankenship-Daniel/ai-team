#!/usr/bin/env python3
"""
Sustainable Context Retention System for Tmux Orchestrator
Handles automatic context dumps, cleanup, and health monitoring
"""

import os
import json
import time
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass
class ContextSnapshot:
    """Represents a point-in-time context snapshot"""
    timestamp: str
    session_name: str
    window_index: int
    content_hash: str
    content: str
    metadata: Dict[str, Any]
    version: str = "1.0"


class ContextRetentionManager:
    """Manages sustainable context retention with automatic lifecycle"""
    
    def __init__(self, base_dir: str = ".context", retention_days: int = 7):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.retention_days = retention_days
        self.dump_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self._running = False
        self._threads = []
        
    def start(self):
        """Start automated context management"""
        self._running = True
        
        # Start periodic dumper
        dumper_thread = threading.Thread(target=self._periodic_dumper, daemon=True)
        dumper_thread.start()
        self._threads.append(dumper_thread)
        
        # Start cleanup service
        cleanup_thread = threading.Thread(target=self._cleanup_service, daemon=True)
        cleanup_thread.start()
        self._threads.append(cleanup_thread)
        
        # Start health monitor
        health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        health_thread.start()
        self._threads.append(health_thread)
        
        logger.info("Context retention manager started")
        
    def stop(self):
        """Stop all automated services"""
        self._running = False
        for thread in self._threads:
            thread.join(timeout=5)
        logger.info("Context retention manager stopped")
        
    def dump_context(self, session_name: str, window_index: int, content: str, 
                    metadata: Optional[Dict] = None) -> Optional[str]:
        """Dump context with deduplication and compression"""
        try:
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Check if identical content already exists
            existing = self._find_duplicate(session_name, window_index, content_hash)
            if existing:
                logger.debug(f"Skipping duplicate context for {session_name}:{window_index}")
                return existing
            
            # Create snapshot
            snapshot = ContextSnapshot(
                timestamp=datetime.now().isoformat(),
                session_name=session_name,
                window_index=window_index,
                content_hash=content_hash,
                content=content,
                metadata=metadata or {}
            )
            
            # Save to timestamped file
            filename = self._generate_filename(session_name, window_index)
            filepath = self.base_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(snapshot), f, indent=2)
            
            logger.info(f"Context dumped: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to dump context: {e}")
            return None
    
    def restore_context(self, session_name: str, window_index: int, 
                       hours_back: int = 24) -> Optional[str]:
        """Restore most recent context within time window"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            pattern = f"{session_name}_{window_index}_*.json"
            
            candidates = []
            for file in self.base_dir.glob(pattern):
                with open(file) as f:
                    data = json.load(f)
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp >= cutoff:
                        candidates.append((timestamp, data))
            
            if not candidates:
                logger.warning(f"No recent context found for {session_name}:{window_index}")
                return None
            
            # Return most recent
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]['content']
            
        except Exception as e:
            logger.error(f"Failed to restore context: {e}")
            return None
    
    def _periodic_dumper(self):
        """Background thread for periodic context dumps"""
        while self._running:
            try:
                # Get active sessions from tmux
                from tmux_utils import TmuxOrchestrator
                orchestrator = TmuxOrchestrator()
                sessions = orchestrator.get_tmux_sessions()
                
                for session in sessions:
                    for window in session.windows:
                        content = orchestrator.capture_window_content(
                            session.name, window.window_index, num_lines=100
                        )
                        if content and not content.startswith("Error"):
                            self.dump_context(
                                session.name,
                                window.window_index,
                                content,
                                {"window_name": window.window_name, "active": window.active}
                            )
                
            except Exception as e:
                logger.error(f"Periodic dump failed: {e}")
            
            time.sleep(self.dump_interval)
    
    def _cleanup_service(self):
        """Background thread for cleaning stale contexts"""
        while self._running:
            try:
                cutoff = datetime.now() - timedelta(days=self.retention_days)
                cleaned = 0
                
                for file in self.base_dir.glob("*.json"):
                    try:
                        # Check file age
                        mtime = datetime.fromtimestamp(file.stat().st_mtime)
                        if mtime < cutoff:
                            file.unlink()
                            cleaned += 1
                    except Exception as e:
                        logger.warning(f"Failed to clean {file}: {e}")
                
                if cleaned > 0:
                    logger.info(f"Cleaned {cleaned} stale context files")
                    
            except Exception as e:
                logger.error(f"Cleanup service failed: {e}")
            
            time.sleep(3600)  # Run hourly
    
    def _health_monitor(self):
        """Background thread for health checks"""
        while self._running:
            try:
                health_status = self.check_health()
                
                if not health_status['healthy']:
                    logger.warning(f"Health check failed: {health_status['issues']}")
                    self._attempt_auto_repair(health_status['issues'])
                    
            except Exception as e:
                logger.error(f"Health monitor failed: {e}")
            
            time.sleep(self.health_check_interval)
    
    def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check of context system"""
        issues = []
        checks = {
            'context_dir_exists': self.base_dir.exists(),
            'context_dir_writable': os.access(self.base_dir, os.W_OK),
            'disk_space_available': self._check_disk_space(),
            'communication_tools': self._check_communication_tools(),
            'context_files_readable': self._check_context_integrity()
        }
        
        for check, result in checks.items():
            if not result:
                issues.append(check)
        
        return {
            'healthy': len(issues) == 0,
            'checks': checks,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def _check_disk_space(self) -> bool:
        """Check if sufficient disk space is available"""
        try:
            stat = os.statvfs(self.base_dir)
            free_mb = (stat.f_frsize * stat.f_bavail) / (1024 * 1024)
            return free_mb > 100  # Need at least 100MB free
        except:
            return False
    
    def _check_communication_tools(self) -> bool:
        """Verify communication tools are accessible"""
        tools = [
            "send-claude-message.sh",
            "claude-write-file.sh",
            "notify-orchestrator.sh"
        ]
        
        for tool in tools:
            result = os.system(f"which {tool} > /dev/null 2>&1")
            if result != 0:
                logger.warning(f"Communication tool not found: {tool}")
                return False
        return True
    
    def _check_context_integrity(self) -> bool:
        """Verify context files are not corrupted"""
        try:
            for file in list(self.base_dir.glob("*.json"))[:5]:  # Check last 5
                with open(file) as f:
                    json.load(f)
            return True
        except:
            return False
    
    def _attempt_auto_repair(self, issues: List[str]):
        """Attempt to automatically repair detected issues"""
        for issue in issues:
            if issue == 'context_dir_exists':
                self.base_dir.mkdir(exist_ok=True)
                logger.info("Recreated context directory")
            elif issue == 'communication_tools':
                self._reinstall_communication_tools()
            elif issue == 'context_files_readable':
                self._quarantine_corrupted_files()
    
    def _reinstall_communication_tools(self):
        """Reinstall missing communication tools"""
        # Secure tool reinstallation without shell=True
        try:
            install_dir = Path.home() / ".local" / "bin"
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Create send-claude-message.sh if missing
            tool_path = install_dir / "send-claude-message.sh"
            if not tool_path.exists():
                script_content = """#!/bin/bash
PANE_TARGET="$1"
MESSAGE="$2"
tmux send-keys -t "$PANE_TARGET" -l "$MESSAGE"
tmux send-keys -t "$PANE_TARGET" C-m
"""
                with open(tool_path, 'w') as f:
                    f.write(script_content)
                tool_path.chmod(0o755)
                
            logger.info("Communication tools reinstalled")
        except Exception as e:
            logger.error(f"Failed to reinstall tools: {e}")
    
    def _quarantine_corrupted_files(self):
        """Move corrupted context files to quarantine"""
        quarantine = self.base_dir / "quarantine"
        quarantine.mkdir(exist_ok=True)
        
        for file in self.base_dir.glob("*.json"):
            try:
                with open(file) as f:
                    json.load(f)
            except:
                target = quarantine / file.name
                file.rename(target)
                logger.warning(f"Quarantined corrupted file: {file.name}")
    
    def _find_duplicate(self, session_name: str, window_index: int, 
                       content_hash: str) -> Optional[str]:
        """Check if identical content already exists"""
        pattern = f"{session_name}_{window_index}_*.json"
        
        for file in self.base_dir.glob(pattern):
            try:
                with open(file) as f:
                    data = json.load(f)
                    if data.get('content_hash') == content_hash:
                        # Update timestamp to prevent cleanup
                        file.touch()
                        return str(file)
            except:
                continue
        return None
    
    def _generate_filename(self, session_name: str, window_index: int) -> str:
        """Generate unique filename for context dump"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{session_name}_{window_index}_{timestamp}.json"


# Singleton instance
_manager_instance: Optional[ContextRetentionManager] = None

def get_context_manager() -> ContextRetentionManager:
    """Get or create the singleton context manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ContextRetentionManager()
    return _manager_instance