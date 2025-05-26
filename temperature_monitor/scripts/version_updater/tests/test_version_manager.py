import re

import pytest
from update_version import VersionManager, Version, Component, BumpType


class TestVersionManager:
    """Test cases for the VersionManager class."""

    @pytest.mark.parametrize(
        "version_str, expected",
        [
            ('version = "1.2.3"', Version(1, 2, 3)),
            ('version = "0.0.1"', Version(0, 0, 1)),
            ('version = "10.20.30"', Version(10, 20, 30)),
        ],
    )
    def test_parse_version_valid(self, version_str, expected):
        """Test parsing valid version strings."""
        result = VersionManager.parse_version(version_str)
        assert result.major == expected.major
        assert result.minor == expected.minor
        assert result.patch == expected.patch

    @pytest.mark.parametrize(
        "invalid_version",
        [
            "1.2",  # Missing patch component
            "1.2.3.4",  # Extra component
            "a.b.c",  # Non-numeric components
            "1.2.c",  # Mixed components
            "",  # Empty string
            "version 1.2.3",  # Extra text
        ],
    )
    def test_parse_version_invalid(self, invalid_version):
        """Test parsing invalid version strings raises ValueError."""
        with pytest.raises(ValueError):
            VersionManager.parse_version(invalid_version)

    def test_parse_version_with_conversion_error(self, monkeypatch):
        """Test that parse_version handles conversion errors correctly"""
        # Mock re.search to return a match object that will cause a conversion error
        class MockMatch:
            @staticmethod
            def group(index):
                if index == 1:
                    return "1"
                elif index == 2:
                    return "not_a_number"  # This will cause ValueError during int conversion
                elif index == 3:
                    return "3"

        def mock_search(*args, **kwargs):
            return MockMatch()

        # Apply the monkeypatch to replace re.search with our mock
        monkeypatch.setattr(re, "search", mock_search)

        with pytest.raises(ValueError) as excinfo:
            VersionManager.parse_version("1.2.3")  # The actual input doesn't matter due to our mock

        assert "Invalid version format" in str(excinfo.value)

    def test_bump_version_increment_major(self):
        """Test incrementing the major component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MAJOR, BumpType.INCREMENT)
        assert new_version.major == 2
        assert new_version.minor == 0
        assert new_version.patch == 0

    def test_bump_version_increment_minor(self):
        """Test incrementing the minor component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MINOR, BumpType.INCREMENT)
        assert new_version.major == 1
        assert new_version.minor == 3
        assert new_version.patch == 0

    def test_bump_version_increment_patch(self):
        """Test incrementing the patch component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.PATCH, BumpType.INCREMENT)
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 4

    def test_bump_version_set_major(self):
        """Test setting the major component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MAJOR, BumpType.SET, 5)
        assert new_version.major == 5
        assert new_version.minor == 2
        assert new_version.patch == 3

    def test_bump_version_set_minor(self):
        """Test setting the minor component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.MINOR, BumpType.SET, 5)
        assert new_version.major == 1
        assert new_version.minor == 5
        assert new_version.patch == 3

    def test_bump_version_set_patch(self):
        """Test setting the patch component."""
        version = Version(1, 2, 3)
        new_version = VersionManager.bump_version(version, Component.PATCH, BumpType.SET, 5)
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 5

    def test_bump_version_set_without_value(self):
        """Test BumpType.SET without a value raises ValueError."""
        version = Version(1, 2, 3)
        with pytest.raises(ValueError):
            VersionManager.bump_version(version, Component.MAJOR, BumpType.SET)
