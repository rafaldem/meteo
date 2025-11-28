import pytest
from pathlib import Path
from unittest.mock import mock_open, patch
from update_version import FileUpdater, VersionManager, StructuredLogger, LoggingConfig


class TestFileUpdater:
    """Test cases for the FileUpdater class."""

    @pytest.fixture
    def logging_config(self):
        """Create a LoggingConfig instance for testing."""
        return LoggingConfig()

    @pytest.fixture
    def structured_logger(self, logging_config):
        """Create a StructuredLogger instance for testing."""
        return StructuredLogger(logging_config)

    @pytest.fixture
    def version_manager(self, structured_logger):
        """Create a StructuredLogger instance for testing."""
        return VersionManager(structured_logger)

    @pytest.fixture
    def file_updater(self, structured_logger, version_manager):
        """Create a FileUpdater instance for testing."""
        return FileUpdater(version_manager, structured_logger)

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

        mock_file.assert_called_once_with("w", encoding="utf-8")
        mock_file().write.assert_called_once_with(test_content)

    @patch('pathlib.Path.open')
    def test_write_file_exception(self, mock_path_open):
        """Test that _write_file raises IOError when file cannot be written."""
        # Set up the mock to raise an IOError when opened
        mock_path_open.side_effect = IOError("Permission denied")

        # Create a test file path and content
        test_file_path = Path("/test/path/file.txt")
        test_content = "Test content"

        # Verify that the method raises IOError with the expected message
        with pytest.raises(IOError) as excinfo:
            FileUpdater._write_file(test_file_path, test_content)

        # Check that the error message contains the file path and original error
        assert "Could not write to file" in str(excinfo.value)
        assert str(test_file_path) in str(excinfo.value)
        assert "Permission denied" in str(excinfo.value)

        # Verify that the mock was called with the correct arguments
        mock_path_open.assert_called_once_with("w", encoding="utf-8")

    @patch("update_version.FileUpdater._read_file")
    @patch("update_version.FileUpdater._write_file")
    def test_update_file_success(self, mock_write, mock_read, file_updater, tmp_path):
        """Test updating version in a file successfully."""
        test_file = tmp_path / "test_file.txt"
        old_content = 'version = "1.2.3"'
        new_content = 'version = "1.2.4"'

        with patch.object(Path, "exists", return_value=True):
            mock_read.return_value = old_content

            file_updater.update_file(test_file, "1.2.3", "1.2.4")

            mock_read.assert_called_once_with(test_file)
            mock_write.assert_called_once_with(test_file, new_content)

    @patch("update_version.FileUpdater._read_file")
    @patch("update_version.FileUpdater._write_file")
    def test_update_file_no_version(self, mock_write, mock_read, file_updater, tmp_path):
        """Test updating a file with no version info."""
        test_file = tmp_path / "test_file.txt"
        content = "No version info here"

        with patch.object(Path, "exists", return_value=True):
            mock_read.return_value = content

            file_updater.update_file(test_file, "1.2.3", "1.2.4")

            mock_read.assert_called_once_with(test_file)
            mock_write.assert_not_called()

    def test_update_file_nonexistent_file(self, file_updater):
        """Test that update_file handles non-existing files correctly."""

        # Create spy objects for the internal methods to verify they aren't called
        with patch.object(file_updater, '_read_file') as mock_read_file, \
                patch.object(file_updater, '_write_file') as mock_write_file, \
                patch('update_version.logger') as mock_logger, \
                patch('pathlib.Path.exists', return_value=False):

            # Call the method with a test file path and versions
            test_file_path = Path("/test/path/nonexistent_file.txt")
            old_version = "1.0.0"
            new_version = "1.1.0"

            # Execute the method
            file_updater.update_file(test_file_path, old_version, new_version)

            # Verify that the method logs a warning
            mock_logger.warning.assert_called_once_with(
                f"File {test_file_path} does not exist, skipping"
            )

            # Verify that _read_file and _write_file are not called
            mock_read_file.assert_not_called()
            mock_write_file.assert_not_called()
