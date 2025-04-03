#!/usr/bin/env python3
"""
Version management utility for updating version numbers across backend and frontend components.
"""

import re
import os
import sys
import argparse
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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

    def __str__(self) -> str:
        """String representation of the version."""
        return f"{self.major}.{self.minor}.{self.patch}"


class VersionConfig:
    """Configuration for version patterns and file paths."""

    VERSION_PATTERN = r"(\d+)\.(\d+)\.(\d+)"
    CURRENT_VERSION_PATTERN = r'CURRENT_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']'

    # File paths could be moved to a configuration file for more flexibility
    BACKEND_FILES = {"version_file": "backend/config.py", "other_files": ["backend/__init__.py", "setup.py"]}

    FRONTEND_FILES = {"package_json": "frontend/package.json", "version_ts": "frontend/src/version.ts"}


class VersionManager:
    """Manages version operations across the application."""

    def parse_version(self, version_string: str) -> Version:
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

    def bump_version(
        self, version: Version, component: Component, bump_type: BumpType, value: Optional[int] = None
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

    def format_version(self, version: Version) -> str:
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

    def _read_file(self, file_path: str) -> str:
        """Read file content safely."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise IOError(f"Could not read file {file_path}: {e}")

    def _write_file(self, file_path: str, content: str) -> None:
        """Write content to file safely."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
                logger.info(f"Updated {file_path}")
        except IOError as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            raise IOError(f"Could not write to file {file_path}: {e}")

    def update_file(self, file_path: str, old_version: str, new_version: str) -> None:
        """Update version in a single file."""
        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist, skipping")
            return

        content = self._read_file(file_path)
        updated_content = content.replace(old_version, new_version)

        if content == updated_content:
            logger.warning(f"No version information found in {file_path}")
            return

        self._write_file(file_path, updated_content)


class BackendVersionUpdater(FileUpdater):
    """Updates version in backend files."""

    def get_current_version(self) -> Version:
        """
        Get current backend version.

        Returns:
            The current backend Version

        Raises:
            ValueError: If version information cannot be found
        """
        try:
            version_file = VersionConfig.BACKEND_FILES["version_file"]
            content = self._read_file(version_file)

            match = re.search(VersionConfig.CURRENT_VERSION_PATTERN, content)
            if not match:
                raise ValueError(f"Could not find version information in {version_file}")

            version_string = match.group(1)
            return self.version_manager.parse_version(version_string)
        except (IOError, ValueError) as e:
            logger.error(f"Error getting current backend version: {e}")
            raise

    def update_version(self, new_version: Version) -> None:
        """
        Update version in backend files.

        Args:
            new_version: The new version to set
        """
        current_version = self.get_current_version()
        old_version_str = self.version_manager.format_version(current_version)
        new_version_str = self.version_manager.format_version(new_version)

        # Update main version file
        version_file = VersionConfig.BACKEND_FILES["version_file"]
        logger.info(f"Updating backend version from {old_version_str} to {new_version_str}")
        self.update_file(version_file, old_version_str, new_version_str)

        # Update other backend files
        for file_path in VersionConfig.BACKEND_FILES["other_files"]:
            self.update_file(file_path, old_version_str, new_version_str)


class FrontendVersionUpdater(FileUpdater):
    """Updates version in frontend files."""

    def get_current_version(self) -> Version:
        """
        Get current frontend version.

        Returns:
            The current frontend Version

        Raises:
            ValueError: If version information cannot be found
        """
        try:
            # Read from package.json
            package_json = VersionConfig.FRONTEND_FILES["package_json"]
            if os.path.exists(package_json):
                content = self._read_file(package_json)
                match = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', content)
                if match:
                    version_string = match.group(1)
                    return self.version_manager.parse_version(version_string)

            # Fall back to version.ts
            version_ts = VersionConfig.FRONTEND_FILES["version_ts"]
            if os.path.exists(version_ts):
                content = self._read_file(version_ts)
                match = re.search(r'export const VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
                if match:
                    version_string = match.group(1)
                    return self.version_manager.parse_version(version_string)

            raise ValueError("Could not find version information in frontend files")
        except (IOError, ValueError) as e:
            logger.error(f"Error getting current frontend version: {e}")
            raise

    def update_version(self, new_version: Version) -> None:
        """
        Update version in frontend files.

        Args:
            new_version: The new version to set
        """
        current_version = self.get_current_version()
        old_version_str = self.version_manager.format_version(current_version)
        new_version_str = self.version_manager.format_version(new_version)

        # Update package.json
        package_json = VersionConfig.FRONTEND_FILES["package_json"]
        if os.path.exists(package_json):
            logger.info(f"Updating frontend version from {old_version_str} to {new_version_str}")
            content = self._read_file(package_json)
            updated_content = re.sub(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', f'"version": "{new_version_str}"', content)
            self._write_file(package_json, updated_content)

        # Update version.ts
        version_ts = VersionConfig.FRONTEND_FILES["version_ts"]
        if os.path.exists(version_ts):
            content = self._read_file(version_ts)
            updated_content = re.sub(
                r'export const VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
                f'export const VERSION = "{new_version_str}"',
                content,
            )
            self._write_file(version_ts, updated_content)


class VersionUpdaterCLI:
    """Command-line interface for version updating."""

    def __init__(self):
        self.version_manager = VersionManager()
        self.backend_updater = BackendVersionUpdater(self.version_manager)
        self.frontend_updater = FrontendVersionUpdater(self.version_manager)

    def parse_arguments(self) -> argparse.Namespace:
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
                    current_version = self.backend_updater.get_current_version()
                    new_version = self.version_manager.bump_version(current_version, component, bump_type, args.value)
                    self.backend_updater.update_version(new_version)
                except Exception as e:
                    logger.error(f"Error updating backend version: {e}")
                    if args.component == "backend":
                        return 1

            # Update frontend version
            if args.component in ["frontend", "both"]:
                try:
                    current_version = self.frontend_updater.get_current_version()
                    new_version = self.version_manager.bump_version(current_version, component, bump_type, args.value)
                    self.frontend_updater.update_version(new_version)
                except Exception as e:
                    logger.error(f"Error updating frontend version: {e}")
                    if args.component == "frontend":
                        return 1

            logger.info("Version update completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1


def main() -> int:
    """Main entry point."""
    cli = VersionUpdaterCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
