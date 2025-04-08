#!/usr/bin/env python3
"""
Version management utility for updating version numbers across backend and frontend components.
"""

import re
import sys
import argparse
import logging
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("version_updater.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
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


class VersionConfig:
    """Configuration for version patterns and file paths."""

    VERSION_PATTERN = r"(\d+)\.(\d+)\.(\d+)"
    VERSION_PY_PATTERN = r'__version__\s*=\s*["\']' + VERSION_PATTERN + r'["\']'
    PYPROJECT_PATTERN = r'version\s*=\s*["\']' + VERSION_PATTERN + r'["\']'
    SETUP_PATTERN = r'version\s*=\s*["\']' + VERSION_PATTERN + r'["\']'

    PROJECT_LOCATION = Path(__file__).parent.parent.resolve()

    FILES = {
        "backend": {
            "version.py": ((PROJECT_LOCATION / "backend/version.py").name, VERSION_PY_PATTERN),
            "pyproject.toml": ("backend/pyproject.toml", PYPROJECT_PATTERN),
        },
        "frontend": {
            "version.py": ((PROJECT_LOCATION / "frontend/version.py").name, VERSION_PY_PATTERN),
            "pyproject.toml": ("frontend/pyproject.toml", PYPROJECT_PATTERN),
        },
        "setup": {
            "setup.py": ("setup.py", SETUP_PATTERN),
        },
    }


class VersionManager:
    """Manages version operations across the application."""

    @staticmethod
    @log_debug_return
    def parse_version(
        version_string: str,
    ) -> Version:
        """
        Parse a version string into a Version object.

        Args:
            version_string: String representation of a version (e.g., "1.2.3")

        Returns:
            Version object

        Raises:
            ValueError: If the version string has an invalid format
        """
        match = re.match(VersionConfig.VERSION_PATTERN, version_string)
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
        self.version_manager = version_manager

    @staticmethod
    @log_debug_return
    def _read_file(file_path: Path) -> str:
        """Read file content safely."""
        try:
            with file_path.open("r", encoding="utf-8") as file:
                return file.read()
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise IOError(f"Could not read file {file_path}: {e}")

    @staticmethod
    def _write_file(file_path: Path, content: str) -> None:
        """Write content to file safely."""
        try:
            with file_path.open("w", encoding="utf-8") as file:
                file.write(content)
                logger.info(f"Updated {file_path}")
                logger.debug(f"Content:\n{content}")
        except IOError as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            raise IOError(f"Could not write to file {file_path}: {e}")

    def update_file(self, file_path: Path, old_version: str, new_version: str) -> None:
        """Update version in a single file."""
        if not file_path.exists():
            logger.warning(f"File {file_path} does not exist, skipping")
            return

        content = self._read_file(file_path)
        updated_content = content.replace(old_version, new_version)
        logger.debug(f"Updated content:\n{updated_content}")

        if content == updated_content:
            logger.warning(f"No version information found in {file_path}")
            return

        self._write_file(file_path, updated_content)


class VersionUpdater(FileUpdater):
    """Updates version files."""

    @log_debug_return
    def get_current_version(self, version_file: Path) -> Version:
        """
        Get current version.

        Returns:
            The current Version

        Raises:
            ValueError: If version information cannot be found
        """
        try:
            logger.debug(f"Reading version information from {version_file}")
            content = self._read_file(version_file)
            component = version_file.parent.name

            file_path, version_file_pattern = VersionConfig.FILES[component][version_file.name]
            match = re.search(version_file_pattern, content)
            if not match:
                raise ValueError(f"Could not find version information in {version_file}")

            version_string_match = re.search(VersionConfig.VERSION_PATTERN, match.group(0))
            version_string = version_string_match.group(0) if version_string_match else None
            logger.debug(f"Found version: {version_string}")
            return self.version_manager.parse_version(version_string)
        except (IOError, ValueError) as e:
            logger.error(f"Error getting current backend version: {e}")
            raise

    def update_version(self, old_version: Version, new_version: Version, component: str) -> None:
        """
        Update version in files.

        Args:
            new_version: The new version to set
            :param old_version:
            :param new_version:
            :param component:
        """
        old_version_str = self.version_manager.format_version(old_version)
        new_version_str = self.version_manager.format_version(new_version)

        for file_key, (file_path_str, version_pattern) in VersionConfig.FILES[component].items():
            file_path = Path(file_path_str)
            if file_path.exists():
                logger.info(f"Updating {file_key} version from {old_version_str} to {new_version_str}")
                self.update_file(file_path, old_version_str, new_version_str)


class VersionUpdaterCLI:
    """Command-line interface for version updating."""

    def __init__(self):
        self.version_manager = VersionManager()
        self.version_updater = VersionUpdater(self.version_manager)

    @staticmethod
    @log_debug_return
    def parse_arguments() -> argparse.Namespace:
        """Parse command line arguments."""
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

        parser.add_argument("--value", type=int, help="Value to set (required for set action)")

        return parser.parse_args()

    def run(self) -> int:
        """
        Run the version update process.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            args = self.parse_arguments()

            # Convert string arguments to enums
            bump_type = BumpType.SET if args.action == "set" else BumpType.INCREMENT
            component = getattr(Component, args.bump_type.upper())

            # Validate arguments
            if bump_type == BumpType.SET and args.value is None:
                logger.error("--value is required for 'set' action")
                return 1

            # Update backend version
            if args.component in ["backend", "both"]:
                try:
                    version_file = Path(VersionConfig.FILES["backend"]["version.py"][0])
                    current_version = self.version_updater.get_current_version(version_file)
                    new_version = self.version_manager.bump_version(current_version, component, bump_type, args.value)
                    self.version_updater.update_version(current_version, new_version, args.component)
                except Exception as e:
                    logger.error(f"Error updating backend version: {e}")
                    if args.component == "backend":
                        return 1

            # Update frontend version
            if args.component in ["frontend", "both"]:
                try:
                    version_file = Path(VersionConfig.FILES["frontend"]["version.py"][0])
                    current_version = self.version_updater.get_current_version(version_file)
                    new_version = self.version_manager.bump_version(current_version, component, bump_type, args.value)
                    self.version_updater.update_version(current_version, new_version, args.component)
                except Exception as e:
                    logger.error(f"Error updating frontend version: {e}")
                    if args.component == "frontend":
                        return 1

            logger.info("Version update completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1


if __name__ == "__main__":
    cli = VersionUpdaterCLI()
    sys.exit(cli.run())
