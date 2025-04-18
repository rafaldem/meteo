from importlib.metadata import files
from pathlib import Path

import pytest
import argparse
from unittest.mock import patch, MagicMock
from update_version import VersionUpdaterCLI, Version, BumpType, Component, FileInfo


class TestVersionUpdaterCLI:
    """Test cases for the VersionUpdaterCLI class."""

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_arguments_defaults(self, mock_parse_args):
        """Test parsing arguments with defaults."""
        mock_args = argparse.Namespace(
            component="both", bump_type="patch", action="increment", value=None, log_level="info"
        )
        mock_parse_args.return_value = mock_args

        result = VersionUpdaterCLI.parse_arguments()

        assert result.component == "both"
        assert result.bump_type == "patch"
        assert result.action == "increment"
        assert result.value is None
        assert result.log_level == "info"

    @patch("update_version.VersionUpdaterCLI.parse_arguments")
    @patch("update_version.VersionManager.bump_version")
    @patch("update_version.VersionUpdater.update_version")
    def test_run_success(self, mock_update, mock_bump, mock_parse_args, cli):
        """Test running the CLI with successful execution."""
        # Patch the instance method directly
        expected_call_count = 3  # One call each for setup, frontend, and backend

        cli.version_updater.get_current_version = MagicMock()

        mock_args = argparse.Namespace(
            component="both", bump_type="patch", action="increment", value=None, log_level="DEBUG"
        )
        mock_parse_args.return_value = mock_args

        current_version = Version(1, 2, 3)
        new_version = Version(1, 2, 4)
        cli.version_updater.get_current_version.return_value = current_version
        mock_bump.return_value = new_version

        result = cli.run()

        assert result == 0, "CLI should return success code (0)"
        # Expected call count is 3 (setup + frontend + backend)

        assert cli.version_updater.get_current_version.call_count == expected_call_count, "Should retrieve version for each component"
        assert mock_bump.call_count == expected_call_count, "Should bump version for each component"
        assert mock_update.call_count == expected_call_count, "Should update version for each component"

    @patch("update_version.logger.error")
    @patch("update_version.VersionUpdaterCLI.parse_arguments")
    def test_run_set_without_value(self, mock_parse_args, mock_logger_error, cli):
        """Test running with 'set' action but no value."""
        mock_args = argparse.Namespace(
            component="backend", bump_type="patch", action="set", value=None, log_level="DEBUG"
        )
        mock_parse_args.return_value = mock_args

        result = cli.run()

        # Check that the CLI returned an error code
        assert result == 1

        assert mock_logger_error.call_count == 1
        assert mock_logger_error.call_args[0][0] == f"--value is required for 'set' action"

    @patch("update_version.logger.warning")
    @patch("update_version.VersionUpdaterCLI.parse_arguments")
    def test_run_component_not_found_in_config(
            self, mock_parse_args, mock_logger_warning, version_updater, cli
    ):
        """Test running with 'set' action but no value."""
        with patch.object(cli, 'config', create=True) as mock_config:
            mock_config.files = {'some_mocked_value': 'here'}

            mock_args = argparse.Namespace(
                component="backend", bump_type="minor", action="increment", value=None, log_level="DEBUG"
            )
            mock_parse_args.return_value = mock_args

            component = "backend"

            file_info = MagicMock(spec=FileInfo)
            file_info.path = MagicMock(spec=Path)
            file_info.path.exists.return_value = False

            result = cli.run()

            # Check that the CLI returned an error code
            assert result == 0

            assert mock_logger_warning.call_count == 2
            assert mock_logger_warning.call_args[0][0] == f"Component {component} not found in configuration"
