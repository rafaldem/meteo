import sys

from update_version import VersionUpdaterCLI, VersionConfig


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
        assert setup_files / "setup.py" == custom_config.files["setup"]["setup.py"].path

        monkeypatch.setattr(
            sys, "argv", ["update_version.py", "--component", "both", "--bump-type", "patch"]
        )

        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()

        assert exit_code == 0

        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
        updated_setup = (setup_files / "setup.py").read_text()

        assert '__version__ = "2.1.2"' in updated_backend_version
        assert 'version = "2.1.2"' in updated_backend_pyproject

        assert '__version__ = "2.3.4"' in updated_frontend_version
        assert 'version = "2.3.4"' in updated_frontend_pyproject

        assert 'version="2.5.1"' in updated_setup

    def test_integration_set_minor(self, setup_files, monkeypatch):
        """Test end-to-end setting the minor version."""

        custom_config = VersionConfig(project_root=setup_files)

        monkeypatch.setattr(
            sys,"argv",
            [
                "update_version.py",
                "--component", "backend",
                "--bump-type", "minor",
                "--action", "set",
                "--value", "5",
                "--log-level", "debug"
            ],
        )

        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()

        assert exit_code == 0

        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()

        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()

        updated_setup = (setup_files / "setup.py").read_text()

        assert '__version__ = "2.5.1"' in updated_backend_version
        assert 'version = "2.5.1"' in updated_backend_pyproject

        assert '__version__ = "2.3.3"' in updated_frontend_version
        assert 'version = "2.3.3"' in updated_frontend_pyproject

        assert 'version="2.6.0"' in updated_setup

    def test_integration_increment_major(self, setup_files, monkeypatch):
        """Test end-to-end incrementing the major version."""

        custom_config = VersionConfig(project_root=setup_files)

        monkeypatch.setattr(
            sys,
            "argv",
            ["update_version.py", "--component", "frontend", "--bump-type", "major"],
        )

        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()

        assert exit_code == 0

        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
        updated_setup = (setup_files / "setup.py").read_text()

        assert '__version__ = "2.1.1"' in updated_backend_version
        assert 'version = "2.1.1"' in updated_backend_pyproject
        assert '__version__ = "3.0.0"' in updated_frontend_version
        assert 'version = "3.0.0"' in updated_frontend_pyproject
        assert 'version="3.0.0"' in updated_setup

    def test_integration_increment_minor(self, setup_files, monkeypatch):
        """Test end-to-end incrementing the minor version."""

        custom_config = VersionConfig(project_root=setup_files)

        monkeypatch.setattr(
            sys,
            "argv",
            ["update_version.py", "--component", "frontend", "--bump-type", "minor"],
        )

        cli = VersionUpdaterCLI(config=custom_config)
        exit_code = cli.run()

        assert exit_code == 0

        updated_backend_version = (setup_files / "backend/version.py").read_text()
        updated_backend_pyproject = (setup_files / "backend/pyproject.toml").read_text()
        updated_frontend_version = (setup_files / "frontend/version.py").read_text()
        updated_frontend_pyproject = (setup_files / "frontend/pyproject.toml").read_text()
        updated_setup = (setup_files / "setup.py").read_text()

        assert '__version__ = "2.1.1"' in updated_backend_version
        assert 'version = "2.1.1"' in updated_backend_pyproject
        assert '__version__ = "2.4.0"' in updated_frontend_version
        assert 'version = "2.4.0"' in updated_frontend_pyproject
        assert 'version="2.6.0"' in updated_setup
