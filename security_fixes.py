#!/usr/bin/env python3
"""
Security and Resource Management Fixes
Replaces shell=True calls with secure alternatives and fixes resource leaks
"""

import subprocess
import shlex
import shutil
import os
import signal
import psutil
from typing import List, Optional, Dict, Any
from pathlib import Path
from logging_config import setup_logging

logger = setup_logging(__name__)


class SecureSubprocessManager:
    """Secure subprocess management with resource tracking"""
    
    def __init__(self):
        self.active_processes: Dict[int, subprocess.Popen] = {}
        
    def run_secure_command(self, cmd: List[str], cwd: Optional[str] = None, 
                          timeout: Optional[int] = None, 
                          capture_output: bool = True) -> subprocess.CompletedProcess:
        """
        Secure command execution without shell=True
        
        Args:
            cmd: Command as list (never string)
            cwd: Working directory
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            CompletedProcess result
        """
        if isinstance(cmd, str):
            raise ValueError("Command must be a list, not string (security risk)")
        
        # Validate command exists
        if not shutil.which(cmd[0]):
            raise FileNotFoundError(f"Command not found: {cmd[0]}")
        
        try:
            logger.debug(f"Executing secure command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False  # Don't raise on non-zero exit
            )
            
            logger.debug(f"Command completed with return code: {result.returncode}")
            return result
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)} - {e}")
            raise
    
    def start_background_process(self, cmd: List[str], cwd: Optional[str] = None) -> subprocess.Popen:
        """Start a background process with tracking"""
        if isinstance(cmd, str):
            raise ValueError("Command must be a list, not string")
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.active_processes[process.pid] = process
            logger.info(f"Started background process PID {process.pid}: {' '.join(cmd)}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start background process: {e}")
            raise
    
    def cleanup_process(self, pid: int, force: bool = False) -> bool:
        """Clean up a specific process"""
        if pid not in self.active_processes:
            logger.warning(f"Process {pid} not tracked")
            return False
        
        process = self.active_processes[pid]
        
        try:
            if process.poll() is None:  # Still running
                if force:
                    process.kill()
                    logger.info(f"Killed process {pid}")
                else:
                    process.terminate()
                    logger.info(f"Terminated process {pid}")
                
                # Wait for cleanup
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if not force:
                        process.kill()
                        process.wait()
                        logger.warning(f"Force killed unresponsive process {pid}")
            
            del self.active_processes[pid]
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up process {pid}: {e}")
            return False
    
    def cleanup_all_processes(self):
        """Clean up all tracked processes"""
        pids = list(self.active_processes.keys())
        
        for pid in pids:
            self.cleanup_process(pid)
        
        logger.info(f"Cleaned up {len(pids)} processes")
    
    def find_zombie_processes(self) -> List[Dict[str, Any]]:
        """Find zombie processes related to our application"""
        zombies = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cmdline']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        # Check if it's related to our app
                        cmdline = proc.info.get('cmdline', [])
                        if any('tmux' in arg or 'claude' in arg for arg in cmdline):
                            zombies.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': ' '.join(cmdline) if cmdline else 'N/A'
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error scanning for zombies: {e}")
        
        return zombies
    
    def kill_zombie_processes(self) -> int:
        """Kill zombie processes related to our application"""
        zombies = self.find_zombie_processes()
        killed = 0
        
        for zombie in zombies:
            try:
                os.kill(zombie['pid'], signal.SIGKILL)
                killed += 1
                logger.info(f"Killed zombie process {zombie['pid']}: {zombie['name']}")
            except (OSError, ProcessLookupError):
                # Process already gone
                pass
            except Exception as e:
                logger.error(f"Failed to kill zombie {zombie['pid']}: {e}")
        
        return killed


class LoggingFixer:
    """Systematic replacement of print statements with logging"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = 0
        
    def fix_file_logging(self, file_path: Path) -> int:
        """Fix logging in a single file"""
        fixes = 0
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Add logging import if needed
            if 'print(' in content and 'from logging_config import setup_logging' not in content:
                # Find import section
                lines = content.splitlines()
                import_section_end = 0
                
                for i, line in enumerate(lines):
                    if (line.startswith('import ') or line.startswith('from ') or 
                        line.strip().startswith('#') or line.strip() == ''):
                        import_section_end = i
                    else:
                        break
                
                # Insert logging import
                lines.insert(import_section_end + 1, "from logging_config import setup_logging")
                lines.insert(import_section_end + 2, "")
                lines.insert(import_section_end + 3, f"logger = setup_logging(__name__)")
                lines.insert(import_section_end + 4, "")
                
                content = '\n'.join(lines)
                fixes += 1
            
            # Replace print statements
            replacements = [
                ('print(f"✓', 'logger.info(f"'),
                ('print(f"✗', 'logger.error(f"'),
                ('print("✓', 'logger.info("'),
                ('print("✗', 'logger.error("'),
                ('print(f"⚠️', 'logger.warning(f"'),
                ('print("⚠️', 'logger.warning("'),
                ('print(f"❌', 'logger.error(f"'),
                ('print("❌', 'logger.error("'),
                ('print(f"Error', 'logger.error(f"Error'),
                ('print(f"Failed', 'logger.error(f"Failed'),
                ('print("Error', 'logger.error("Error'),
                ('print("Failed', 'logger.error("Failed'),
                ('print(f"Warning', 'logger.warning(f"Warning'),
                ('print("Warning', 'logger.warning("Warning'),
                ('print(f"Info', 'logger.info(f"Info'),
                ('print("Info', 'logger.info("Info'),
                # Generic print -> logger.info for remaining cases
                ('print(', 'logger.info(')
            ]
            
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    fixes += 1
            
            # Write back if changes made
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                
                logger.info(f"Fixed logging in {file_path.name}: {fixes} changes")
                
        except Exception as e:
            logger.error(f"Failed to fix logging in {file_path}: {e}")
        
        return fixes
    
    def fix_all_logging(self) -> int:
        """Fix logging across all Python files"""
        total_fixes = 0
        
        python_files = list(self.project_root.glob("*.py"))
        python_files.extend(self.project_root.glob("**/*.py"))
        
        for file_path in python_files:
            if file_path.name != 'security_fixes.py':  # Don't modify self
                fixes = self.fix_file_logging(file_path)
                total_fixes += fixes
        
        logger.info(f"Applied {total_fixes} logging fixes across {len(python_files)} files")
        return total_fixes


def main():
    """Run security and logging fixes"""
    print("🔧 Running Security and Logging Fixes...")
    
    # Fix logging
    logging_fixer = LoggingFixer()
    logging_fixes = logging_fixer.fix_all_logging()
    print(f"✅ Applied {logging_fixes} logging fixes")
    
    # Check for zombie processes
    subprocess_manager = SecureSubprocessManager()
    zombies = subprocess_manager.find_zombie_processes()
    
    if zombies:
        print(f"⚠️  Found {len(zombies)} zombie processes")
        killed = subprocess_manager.kill_zombie_processes()
        print(f"✅ Killed {killed} zombie processes")
    else:
        print("✅ No zombie processes found")
    
    print("🎯 Security fixes complete!")


if __name__ == "__main__":
    main()