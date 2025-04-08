import os
import sys
import re
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open, MagicMock, call
from update_version import BumpType, Component, Version, VersionConfig, VersionManager, FileUpdater, VersionUpdater, VersionUpdaterCLI


class TestVersionUpdaterCLI:
    """Test the VersionUpdaterCLI class."""

    def setup_method(self):
        """Set up test environment."""
        self.cli = VersionUpdaterCLI()
        self.cli.version_updater = MagicMock()
        self.cli.version_manager = MagicMock()

    def test_parse_arguments_defaults(self):
        """Test parsing command-line arguments with defaults."""
        with patch('sys.argv', ['update_version.py']):
            args = self.cli.parse_arguments()
            assert args.component == 'both'
            assert args.bump_type == 'patch'
            assert args.action == 'increment'
            assert args.value is None

    def test_parse_arguments_custom(self):
        """Test parsing custom command-line arguments."""
        with patch('sys.argv', ['update_version.py', '--component',
            'backend', '--bump-type', 'minor', '--action', 'set', '--value',
            '5']):
            args = self.cli.parse_arguments()
            assert args.component == 'backend'
            assert args.bump_type == 'minor'
            assert args.action == 'set'
            assert args.value == 5

    def test_run_set_without_value(self):
        """Test running with 'set' action but no value."""
        with patch('sys.argv', ['update_version.py', '--action', 'set']):
            exit_code = self.cli.run()
            assert exit_code == 1
            self.cli.version_updater.update_version.assert_not_called()

    def test_run_update_backend(self):
        """Test running update for backend only."""
        with patch('sys.argv', ['update_version.py', '--component', 'backend']
            ):
            current_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            self.cli.version_updater.get_current_version.return_value = (
                current_version)
            self.cli.version_manager.bump_version.return_value = new_version
            exit_code = self.cli.run()
            assert exit_code == 0
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_manager.bump_version.assert_called_once_with(
                current_version, Component.PATCH, BumpType.INCREMENT, None)
            self.cli.version_updater.update_version.assert_called_once_with(
                new_version)

    def test_run_update_frontend(self):
        """Test running update for frontend only."""
        with patch('sys.argv', ['update_version.py', '--component', 'frontend']
            ):
            current_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            self.cli.version_updater.get_current_version.return_value = (
                current_version)
            self.cli.version_manager.bump_version.return_value = new_version
            exit_code = self.cli.run()
            assert exit_code == 0
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_manager.bump_version.assert_called_once_with(
                current_version, Component.PATCH, BumpType.INCREMENT, None)
            self.cli.version_updater.update_version.assert_called_once_with(
                new_version)

    def test_run_update_both(self):
        """Test running update for both backend and frontend."""
        with patch('sys.argv', ['update_version.py', '--component', 'both']):
            backend_version = Version(1, 2, 3)
            frontend_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            self.cli.version_updater.get_current_version.return_value = (
                backend_version)
            self.cli.version_updater.get_current_version.return_value = (
                frontend_version)
            self.cli.version_manager.bump_version.return_value = new_version
            exit_code = self.cli.run()
            assert exit_code == 0
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_updater.update_version.assert_called_once_with(
                new_version)
            assert self.cli.version_manager.bump_version.call_count == 2

    def test_run_backend_error(self):
        """Test handling backend update errors."""
        with patch('sys.argv', ['update_version.py', '--component', 'backend']
            ):
            self.cli.version_updater.get_current_version.side_effect = (
                ValueError('Error'))
            exit_code = self.cli.run()
            assert exit_code == 1
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_updater.update_version.assert_not_called()

    def test_run_frontend_error(self):
        """Test handling frontend update errors."""
        with patch('sys.argv', ['update_version.py', '--component', 'frontend']
            ):
            self.cli.version_updater.get_current_version.side_effect = (
                ValueError('Error'))
            exit_code = self.cli.run()
            assert exit_code == 1
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_updater.update_version.assert_not_called()

    def test_run_both_backend_error(self):
        """Test handling backend error when updating both components."""
        with patch('sys.argv', ['update_version.py', '--component', 'both']):
            self.cli.version_updater.get_current_version.side_effect = (
                ValueError('Error'))
            frontend_version = Version(1, 2, 3)
            new_version = Version(1, 2, 4)
            self.cli.version_updater.get_current_version.return_value = (
                frontend_version)
            self.cli.version_manager.bump_version.return_value = new_version
            exit_code = self.cli.run()
            assert exit_code == 0
            self.cli.version_updater.get_current_version.assert_called_once()
            self.cli.version_updater.update_version.assert_not_called()
