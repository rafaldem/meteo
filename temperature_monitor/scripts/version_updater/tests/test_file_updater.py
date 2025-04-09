import pytest
from pathlib import Path
from unittest.mock import mock_open, patch
from update_version import FileUpdater, VersionManager


class TestFileUpdater:
    """Test cases for the FileUpdater class."""

    @pytest.fixture
    def file_updater(self):
        """Create a FileUpdater instance for testing."""
        return FileUpdater(VersionManager())

    def test_read_file_success(self, file_updater, tmp_path):
        """Test reading a file successfully."""
        test_file = tmp_path / "test_file.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        result = file_updater._read_file(test_file)
        assert result == test_content

    def test_read_file_nonexistent(self, file_updater):
        """Test reading a nonexistent file raises IOError."""
        with pytest.raises(IOError):
            file_updater._read_file(Path("nonexistent_file.txt"))

    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_write_file_success(self, mock_file, file_updater, tmp_path):
        """Test writing to a file successfully."""
        test_file = tmp_path / "test_file.txt"
        test_content = "New content"

        file_updater._write_file(test_file, test_content)

        # Check that the file was opened for writing
        mock_file.assert_called_once_with("w", encoding="utf-8")
        # Check that write was called with the content
        mock_file().write.assert_called_once_with(test_content)

    @patch("update_version.FileUpdater._read_file")
    @patch("update_version.FileUpdater._write_file")
    def test_update_file_success(self, mock_write, mock_read, file_updater, tmp_path):
        """Test updating version in a file successfully."""
        test_file = tmp_path / "test_file.txt"
        old_content = "version = '1.2.3'"
        new_content = "version = '1.2.4'"

        # Mock file exists
        with patch.object(Path, "exists", return_value=True):
            # Mock read_file to return old content
            mock_read.return_value = old_content

            file_updater.update_file(test_file, "1.2.3", "1.2.4")

            # Check that read_file was called
            mock_read.assert_called_once_with(test_file)
            # Check that write_file was called with updated content
            mock_write.assert_called_once_with(test_file, new_content)

    @patch("update_version.FileUpdater._read_file")
    @patch("update_version.FileUpdater._write_file")
    def test_update_file_no_version(self, mock_write, mock_read, file_updater, tmp_path):
        """Test updating a file with no version info."""
        test_file = tmp_path / "test_file.txt"
        content = "No version info here"

        # Mock file exists
        with patch.object(Path, "exists", return_value=True):
            # Mock read_file to return content without version
            mock_read.return_value = content

            file_updater.update_file(test_file, "1.2.3", "1.2.4")

            # Check that read_file was called
            mock_read.assert_called_once_with(test_file)
            # Check that write_file was not called since content didn't change
            mock_write.assert_not_called()
