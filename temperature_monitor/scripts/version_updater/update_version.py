#!/usr/bin/env python3
"""
Version management utility for updating version numbers across backend and frontend components.
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


logger = logging.getLogger(__name__)


def setup_logging(log_file: str = "version_updater.log") -> None:
    """
    Set up logging configuration.

    Args:
        log_file: Path to the log file
    """
    console_formatter = logging.Formatter("%(message)s")
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel("INFO")
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel("DEBUG")
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def log_debug_return(func):
    """
    Decorator to log the return value of functions at the debug level.
    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.debug(f"Function '{func.__name__}' returned: {result}")
        return result

    return wrapper


class BumpType(Enum):
    """Type of version bump operation."""

    INCREMENT = "increment"
    SET = "set"


class Component(Enum):
    """Version component to bump."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    OTHER = "other"


@dataclass
class Version:
    """Class representing a semantic version."""

    major: int
    minor: int
    patch: int

    @log_debug_return
    def __str__(self) -> str:
        """String representation of the version."""
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class VersionPattern:
    """Class for version patterns used in different file types."""

    base: str = r'"(\d+)\.(\d+)\.(\d+)"'
    version_py: str = r'__version__\s*=\s*' + base
    pyproject: str = r'version\s*=\s*' + base
    setup: str = r'version\s*=\s*' + base


@dataclass
class FileInfo:
    """Information about a file containing version information."""

    path: Path
    pattern: str


@dataclass
class VersionConfig:
    """Configuration for version patterns and file paths."""

    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.resolve())
    patterns: VersionPattern = field(default_factory=VersionPattern)

    def __post_init__(self):
        """Initialize file paths after initialization."""
        self.files: Dict[str, Dict[str, FileInfo]] = {
            "backend": {
                "version.py": FileInfo(self.project_root / "backend/version.py", self.patterns.version_py),
                "pyproject.toml": FileInfo(self.project_root / "backend/pyproject.toml", self.patterns.pyproject),
            },
            "frontend": {
                "version.py": FileInfo(self.project_root / "frontend/version.py", self.patterns.version_py),
                "pyproject.toml": FileInfo(self.project_root / "frontend/pyproject.toml", self.patterns.pyproject),
            },
            "setup": {
                "setup.py": FileInfo(self.project_root / "setup.py", self.patterns.setup),
            },
        }


class VersionManager:
    """Manages version operations across the application."""

    @staticmethod
    @log_debug_return
    def parse_version(version_string: str) -> Version:
        """
        Parse a version string into a Version object.

        Args:
            version_string: String representation of a version (e.g., "1.2.3")

        Returns:
            Version object

        Raises:
            ValueError: If the version string has an invalid format
        """
        pattern = VersionPattern().base
        match = re.search(pattern, version_string)
        if not match:
            raise ValueError(f"Invalid version format: {version_string}")

        try:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))
            return Version(major, minor, patch)

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing version '{version_string}': {e}")
            raise ValueError(f"Invalid version format: {version_string}")

    @staticmethod
    @log_debug_return
    def bump_version(
        version: Version,
        component: Component,
        bump_type: BumpType,
        value: Optional[int] = None,
    ) -> Version:
        """
        Bump a version according to specified component and bump type.

        Args:
            version: The current version object
            component: Which component to bump (MAJOR, MINOR, PATCH)
            bump_type: How to bump (INCREMENT, SET)
            value: The value to set (required for SET bump_type)

        Returns:
            A new Version object with the updated component

        Raises:
            ValueError: If the bump operation is invalid
        """
        major, minor, patch = version.major, version.minor, version.patch

        if bump_type == BumpType.INCREMENT:
            if component == Component.MAJOR:
                major += 1
                minor = 0
                patch = 0
            elif component == Component.MINOR:
                minor += 1
                patch = 0
            elif component == Component.PATCH:
                patch += 1
        elif bump_type == BumpType.SET and value is not None:
            if component == Component.MAJOR:
                major = value
            elif component == Component.MINOR:
                minor = value
            elif component == Component.PATCH:
                patch = value
        else:
            raise ValueError(f"Invalid bump operation: {bump_type} with value {value}")

        return Version(major, minor, patch)

    @staticmethod
    @log_debug_return
    def format_version(version: Version) -> str:
        """
        Format a version object as a string.

        Args:
            version: The Version object

        Returns:
            A string representation of the version
        """
        return str(version)


class FileUpdater:
    """Base class for updating version in files."""

    def __init__(self, version_manager: VersionManager):
        """
        Initialize the file updater.

        Args:
            version_manager: The version manager instance
        """
        self.version_manager = version_manager

    @staticmethod
    @log_debug_return
    def _read_file(file_path: Path) -> str:
        """
        Read file content safely.

        Args:
            file_path: Path to the file

        Returns:
            The content of the file

        Raises:
            IOError: If the file cannot be read
        """
        try:
            with file_path.open("r", encoding="utf-8") as file:
                return file.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise IOError(f"Could not read file {file_path}: {e}")

    @staticmethod
    def _write_file(file_path: Path, content: str) -> None:
        """
        Write content to file safely.

        Args:
            file_path: Path to the file
            content: Content to write

        Raises:
            IOError: If the file cannot be written
        """
        try:
            with file_path.open("w", encoding="utf-8") as file:
                file.write(content)
                logger.info(f"Updated {file_path}")
                logger.debug(f"Content:\n{content}")
        except IOError as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            raise IOError(f"Could not write to file {file_path}: {e}")

    def update_file(self, file_path: Path, old_version: str, new_version: str) -> None:
        """
        Update version in a single file.

        Args:
            file_path: Path to the file
            old_version: Old version string to replace
            new_version: New version string
        """
        if not file_path.exists():
            logger.warning(f"File {file_path} does not exist, skipping")
            return

        content = self._read_file(file_path)
        updated_content = content.replace(old_version, new_version)

        if content == updated_content:
            logger.warning(f"No version information found in {file_path}")
            return

        self._write_file(file_path, updated_content)


class VersionUpdater(FileUpdater):
    """Updates version files."""

    def __init__(self, version_manager: VersionManager, config: Optional[VersionConfig] = None):
        """
        Initialize the version updater.

        Args:
            version_manager: The version manager instance
            config: The version configuration
        """
        super().__init__(version_manager)
        self.config = config or VersionConfig()

    @log_debug_return
    def get_current_version(self, version_file_info: FileInfo) -> Version:
        """
        Get current version from a file.

        Args:
            version_file_info: Version file information

        Returns:
            The current Version

        Raises:
            ValueError: If version information cannot be found
        """
        try:
            logger.debug(f"Reading version information from {version_file_info}")
            content = self._read_file(version_file_info.path)

            match = re.search(version_file_info.pattern, content)
            if not match:
                raise ValueError(f"Could not find version information in {version_file_info.path}")

            version_pattern = VersionPattern().base
            version_string_match = re.search(version_pattern, match.group(0))
            if not version_string_match:
                raise ValueError(f"Could not extract version from {match.group(0)}")

            version_string = version_string_match.group(0)
            logger.debug(f"Found version: {version_string}")
            return self.version_manager.parse_version(version_string)

        except (IOError, ValueError) as e:
            logger.error(f"Error getting current version from {version_file_info.path}: {e}")
            raise

    def update_version(self, old_version: Version, new_version: Version, component: str) -> None:
        """
        Update version in files for a component.

        Args:
            old_version: The current version
            new_version: The new version to set
            component: Which component to update (backend, frontend, both or setup)
        """
        old_version_str = self.version_manager.format_version(old_version)
        new_version_str = self.version_manager.format_version(new_version)

        component_files = self.config.files.get(component, {})
        if not component_files:
            logger.warning(f"No files defined for component: {component}")
            return

        for file_key, file_info in component_files.items():
            if file_info.path.exists():
                logger.info(f"Updating {file_key} version from {old_version_str} to {new_version_str}")
                self.update_file(file_info.path, old_version_str, new_version_str)
            else:
                logger.warning(f"File {file_info.path} does not exist, skipping")


class VersionUpdaterCLI:
    """Command-line interface for version updating."""

    def __init__(self, config: Optional[VersionConfig] = None):
        """
        Initialize the CLI.

        Args:
            config: The version configuration
        """
        setup_logging()
        self.config = config or VersionConfig()
        self.version_manager = VersionManager()
        self.version_updater = VersionUpdater(self.version_manager, self.config)

    @staticmethod
    @log_debug_return
    def parse_arguments() -> argparse.Namespace:
        """
        Parse command line arguments.

        Returns:
            Parsed arguments
        """
        parser = argparse.ArgumentParser(description="Version update utility for backend and frontend components.")

        parser.add_argument(
            "--component",
            choices=["backend", "frontend", "both", "other"],
            default="other",
            help="Which component to update (default: other)",
        )

        parser.add_argument(
            "--bump-type",
            choices=["major", "minor", "patch"],
            default="patch",
            help="Which part of the version to bump (default: patch)",
        )

        parser.add_argument(
            "--action",
            choices=["increment", "set"],
            default="increment",
            help="How to modify the version (default: increment)",
        )

        parser.add_argument(
            "--value",
            type=int,
            help="Value to set (required for set action)",
        )

        parser.add_argument(
            "--log-level",
            choices=["debug", "info", "warning", "error", "critical"],
            default="info",
            help="Logging level (default: info)",
        )

        return parser.parse_args()

    def run(self) -> int | str:
        """
        Run the version update process.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            args = self.parse_arguments()

            setup_logging()
            logger.debug(f"Args: {args}")

            bump_type = BumpType.SET if args.action == "set" else BumpType.INCREMENT
            component_enum = getattr(Component, args.bump_type.upper())

            if bump_type == BumpType.SET and args.value is None:
                error = "--value is required for 'set' action"
                logger.error(error)
                return error

            component_list = ["setup"]
            if args.component == "both":
                component_list += ["frontend", "backend"]
            elif args.component in ["frontend", "backend"]:
                component_list += [args.component]
            elif args.component == "other":
                pass
            else:
                error = f"Invalid component: {args.component}! Should be one of: backend, frontend, both or setup."
                logger.error(error)
                return error

            for component_name in component_list:
                if component_name not in self.config.files:
                    logger.warning(f"Component {component_name} not found in configuration")
                    continue

                try:
                    component_file_name = "setup.py" if component_name == "setup" else "version.py"
                    component_file_info = self.config.files[component_name][component_file_name]
                    if not component_file_info.path.exists():
                        logger.error(f"{component_name.capitalize()} version file {component_file_info} does not exist")
                        if args.component == component_name:
                            error = (
                                f"Invalid component: {args.component}!"
                                f" Should be one of: backend, frontend, both or setup."
                            )
                            logger.error(error)
                            return error
                        continue

                    current_version = self.version_updater.get_current_version(component_file_info)
                    if component_name == "setup":
                        bump_type = BumpType.INCREMENT
                        args_value = None
                    else:
                        bump_type = BumpType.SET if args.action == "set" else BumpType.INCREMENT
                        args_value = args.value

                    new_version = self.version_manager.bump_version(
                        version=current_version,
                        component=component_enum,
                        bump_type=bump_type,
                        value=args_value
                    )
                    self.version_updater.update_version(current_version, new_version, component_name)
                    logger.info(f"Updated {component_name} version from {current_version} to {new_version}")

                except Exception as e:
                    error = f"Error updating {component_name} version: {e}"
                    logger.error(error)
                    if args.component == component_name:
                        return error

            logger.info("Version update completed successfully")
            return 0

        except Exception as e:
            error = f"Unexpected error: {e}"
            logger.error(error)
            return error


if __name__ == "__main__":
    cli = VersionUpdaterCLI()
    sys.exit(cli.run())
