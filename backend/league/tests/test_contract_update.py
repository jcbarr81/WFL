import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division
from users.models import User

pytestmark = pytest.mark.django_db


def auth_client():
    user = User.objects.create_user(email="owner@example.com", password="password123")
    client = APIClient()
    client.post(reverse("users:login"), {"email": user.email, "password": "password123"}, format="json")
    return client


def create_league(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League"}, format="json")
    assert resp.status_code == 201
    return resp.json()["id"]


def scaffold_team(client, league_id, conference, division, abbr, name):
    payload = {
        "name": name,
        "city": name,
        "nickname": name,
        "abbreviation": abbr,
        "primary_color": "#111111",
        "secondary_color": "#eeeeee",
        "conference": conference.id,
        "division": division.id,
    }
    resp = client.post(reverse("league:team-create", args=[league_id]), payload, format="json")
    assert resp.status_code == 201
    return resp.json()["id"]


def add_player(client, league_id, team_id, first_name):
    roster_url = reverse("league:team-roster-add", args=[league_id, team_id])
    resp = client.post(
        roster_url,
        {"first_name": first_name, "last_name": "Player", "position": "QB", "age": 25},
        format="json",
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_contract_update_respects_cap():
    client = auth_client()
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    team_id = scaffold_team(client, league_id, conference, division, "A1", "Alpha")
    player_id = add_player(client, league_id, team_id, "Cap")

    url = reverse("league:contract-update", args=[league_id, player_id])

    # Exceeds cap (league cap default 200,000,000 so use a lower cap)
    from league.models import League

    league = League.objects.get(pk=league_id)
    league.salary_cap = 1000
    league.save()

    resp = client.put(url, {"salary": 900, "bonus": 200, "years": 2, "start_year": 2025}, format="json")
    assert resp.status_code == 400
    assert "Cap exceeded" in str(resp.json())

    # Valid contract within cap
    resp_ok = client.put(url, {"salary": 500, "bonus": 100, "years": 2, "start_year": 2025}, format="json")
    assert resp_ok.status_code == 200
    body = resp_ok.json()
    assert body["salary"] == "500.00"
    assert body["bonus"] == "100.00"
