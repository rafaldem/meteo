from update_version import Version


def test_version_str_representation():
    """Test the string representation of a Version object."""
    version = Version(1, 2, 3)
    assert str(version) == "1.2.3"


def test_version_attributes():
    """Test accessing attributes of a Version object."""
    version = Version(1, 2, 3)
    assert version.major == 1
    assert version.minor == 2
    assert version.patch == 3
