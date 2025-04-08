import pytest
from pathlib import Path
from update_version import FileUpdater

class TestFileUpdater:
    """Test the FileUpdater class."""

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