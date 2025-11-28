import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_health_check():
    client = APIClient()
    resp = client.get(reverse("users:health"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_me_sets_session():
    client = APIClient()
    payload = {
        "email": "newowner@example.com",
        "password": "strongpassword",
        "first_name": "New",
        "last_name": "Owner",
        "is_commissioner": True,
    }
    resp = client.post(reverse("users:register"), payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["is_commissioner"] is True

    # Session should be established after register
    me = client.get(reverse("users:me"))
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_login_logout_cycle(django_user_model):
    user = django_user_model.objects.create_user(
        email="user@example.com", password="pass12345", is_commissioner=False
    )
    client = APIClient()
    resp = client.post(
        reverse("users:login"),
        {"email": "user@example.com", "password": "pass12345"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"

    me = client.get(reverse("users:me"))
    assert me.status_code == 200

    logout_resp = client.post(reverse("users:logout"))
    assert logout_resp.status_code == 204

    me_after = client.get(reverse("users:me"))
    assert me_after.status_code == 403
