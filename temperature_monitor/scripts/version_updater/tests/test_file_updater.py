from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

from update_version import FileUpdater


class TestFileUpdater:
    """Test the FileUpdater class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = MagicMock()
        self.file_updater = FileUpdater(self.version_manager)
    import pytest
    from pathlib import Path
    from update_version import FileUpdater

    def test_read_file_success(self, tmp_path):
        """Test reading a file successfully."""
        test_file = tmp_path / "test_file.txt"
        content = "This is a test file."
        test_file.write_text(content, encoding="utf-8")

        result = FileUpdater._read_file(test_file)

        assert result == content

    def test_read_file_not_found(self):
        """Test reading from a non-existent file."""
        nonexistent_file = Path("nonexistent_file.txt")

        with pytest.raises(IOError, match="Could not read file"):
            FileUpdater._read_file(nonexistent_file)

    def test_read_file_permission_error(self, tmp_path):
        """Test reading a file with permission issues."""
        test_file = tmp_path / "test_file.txt"
        test_file.touch(mode=0o000)  # Make file unreadable

        with pytest.raises(IOError, match="Could not read file"):
            FileUpdater._read_file(test_file)

    def test_write_file(self):
        """Test writing to a file."""
        mock_content = "new content"
        with patch("builtins.open", mock_open()) as mock_file:
            self.file_updater._write_file(Path("test_file.py"), mock_content)
            mock_file.assert_called_once_with(Path("test_file.py"), "w", encoding="utf-8")
            mock_file.write.assert_called_once_with(mock_content)

    def test_write_file_error(self):
        """Test writing to a file with error."""
        with patch("builtins.open", side_effect=IOError("Error")):
            with pytest.raises(IOError):
                self.file_updater._write_file(Path("test_file.py"), "content")

    @patch("os.path.exists")
    def test_update_file(self, mock_exists):
        """Test updating a file."""
        mock_exists.return_value = True
        mock_content = "version = 1.2.3"
        mock_updated_content = "version = 2.0.0"
        with patch.object(self.file_updater, "_read_file", return_value=mock_content):
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file(Path("test_file.py"), "1.2.3", "2.0.0")
                mock_write.assert_called_once_with(Path("test_file.py"), mock_updated_content)

    @patch("os.path.exists")
    def test_update_file_no_changes(self, mock_exists):
        """Test updating a file with no changes."""
        mock_exists.return_value = True
        mock_content = "no version here"
        with patch.object(self.file_updater, "_read_file", return_value=mock_content):
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file(Path("test_file.py"), "1.2.3", "2.0.0")
                mock_write.assert_not_called()

    @patch("os.path.exists")
    def test_update_nonexistent_file(self, mock_exists):
        """Test updating a non-existent file."""
        mock_exists.return_value = False
        with patch.object(self.file_updater, "_read_file") as mock_read:
            with patch.object(self.file_updater, "_write_file") as mock_write:
                self.file_updater.update_file(Path("nonexistent.py"), "1.2.3", "2.0.0")
                mock_read.assert_not_called()
                mock_write.assert_not_called()
