#!/usr/bin/env python3
"""
Version management utility for updating version numbers across backend and frontend components.
"""

import re
import sys
import logging
import argparse
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Union, Any


# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(log_file: str = "version_updater.log", log_level: int = logging.INFO) -> None:
    """
    Set up logging configuration.

    Args:
        log_file: Path to the log file
        log_level: Logging level
    """
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Add handlers
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

    base: str = r"(\d+)\.(\d+)\.(\d+)"
    version_py: str = r'__version__\s*=\s*["\']' + base + r'["\']'
    pyproject: str = r'version\s*=\s*["\']' + base + r'["\']'
    setup: str = r'version\s*=\s*["\']' + base + r'["\']'


@dataclass
class FileInfo:
    """Information about a file containing version information."""

    path: Path
    pattern: str


@dataclass
class VersionConfig:
    """Configuration for version patterns and file paths."""

    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.resolve())
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
        match = re.match(pattern, version_string)
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
        version: Version, component: Component, bump_type: BumpType, value: Optional[int] = None
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
        except IOError as e:
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
    def get_current_version(self, version_file: Path) -> Version:
        """
        Get current version from a file.

        Args:
            version_file: Path to the version file

        Returns:
            The current Version

        Raises:
            ValueError: If version information cannot be found
        """
        try:
            logger.debug(f"Reading version information from {version_file}")
            content = self._read_file(version_file)
            component = version_file.parent.name

            # Get the pattern for this file
            file_info = None
            for component_name, files in self.config.files.items():
                for file_key, info in files.items():
                    if Path(info.path).name == version_file.name:
                        file_info = info
                        break
                if file_info:
                    break

            if not file_info:
                raise ValueError(f"Unknown file: {version_file}")

            # Extract version using the pattern
            match = re.search(file_info.pattern, content)
            if not match:
                raise ValueError(f"Could not find version information in {version_file}")

            # Extract the actual version string
            version_pattern = VersionPattern().base
            version_string_match = re.search(version_pattern, match.group(0))
            if not version_string_match:
                raise ValueError(f"Could not extract version from {match.group(0)}")

            version_string = version_string_match.group(0)
            logger.debug(f"Found version: {version_string}")
            return self.version_manager.parse_version(version_string)

        except (IOError, ValueError) as e:
            logger.error(f"Error getting current version from {version_file}: {e}")
            raise

    def update_version(self, old_version: Version, new_version: Version, component: str) -> None:
        """
        Update version in files for a component.

        Args:
            old_version: The current version
            new_version: The new version to set
            component: Which component to update (backend, frontend, both)
        """
        old_version_str = self.version_manager.format_version(old_version)
        new_version_str = self.version_manager.format_version(new_version)

        # Get files for the component
        component_files = self.config.files.get(component, {})
        if not component_files:
            logger.warning(f"No files defined for component: {component}")
            return

        for file_key, file_info in component_files.items():
            file_path = Path(file_info.path)
            if file_path.exists():
                logger.info(f"Updating {file_key} version from {old_version_str} to {new_version_str}")
                self.update_file(file_path, old_version_str, new_version_str)
            else:
                logger.warning(f"File {file_path} does not exist, skipping")


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
            choices=["backend", "frontend", "both"],
            default="both",
            help="Which component to update (default: both)",
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

    def run(self) -> int:
        """
        Run the version update process.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            args = self.parse_arguments()

            # Set log level
            log_level = getattr(logging, args.log_level.upper())
            setup_logging(log_level=log_level)

            # Convert string arguments to enums
            bump_type = BumpType.SET if args.action == "set" else BumpType.INCREMENT
            component_enum = getattr(Component, args.bump_type.upper())

            # Validate arguments
            if bump_type == BumpType.SET and args.value is None:
                logger.error("--value is required for 'set' action")
                return 1

            # Update backend version
            if args.component in ["backend", "both"]:
                try:
                    # Get the backend version file path
                    backend_version_file = Path(self.config.files["backend"]["version.py"].path)
                    if not backend_version_file.exists():
                        logger.error(f"Backend version file {backend_version_file} does not exist")
                        if args.component == "backend":
                            return 1
                    else:
                        # Update the backend version
                        current_version = self.version_updater.get_current_version(backend_version_file)
                        new_version = self.version_manager.bump_version(
                            current_version, component_enum, bump_type, args.value
                        )
                        self.version_updater.update_version(current_version, new_version, "backend")
                except Exception as e:
                    logger.error(f"Error updating backend version: {e}")
                    if args.component == "backend":
                        return 1

            # Update frontend version
            if args.component in ["frontend", "both"]:
                try:
                    # Get the frontend version file path
                    frontend_version_file = Path(self.config.files["frontend"]["version.py"].path)
                    if not frontend_version_file.exists():
                        logger.error(f"Frontend version file {frontend_version_file} does not exist")
                        if args.component == "frontend":
                            return 1
                    else:
                        # Update the frontend version
                        current_version = self.version_updater.get_current_version(frontend_version_file)
                        new_version = self.version_manager.bump_version(
                            current_version, component_enum, bump_type, args.value
                        )
                        self.version_updater.update_version(current_version, new_version, "frontend")
                except Exception as e:
                    logger.error(f"Error updating frontend version: {e}")
                    if args.component == "frontend":
                        return 1

            # Update setup.py if both components are updated
            if args.component == "both":
                try:
                    # Get the setup.py file path
                    setup_file = Path(self.config.files["setup"]["setup.py"].path)
                    if setup_file.exists():
                        # We use the backend version for the setup.py file
                        backend_version_file = Path(self.config.files["backend"]["version.py"].path)
                        current_version = self.version_updater.get_current_version(backend_version_file)
                        new_version = self.version_manager.bump_version(
                            current_version, component_enum, bump_type, args.value
                        )
                        self.version_updater.update_version(current_version, new_version, "setup")
                except Exception as e:
                    logger.error(f"Error updating setup.py version: {e}")
                    # Don't fail the entire process for setup.py

            logger.info("Version update completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1


if __name__ == "__main__":
    cli = VersionUpdaterCLI()
    sys.exit(cli.run())
