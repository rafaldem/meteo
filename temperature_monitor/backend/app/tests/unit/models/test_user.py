from models import User, UserRole


def test_user_creation(self, db_session):
    """Test creating a user."""
    user = User(username="testuser", email="test@example.com", password_hash="hashed_password", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    retrieved_user = User.query.filter_by(username="testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.password_hash == "hashed_password"
    assert retrieved_user.role == UserRole.USER

def test_user_to_dict(self, db_session):
    """Test the to_dict method of the User model."""
    user = User.query.filter_by(username="admin").first()
    user_dict = user.to_dict()

    assert user_dict["username"] == "admin"
    assert user_dict["email"] == "admin@example.com"
    assert user_dict["role"] == "admin"
    assert "password_hash" not in user_dict  # Ensure password hash is not exposed
    assert "theme" in user_dict
    assert "dashboard_layout" in user_dict
