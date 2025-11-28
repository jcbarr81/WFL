import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db


def authenticated_client(email="owner@example.com", password="password123"):
    user = User.objects.create_user(email=email, password=password, is_commissioner=True)
    client = APIClient()
    resp = client.post(reverse("users:login"), {"email": email, "password": password}, format="json")
    assert resp.status_code == 200
    return client, user


def test_create_league_and_default_structure():
    client, user = authenticated_client()
    payload = {
        "name": "Test League",
        "conference_count": 2,
        "division_count_per_conference": 2,
        "teams_per_division": 4,
        "free_agency_mode": "auction",
        "allow_cap_growth": True,
        "allow_playoff_expansion": False,
        "enable_realignment": True,
    }

    resp = client.post(reverse("league:league-list-create"), payload, format="json")
    assert resp.status_code == 201
    league_id = resp.json()["id"]

    detail = client.get(reverse("league:league-detail", args=[league_id]))
    assert detail.status_code == 200
    body = detail.json()
    assert body["name"] == "Test League"
    assert body["created_by"] == user.id

    # conferences/divisions scaffold created
    assert body["conference_count"] == 2
    assert body["division_count_per_conference"] == 2


def test_list_leagues_scoped_to_owner():
    client, user = authenticated_client()
    other = User.objects.create_user(email="other@example.com", password="password123")

    client.post(reverse("league:league-list-create"), {"name": "Mine"}, format="json")

    other_client = APIClient()
    other_client.post(reverse("users:login"), {"email": "other@example.com", "password": "password123"}, format="json")
    other_client.post(reverse("league:league-list-create"), {"name": "Theirs"}, format="json")

    resp = client.get(reverse("league:league-list-create"))
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()]
    assert names == ["Mine"]
