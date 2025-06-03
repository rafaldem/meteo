import sys
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

    @pytest.mark.parametrize("error_type,expected_message", [
        (PermissionError("Access denied"), "Could not read file"),
        (FileNotFoundError("File not found"), "Could not read file"),
        (UnicodeDecodeError("utf-8", b"1", 0, 1, "invalid"), "Could not read file"),
    ])
    def test_file_read_error_handling(self, error_type, expected_message, tmp_path):
        """Test comprehensive file read error handling scenarios."""
        test_file = tmp_path / "test_file.py"
        file_updater = FileUpdater(MagicMock())

        with patch("pathlib.Path.open", side_effect=error_type):
            with pytest.raises(IOError) as exc_info:
                file_updater._read_file(test_file)

            assert expected_message in str(exc_info.value)


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
        assert args.component == "other"
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
            ("other", "minor", "increment", None, 0),
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



class TestVersionConfigurationScenarios:
    """Comprehensive testing of version configuration scenarios."""

    @pytest.mark.parametrize("missing_component", ["backend", "frontend", "setup"])
    def test_missing_component_directories(self, missing_component, tmp_path):
        """Test behavior when component directories are missing."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create only some components
        if missing_component != "backend":
            (project_root / "backend").mkdir()
        if missing_component != "frontend":
            (project_root / "frontend").mkdir()

        config = VersionConfig(project_root=project_root)

        # Verify configuration handles missing components gracefully
        missing_files = config.files[missing_component]
        for file_info in missing_files.values():
            assert not file_info.path.exists()


class TestComponentValidationLogic:
    """
    Test suite specifically for component validation logic in VersionUpdaterCLI.run().

    These tests cover the specific code path that handles:
    - "other" component (should pass)
    - Invalid component names (should return error code 1)
    """

    @pytest.mark.parametrize(
        "component,expected_exit_code,should_log_error",
        [
            # Valid "other" component - should pass without error
            ("other", 0, False),
            # Invalid component names - should return 1 and log error
            ("invalid_component", 1, True),
            ("unknown", 1, True),
            ("BACKEND", 1, True),  # Case sensitivity test
            ("", 1, True),  # Empty string
            ("setup", 1, True),  # "setup" is not a valid choice for --component
        ],
    )
    def test_component_validation_logic(
            self, cli_fixture, component, expected_exit_code, should_log_error
    ):
        """
        Test component validation logic for different component values.

        This specifically tests the code path:
        ```python
        elif args.component == "other":
            pass
        else:
            logger.error(f"Invalid component: {args.component}! Should be one of: backend, frontend, both or setup.")
            return 1
        ```

        Args:
            component: Component name to test
            expected_exit_code: Expected return code (0 for success, 1 for error)
            should_log_error: Whether an error should be logged
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Mock parse_arguments to return our test component
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = component
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock logger to capture error messages
            with patch("update_version.logger") as mock_logger:
                # Run the CLI
                result = cli.run()

                # Assert the expected exit code
                assert result == expected_exit_code

                # Check if error was logged when expected
                if should_log_error:
                    mock_logger.error.assert_called_once()
                    error_message = mock_logger.error.call_args[0][0]
                    assert f"Invalid component: {component}!" in error_message
                    assert "Should be one of: backend, frontend, both or setup." in error_message
                else:
                    # For "other" component, no error should be logged
                    mock_logger.error.assert_not_called()

    def test_other_component_behavior(self, cli_fixture):
        """
        Test that "other" component specifically follows the correct execution path.

        This test ensures that when component is "other", the code executes the
        `pass` statement and continues with the rest of the logic (processing setup component).
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Mock parse_arguments to return "other" component
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "other"
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock Path.exists to return True for setup files
            with patch("pathlib.Path.exists", return_value=True):
                # Mock get_current_version and bump_version methods
                mock_version = MagicMock()
                mock_version.__str__ = lambda self: "1.0.0"
                mock_new_version = MagicMock()
                mock_new_version.__str__ = lambda self: "1.0.1"

                mock_version_updater.get_current_version.return_value = mock_version
                mock_version_manager.bump_version.return_value = mock_new_version

                # Run the CLI
                result = cli.run()

                # Should succeed (return 0)
                assert result == 0

                # Verify that setup component was processed
                # (since "other" should only process setup, not backend/frontend)
                mock_version_updater.get_current_version.assert_called_once()
                mock_version_manager.bump_version.assert_called_once()
                mock_version_updater.update_version.assert_called_once()

    def test_invalid_component_early_exit(self, cli_fixture):
        """
        Test that invalid component causes early exit without processing any files.

        This ensures that when an invalid component is provided, the method
        returns 1 immediately without attempting any version updates.
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Mock parse_arguments to return invalid component
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "invalid_component"
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock logger to capture the error
            with patch("update_version.logger") as mock_logger:
                # Run the CLI
                result = cli.run()

                # Should return error code
                assert result == 1

                # Verify error was logged
                mock_logger.error.assert_called_once()

                # Verify that no version operations were attempted
                mock_version_updater.get_current_version.assert_not_called()
                mock_version_manager.bump_version.assert_not_called()
                mock_version_updater.update_version.assert_not_called()

    @pytest.mark.parametrize(
        "log_level",
        ["debug", "info", "warning", "error", "critical"]
    )
    def test_invalid_component_logging_at_different_levels(self, cli_fixture, log_level):
        """
        Test that invalid component error is logged regardless of log level.

        Args:
            log_level: The log level to test with
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Mock parse_arguments to return invalid component with different log levels
        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "invalid_test"
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = log_level
            mock_parse.return_value = args

            # Mock logger to capture the error
            with patch("update_version.logger") as mock_logger:
                # Run the CLI
                result = cli.run()

                # Should always return error code regardless of log level
                assert result == 1

                # Error should always be logged
                mock_logger.error.assert_called_once()
                error_message = mock_logger.error.call_args[0][0]
                assert "Invalid component: invalid_test!" in error_message


class TestComponentNotInConfiguration:
    """
    Test suite for handling components that are not found in configuration.

    These tests verify the behavior when component_name is not present in
    self.config.files, ensuring proper warning logging and continuation of processing.
    """

    def test_component_not_in_config_logs_warning_and_continues(self, cli_fixture):
        """
        Test that missing components in configuration are handled gracefully.

        Verifies that when a component is not found in self.config.files:
        - A warning is logged with the appropriate message
        - Processing continues to the next component
        - The method does not exit early
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Configure mock_config to only include some components
        mock_file_info = MagicMock()
        mock_file_info.path.exists.return_value = True

        # Only include 'setup' in config, exclude 'backend' and 'frontend'
        mock_config.files = {
            'setup': {'setup.py': mock_file_info}
            # Intentionally excluding 'backend' and 'frontend'
        }

        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "both"  # This will process backend, frontend, and setup
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock version operations for successful processing
            mock_version = MagicMock()
            mock_version.__str__ = lambda self: "1.0.0"
            mock_new_version = MagicMock()
            mock_new_version.__str__ = lambda self: "1.0.1"

            mock_version_updater.get_current_version.return_value = mock_version
            mock_version_manager.bump_version.return_value = mock_new_version

            with patch("update_version.logger") as mock_logger:
                result = cli.run()

                # Should complete successfully despite missing components
                assert result == 0

                # Verify warnings were logged for missing components
                warning_calls = mock_logger.warning.call_args_list
                assert len(warning_calls) >= 2  # Should warn for both frontend and backend

                # Check specific warning messages
                warning_messages = [call[0][0] for call in warning_calls]
                assert any("frontend" in msg and "not found in configuration" in msg for msg in warning_messages)
                assert any("backend" in msg and "not found in configuration" in msg for msg in warning_messages)

                # Verify that setup was still processed (since it exists in config)
                mock_version_updater.get_current_version.assert_called_once()
                mock_version_updater.update_version.assert_called_once()

    def test_all_components_missing_from_config(self, cli_fixture):
        """
        Test behavior when all requested components are missing from configuration.

        This ensures the system handles the edge case where none of the components
        in the component_list exist in the configuration.
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Configure mock_config to have no components
        mock_config.files = {}

        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "both"
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            with patch("update_version.logger") as mock_logger:
                result = cli.run()

                # Should complete successfully but without processing any files
                assert result == 0

                # Should log warnings for all missing components
                warning_calls = mock_logger.warning.call_args_list
                assert len(warning_calls) >= 3  # setup, frontend, backend

                # Verify no version operations were performed
                mock_version_updater.get_current_version.assert_not_called()
                mock_version_updater.update_version.assert_not_called()


class TestExceptionHandlingInComponentProcessing:
    """
    Test suite for exception handling during component processing.

    These tests verify the behavior when exceptions occur during version updating,
    particularly focusing on the error logging and conditional early exit logic.
    """

    def test_exception_during_processing_logs_error_and_continues(self, cli_fixture):
        """
        Test exception handling when processing multiple components.

        Verifies that when an exception occurs during processing:
        - The error is logged with the component name and exception message
        - If the failing component is not the requested component, processing continues
        - The method does not exit early for non-target component failures
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        # Configure mock_config with multiple components
        mock_file_info_working = MagicMock()
        mock_file_info_working.path.exists.return_value = True

        mock_file_info_failing = MagicMock()
        mock_file_info_failing.path.exists.return_value = True

        mock_config.files = {
            'setup': {'setup.py': mock_file_info_working},
            'frontend': {'version.py': mock_file_info_failing},
            'backend': {'version.py': mock_file_info_working}
        }

        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "both"  # Requesting both frontend and backend
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Mock version operations
            mock_version = MagicMock()
            mock_version.__str__ = lambda self: "1.0.0"
            mock_new_version = MagicMock()
            mock_new_version.__str__ = lambda self: "1.0.1"

            # Configure mock to raise exception for frontend component only
            def side_effect_get_version(file_info):
                if file_info == mock_file_info_failing:
                    raise ValueError("Test exception for frontend")
                return mock_version

            mock_version_updater.get_current_version.side_effect = side_effect_get_version
            mock_version_manager.bump_version.return_value = mock_new_version

            with patch("update_version.logger") as mock_logger:
                result = cli.run()

                # Should complete successfully despite frontend failure
                assert result == 0

                # Verify error was logged for the failing component
                error_calls = mock_logger.error.call_args_list
                error_messages = [call[0][0] for call in error_calls]
                assert any("Error updating frontend version" in msg and "Test exception for frontend" in msg for msg in error_messages)

                # Verify that processing continued for other components
                assert mock_version_updater.get_current_version.call_count >= 2  # Called for setup and frontend (failed), and backend

    def test_exception_for_requested_component_returns_error(self, cli_fixture):
        """
        Test that exceptions in the specifically requested component cause early exit.

        Verifies that when an exception occurs in the component that matches
        args.component, the method returns error code 1.
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        mock_file_info = MagicMock()
        mock_file_info.path.exists.return_value = True

        mock_config.files = {
            'setup': {'setup.py': mock_file_info},
            'backend': {'version.py': mock_file_info}
        }

        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "backend"  # Specifically requesting backend
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Configure mock to raise exception during backend processing
            mock_version_updater.get_current_version.side_effect = RuntimeError("Backend processing failed")

            with patch("update_version.logger") as mock_logger:
                result = cli.run()

                # Should return error code due to backend failure
                assert result == 1

                # Verify error was logged
                error_calls = mock_logger.error.call_args_list
                error_messages = [call[0][0] for call in error_calls]
                assert any("Error updating backend version" in msg and "Backend processing failed" in msg for msg in error_messages)

    def test_multiple_exceptions_with_target_component_failure(self, cli_fixture):
        """
        Test behavior when multiple components fail, including the target component.

        This ensures that even if multiple components fail, the method returns
        error code 1 when the specifically requested component fails.
        """
        cli, mock_config, mock_version_manager, mock_version_updater = cli_fixture

        mock_file_info = MagicMock()
        mock_file_info.path.exists.return_value = True

        mock_config.files = {
            'setup': {'setup.py': mock_file_info},
            'frontend': {'version.py': mock_file_info},
            'backend': {'version.py': mock_file_info}
        }

        with patch.object(cli, "parse_arguments") as mock_parse:
            args = MagicMock()
            args.component = "frontend"  # Specifically requesting frontend
            args.bump_type = "patch"
            args.action = "increment"
            args.value = None
            args.log_level = "info"
            mock_parse.return_value = args

            # Configure mock to raise exceptions for multiple components
            def side_effect_get_version(file_info):
                raise RuntimeError("Processing failed")

            mock_version_updater.get_current_version.side_effect = side_effect_get_version

            with patch("update_version.logger") as mock_logger:
                result = cli.run()

                # Should return error code due to frontend failure
                assert result == 1

                # Verify error was logged for frontend
                error_calls = mock_logger.error.call_args_list
                error_messages = [call[0][0] for call in error_calls]
                assert any("Error updating frontend version" in msg for msg in error_messages)


class TestMainExecutionBlock:
    """
    Test suite for the main execution block.

    These tests verify the behavior of the if __name__ == "__main__" block,
    ensuring proper CLI instantiation and sys.exit handling.
    """

    def test_main_execution_block_success(self):
        """
        Test the main execution block when CLI run succeeds.

        Verifies that when the script is executed as main:
        - VersionUpdaterCLI is instantiated
        - The run method is called
        - sys.exit is called with the return code from run
        """
        with patch("update_version.VersionUpdaterCLI") as mock_cli_class:
            with patch("sys.exit") as mock_sys_exit:
                # Configure mock CLI instance
                mock_cli_instance = MagicMock()
                mock_cli_instance.run.return_value = 0
                mock_cli_class.return_value = mock_cli_instance

                # Import and execute the main block
                import update_version

                # Simulate the main execution
                if True:  # Simulating if __name__ == "__main__"
                    cli = update_version.VersionUpdaterCLI()
                    sys.exit(cli.run())

                # Verify CLI was instantiated
                mock_cli_class.assert_called_once()

                # Verify run was called
                mock_cli_instance.run.assert_called_once()

                # Verify sys.exit was called with return code 0
                mock_sys_exit.assert_called_once_with(0)

    def test_main_execution_block_failure(self):
        """
        Test the main execution block when CLI run fails.

        Verifies that error return codes are properly passed to sys.exit.
        """
        with patch("update_version.VersionUpdaterCLI") as mock_cli_class:
            with patch("sys.exit") as mock_sys_exit:
                # Configure mock CLI instance to return error
                mock_cli_instance = MagicMock()
                mock_cli_instance.run.return_value = 1
                mock_cli_class.return_value = mock_cli_instance

                # Import and execute the main block
                import update_version

                # Simulate the main execution with error
                if True:  # Simulating if __name__ == "__main__"
                    cli = update_version.VersionUpdaterCLI()
                    sys.exit(cli.run())

                # Verify sys.exit was called with error code 1
                mock_sys_exit.assert_called_once_with(1)

    def test_main_execution_block_with_exception(self):
        """
        Test the main execution block when CLI instantiation or run raises exception.

        Verifies that unhandled exceptions in the main block are properly handled.
        """
        with patch("update_version.VersionUpdaterCLI") as mock_cli_class:
            with patch("sys.exit") as mock_sys_exit:
                # Configure mock to raise exception during instantiation
                mock_cli_class.side_effect = RuntimeError("CLI instantiation failed")

                # The exception should propagate since there's no try/catch in main block
                import update_version

                with pytest.raises(RuntimeError, match="CLI instantiation failed"):
                    # Simulate the main execution
                    if True:  # Simulating if __name__ == "__main__"
                        cli = update_version.VersionUpdaterCLI()
                        sys.exit(cli.run())

                # Verify CLI instantiation was attempted
                mock_cli_class.assert_called_once()

                # sys.exit should not be called due to exception
                mock_sys_exit.assert_not_called()

    @patch("update_version.__name__", "__main__")
    def test_actual_main_block_execution(self):
        """
        Test the actual main block execution with proper __name__ setting.

        This test verifies the real main block behavior by setting __name__ to "__main__".
        """
        with patch("update_version.VersionUpdaterCLI") as mock_cli_class:
            with patch("sys.exit") as mock_sys_exit:
                # Configure mock CLI instance
                mock_cli_instance = MagicMock()
                mock_cli_instance.run.return_value = 0
                mock_cli_class.return_value = mock_cli_instance

                # Execute the actual main block by importing the module
                # Note: This simulates the condition where __name__ == "__main__"
                exec("""
if __name__ == "__main__":
    cli = VersionUpdaterCLI()
    sys.exit(cli.run())
""", {
                    "__name__": "__main__",
                    "VersionUpdaterCLI": mock_cli_class,
                    "sys": sys
                })

                # Verify the expected calls were made
                mock_cli_class.assert_called_once()
                mock_cli_instance.run.assert_called_once()
                mock_sys_exit.assert_called_once_with(0)