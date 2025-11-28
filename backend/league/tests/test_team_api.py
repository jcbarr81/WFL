import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division
from users.models import User

pytestmark = pytest.mark.django_db


def setup_league(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League"}, format="json")
    assert resp.status_code == 201
    league_id = resp.json()["id"]
    return league_id


def auth_client():
    user = User.objects.create_user(email="owner@example.com", password="password123")
    client = APIClient()
    client.post(reverse("users:login"), {"email": user.email, "password": "password123"}, format="json")
    return client


def test_create_team_requires_matching_hierarchy():
    client = auth_client()
    league_id = setup_league(client)

    # fetch conference/division created by scaffold
    list_resp = client.get(reverse("league:league-detail", args=[league_id]))
    assert list_resp.status_code == 200

    # pull first conference/division ids from scaffold
    # Since detail serializer does not include nested conf/div, fetch from DB
    conference = Conference.objects.filter(league_id=league_id).order_by("id").first()
    division = Division.objects.filter(conference=conference).order_by("id").first()

    payload = {
        "name": "Team One",
        "city": "City",
        "nickname": "Nick",
        "abbreviation": "CT1",
        "primary_color": "#111111",
        "secondary_color": "#eeeeee",
        "conference": conference.id,
        "division": division.id,
    }

    resp = client.post(
        reverse("league:team-create", args=[league_id]),
        payload,
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["league"] == league_id
    assert body["conference"] == conference.id
    assert body["division"] == division.id


def test_create_team_rejects_wrong_conference():
    client = auth_client()
    league_id = setup_league(client)

    other_league_resp = client.post(reverse("league:league-list-create"), {"name": "Other"}, format="json")
    other_league_id = other_league_resp.json()["id"]

    conference_other = Conference.objects.filter(league_id=other_league_id).first()
    division_other = Division.objects.filter(conference=conference_other).first()

    payload = {
        "name": "Bad Team",
        "city": "Else",
        "nickname": "Wrong",
        "abbreviation": "BAD",
        "conference": conference_other.id,
        "division": division_other.id,
    }

    resp = client.post(
        reverse("league:team-create", args=[league_id]), payload, format="json"
    )
    assert resp.status_code == 400
    assert "conference" in resp.json()
