import tempfile
from pathlib import Path
from unittest.mock import patch, call

import pytest

from update_version import Version, VersionConfig, VersionManager, VersionUpdater


class TestVersionUpdater:
    """Test the VersionUpdater class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = VersionManager()
        self.version_updater = VersionUpdater(self.version_manager)
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).parent)

    @patch("os.path.exists")
    def test_get_current_version(self, mock_exists):
        """Test getting the current backend version."""
        mock_exists.return_value = True
        mock_content = '__version__ = "1.2.3"'
        with patch.object(self.version_updater, "_read_file", return_value=mock_content):
            version = self.version_updater.get_current_version(Path("backend/version.py"))
            assert version.major == 1
            assert version.minor == 2
            assert version.patch == 3

    @patch("os.path.exists")
    def test_get_current_version_not_found(self, mock_exists):
        """Test getting the current backend version when not found."""
        mock_exists.return_value = True
        mock_content = 'NO_VERSION_HERE = "something"'
        with patch.object(self.version_updater, "_read_file", return_value=mock_content):
            with pytest.raises(ValueError):
                self.version_updater.get_current_version(Path("backend/version.py"))

    @patch("os.path.exists")
    def test_update_version(self, mock_exists):
        """Test updating the backend version."""
        mock_exists.return_value = True
        with patch.object(self.version_updater, "get_current_version", return_value=Version(1, 2, 3)):
            with patch.object(self.version_updater, "update_file") as mock_update:
                new_version = Version(2, 0, 0)
                self.version_updater.update_version(new_version, "backend")
                expected_calls = [
                    call(VersionConfig.FILES["backend"]["version.py"], "1.2.3", "2.0.0"),
                    call(VersionConfig.FILES["backend"]["pyproject.toml"], "1.2.3", "2.0.0"),
                ]
                mock_update.assert_has_calls(expected_calls)
