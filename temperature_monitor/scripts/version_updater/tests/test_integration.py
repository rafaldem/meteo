import tempfile
from pathlib import Path
from unittest.mock import patch

from update_version import VersionConfig, VersionUpdaterCLI


class TestIntegration:
    """Integration tests for the version update utility."""

    def setup_method(self):
        """Set up test environment with temporary files."""
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).parent)

        self.backend_dir = Path(self.temp_dir.name, "backend")
        self.backend_dir.mkdir(parents=True, exist_ok=True)
        self.backend_version_path = self.backend_dir / "version.py"
        self.backend_pyproject_path = self.backend_dir / "pyproject.toml"

        self.frontend_dir = Path(self.temp_dir.name, "frontend")
        self.frontend_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_version_path = self.backend_dir / "version.py"
        self.frontend_pyproject_path = self.backend_dir / "pyproject.toml"

        self.setup_path = Path(self.temp_dir.name, "setup.py")

        with self.backend_version_path.open("w") as f:
            f.write('__version__ = "0.1.0"  # Keep this consistent with pyproject.toml\n')
        with self.backend_pyproject_path.open("w") as f:
            f.write(
                """[project]
name = "temperature-monitor-backend"
version = "0.1.0"
description = "Temperature monitoring application (backend)\"
"""
            )
        with self.frontend_version_path.open("w") as f:
            f.write('__version__ = "0.1.0"  # Keep this consistent with pyproject.toml\n')
        with self.frontend_pyproject_path.open("w") as f:
            f.write(
                """[project]
name = "temperature-monitor-frontend"
version = "0.1.0"
description = "Temperature monitoring application (frontend)\"
"""
            )
        with self.setup_path.open("w") as f:
            f.write(
                """setup(
   name="temperature_monitor"
   version="0.1.0",  # This will be managed by the version updater
"""
            )

        self.original_backend_files = VersionConfig.FILES["backend"]
        self.original_frontend_files = VersionConfig.FILES["frontend"]
        VersionConfig.PROJECT_LOCATION = self.temp_dir.name
        VersionConfig.BACKEND_FILES = {
            "version.py": self.backend_version_path.name,
            "pyproject.toml": self.backend_pyproject_path.name,
        }
        VersionConfig.FRONTEND_FILES = {
            "version.py": self.frontend_version_path.name,
            "pyproject.toml": self.frontend_pyproject_path.name,
        }

    def teardown_method(self):
        """Clean up test environment."""
        VersionConfig.FILES["backend"] = self.original_backend_files
        VersionConfig.FILES["frontend"] = self.original_frontend_files
        self.temp_dir.cleanup()

    def test_integration_backend_patch(self):
        """Test updating backend patch version."""
        with patch("sys.argv", ["update_version.py", "--component", "backend"]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            assert exit_code == 0
            with self.backend_version_path.open() as f:
                assert '__version__ = "1.2.4"' in f.read()
            with self.backend_pyproject_path.open() as f:
                assert 'version =  "1.2.4"' in f.read()
            with self.setup_path.open() as f:
                assert 'version="1.2.4"' in f.read()

    def test_integration_frontend_minor(self):
        """Test updating frontend minor version."""
        with patch("sys.argv", ["update_version.py", "--component", "frontend", "--bump-type", "minor"]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            assert exit_code == 0
            with self.frontend_version_path.open() as f:
                assert '__version__ = "1.2.4"' in f.read()
            with self.frontend_pyproject_path.open() as f:
                assert 'version =  "1.2.4"' in f.read()
            with self.setup_path.open() as f:
                assert 'version="1.2.4"' in f.read()

    def test_integration_both_major(self):
        """Test updating both components' major version."""
        with patch("sys.argv", ["update_version.py", "--component", "both", "--bump-type", "major"]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            assert exit_code == 0

            with self.backend_version_path.open() as f:
                assert '__version__ = "2.0.0"' in f.read()
            with self.backend_pyproject_path.open() as f:
                assert 'version =  "2.0.0"' in f.read()

            with self.frontend_version_path.open() as f:
                assert '__version__ = "2.0.0"' in f.read()
            with self.frontend_pyproject_path.open() as f:
                assert 'version =  "2.0.0"' in f.read()

            with self.setup_path.open() as f:
                assert 'version="2.0.0"' in f.read()

    def test_integration_set_version(self):
        """Test setting a specific version."""
        with patch(
            "sys.argv",
            ["update_version.py", "--component", "both", "--action", "set", "--bump-type", "minor", "--value", "5"],
        ):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            assert exit_code == 0


            with self.backend_version_path.open() as f:
                assert '__version__ = "1.5.3"' in f.read()
            with self.backend_pyproject_path.open() as f:
                assert 'version =  "1.5.3"' in f.read()

            with self.frontend_version_path.open() as f:
                assert '__version__ = "1.5.3"' in f.read()
            with self.frontend_pyproject_path.open() as f:
                assert 'version =  "1.5.3"' in f.read()

            with self.setup_path.open() as f:
                assert 'version="1.5.3"' in f.read()
