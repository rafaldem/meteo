from update_version import Version


class TestVersion:
    """Test the Version class."""

    def test_version_creation(self):
        """Test creating a Version object."""
        version = Version(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_string_representation(self):
        """Test the string representation of a Version."""
        version = Version(1, 2, 3)
        assert str(version) == "1.2.3"
