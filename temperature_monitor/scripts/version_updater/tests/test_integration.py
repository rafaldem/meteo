import sys
import tempfile
import shutil
from pathlib import Path

import pytest

from update_version import VersionUpdaterCLI, VersionConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_directory = tempfile.mkdtemp()
    yield Path(temp_directory)
    shutil.rmtree(temp_directory)


@pytest.fixture
def setup_files(temp_dir):
    """Set up the test files with initial version strings."""
    backend_dir = temp_dir / "backend"
    frontend_dir = temp_dir / "frontend"
    backend_dir.mkdir(exist_ok=True)
    frontend_dir.mkdir(exist_ok=True)

    (backend_dir / "version.py").write_text('__version__ = "1.2.3"\n')
    (backend_dir / "pyproject.toml").write_text('[project]\nname = "backend"\nversion = "1.2.3"\n')

    (frontend_dir / "version.py").write_text('__version__ = "1.2.3"\n')
    (frontend_dir / "pyproject.toml").write_text('[project]\nname = "frontend"\nversion = "1.2.3"\n')

    (temp_dir / "setup.py").write_text(
        'from setuptools import setup\nsetup(\n    name="project",\n    version="1.2.3",\n)\n'
    )

    return temp_dir


class TestIntegration:
    """Integration tests for the version updater."""

    def test_integration_increment_patch(self, setup_files, monkeypatch):
        """Test end-to-end incrementing the patch version."""
        # Instead of patching the VersionConfig directly, create a real instance
        # with our temp directory as the project_root. This will correctly initialize
        # all the file paths within __post_init__
        custom_config = VersionConfig(project_root=setup_files)

        assert setup_files / "backend/version.py" == custom_config.files["backend"]["version.py"].path
        assert setup_files / "frontend/version.py" == custom_config.files["frontend"]["version.py"].path

        monkeypatch.setattr(sys, "argv", ["update_version.py", "--component", "both", "--bump-type", "patch"])

        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()

        assert exit_code == 0

        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
        updated_setup = (setup_files / "setup.py").read_text()

        assert '__version__ = "1.2.4"' in updated_backend_version
        assert '__version__ = "1.2.4"' in updated_frontend_version
        assert 'version = "1.2.4"' in updated_backend_pyproject
        assert 'version = "1.2.4"' in updated_frontend_pyproject
        assert 'version="1.2.4"' in updated_setup

    def test_integration_set_minor(self, setup_files, monkeypatch):
        """Test end-to-end setting the minor version."""
    
        custom_config = VersionConfig(project_root=setup_files)
    
        monkeypatch.setattr(
            sys,
            "argv",
            ["update_version.py", "--component", "backend", "--bump-type", "minor", "--action", "set", "--value", "5"],
        )
    
        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()
    
        assert exit_code == 0
    
        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
    
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
    
        assert '__version__ = "1.5.3"' in updated_backend_version
        assert 'version = "1.5.3"' in updated_backend_pyproject
    
        assert '__version__ = "1.2.3"' in updated_frontend_version
        assert 'version = "1.2.3"' in updated_frontend_pyproject
    
    def test_integration_increment_major(self, setup_files, monkeypatch):
        """Test end-to-end incrementing the major version."""
    
        custom_config = VersionConfig(project_root=setup_files)
    
        monkeypatch.setattr(
            sys,
            "argv",
            ["update_version.py", "--component", "both", "--bump-type", "major"],
        )
    
        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()
    
        assert exit_code == 0
    
        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
        updated_setup = (setup_files / "setup.py").read_text()
    
        assert '__version__ = "2.0.0"' in updated_backend_version
        assert 'version = "2.0.0"' in updated_backend_pyproject
        assert '__version__ = "2.0.0"' in updated_frontend_version
        assert 'version = "2.0.0"' in updated_frontend_pyproject
        assert 'version="2.0.0"' in updated_setup

