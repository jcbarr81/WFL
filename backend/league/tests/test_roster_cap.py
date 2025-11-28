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
    return client, user


def create_league(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League", "salary_cap": 1000000}, format="json")
    assert resp.status_code == 201
    return resp.json()["id"]


def get_scaffold_ids(league_id):
    conference = Conference.objects.filter(league_id=league_id).order_by("id").first()
    division = Division.objects.filter(conference=conference).order_by("id").first()
    return conference, division


def create_team(client, league_id, conference, division, abbr="T1"):
    payload = {
        "name": "Team One",
        "city": "City",
        "nickname": "Nick",
        "abbreviation": abbr,
        "primary_color": "#111111",
        "secondary_color": "#eeeeee",
        "conference": conference.id,
        "division": division.id,
    }
    resp = client.post(reverse("league:team-create", args=[league_id]), payload, format="json")
    assert resp.status_code == 201
    return resp.json()["id"]


def test_roster_limit_enforced():
    client, _ = auth_client()
    league_id = create_league(client)
    conference, division = get_scaffold_ids(league_id)
    team_id = create_team(client, league_id, conference, division)

    roster_url = reverse("league:team-roster-add", args=[league_id, team_id])
    # Set small roster limit
    league_detail = client.get(reverse("league:league-detail", args=[league_id])).json()
    assert league_detail["roster_size_limit"] == 53

    # Force limit to 1 for test
    from league.models import League

    league = League.objects.get(pk=league_id)
    league.roster_size_limit = 1
    league.save()

    first_player = {
        "first_name": "John",
        "last_name": "Doe",
        "position": "QB",
        "age": 25,
    }
    resp1 = client.post(roster_url, first_player, format="json")
    assert resp1.status_code == 201

    second_player = {
        "first_name": "Jane",
        "last_name": "Smith",
        "position": "RB",
        "age": 24,
    }
    resp2 = client.post(roster_url, second_player, format="json")
    assert resp2.status_code == 400
    assert "Roster limit" in resp2.json()["detail"]


def test_cap_validation_blocks_overage():
    client, _ = auth_client()
    league_id = create_league(client)
    conference, division = get_scaffold_ids(league_id)
    team_id = create_team(client, league_id, conference, division)

    roster_url = reverse("league:team-roster-add", args=[league_id, team_id])

    player_data = {
        "first_name": "Cap",
        "last_name": "Buster",
        "position": "QB",
        "age": 28,
        "contract": {
            "salary": 800000,
            "bonus": 300000,
            "years": 3,
            "start_year": 2025,
        },
    }
    resp = client.post(roster_url, player_data, format="json")
    assert resp.status_code == 400
    assert "Cap exceeded" in str(resp.json())

    # valid smaller contract
    player_data["contract"]["salary"] = 400000
    player_data["contract"]["bonus"] = 100000
    resp_ok = client.post(roster_url, player_data, format="json")
    assert resp_ok.status_code == 201
