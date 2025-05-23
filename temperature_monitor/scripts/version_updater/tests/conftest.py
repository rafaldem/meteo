from unittest.mock import MagicMock, patch

import pytest
from pathlib import Path
import tempfile
import shutil

from update_version import (
    VersionUpdaterCLI,
    VersionConfig,
    Version,
    VersionManager,
    VersionUpdater,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_setup_py():
    """Create a mock setup.py file content."""
    return """
from setuptools import setup

setup(
    name="test-project",
    version="1.1.1",
    description="Test project",
)
"""


@pytest.fixture
def mock_version_py():
    """Create a mock version.py file content."""
    return '__version__ = "1.2.2"'


@pytest.fixture
def mock_pyproject_toml():
    """Create a mock pyproject.toml file content."""
    return """
[project]
name = "test-project"
version = "1.3.3"
description = "Test project"
"""


@pytest.fixture
def version_updater():
    """Create a VersionUpdater instance for testing."""
    return VersionUpdater(VersionManager())


@pytest.fixture
def setup_files(temp_dir):
    """Set up the test files with initial version strings."""
    backend_dir = temp_dir / "backend"
    frontend_dir = temp_dir / "frontend"
    backend_dir.mkdir(exist_ok=True)
    frontend_dir.mkdir(exist_ok=True)

    (backend_dir / "version.py").write_text('__version__ = "2.1.1"\n')
    (backend_dir / "pyproject.toml").write_text('[project]\nname = "backend"\nversion = "2.1.1"\n')

    (frontend_dir / "version.py").write_text('__version__ = "2.3.3"\n')
    (frontend_dir / "pyproject.toml").write_text('[project]\nname = "frontend"\nversion = "2.3.3"\n')

    (temp_dir / "setup.py").write_text(
        'from setuptools import setup\nsetup(\n    name="project",\n    version="2.5.0",\n)\n'
    )

    return temp_dir


# Fixture for creating a CLI instance with mocked dependencies
@pytest.fixture
def cli_fixture():
    """
    Create a VersionUpdaterCLI instance with mocked dependencies.

    Returns:
        tuple: (cli_instance, mock_config, mock_version_manager, mock_version_updater)
    """
    # Create mocks for dependencies
    mock_config = MagicMock(spec=VersionConfig)
    mock_version_manager = MagicMock(spec=VersionManager)
    mock_version_updater = MagicMock(spec=VersionUpdater)

    # Setup mock config with realistic defaults
    mock_config.project_root = Path("/fake/project/root")
    mock_config.files = [MagicMock()]

    # Setup mock version manager
    mock_version = Version(1, 2, 3)
    mock_version_manager.parse_version.return_value = mock_version
    mock_version_manager.format_version.return_value = "1.2.3"

    # Setup mock version updater
    mock_version_updater.get_current_version.return_value = mock_version

    # Create CLI instance with mocks
    with patch("update_version.VersionConfig", return_value=mock_config):
        with patch("update_version.VersionManager", return_value=mock_version_manager):
            with patch("update_version.VersionUpdater", return_value=mock_version_updater):
                cli = VersionUpdaterCLI()

    return cli, mock_config, mock_version_manager, mock_version_updater
