import pytest
import argparse
from unittest.mock import patch, MagicMock
from update_version import VersionUpdaterCLI, Version, BumpType, Component


class TestVersionUpdaterCLI:
    """Test cases for the VersionUpdaterCLI class."""

    @pytest.fixture
    def cli(self):
        """Create a VersionUpdaterCLI instance for testing."""
        return VersionUpdaterCLI()

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_arguments_defaults(self, mock_parse_args):
        """Test parsing arguments with defaults."""
        mock_args = argparse.Namespace(component="both", bump_type="patch", action="increment", value=None)
        mock_parse_args.return_value = mock_args

        result = VersionUpdaterCLI.parse_arguments()

        assert result.component == "both"
        assert result.bump_type == "patch"
        assert result.action == "increment"
        assert result.value is None

    @patch("update_version.VersionUpdaterCLI.parse_arguments")
    @patch("update_version.VersionUpdater.get_current_version")
    @patch("update_version.VersionManager.bump_version")
    @patch("update_version.VersionUpdater.update_version")
    def test_run_success(self, mock_update, mock_bump, mock_get_version, mock_parse_args, cli):
        """Test running the CLI with successful execution."""
        # Setup mock arguments
        mock_args = argparse.Namespace(component="both", bump_type="patch", action="increment", value=None)
        mock_parse_args.return_value = mock_args

        # Setup mock versions
        current_version = Version(1, 2, 3)
        new_version = Version(1, 2, 4)
        mock_get_version.return_value = current_version
        mock_bump.return_value = new_version

        result = cli.run()

        # Check that the CLI ran successfully
        assert result == 0
        # Check that get_current_version was called twice (once for backend, once for frontend)
        assert mock_get_version.call_count == 2
        # Check that bump_version was called twice
        assert mock_bump.call_count == 2
        # Check that update_version was called twice
        assert mock_update.call_count == 2

    @patch("update_version.VersionUpdaterCLI.parse_arguments")
    def test_run_set_without_value(self, mock_parse_args, cli):
        """Test running with 'set' action but no value."""
        # Setup mock arguments
        mock_args = argparse.Namespace(component="backend", bump_type="patch", action="set", value=None)
        mock_parse_args.return_value = mock_args

        result = cli.run()

        # Check that the CLI returned an error code
        assert result == 1
