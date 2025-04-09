import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from update_version import VersionUpdater, VersionManager, Version, VersionConfig


class TestVersionUpdater:
    """Test cases for the VersionUpdater class."""

    @pytest.fixture
    def version_updater(self):
        """Create a VersionUpdater instance for testing."""
        return VersionUpdater(VersionManager())

    @patch("update_version.FileUpdater._read_file")
    def test_get_current_version_backend(self, mock_read, version_updater):
        """Test getting the current backend version."""
        mock_content = '__version__ = "1.2.3"'
        mock_read.return_value = mock_content

        with patch("pathlib.Path.parent", new_callable=MagicMock) as mock_parent:
            # Set up mock parent.name to return "backend"
            mock_parent.name = "backend"
            version_file = Path("version.py")
            version_file.parent = mock_parent

            result = version_updater.get_current_version(version_file)

            assert result.major == 1
            assert result.minor == 2
            assert result.patch == 3

    @patch("update_version.FileUpdater._read_file")
    def test_get_current_version_invalid_pattern(self, mock_read, version_updater):
        """Test getting version with invalid pattern raises ValueError."""
        mock_content = "invalid version format"
        mock_read.return_value = mock_content

        with patch("pathlib.Path.parent", new_callable=MagicMock) as mock_parent:
            # Set up mock parent.name to return "backend"
            mock_parent.name = "backend"
            version_file = Path("version.py")
            version_file.parent = mock_parent

            with pytest.raises(ValueError):
                version_updater.get_current_version(version_file)

    @patch("update_version.VersionUpdater.update_file")
    @patch("pathlib.Path.exists", return_value=True)
    def test_update_version(self, mock_exists, mock_update_file, version_updater):
        """Test updating version in files."""
        old_version = Version(1, 2, 3)
        new_version = Version(1, 2, 4)
        component = "backend"

        version_updater.update_version(old_version, new_version, component)

        # Check that update_file was called for each file in the component
        assert mock_update_file.call_count == len(VersionConfig.FILES[component])
