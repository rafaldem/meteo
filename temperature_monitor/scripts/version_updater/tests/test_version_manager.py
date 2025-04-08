import pytest

from update_version import BumpType, Component, Version, VersionManager


class TestVersionManager:
    """Test the VersionManager class."""

    def setup_method(self):
        """Set up test environment."""
        self.version_manager = VersionManager()

    def test_parse_valid_version(self):
        """Test parsing a valid version string."""
        version = self.version_manager.parse_version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_parse_invalid_version(self):
        """Test parsing an invalid version string."""
        with pytest.raises(ValueError):
            self.version_manager.parse_version("invalid")
        with pytest.raises(ValueError):
            self.version_manager.parse_version("1.2")
        with pytest.raises(ValueError):
            self.version_manager.parse_version("1.2.a")

    def test_bump_version_increment_patch(self):
        """Test incrementing the patch version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.PATCH, BumpType.INCREMENT)
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 4

    def test_bump_version_increment_minor(self):
        """Test incrementing the minor version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.MINOR, BumpType.INCREMENT)
        assert new_version.major == 1
        assert new_version.minor == 3
        assert new_version.patch == 0

    def test_bump_version_increment_major(self):
        """Test incrementing the major version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.MAJOR, BumpType.INCREMENT)
        assert new_version.major == 2
        assert new_version.minor == 0
        assert new_version.patch == 0

    def test_bump_version_set_patch(self):
        """Test setting the patch version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.PATCH, BumpType.SET, value=5)
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 5

    def test_bump_version_set_minor(self):
        """Test setting the minor version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.MINOR, BumpType.SET, value=5)
        assert new_version.major == 1
        assert new_version.minor == 5
        assert new_version.patch == 3

    def test_bump_version_set_major(self):
        """Test setting the major version."""
        version = Version(1, 2, 3)
        new_version = self.version_manager.bump_version(version, Component.MAJOR, BumpType.SET, value=5)
        assert new_version.major == 5
        assert new_version.minor == 2
        assert new_version.patch == 3

    def test_bump_version_invalid_operation(self):
        """Test invalid bump operation."""
        version = Version(1, 2, 3)
        with pytest.raises(ValueError):
            self.version_manager.bump_version(version, Component.MAJOR, BumpType.SET)

    def test_format_version(self):
        """Test formatting a version."""
        version = Version(1, 2, 3)
        assert self.version_manager.format_version(version) == "1.2.3"
