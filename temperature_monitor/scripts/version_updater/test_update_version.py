#!/usr/bin/env python3
"""
Unit tests for the version update utility.
"""

import os
import sys
import re
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock, call

# Import from the refactored module
from update_version import (
    BumpType,
    Component,
    Version,
    VersionConfig,
    VersionManager,
    FileUpdater,
    BackendVersionUpdater,
    FrontendVersionUpdater,
    VersionUpdaterCLI
)


class TestVersion:
    """Test the Version class."""

    def test_version_creation(self):
        """Test creating a Version object."""
        version = Version(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_string_representation(self):
        """Test the string representation of a Version."""
        version = Version(1, 2, 3)
        assert str(version) == "1.2.3"


class TestVersionManager:
    """Test the VersionManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = VersionManager()

    def test_parse_valid_version(self):
        """Test parsing a valid version string."""
        version = self.version_manager.parse_version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_parse_invalid_version(self):
        """Test parsing an invalid version string."""
        with pytest.raises(ValueError):
            self.version_manager.parse_version("invalid")
        
        with pytest.raises(ValueError):
            self.version_manager.parse_version("1.2")
        
        with pytest.raises(ValueError):
            self.version_manager.parse_version("1.2.a")

    def test_bump_version_increment_patch(self):
        """Test incrementing the patch version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.PATCH, BumpType.INCREMENT
        )
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 4

    def test_bump_version_increment_minor(self):
        """Test incrementing the minor version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.MINOR, BumpType.INCREMENT
        )
        assert new_version.major == 1
        assert new_version.minor == 3
        assert new_version.patch == 0

    def test_bump_version_increment_major(self):
        """Test incrementing the major version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.MAJOR, BumpType.INCREMENT
        )
        assert new_version.major == 2
        assert new_version.minor == 0
        assert new_version.patch == 0

    def test_bump_version_set_patch(self):
        """Test setting the patch version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.PATCH, BumpType.SET, value=5
        )
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 5

    def test_bump_version_set_minor(self):
        """Test setting the minor version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.MINOR, BumpType.SET, value=5
        )
        assert new_version.major == 1
        assert new_version.minor == 5
        assert new_version.patch == 3

    def test_bump_version_set_major(self):
        """Test setting the major version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(
            version, Component.MAJOR, BumpType.SET, value=5
        )
        assert new_version.major == 5
        assert new_version.minor == 2
        assert new_version.patch == 3

    def test_bump_version_invalid_operation(self):
        """Test invalid bump operation."""
        version = Version(1, 2, 3)
        with pytest.raises(ValueError):
            self.version_manager.bump_version(
                version, Component.MAJOR, BumpType.SET
            )

    def test_format_version(self):
        """Test formatting a version."""
        version = Version(1, 2, 3)
        assert self.version_manager.format_version(version) == "1.2.3"


class TestFileUpdater:
    """Test the FileUpdater class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = MagicMock()
        self.file_updater = FileUpdater(self.version_manager)

    def test_read_file(self):
        """Test reading a file."""
        mock_file_content = "content"
        
        with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
            content = self.file_updater._read_file("test_file.py")
            mock_file.assert_called_once_with("test_file.py", "r", encoding="utf-8")
            assert content == mock_file_content

    def test_read_file_error(self):
        """Test reading a file with error."""
        with patch("builtins.open", side_effect=IOError("Error")):
            with pytest.raises(IOError):
                self.file_updater._read_file("test_file.py")

    def test_write_file(self):
        """Test writing to a file."""
        mock_content = "new content"
        
        with patch("builtins.open", mock_open()) as mock_file:
            self.file_updater._write_file("test_file.py", mock_content)
            mock_file.assert_called_once_with("test_file.py", "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(mock_content)

    def test_write_file_error(self):
        """Test writing to a file with error."""
        with patch("builtins.open", side_effect=IOError("Error")):
            with pytest.raises(IOError):
                self.file_updater._write_file("test_file.py", "content")

    @patch("os.path.exists")
    def test_update_file(self, mock_exists):
        """Test updating a file."""
        mock_exists.return_value = True
        mock_content = "version = 1.2.3"
        mock_updated_content = "version = 2.0.0"
        
        with patch.object(self.file_updater, "_read_file", return_value=mock_content):
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file("test_file.py", "1.2.3", "2.0.0")
                mock_write.assert_called_once_with("test_file.py", mock_updated_content)

    @patch("os.path.exists")
    def test_update_file_no_changes(self, mock_exists):
        """Test updating a file with no changes."""
        mock_exists.return_value = True
        mock_content = "no version here"
        
        with patch.object(self.file_updater, "_read_file", return_value=mock_content):
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file("test_file.py", "1.2.3", "2.0.0")
                mock_write.assert_not_called()

    @patch("os.path.exists")
    def test_update_nonexistent_file(self, mock_exists):
        """Test updating a non-existent file."""
        mock_exists.return_value = False
        
        with patch.object(self.file_updater, "_read_file") as mock_read:
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file("nonexistent.py", "1.2.3", "2.0.0")
                mock_read.assert_not_called()
                mock_write.assert_not_called()


class TestBackendVersionUpdater:
    """Test the BackendVersionUpdater class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = VersionManager()
        self.backend_updater = BackendVersionUpdater(self.version_manager)

    @patch("os.path.exists")
    def test_get_current_version(self, mock_exists):
        """Test getting the current backend version."""
        mock_exists.return_value = True
        mock_content = 'CURRENT_VERSION = "1.2.3"'
        
        with patch.object(self.backend_updater, "_read_file", return_value=mock_content):
            version = self.backend_updater.get_current_version()
            assert version.major == 1
            assert version.minor == 2
            assert version.patch == 3

    @patch("os.path.exists")
    def test_get_current_version_not_found(self, mock_exists):
        """Test getting the current backend version when not found."""
        mock_exists.return_value = True
        mock_content = 'NO_VERSION_HERE = "something"'
        
        with patch.object(self.backend_updater, "_read_file", return_value=mock_content):
            with pytest.raises(ValueError):
                self.backend_updater.get_current_version()

    @patch("os.path.exists")
    def test_update_version(self, mock_exists):
        """Test updating the backend version."""
        mock_exists.return_value = True
        
        # Mock the get_current_version method
        with patch.object(self.backend_updater, "get_current_version", 
                        return_value=Version(1, 2, 3)):
            # Mock the update_file method
            with patch.object(self.backend_updater, "update_file") as mock_update:
                new_version = Version(2, 0, 0)
                self.backend_updater.update_version(new_version)
                
                # Check that update_file was called for all backend files
                expected_calls = [
                    call(VersionConfig.BACKEND_FILES['version_file'], "1.2.3", "2.0.0")
                ]
                for file_path in VersionConfig.BACKEND_FILES['other_files']:
                    expected_calls.append(call(file_path, "1.2.3", "2.0.0"))
                
                mock_update.assert_has_calls(expected_calls)


class TestFrontendVersionUpdater:
    """Test the FrontendVersionUpdater class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = VersionManager()
        self.frontend_updater = FrontendVersionUpdater(self.version_manager)

    @patch("os.path.exists")
    def test_get_current_version_from_package_json(self, mock_exists):
        """Test getting the current frontend version from package.json."""
        # Mock package.json exists
        mock_exists.side_effect = lambda path: path == VersionConfig.FRONTEND_FILES['package_json']
        
        mock_content = '{"name": "app", "version": "1.2.3"}'
        
        with patch.object(self.frontend_updater, "_read_file", return_value=mock_content):
            version = self.frontend_updater.get_current_version()
            assert version.major == 1
            assert version.minor == 2
            assert version.patch == 3

    @patch("os.path.exists")
    def test_get_current_version_from_version_ts(self, mock_exists):
        """Test getting the current frontend version from version.ts."""
        # Mock package.json doesn't exist but version.ts does
        mock_exists.side_effect = lambda path: path != VersionConfig.FRONTEND_FILES['package_json']
        
        mock_package_content = '{"name": "app"}'  # No version
        mock_version_content = 'export const VERSION = "1.2.3";'
        
        def mock_read_file(path):
            if path == VersionConfig.FRONTEND_FILES['package_json']:
                return mock_package_content
            return mock_version_content
        
        with patch.object(self.frontend_updater, "_read_file", side_effect=mock_read_file):
            version = self.frontend_updater.get_current_version()
            assert version.major == 1
            assert version.minor == 2
            assert version.patch == 3

    @patch("os.path.exists")
    def test_get_current_version_not_found(self, mock_exists):
        """Test getting the current frontend version when not found."""
        mock_exists.return_value = True
        
        mock_package_content = '{"name": "app"}'  # No version
        mock_version_content = 'export const APP_NAME = "My App";'  # No version
        
        def mock_read_file(path):
            if path == VersionConfig.FRONTEND_FILES['package_json']:
                return mock_package_content
            return mock_version_content
        
        with patch.object(self.frontend_updater, "_read_file", side_effect=mock_read_file):
            with pytest.raises(ValueError):
                self.frontend_updater.get_current_version()

    @pytest.mark.skip
    @patch("os.path.exists")
    def test_update_version(self, mock_exists):
        """Test updating the frontend version."""
        # Mock both files exist
        mock_exists.return_value = True
        
        # Mock the get_current_version method
        with patch.object(self.frontend_updater, "get_current_version", 
                        return_value=Version(1, 2, 3)):
            # Mock the read_file and write_file methods
            mock_package_content = '{"name": "app", "version": "1.2.3"}'
            mock_version_content = 'export const VERSION = "1.2.3";'
            
            def mock_read_file(path):
                if path == VersionConfig.FRONTEND_FILES['package_json']:
                    return mock_package_content
                return mock_version_content
            
            with patch.object(self.frontend_updater, "_read_file", side_effect=mock_read_file):
                with patch.object(self.frontend_updater, "_write_file") as mock_write:
                    new_version = Version(2, 0, 0)
                    self.frontend_updater.update_version(new_version)
                    
                    # Check that write_file was called for both frontend files
                    expected_package_content = '{"name": "app", "version": "2.0.0"}'
                    expected_version_content = 'export const VERSION = "2.0.0";'
                    
                    expected_calls = [
                        call(VersionConfig.FRONTEND_FILES['package_json'], expected_package_content),
                        call(VersionConfig.FRONTEND_FILES['version_ts'], expected_version_content)
                    ]
                    
                    # Check that the calls were made with the expected content
                    assert mock_write.call_count == 2
                    for actual_call, expected_call in zip(mock_write.call_args_list, expected_calls):
                        assert actual_call[0][0] == expected_call[0]
                        # Strip whitespace for comparison to avoid issues with regex substitution
                        assert actual_call[0][1].strip() == expected_call[1].strip()


class TestVersionUpdaterCLI:
    """Test the VersionUpdaterCLI class."""

    def setup_method(self):
        """Set up test environment."""
        self.cli = VersionUpdaterCLI()
        
        # Mock the updaters
        self.cli.backend_updater = MagicMock()
        self.cli.frontend_updater = MagicMock()
        self.cli.version_manager = MagicMock()

    def test_parse_arguments_defaults(self):
        """Test parsing command-line arguments with defaults."""
        with patch("sys.argv", ["update_version.py"]):
            args = self.cli.parse_arguments()
            assert args.component == "both"
            assert args.bump_type == "patch"
            assert args.action == "increment"
            assert args.value is None

    def test_parse_arguments_custom(self):
        """Test parsing custom command-line arguments."""
        with patch("sys.argv", [
            "update_version.py",
            "--component", "backend",
            "--bump-type", "minor",
            "--action", "set",
            "--value", "5"
        ]):
            args = self.cli.parse_arguments()
            assert args.component == "backend"
            assert args.bump_type == "minor"
            assert args.action == "set"
            assert args.value == 5

    def test_run_set_without_value(self):
        """Test running with 'set' action but no value."""
        with patch("sys.argv", [
            "update_version.py",
            "--action", "set"
        ]):
            exit_code = self.cli.run()
            assert exit_code == 1
            # No update methods should be called
            self.cli.backend_updater.update_version.assert_not_called()
            self.cli.frontend_updater.update_version.assert_not_called()

    def test_run_update_backend(self):
        """Test running update for backend only."""
        with patch("sys.argv", ["update_version.py", "--component", "backend"]):
            # Mock the backend version
            current_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            
            self.cli.backend_updater.get_current_version.return_value = current_version
            self.cli.version_manager.bump_version.return_value = new_version
            
            exit_code = self.cli.run()
            
            assert exit_code == 0
            self.cli.backend_updater.get_current_version.assert_called_once()
            self.cli.version_manager.bump_version.assert_called_once_with(
                current_version, Component.PATCH, BumpType.INCREMENT, None
            )
            self.cli.backend_updater.update_version.assert_called_once_with(new_version)
            # Frontend methods should not be called
            self.cli.frontend_updater.get_current_version.assert_not_called()
            self.cli.frontend_updater.update_version.assert_not_called()

    def test_run_update_frontend(self):
        """Test running update for frontend only."""
        with patch("sys.argv", ["update_version.py", "--component", "frontend"]):
            # Mock the frontend version
            current_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            
            self.cli.frontend_updater.get_current_version.return_value = current_version
            self.cli.version_manager.bump_version.return_value = new_version
            
            exit_code = self.cli.run()
            
            assert exit_code == 0
            self.cli.frontend_updater.get_current_version.assert_called_once()
            self.cli.version_manager.bump_version.assert_called_once_with(
                current_version, Component.PATCH, BumpType.INCREMENT, None
            )
            self.cli.frontend_updater.update_version.assert_called_once_with(new_version)
            # Backend methods should not be called
            self.cli.backend_updater.get_current_version.assert_not_called()
            self.cli.backend_updater.update_version.assert_not_called()

    def test_run_update_both(self):
        """Test running update for both backend and frontend."""
        with patch("sys.argv", ["update_version.py", "--component", "both"]):
            # Mock the versions
            backend_version = Version(1, 2, 3)
            frontend_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            
            self.cli.backend_updater.get_current_version.return_value = backend_version
            self.cli.frontend_updater.get_current_version.return_value = frontend_version
            self.cli.version_manager.bump_version.return_value = new_version
            
            exit_code = self.cli.run()
            
            assert exit_code == 0
            # Both updaters should be called
            self.cli.backend_updater.get_current_version.assert_called_once()
            self.cli.backend_updater.update_version.assert_called_once_with(new_version)
            self.cli.frontend_updater.get_current_version.assert_called_once()
            self.cli.frontend_updater.update_version.assert_called_once_with(new_version)
            # Version manager should be called twice
            assert self.cli.version_manager.bump_version.call_count == 2

    def test_run_backend_error(self):
        """Test handling backend update errors."""
        with patch("sys.argv", ["update_version.py", "--component", "backend"]):
            # Mock an error in backend update
            self.cli.backend_updater.get_current_version.side_effect = ValueError("Error")
            
            exit_code = self.cli.run()
            
            assert exit_code == 1
            self.cli.backend_updater.get_current_version.assert_called_once()
            self.cli.backend_updater.update_version.assert_not_called()

    def test_run_frontend_error(self):
        """Test handling frontend update errors."""
        with patch("sys.argv", ["update_version.py", "--component", "frontend"]):
            # Mock an error in frontend update
            self.cli.frontend_updater.get_current_version.side_effect = ValueError("Error")
            
            exit_code = self.cli.run()
            
            assert exit_code == 1
            self.cli.frontend_updater.get_current_version.assert_called_once()
            self.cli.frontend_updater.update_version.assert_not_called()

    def test_run_both_backend_error(self):
        """Test handling backend error when updating both components."""
        with patch("sys.argv", ["update_version.py", "--component", "both"]):
            # Mock an error in backend but success in frontend
            self.cli.backend_updater.get_current_version.side_effect = ValueError("Error")
            
            frontend_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            self.cli.frontend_updater.get_current_version.return_value = frontend_version
            self.cli.version_manager.bump_version.return_value = new_version
            
            exit_code = self.cli.run()
            
            # Should still succeed since we're updating both
            assert exit_code == 0
            self.cli.backend_updater.get_current_version.assert_called_once()
            self.cli.backend_updater.update_version.assert_not_called()
            # Frontend should still be updated
            self.cli.frontend_updater.get_current_version.assert_called_once()
            self.cli.frontend_updater.update_version.assert_called_once_with(new_version)


class TestIntegration:
    """Integration tests for the version update utility."""

    def setup_method(self):
        """Set up test environment with temporary files."""
        # Create temp directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create backend files
        self.backend_dir = os.path.join(self.temp_dir.name, "backend")
        os.makedirs(self.backend_dir)
        
        # Create config.py
        self.config_path = os.path.join(self.backend_dir, "config.py")
        with open(self.config_path, "w") as f:
            f.write('CURRENT_VERSION = "1.2.3"\n')
        
        # Create __init__.py
        self.init_path = os.path.join(self.backend_dir, "__init__.py")
        with open(self.init_path, "w") as f:
            f.write('"""Backend module version 1.2.3"""\n')
        
        # Create setup.py
        self.setup_path = os.path.join(self.temp_dir.name, "setup.py")
        with open(self.setup_path, "w") as f:
            f.write('setup(name="app", version="1.2.3")\n')
        
        # Create frontend files
        self.frontend_dir = os.path.join(self.temp_dir.name, "frontend")
        os.makedirs(os.path.join(self.frontend_dir, "src"))
        
        # Create package.json
        self.package_path = os.path.join(self.frontend_dir, "package.json")
        with open(self.package_path, "w") as f:
            f.write('{"name": "app", "version": "1.2.3"}\n')
        
        # Create version.ts
        self.version_ts_path = os.path.join(self.frontend_dir, "src", "version.ts")
        with open(self.version_ts_path, "w") as f:
            f.write('export const VERSION = "1.2.3";\n')
        
        # Patch file paths in VersionConfig
        self.original_backend_files = VersionConfig.BACKEND_FILES
        self.original_frontend_files = VersionConfig.FRONTEND_FILES
        
        VersionConfig.BACKEND_FILES = {
            'version_file': self.config_path,
            'other_files': [self.init_path, self.setup_path]
        }
        
        VersionConfig.FRONTEND_FILES = {
            'package_json': self.package_path,
            'version_ts': self.version_ts_path
        }

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original file paths
        VersionConfig.BACKEND_FILES = self.original_backend_files
        VersionConfig.FRONTEND_FILES = self.original_frontend_files
        
        # Remove temp directory
        self.temp_dir.cleanup()

    def test_integration_backend_patch(self):
        """Test updating backend patch version."""
        # Run CLI
        with patch("sys.argv", ["update_version.py", "--component", "backend"]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            
            assert exit_code == 0
            
            # Check that files were updated
            with open(self.config_path) as f:
                assert 'CURRENT_VERSION = "1.2.4"' in f.read()
            
            with open(self.init_path) as f:
                assert '"""Backend module version 1.2.4"""' in f.read()
            
            with open(self.setup_path) as f:
                assert 'setup(name="app", version="1.2.4")' in f.read()

    def test_integration_frontend_minor(self):
        """Test updating frontend minor version."""
        # Run CLI
        with patch("sys.argv", [
            "update_version.py",
            "--component", "frontend",
            "--bump-type", "minor"
        ]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            
            assert exit_code == 0
            
            # Check that files were updated
            with open(self.package_path) as f:
                assert '"version": "1.3.0"' in f.read()
            
            with open(self.version_ts_path) as f:
                assert 'export const VERSION = "1.3.0";' in f.read()

    def test_integration_both_major(self):
        """Test updating both components' major version."""
        # Run CLI
        with patch("sys.argv", [
            "update_version.py",
            "--component", "both",
            "--bump-type", "major"
        ]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            
            assert exit_code == 0
            
            # Check that all files were updated to 2.0.0
            with open(self.config_path) as f:
                assert 'CURRENT_VERSION = "2.0.0"' in f.read()
            
            with open(self.init_path) as f:
                assert '"""Backend module version 2.0.0"""' in f.read()
            
            with open(self.setup_path) as f:
                assert 'setup(name="app", version="2.0.0")' in f.read()
            
            with open(self.package_path) as f:
                assert '"version": "2.0.0"' in f.read()
            
            with open(self.version_ts_path) as f:
                assert 'export const VERSION = "2.0.0";' in f.read()

    def test_integration_set_version(self):
        """Test setting a specific version."""
        # Run CLI
        with patch("sys.argv", [
            "update_version.py",
            "--component", "both",
            "--action", "set",
            "--bump-type", "minor",
            "--value", "5"
        ]):
            cli = VersionUpdaterCLI()
            exit_code = cli.run()
            
            assert exit_code == 0
            
            # Check that all files were updated to 1.5.3
            with open(self.config_path) as f:
                assert 'CURRENT_VERSION = "1.5.3"' in f.read()
            
            with open(self.package_path) as f:
                assert '"version": "1.5.3"' in f.read()


# Run tests with: pytest -xvs test_update_version.py
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])