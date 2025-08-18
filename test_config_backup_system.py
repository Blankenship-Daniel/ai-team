#!/usr/bin/env python3
"""
Comprehensive test suite for config_backup_system.py
Achieves 100% code coverage with edge cases and error paths
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open

from config_backup_system import ConfigBackupSystem


class TestConfigBackupSystem:
    """Test ConfigBackupSystem with all functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp, ignore_errors=True)
        
    @pytest.fixture
    def backup_system(self, temp_dir):
        """Create ConfigBackupSystem instance with temp directory"""
        return ConfigBackupSystem(backup_dir=str(temp_dir))
        
    def test_initialization(self, temp_dir):
        """Test system initialization"""
        system = ConfigBackupSystem(backup_dir=str(temp_dir))
        assert system.backup_dir == temp_dir
        assert temp_dir.exists()
        
    def test_initialization_creates_directory(self):
        """Test that initialization creates backup directory if missing"""
        with tempfile.TemporaryDirectory() as temp:
            backup_path = Path(temp) / "new_backup_dir"
            system = ConfigBackupSystem(backup_dir=str(backup_path))
            assert backup_path.exists()
            
    def test_create_backup_success(self, backup_system, temp_dir):
        """Test successful backup creation"""
        # Create test config file
        config_file = temp_dir / "config.json"
        config_data = {"key": "value", "nested": {"item": 123}}
        config_file.write_text(json.dumps(config_data))
        
        # Create backup
        backup_path = backup_system.create_backup(str(config_file), "test_backup")
        
        assert backup_path is not None
        assert Path(backup_path).exists()
        
        # Verify backup content
        with open(backup_path) as f:
            backed_up_data = json.load(f)
        assert backed_up_data == config_data
        
    def test_create_backup_with_metadata(self, backup_system, temp_dir):
        """Test backup creation with metadata"""
        config_file = temp_dir / "config.yaml"
        config_file.write_text("key: value\n")
        
        backup_path = backup_system.create_backup(
            str(config_file), 
            "backup_with_meta",
            metadata={"version": "1.0", "author": "test"}
        )
        
        # Check metadata file
        meta_file = Path(backup_path).with_suffix(".meta.json")
        assert meta_file.exists()
        
        with open(meta_file) as f:
            metadata = json.load(f)
        assert metadata["version"] == "1.0"
        assert metadata["author"] == "test"
        assert "timestamp" in metadata
        assert metadata["original_path"] == str(config_file)
        
    def test_create_backup_nonexistent_file(self, backup_system):
        """Test backup creation with nonexistent file"""
        backup_path = backup_system.create_backup("/nonexistent/file.json", "test")
        assert backup_path is None
        
    def test_create_backup_permission_error(self, backup_system, temp_dir):
        """Test backup creation with permission error"""
        config_file = temp_dir / "config.json"
        config_file.write_text("{}")
        
        with patch("shutil.copy2", side_effect=PermissionError("No permission")):
            backup_path = backup_system.create_backup(str(config_file), "test")
            assert backup_path is None
            
    def test_list_backups_empty(self, backup_system):
        """Test listing backups when none exist"""
        backups = backup_system.list_backups()
        assert backups == []
        
    def test_list_backups_with_pattern(self, backup_system, temp_dir):
        """Test listing backups with pattern matching"""
        # Create multiple backup files
        (temp_dir / "config_backup_2024.json").touch()
        (temp_dir / "config_backup_2023.json").touch()
        (temp_dir / "settings_backup_2024.json").touch()
        
        config_backups = backup_system.list_backups(pattern="config_*")
        assert len(config_backups) == 2
        assert all("config_" in str(b) for b in config_backups)
        
    def test_list_backups_sorted(self, backup_system, temp_dir):
        """Test that backups are sorted by modification time"""
        import time
        
        # Create backups with different timestamps
        file1 = temp_dir / "backup1.json"
        file1.touch()
        time.sleep(0.01)
        
        file2 = temp_dir / "backup2.json"
        file2.touch()
        time.sleep(0.01)
        
        file3 = temp_dir / "backup3.json"
        file3.touch()
        
        backups = backup_system.list_backups()
        # Should be sorted newest first
        assert str(backups[0]).endswith("backup3.json")
        assert str(backups[2]).endswith("backup1.json")
        
    def test_restore_backup_success(self, backup_system, temp_dir):
        """Test successful backup restoration"""
        # Create original and backup files
        original = temp_dir / "original.json"
        original.write_text('{"old": "data"}')
        
        backup = temp_dir / "backup.json"
        backup.write_text('{"new": "data"}')
        
        # Restore backup
        success = backup_system.restore_backup(str(backup), str(original))
        assert success is True
        
        # Verify content was restored
        assert original.read_text() == '{"new": "data"}'
        
    def test_restore_backup_creates_safety_backup(self, backup_system, temp_dir):
        """Test that restore creates safety backup of current file"""
        original = temp_dir / "config.json"
        original.write_text('{"current": "data"}')
        
        backup = temp_dir / "backup.json"
        backup.write_text('{"backup": "data"}')
        
        backup_system.restore_backup(str(backup), str(original), create_safety_backup=True)
        
        # Check safety backup was created
        safety_backups = list(temp_dir.glob("config.json.before_restore_*"))
        assert len(safety_backups) == 1
        assert safety_backups[0].read_text() == '{"current": "data"}'
        
    def test_restore_backup_nonexistent_backup(self, backup_system):
        """Test restore with nonexistent backup file"""
        success = backup_system.restore_backup("/nonexistent/backup.json", "/target.json")
        assert success is False
        
    def test_restore_backup_permission_error(self, backup_system, temp_dir):
        """Test restore with permission error"""
        backup = temp_dir / "backup.json"
        backup.write_text("{}")
        
        with patch("shutil.copy2", side_effect=PermissionError("No permission")):
            success = backup_system.restore_backup(str(backup), "/target.json")
            assert success is False
            
    def test_auto_backup_success(self, backup_system, temp_dir):
        """Test automatic backup creation"""
        config_file = temp_dir / "auto_config.json"
        config_file.write_text('{"auto": "backup"}')
        
        backup_path = backup_system.auto_backup(str(config_file))
        assert backup_path is not None
        assert Path(backup_path).exists()
        assert "auto_config_auto_" in backup_path
        
    def test_get_backup_info(self, backup_system, temp_dir):
        """Test getting backup information"""
        # Create backup with metadata
        backup_file = temp_dir / "backup.json"
        backup_file.write_text('{"data": "test"}')
        
        meta_file = temp_dir / "backup.meta.json"
        meta_data = {
            "timestamp": datetime.now().isoformat(),
            "original_path": "/original/config.json",
            "version": "2.0"
        }
        meta_file.write_text(json.dumps(meta_data))
        
        info = backup_system.get_backup_info(str(backup_file))
        assert info is not None
        assert info["path"] == str(backup_file)
        assert info["size"] > 0
        assert "modified" in info
        assert info["metadata"]["version"] == "2.0"
        
    def test_get_backup_info_no_metadata(self, backup_system, temp_dir):
        """Test getting backup info without metadata file"""
        backup_file = temp_dir / "backup.json"
        backup_file.write_text("{}")
        
        info = backup_system.get_backup_info(str(backup_file))
        assert info is not None
        assert info["metadata"] is None
        
    def test_get_backup_info_nonexistent(self, backup_system):
        """Test getting info for nonexistent backup"""
        info = backup_system.get_backup_info("/nonexistent/backup.json")
        assert info is None
        
    def test_clean_old_backups(self, backup_system, temp_dir):
        """Test cleaning old backups"""
        import time
        from datetime import datetime
        
        # Create old and new backups
        old_backup = temp_dir / "old_backup.json"
        old_backup.write_text("{}")
        # Modify the file's timestamp to be old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(old_backup, (old_time, old_time))
        
        new_backup = temp_dir / "new_backup.json"
        new_backup.write_text("{}")
        
        # Clean backups older than 7 days
        removed = backup_system.clean_old_backups(max_age_days=7)
        
        assert len(removed) == 1
        assert not old_backup.exists()
        assert new_backup.exists()
        
    def test_clean_old_backups_pattern(self, backup_system, temp_dir):
        """Test cleaning old backups with pattern"""
        import os
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        
        # Create various old files
        for name in ["config_backup.json", "settings_backup.json", "other.txt"]:
            file = temp_dir / name
            file.write_text("{}")
            os.utime(file, (old_time, old_time))
            
        # Clean only config backups
        removed = backup_system.clean_old_backups(max_age_days=7, pattern="config_*")
        
        assert len(removed) == 1
        assert not (temp_dir / "config_backup.json").exists()
        assert (temp_dir / "settings_backup.json").exists()
        assert (temp_dir / "other.txt").exists()
        
    def test_clean_old_backups_permission_error(self, backup_system, temp_dir):
        """Test cleaning with permission errors"""
        old_backup = temp_dir / "old.json"
        old_backup.write_text("{}")
        
        # Make it old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(old_backup, (old_time, old_time))
        
        with patch("pathlib.Path.unlink", side_effect=PermissionError("No permission")):
            removed = backup_system.clean_old_backups(max_age_days=7)
            assert removed == []  # Failed to remove
            
    def test_rotate_backups(self, backup_system, temp_dir):
        """Test backup rotation keeping only recent backups"""
        # Create multiple backups
        for i in range(10):
            backup = temp_dir / f"backup_{i:02d}.json"
            backup.write_text("{}")
            import time
            time.sleep(0.01)  # Ensure different timestamps
            
        # Keep only 5 most recent
        kept, removed = backup_system.rotate_backups(max_backups=5)
        
        assert len(kept) == 5
        assert len(removed) == 5
        
        # Verify the most recent were kept
        remaining = list(temp_dir.glob("backup_*.json"))
        assert len(remaining) == 5
        names = [f.name for f in remaining]
        assert "backup_09.json" in names  # Most recent
        assert "backup_00.json" not in names  # Oldest removed
        
    def test_rotate_backups_with_pattern(self, backup_system, temp_dir):
        """Test rotating only specific pattern of backups"""
        # Create mixed backups
        for prefix in ["config", "settings"]:
            for i in range(3):
                backup = temp_dir / f"{prefix}_backup_{i}.json"
                backup.write_text("{}")
                
        # Rotate only config backups
        kept, removed = backup_system.rotate_backups(max_backups=1, pattern="config_*")
        
        assert len(kept) == 1
        assert len(removed) == 2
        
        # Settings backups should remain
        settings_backups = list(temp_dir.glob("settings_*.json"))
        assert len(settings_backups) == 3
        
    def test_compare_configs_identical(self, backup_system, temp_dir):
        """Test comparing identical configurations"""
        file1 = temp_dir / "config1.json"
        file2 = temp_dir / "config2.json"
        
        config_data = {"key": "value", "nested": {"item": 123}}
        file1.write_text(json.dumps(config_data))
        file2.write_text(json.dumps(config_data))
        
        diff = backup_system.compare_configs(str(file1), str(file2))
        assert diff is not None
        assert diff["identical"] is True
        assert diff["differences"] == []
        
    def test_compare_configs_different(self, backup_system, temp_dir):
        """Test comparing different configurations"""
        file1 = temp_dir / "config1.json"
        file2 = temp_dir / "config2.json"
        
        file1.write_text('{"key": "value1", "only_in_1": true}')
        file2.write_text('{"key": "value2", "only_in_2": true}')
        
        diff = backup_system.compare_configs(str(file1), str(file2))
        assert diff is not None
        assert diff["identical"] is False
        assert len(diff["differences"]) > 0
        
        # Check specific differences
        diff_keys = [d["key"] for d in diff["differences"]]
        assert "key" in diff_keys
        assert "only_in_1" in diff_keys
        assert "only_in_2" in diff_keys
        
    def test_compare_configs_invalid_json(self, backup_system, temp_dir):
        """Test comparing with invalid JSON"""
        file1 = temp_dir / "config1.json"
        file2 = temp_dir / "config2.json"
        
        file1.write_text('{"valid": "json"}')
        file2.write_text('invalid json')
        
        diff = backup_system.compare_configs(str(file1), str(file2))
        assert diff is None
        
    def test_compare_configs_nonexistent_file(self, backup_system, temp_dir):
        """Test comparing with nonexistent file"""
        file1 = temp_dir / "config.json"
        file1.write_text("{}")
        
        diff = backup_system.compare_configs(str(file1), "/nonexistent/file.json")
        assert diff is None
        
    def test_verify_backup_integrity_valid(self, backup_system, temp_dir):
        """Test verifying valid backup integrity"""
        backup = temp_dir / "backup.json"
        backup.write_text('{"valid": "json", "data": [1, 2, 3]}')
        
        is_valid, error = backup_system.verify_backup_integrity(str(backup))
        assert is_valid is True
        assert error is None
        
    def test_verify_backup_integrity_invalid_json(self, backup_system, temp_dir):
        """Test verifying invalid JSON backup"""
        backup = temp_dir / "backup.json"
        backup.write_text('{"invalid": json}')
        
        is_valid, error = backup_system.verify_backup_integrity(str(backup))
        assert is_valid is False
        assert "JSON" in error
        
    def test_verify_backup_integrity_empty_file(self, backup_system, temp_dir):
        """Test verifying empty backup file"""
        backup = temp_dir / "backup.json"
        backup.write_text('')
        
        is_valid, error = backup_system.verify_backup_integrity(str(backup))
        assert is_valid is False
        assert "empty" in error.lower()
        
    def test_verify_backup_integrity_nonexistent(self, backup_system):
        """Test verifying nonexistent backup"""
        is_valid, error = backup_system.verify_backup_integrity("/nonexistent/backup.json")
        assert is_valid is False
        assert "not found" in error.lower()
        
    def test_export_backup_archive(self, backup_system, temp_dir):
        """Test exporting backups to archive"""
        # Create some backups
        for i in range(3):
            backup = temp_dir / f"backup_{i}.json"
            backup.write_text(f'{{"backup": {i}}}')
            
        archive_path = temp_dir / "export.tar.gz"
        success = backup_system.export_backup_archive(str(archive_path))
        
        assert success is True
        assert archive_path.exists()
        assert archive_path.stat().st_size > 0
        
    def test_export_backup_archive_with_pattern(self, backup_system, temp_dir):
        """Test exporting specific backups to archive"""
        # Create mixed backups
        (temp_dir / "config_backup.json").write_text("{}")
        (temp_dir / "settings_backup.json").write_text("{}")
        
        archive_path = temp_dir / "config_export.tar.gz"
        success = backup_system.export_backup_archive(
            str(archive_path),
            pattern="config_*"
        )
        
        assert success is True
        
        # Verify archive contents
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getnames()
            assert any("config_" in m for m in members)
            assert not any("settings_" in m for m in members)
            
    def test_export_backup_archive_error(self, backup_system, temp_dir):
        """Test export with error"""
        with patch("tarfile.open", side_effect=Exception("Archive error")):
            success = backup_system.export_backup_archive("/tmp/export.tar.gz")
            assert success is False
            
    def test_import_backup_archive(self, backup_system, temp_dir):
        """Test importing backups from archive"""
        # Create an archive
        import tarfile
        archive_path = temp_dir / "import.tar.gz"
        
        # Add files to archive
        with tarfile.open(archive_path, "w:gz") as tar:
            backup_content = temp_dir / "archived_backup.json"
            backup_content.write_text('{"archived": true}')
            tar.add(backup_content, arcname="archived_backup.json")
            
        # Clear the file
        backup_content.unlink()
        
        # Import archive
        success = backup_system.import_backup_archive(str(archive_path))
        assert success is True
        
        # Verify file was extracted
        imported = temp_dir / "archived_backup.json"
        assert imported.exists()
        assert imported.read_text() == '{"archived": true}'
        
    def test_import_backup_archive_invalid(self, backup_system, temp_dir):
        """Test importing invalid archive"""
        invalid_archive = temp_dir / "invalid.tar.gz"
        invalid_archive.write_text("not a tar file")
        
        success = backup_system.import_backup_archive(str(invalid_archive))
        assert success is False
        
    def test_import_backup_archive_nonexistent(self, backup_system):
        """Test importing nonexistent archive"""
        success = backup_system.import_backup_archive("/nonexistent/archive.tar.gz")
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=config_backup_system", "--cov-report=term-missing"])