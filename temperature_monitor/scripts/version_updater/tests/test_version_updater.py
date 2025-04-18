from unittest import mock

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from update_version import VersionUpdater, VersionManager, Version, FileInfo


class TestVersionUpdater:
    """Test cases for the VersionUpdater class."""

    INVALID_VERSION_FORMATS = [
        "invalid version format",
        "version = 1.2.3",  # Missing quotes
        "__version = '1.2.3'",  # Missing underscore
    ]

    @pytest.fixture
    def versions(self):
        """Create test versions."""
        return {
            "old": Version(1, 2, 3),
            "new": Version(1, 2, 4)
        }

    @patch("update_version.FileUpdater._read_file")
    def test_get_current_version_backend(self, mock_read, version_updater):
        """Test getting the current backend version."""
        mock_content = '__version__ = "1.2.3"'
        mock_read.return_value = mock_content

        mock_path = MagicMock(spec=Path)
        mock_version_file_info = MagicMock(spec=FileInfo)
        mock_version_file_info.path = mock_path
        mock_version_file_info.path.name = "version.py"
        mock_version_file_info.path.__str__.return_value = "version.py"
        mock_version_file_info.path.parent = MagicMock()
        mock_version_file_info.path.parent.name = "backend"
        mock_version_file_info.pattern = r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'

        result = version_updater.get_current_version(mock_version_file_info)
    
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3

    @pytest.mark.parametrize("invalid_content", INVALID_VERSION_FORMATS)
    @patch("update_version.FileUpdater._read_file")
    def test_get_current_version_invalid_pattern(self, mock_read, invalid_content, version_updater):
        """Test that ValueError is raised when trying to parse invalid version formats."""
        mock_read.return_value = invalid_content

        mock_path = MagicMock(spec=Path)
        mock_version_file_info = MagicMock()
        mock_version_file_info.path = mock_path
        mock_version_file_info.path.parent.name = "backend"
        mock_version_file_info.pattern = r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'

        with pytest.raises(ValueError, match="Could not find version information"):
            version_updater.get_current_version(mock_version_file_info)

    def test_could_not_extract_version_exception(self, version_updater):
        """Test that get_current_version raises ValueError when version can't be extracted from a match."""
        test_file_path = Path("/test/path/version_file.py")
        test_pattern = r'__version__\s*=\s*["\'](.+?)["\']'
        file_info = FileInfo(path=test_file_path, pattern=test_pattern)

        file_content = '__version__ = "invalid-version-format"'

        with patch.object(version_updater, '_read_file', return_value=file_content):
            # Mock re.search to simulate our scenario:
            # First call: finds the pattern match in the file (e.g., __version__ = "invalid-version-format")
            # Second call: fails to extract a valid version from that match
            with patch('re.search') as mock_re_search:
                # The first re.search should succeed and return the full version string match
                first_match = MagicMock()
                first_match.group.return_value = 'invalid-version-format'

                # The second re.search should fail to find a valid version pattern
                second_match = None

                mock_re_search.side_effect = [first_match, second_match]

                with pytest.raises(ValueError) as excinfo:
                    version_updater.get_current_version(file_info)

                error_message = str(excinfo.value)
                assert "Could not extract version from invalid-version-format" in error_message

                # Verify re.search was called twice with the right patterns
                assert mock_re_search.call_count == 2
                # First call should use the file pattern
                assert mock_re_search.call_args_list[0][0][0] == test_pattern
                # Second call should use the version pattern (from VersionPattern().base)
                # We don't check the exact pattern as it's defined in the VersionPattern class

    @patch("update_version.VersionUpdater.update_file")
    @patch("pathlib.Path.exists", return_value=True)
    def test_update_version(self, mock_exists, mock_update_file, version_updater):
        """Test updating version in files."""
        old_version = Version(1, 2, 3)
        new_version = Version(1, 2, 4)
        component = "backend"

        version_updater.update_version(old_version, new_version, component)

        assert mock_exists.called

        # Check that update_file was called for each file in the component
        assert mock_update_file.call_count == 2
        calls = mock_update_file.call_args_list
        for call in calls:
            args, kwargs = call
            # First arg should be a Path object
            assert isinstance(args[0], Path) or mock.ANY
            # Second and third args should be version strings
            assert args[1] == "1.2.3"
            assert args[2] == "1.2.4"

    @patch("update_version.logger.warning")
    @patch("update_version.VersionUpdater.update_file")
    def test_no_files_defined_for_component(self, mock_update_file, mock_logger_warning, version_updater, versions):
        """Test handling when no files are defined for a component."""
        component = "test_component"
        version_updater.config.files = {
            "another_component": {"file1": MagicMock()}
        }

        version_updater.update_version(versions["old"], versions["new"], component)

        assert mock_update_file.call_count == 0

        assert mock_logger_warning.call_count == 1
        assert mock_logger_warning.call_args[0][0] == f"No files defined for component: {component}"

    @patch("update_version.logger.warning")
    @patch("update_version.VersionUpdater.update_file")
    def test_file_does_not_exist(self, mock_update_file, mock_logger_warning, version_updater, versions):
        """Test handling when a file defined for a component doesn't exist."""
        component = "test_component"

        file_info = MagicMock(spec=FileInfo)
        file_info.path = MagicMock(spec=Path)
        file_info.path.exists.return_value = False

        version_updater.config.files = {
            component: {"config_file": file_info}
        }

        version_updater.update_version(versions["old"], versions["new"], component)

        assert mock_update_file.call_count == 0

        assert mock_logger_warning.call_count == 1
        assert mock_logger_warning.call_args[0][0] == f"File {file_info.path} does not exist, skipping"
