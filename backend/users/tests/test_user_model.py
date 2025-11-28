import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_email():
    user = User.objects.create_user(email="owner@example.com", password="password123", is_commissioner=True)

    assert user.email == "owner@example.com"
    assert user.is_commissioner is True
    assert user.is_staff is False
    assert user.check_password("password123")


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(email="admin@example.com", password="adminpass")

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True
    assert admin.check_password("adminpass")
