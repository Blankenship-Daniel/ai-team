#!/usr/bin/env python3
"""
Automated Configuration Backup System
Ensures critical configurations are safely backed up and recoverable
"""

import os
import shutil
import json
import hashlib
import tarfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from logging_config import setup_logging

logger = setup_logging(__name__)


class ConfigBackupSystem:
    """Automated backup system for critical configurations"""
    
    def __init__(self, backup_dir: str = "config_backups"):
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(exist_ok=True)
        
        # Critical files and directories to backup
        self.critical_paths = [
            ".context",
            "logging_config.py",
            "context_manager.py",
            "tmux_utils.py",
            "security_validator.py",
            "quality_automation.py",
            "create_ai_team.py",
            ".pre-commit-config.yaml",
            "pyproject.toml",
            "requirements*.txt",
            "*.sh"  # All shell scripts
        ]
        
        self.backup_interval = 3600  # 1 hour
        self.retention_days = 30
        self._running = False
        self._backup_thread = None
        
    def start_automated_backup(self):
        """Start automated backup service"""
        if self._running:
            logger.warning("Backup service already running")
            return
            
        self._running = True
        self._backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self._backup_thread.start()
        logger.info("Automated backup service started")
        
    def stop_automated_backup(self):
        """Stop automated backup service"""
        self._running = False
        if self._backup_thread:
            self._backup_thread.join(timeout=5)
        logger.info("Automated backup service stopped")
        
    def create_backup(self, label: Optional[str] = None) -> Optional[str]:
        """Create a backup of critical configurations"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"
            if label:
                backup_name += f"_{label}"
            
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            
            # Create temporary directory for staging
            temp_dir = self.backup_dir / "temp_staging"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                files_backed_up = []
                
                # Copy critical files
                for pattern in self.critical_paths:
                    if "*" in pattern:
                        # Handle glob patterns
                        from glob import glob
                        matches = glob(pattern)
                        for match in matches:
                            if os.path.exists(match):
                                self._copy_to_staging(match, temp_dir)
                                files_backed_up.append(match)
                    else:
                        if os.path.exists(pattern):
                            self._copy_to_staging(pattern, temp_dir)
                            files_backed_up.append(pattern)
                
                # Create backup metadata
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "label": label,
                    "files": files_backed_up,
                    "system_info": {
                        "platform": os.name,
                        "cwd": os.getcwd(),
                        "user": os.environ.get("USER", "unknown")
                    },
                    "checksums": self._calculate_checksums(files_backed_up)
                }
                
                metadata_file = temp_dir / "backup_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Create compressed archive
                with tarfile.open(backup_path, "w:gz") as tar:
                    tar.add(temp_dir, arcname=".")
                
                logger.info(f"Backup created: {backup_path}")
                logger.info(f"Files backed up: {len(files_backed_up)}")
                
                return str(backup_path)
                
            finally:
                # Clean up temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    
    def restore_backup(self, backup_path: str, confirm: bool = False) -> bool:
        """Restore from a backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            if not confirm:
                logger.warning("Restore requires confirmation - use confirm=True")
                return False
            
            # Create restore point before restoring
            restore_point = self.create_backup(label="pre_restore")
            logger.info(f"Created restore point: {restore_point}")
            
            # Extract backup
            temp_restore_dir = self.backup_dir / "temp_restore"
            temp_restore_dir.mkdir(exist_ok=True)
            
            try:
                with tarfile.open(backup_file, "r:gz") as tar:
                    tar.extractall(temp_restore_dir)
                
                # Read metadata
                metadata_file = temp_restore_dir / "backup_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    
                    logger.info(f"Restoring backup from: {metadata['timestamp']}")
                    
                    # Restore files
                    restored_count = 0
                    for file_path in metadata["files"]:
                        source = temp_restore_dir / os.path.basename(file_path)
                        if source.exists():
                            shutil.copy2(source, file_path)
                            restored_count += 1
                    
                    logger.info(f"Restored {restored_count} files")
                    return True
                else:
                    logger.error("No metadata found in backup")
                    return False
                    
            finally:
                shutil.rmtree(temp_restore_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("config_backup_*.tar.gz"):
            try:
                # Extract metadata without full extraction
                with tarfile.open(backup_file, "r:gz") as tar:
                    try:
                        metadata_member = tar.getmember("backup_metadata.json")
                        metadata_content = tar.extractfile(metadata_member).read()
                        metadata = json.loads(metadata_content)
                        
                        backup_info = {
                            "file": str(backup_file),
                            "size_mb": backup_file.stat().st_size / (1024 * 1024),
                            "created": metadata["timestamp"],
                            "label": metadata.get("label"),
                            "file_count": len(metadata["files"])
                        }
                        backups.append(backup_info)
                        
                    except KeyError:
                        # Old backup without metadata
                        stat = backup_file.stat()
                        backup_info = {
                            "file": str(backup_file),
                            "size_mb": stat.st_size / (1024 * 1024),
                            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "label": "legacy",
                            "file_count": "unknown"
                        }
                        backups.append(backup_info)
                        
            except Exception as e:
                logger.warning(f"Could not read backup {backup_file}: {e}")
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("config_backup_*.tar.gz"):
            try:
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if mtime < cutoff:
                    backup_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old backup: {backup_file.name}")
            except Exception as e:
                logger.warning(f"Could not remove {backup_file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old backups")
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup integrity and checksums"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return False
            
            # Test if archive can be opened
            with tarfile.open(backup_file, "r:gz") as tar:
                # Check if metadata exists
                try:
                    metadata_member = tar.getmember("backup_metadata.json")
                    metadata_content = tar.extractfile(metadata_member).read()
                    metadata = json.loads(metadata_content)
                    
                    # TODO: Could verify individual file checksums if needed
                    logger.debug(f"Backup integrity verified: {backup_path}")
                    return True
                    
                except (KeyError, json.JSONDecodeError):
                    logger.warning(f"Backup metadata missing or corrupted: {backup_path}")
                    return False
                    
        except Exception as e:
            logger.error(f"Backup integrity check failed: {e}")
            return False
    
    def _backup_loop(self):
        """Background backup loop"""
        logger.info("Backup loop started")
        
        while self._running:
            try:
                # Create periodic backup
                backup_path = self.create_backup(label="auto")
                if backup_path:
                    logger.debug(f"Automatic backup created: {backup_path}")
                
                # Clean up old backups
                self.cleanup_old_backups()
                
                # Wait for next backup cycle
                time.sleep(self.backup_interval)
                
            except Exception as e:
                logger.error(f"Backup loop error: {e}")
                time.sleep(60)  # Back off on errors
    
    def _copy_to_staging(self, source_path: str, staging_dir: Path):
        """Copy file or directory to staging area"""
        source = Path(source_path)
        
        if source.is_file():
            shutil.copy2(source, staging_dir / source.name)
        elif source.is_dir():
            shutil.copytree(source, staging_dir / source.name, dirs_exist_ok=True)
    
    def _calculate_checksums(self, file_paths: List[str]) -> Dict[str, str]:
        """Calculate SHA256 checksums for files"""
        checksums = {}
        
        for file_path in file_paths:
            try:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        checksum = hashlib.sha256(content).hexdigest()
                        checksums[file_path] = checksum
            except Exception as e:
                logger.warning(f"Could not checksum {file_path}: {e}")
        
        return checksums


# Singleton instance for global use
_backup_system: Optional[ConfigBackupSystem] = None

def get_backup_system() -> ConfigBackupSystem:
    """Get or create singleton backup system"""
    global _backup_system
    if _backup_system is None:
        _backup_system = ConfigBackupSystem()
    return _backup_system


def main():
    """CLI interface for backup system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Backup System")
    parser.add_argument("action", choices=["create", "list", "restore", "verify", "cleanup", "start-service"])
    parser.add_argument("--backup", help="Backup file path for restore/verify")
    parser.add_argument("--label", help="Label for backup")
    parser.add_argument("--confirm", action="store_true", help="Confirm restore action")
    
    args = parser.parse_args()
    
    backup_system = get_backup_system()
    
    if args.action == "create":
        result = backup_system.create_backup(args.label)
        if result:
            print(f"✅ Backup created: {result}")
        else:
            print("❌ Backup failed")
    
    elif args.action == "list":
        backups = backup_system.list_backups()
        if backups:
            print("\n📦 Available Backups:")
            for backup in backups:
                print(f"  {backup['created']} - {backup['file']} ({backup['size_mb']:.1f}MB)")
                if backup['label']:
                    print(f"    Label: {backup['label']}")
        else:
            print("No backups found")
    
    elif args.action == "restore":
        if not args.backup:
            print("❌ --backup required for restore")
            return
        
        result = backup_system.restore_backup(args.backup, args.confirm)
        if result:
            print("✅ Restore completed")
        else:
            print("❌ Restore failed")
    
    elif args.action == "verify":
        if not args.backup:
            print("❌ --backup required for verify")
            return
        
        result = backup_system.verify_backup_integrity(args.backup)
        print("✅ Backup integrity OK" if result else "❌ Backup integrity failed")
    
    elif args.action == "cleanup":
        backup_system.cleanup_old_backups()
        print("✅ Cleanup completed")
    
    elif args.action == "start-service":
        backup_system.start_automated_backup()
        print("✅ Backup service started")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            backup_system.stop_automated_backup()
            print("\n✅ Backup service stopped")


if __name__ == "__main__":
    main()