from app.models import AppSettings


def test_app_settings_creation(db_session):
    """Test creating an app setting."""
    setting = AppSettings(key="test_setting", value="test_value", description="A test setting", requires_admin=True)
    db_session.add(setting)
    db_session.commit()

    retrieved_setting = AppSettings.query.filter_by(key="test_setting").first()
    assert retrieved_setting is not None
    assert retrieved_setting.value == "test_value"
    assert retrieved_setting.description == "A test setting"
    assert retrieved_setting.requires_admin is True


def test_to_dict_structure(sample_app_settings):
    """Test that to_dict returns a dictionary with correct keys."""
    result = sample_app_settings.to_dict()
    assert isinstance(result, dict)
    expected_keys = {"id", "key", "value", "description", "requires_admin"}
    assert result.keys() == expected_keys


def test_to_dict_values(sample_app_settings):
    """Test that to_dict returns correct values."""
    result = sample_app_settings.to_dict()
    assert result["id"] == sample_app_settings.id
    assert result["key"] == sample_app_settings.key
    assert result["value"] == sample_app_settings.value
    assert result["description"] == sample_app_settings.description
    assert result["requires_admin"] == sample_app_settings.requires_admin


def test_to_dict_default_values():
    """Test that to_dict handles default values correctly."""
    app_settings = AppSettings(id=2, key="default_key", value=None, description=None)
    result = app_settings.to_dict()
    assert result["id"] == 2
    assert result["key"] == "default_key"
    assert result["value"] is None
    assert result["description"] is None
    assert result["requires_admin"] is False
