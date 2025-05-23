import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from update_version import (
    VersionUpdaterCLI,
    VersionConfig,
    BumpType,
    Component,
    Version,
    VersionManager,
    VersionUpdater,
)

class TestVersionUpdaterCLI:
    """
    Test suite for the VersionUpdaterCLI class.

    Tests command-line argument parsing and execution behavior of the version
    updater's command-line interface.
    """

    def test_parse_arguments_defaults(self, cli_fixture):
        """
        Test that default arguments are correctly handled when no CLI args are provided.
        """
        cli, _, _, _ = cli_fixture

        # Simulate empty command line arguments
        with patch("sys.argv", ["update_version.py"]):
            args = cli.parse_arguments()

        # Verify default values
        assert args.component == "patch"
        assert args.bump == "increment"
        assert args.value is None
        assert args.verbose is False
        assert args.config_file == "version.yml"

    @pytest.mark.parametrize(
        "component,bump_type,value,expected_version",
        [
            ("major", "increment", None, "2.0.0"),
            ("minor", "increment", None, "1.3.0"),
            ("patch", "increment", None, "1.2.4"),
            ("major", "set", "5", "5.0.0"),
            ("minor", "set", "8", "1.8.0"),
            ("patch", "set", "9", "1.2.9"),
        ],
    )
    def test_run_success(self, cli_fixture, component, bump_type, value, expected_version):
        """
        Test successful version updates with different parameter combinations.

        Args:
            component: The version component to modify (major, minor, or patch)
            bump_type: The type of version change (increment or set)
            value: The explicit value when using set bump type
            expected_version: The expected resulting version
        """
        cli, _, mock_version_manager, mock_version_updater = cli_fixture

        # Setup the original version
        original_version = Version(1, 2, 3)
        mock_version_updater.get_current_version.return_value = original_version

        # Setup the expected updated version
        major, minor, patch_int = map(int, expected_version.split("."))
        updated_version = Version(major, minor, patch_int)
        mock_version_updater.update_version.return_value = updated_version
        mock_version_manager.format_version.return_value = expected_version

        # Prepare command line arguments
        argv = ["update_version.py", "--component", component, "--bump", bump_type]
        if value:
            argv.extend(["--value", value])

        # Execute the command
        with patch("sys.argv", argv):
            with patch("builtins.print") as mock_print:
                result = cli.run()

        # Verify results
        assert result == 0

        # Check that update_version was called with correct parameters
        if bump_type == "increment":
            mock_version_updater.update_version.assert_called_once_with(
                getattr(Component, component.upper()), BumpType.INCREMENT, None
            )
        else:  # set
            mock_version_updater.update_version.assert_called_once_with(
                getattr(Component, component.upper()), BumpType.SET, int(value)
            )

        # Verify the output message
        mock_print.assert_any_call(f"Version updated to: {expected_version}")

    def test_run_set_without_value(self, cli_fixture):
        """
        Test that an error is raised when using 'set' bump type without a value.
        """
        cli, _, _, _ = cli_fixture

        # Prepare command line arguments with set but no value
        with patch("sys.argv", ["update_version.py", "--bump", "set"]):
            with patch("builtins.print") as mock_print:
                result = cli.run()

        # Verify failure
        assert result == 1
        mock_print.assert_any_call("Error: When using 'set' bump type, a value must be provided.")

    def test_run_component_not_found_in_config(self, cli_fixture):
        """
        Test behavior when a requested version component doesn't exist in the config.
        """
        cli, _, _, mock_version_updater = cli_fixture

        # Make update_version raise a KeyError
        mock_version_updater.update_version.side_effect = KeyError("Component not found")

        # Prepare command line arguments
        with patch("sys.argv", ["update_version.py", "--component", "major"]):
            with patch("builtins.print") as mock_print:
                result = cli.run()

        # Verify error handling
        assert result == 1
        mock_print.assert_any_call("Error: Component not found")

    def test_run_with_verbose_flag(self, cli_fixture):
        """
        Test that verbose mode outputs additional information.
        """
        cli, mock_config, _, mock_version_updater = cli_fixture

        # Setup the version
        original_version = Version(1, 2, 3)
        updated_version = Version(1, 2, 4)
        mock_version_updater.get_current_version.return_value = original_version
        mock_version_updater.update_version.return_value = updated_version

        # Add files to config for verbose output
        mock_config.files = [MagicMock(path=Path("version.py")), MagicMock(path=Path("setup.py"))]

        # Prepare command line arguments with verbose flag
        with patch("sys.argv", ["update_version.py", "--verbose"]):
            with patch("builtins.print") as mock_print:
                result = cli.run()

        # Verify verbose output
        assert result == 0
        mock_print.assert_any_call("Current version: 1.2.3")
        mock_print.assert_any_call("Updated files:")
        for file_mock in mock_config.files:
            mock_print.assert_any_call(f"  - {file_mock.path}")

    def test_missing_config_file(self, cli_fixture):
        """
        Test behavior when the specified config file doesn't exist.
        """
        cli, _, _, _ = cli_fixture

        # Make VersionConfig raise FileNotFoundError
        with patch("update_version.VersionConfig", side_effect=FileNotFoundError("Config not found")):
            with patch("sys.argv", ["update_version.py"]):
                with patch("builtins.print") as mock_print:
                    result = cli.run()

        # Verify error handling
        assert result == 1
        mock_print.assert_any_call("Error: Config not found")
