import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

from update_version import (
    VersionUpdaterCLI,
    VersionConfig,
    BumpType,
    Component,
    Version,
    VersionManager,
    VersionUpdater,
    FileUpdater,
    setup_logging,
    FileInfo
)


@pytest.fixture
def fresh_logger():
    """
    Fixture providing a fresh logger with no handlers for testing.

    This ensures each test starts with a clean logger state.
    """
    test_logger = logging.getLogger("test_logger")
    # Store original handlers
    original_handlers = test_logger.handlers.copy()
    # Clear handlers for the test
    test_logger.handlers = []

    yield test_logger

    # Restore original handlers after the test
    test_logger.handlers = original_handlers


class TestSetupLogging:
    """
    Tests for the setup_logging function.

    These tests verify that the logger is configured correctly with appropriate handlers.
    """

    def test_setup_logging_debug_mode(self, fresh_logger):
        """
        Test setup_logging function when debug mode is enabled.
        Verifies that appropriate handlers are added to the logger.
        """
        with patch("update_version.logger", fresh_logger):
            # Call the function with debug level
            setup_logging()

            # Verify that handlers were added
            assert len(fresh_logger.handlers) == 2

            # Check handler types and levels
            # Explicitly check for StreamHandler (but not its subclasses)
            console_handlers = [h for h in fresh_logger.handlers if type(h) is logging.StreamHandler]
            file_handlers = [h for h in fresh_logger.handlers if type(h) is logging.FileHandler]

            assert len(console_handlers) == 1
            assert len(file_handlers) == 1

            # In debug mode, both handlers should capture detailed logs
            assert console_handlers[0].level == logging.INFO
            assert file_handlers[0].level == logging.DEBUG

    def test_setup_logging_normal_mode(self, fresh_logger):
        """
        Test setup_logging function in normal mode (non-debug).
        Verifies that appropriate handlers are added to the logger.
        """
        with patch("update_version.logger", fresh_logger):
            # Call the function with default settings
            setup_logging()

            # Verify that handlers were added
            assert len(fresh_logger.handlers) == 2

            # Explicitly check for StreamHandler (but not its subclasses)
            console_handlers = [h for h in fresh_logger.handlers if type(h) is logging.StreamHandler]
            file_handlers = [h for h in fresh_logger.handlers if type(h) is logging.FileHandler]

            assert len(console_handlers) == 1
            assert len(file_handlers) == 1

            # Verify console handler shows info while file handler stores more details
            assert console_handlers[0].level == logging.INFO
            assert file_handlers[0].level == logging.DEBUG


class TestLogDebugReturn:
    """
    Tests for the log_debug_return decorator.

    This test confirms that the decorator correctly logs the return value of functions.
    """

    def test_log_debug_return_functionality(self):
        """
        Test that log_debug_return correctly logs the function return value.
        """
        # Create a test function with the decorator
        @patch("update_version.logger")
        def test_decorated_function(mock_logger):
            # Define a function locally that uses the decorator from update_version
            from update_version import log_debug_return

            @log_debug_return
            def test_func():
                return "test_value"

            # Call the function
            inner_result = test_func()

            # Verify logger was called with the right message
            mock_logger.debug.assert_called_once()
            log_message = mock_logger.debug.call_args[0][0]
            assert "test_func" in log_message
            assert "test_value" in log_message

            return inner_result

        # Call the test function and verify it returns the expected value
        result = test_decorated_function()
        assert result == "test_value"


class TestFileUpdaterEdgeCases:
    """
    Tests for edge cases in the FileUpdater class.

    These tests verify that the FileUpdater correctly handles IO errors.
    """

    def test_read_file_io_error(self):
        """
        Test _read_file method when IO error occurs.
        Verifies that IOError is properly propagated.
        """
        # Create a mock version manager
        mock_version_manager = MagicMock()
        file_updater = FileUpdater(mock_version_manager)

        # Create a file path for testing
        test_file_path = Path("nonexistent_file.py")

        # Simulate file opening raising an IOError
        original_error_msg = "File not found"

        # Must patch the specific open method being used
        with patch("pathlib.Path.open", side_effect=IOError(original_error_msg)):
            with pytest.raises(IOError) as excinfo:
                file_updater._read_file(test_file_path)

            # Verify error message contains the original message
            assert original_error_msg in str(excinfo.value)

    def test_write_file_io_error(self):
        """
        Test _write_file method when IO error occurs.
        Verifies that IOError is properly propagated.
        """
        # Create a mock version manager
        mock_version_manager = MagicMock()
        file_updater = FileUpdater(mock_version_manager)

        # Create a file path for testing
        test_file_path = Path("readonly_file.py")
        content = "test content"

        # Simulate file opening raising an IOError during write
        original_error_msg = "Permission denied"

        # Must patch the specific open method being used
        with patch("pathlib.Path.open", side_effect=IOError(original_error_msg)):
            with pytest.raises(IOError) as excinfo:
                file_updater._write_file(test_file_path, content)

            # Verify error message contains the original message
            assert original_error_msg in str(excinfo.value)


class TestVersionManagerEdgeCases:
    """
    Tests for edge cases in the VersionManager class.

    These tests verify that the VersionManager correctly handles invalid inputs.
    """

    def test_parse_version_with_invalid_format(self):
        """
        Test parse_version with an invalid version format.
        Verifies that ValueError is raised for invalid formats.
        """
        version_manager = VersionManager()

        # Test with invalid version format
        with pytest.raises(ValueError) as excinfo:
            version_manager.parse_version("invalid_version")

        # Verify error message mentions invalid format
        assert "Invalid version format" in str(excinfo.value)

    def test_bump_version_with_invalid_operation(self):
        """
        Test bump_version with an invalid operation.
        Verifies that ValueError is raised for invalid operations.
        """
        version_manager = VersionManager()
        version = Version(1, 2, 3)

        # Test with invalid operation (SET with no value)
        with pytest.raises(ValueError) as excinfo:
            version_manager.bump_version(
                version, Component.MAJOR, BumpType.SET, None
            )

        # Verify error message mentions invalid operation
        assert "Invalid bump operation" in str(excinfo.value)


class TestVersionUpdaterErrors:
    """
    Tests for error handling in the VersionUpdater class.

    These tests verify that the VersionUpdater correctly handles various error conditions.
    """

    def test_get_current_version_file_not_found(self):
        """
        Test get_current_version when the version file doesn't exist.
        Verifies that the appropriate error is raised.
        """
        # Create mock components
        mock_version_manager = MagicMock()
        mock_config = MagicMock(spec=VersionConfig)

        # Create a file info object for testing
        file_info = FileInfo(
            path=Path("nonexistent_file.py"),
            pattern=r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
        )

        # Create the VersionUpdater instance
        version_updater = VersionUpdater(mock_version_manager, mock_config)

        # Patch the _read_file method to raise IOError
        with patch.object(
                FileUpdater, "_read_file", side_effect=IOError("File not found")
        ):
            # Test the method, should raise IOError
            with pytest.raises(IOError) as excinfo:
                version_updater.get_current_version(file_info)

            # Verify error message
            assert "File not found" in str(excinfo.value)

    def test_get_current_version_no_version_found(self):
        """
        Test get_current_version when no version information is found in the file.
        Verifies that ValueError is raised.
        """
        # Create mock components
        mock_version_manager = MagicMock()
        mock_config = MagicMock(spec=VersionConfig)

        # Create a file info object for testing
        file_info = FileInfo(
            path=Path("version.py"),
            pattern=r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"'
        )

        # Create the VersionUpdater instance
        version_updater = VersionUpdater(mock_version_manager, mock_config)

        # Mock _read_file to return content without version info
        with patch.object(
                FileUpdater, "_read_file", return_value="# No version here"
        ):
            # Test the method, should raise ValueError
            with pytest.raises(ValueError) as excinfo:
                version_updater.get_current_version(file_info)

            # Verify error message mentions no version found
            assert "Could not find version information" in str(excinfo.value)


class TestVersionUpdaterCLIAdditional:
    """
    Additional tests for the VersionUpdaterCLI class.

    These tests verify that the CLI handles error conditions correctly.
    """

    def test_run_with_set_action_missing_value(self):
        """
        Test run method when 'set' action is used without a value.
        Verifies that the method returns an error code.
        """
        # Create CLI instance
        cli = VersionUpdaterCLI()

        # Create a mock for parse_arguments that returns args with missing value
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.action = "set"
            args.value = None  # Missing required value
            args.log_level = "info"
            mock_parse.return_value = args

            # Call run method and verify it returns error code
            result = cli.run()
            assert result == 1

    def test_run_with_nonexistent_component_file(self):
        """
        Test run method when component file doesn't exist.
        Verifies that the method returns an error code.
        """
        # Create CLI instance
        cli = VersionUpdaterCLI()

        # Mock parse_arguments to return valid args
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "backend"
            args.action = "increment"
            args.bump_type = "patch"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock Path.exists to return False for version file
            with patch("pathlib.Path.exists", return_value=False):
                # Call run method and verify it returns error code
                result = cli.run()
                assert result == 1


@pytest.fixture
def cli_fixture():
    """
    Fixture providing a VersionUpdaterCLI instance with mocked dependencies.

    This allows tests to verify behavior without actual file system operations.
    """
    # Create mocks for dependencies
    mock_config = MagicMock(spec=VersionConfig)
    mock_version_manager = MagicMock(spec=VersionManager)
    mock_version_updater = MagicMock(spec=VersionUpdater)

    # Configure mock_config.files with necessary structure
    # The run method needs files for 'setup', 'frontend', and 'backend'
    mock_file_info = MagicMock()
    mock_file_info.path.exists.return_value = True

    mock_config.files = {
        'setup': {'setup.py': mock_file_info},
        'frontend': {'version.py': mock_file_info},
        'backend': {'version.py': mock_file_info}
    }

    # Create CLI instance with mocks
    cli = VersionUpdaterCLI(config=mock_config)
    cli.version_manager = mock_version_manager
    cli.version_updater = mock_version_updater

    # Return CLI and mocks for use in tests
    return cli, mock_config, mock_version_manager, mock_version_updater


class TestVersionUpdaterCLI:
    """
    Test suite for the VersionUpdaterCLI class.

    Tests command-line argument parsing and execution behavior of the version
    updater's command-line interface.
    """

    def test_parse_arguments_defaults(self):
        """
        Test that default arguments are correctly handled when no CLI args are provided.
        """
        cli = VersionUpdaterCLI()

        # Simulate empty command line arguments
        with patch("sys.argv", ["update_version.py"]):
            args = cli.parse_arguments()

        # Verify default values match expected defaults from implementation
        assert args.component == "both"
        assert args.bump_type == "patch"
        assert args.action == "increment"
        assert args.value is None
        assert args.log_level == "info"

    @pytest.mark.parametrize(
        "component,bump_type,action,value,expected_exit_code",
        [
            # Valid combinations
            ("backend", "patch", "increment", None, 0),
            ("frontend", "minor", "increment", None, 0),
            ("both", "major", "increment", None, 0),
            ("backend", "patch", "set", 5, 0),
            # Invalid combinations
            ("backend", "patch", "set", None, 1),  # Missing value for set action
            ("invalid", "patch", "increment", None, 1),  # Invalid component
        ],
    )
    def test_run_with_different_parameters(
            self, cli_fixture, component, bump_type, action, value, expected_exit_code
    ):
        """
        Test run method with different parameter combinations.

        Args:
            component: Component to update (backend, frontend, both)
            bump_type: Version part to modify (major, minor, patch)
            action: Action to perform (increment, set)
            value: Value to set when using set action
            expected_exit_code: Expected return code from run method
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Mock Path.exists to avoid file system dependency
        with patch("pathlib.Path.exists", return_value=True):
            # Mock parse_arguments to return our test parameters
            with patch.object(cli, "parse_arguments") as mock_parse:
                args = MagicMock()
                args.component = component
                args.bump_type = bump_type
                args.action = action
                args.value = value
                args.log_level = "info"
                mock_parse.return_value = args

                # Run the CLI and check the result
                result = cli.run()
                assert result == expected_exit_code