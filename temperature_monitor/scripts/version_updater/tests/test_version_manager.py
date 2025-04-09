import pytest
from update_version import VersionManager, Version, Component, BumpType


class TestVersionManager:
    """Test cases for the VersionManager class."""

    def test_parse_version_valid(self):
        """Test parsing valid version strings."""
        test_cases = [
            ("1.2.3", Version(1, 2, 3)),
            ("0.0.1", Version(0, 0, 1)),
            ("10.20.30", Version(10, 20, 30)),
        ]

        for version_str, expected in test_cases:
            result = VersionManager.parse_version(version_str)
            assert result.major == expected.major
            assert result.minor == expected.minor
            assert result.patch == expected.patch

    def test_parse_version_invalid(self):
        """Test parsing invalid version strings raises ValueError."""
        invalid_versions = [
            "1.2",  # Missing patch component
            "1.2.3.4",  # Extra component
            "a.b.c",  # Non-numeric components
            "1.2.c",  # Mixed components
            "",  # Empty string
            "version 1.2.3",  # Extra text
        ]

        for invalid_version in invalid_versions:
            with pytest.raises(ValueError):
                VersionManager.parse_version(invalid_version)

    def test_bump_version_increment_major(self):
        """Test incrementing the major component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MAJOR, BumpType.INCREMENT)
        assert new_version.major == 2
        assert new_version.minor == 0  # Reset to 0
        assert new_version.patch == 0  # Reset to 0

    def test_bump_version_increment_minor(self):
        """Test incrementing the minor component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MINOR, BumpType.INCREMENT)
        assert new_version.major == 1  # Unchanged
        assert new_version.minor == 3
        assert new_version.patch == 0  # Reset to 0

    def test_bump_version_increment_patch(self):
        """Test incrementing the patch component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.PATCH, BumpType.INCREMENT)
        assert new_version.major == 1  # Unchanged
        assert new_version.minor == 2  # Unchanged
        assert new_version.patch == 4

    def test_bump_version_set_major(self):
        """Test setting the major component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MAJOR, BumpType.SET, 5)
        assert new_version.major == 5
        assert new_version.minor == 2  # Unchanged
        assert new_version.patch == 3  # Unchanged

    def test_bump_version_set_without_value(self):
        """Test BumpType.SET without a value raises ValueError."""
        version = Version(1, 2, 3)
        with pytest.raises(ValueError):
            VersionManager.bump_version(version, Component.MAJOR, BumpType.SET)
