import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division
from users.models import User

pytestmark = pytest.mark.django_db


def auth_client(is_commish=False):
    user = User.objects.create_user(email=f"owner{User.objects.count()}@example.com", password="password123", is_commissioner=is_commish)
    client = APIClient()
    client.post(reverse("users:login"), {"email": user.email, "password": "password123"}, format="json")
    return client, user


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


def test_trade_accept_and_reverse():
    client, _ = auth_client(is_commish=True)
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    team_a = scaffold_team(client, league_id, conference, division, "A1", "Alpha")
    team_b = scaffold_team(client, league_id, conference, division, "B1", "Beta")

    player_a = add_player(client, league_id, team_a, "Alice")
    player_b = add_player(client, league_id, team_b, "Bob")

    trade_url = reverse("league:trade-list-create", args=[league_id])
    payload = {
        "from_team": team_a,
        "to_team": team_b,
        "items": [
            {"player": player_a},
            {"player": player_b},
        ],
    }
    create_resp = client.post(trade_url, payload, format="json")
    assert create_resp.status_code == 201
    trade_id = create_resp.json()["id"]

    accept_url = reverse("league:trade-accept", args=[trade_id])
    accept_resp = client.put(accept_url, {}, format="json")
    assert accept_resp.status_code == 200

    roster_b = client.get(reverse("league:team-roster", args=[league_id, team_b])).json()
    roster_a = client.get(reverse("league:team-roster", args=[league_id, team_a])).json()
    assert any(p["id"] == player_a for p in roster_b)
    assert any(p["id"] == player_b for p in roster_a)

    reverse_url = reverse("league:trade-reverse", args=[trade_id])
    reverse_resp = client.put(reverse_url, {}, format="json")
    assert reverse_resp.status_code == 200

    roster_a_after = client.get(reverse("league:team-roster", args=[league_id, team_a])).json()
    roster_b_after = client.get(reverse("league:team-roster", args=[league_id, team_b])).json()
    assert any(p["id"] == player_a for p in roster_a_after)
    assert any(p["id"] == player_b for p in roster_b_after)


def test_trade_creation_requires_team_owner_or_commish():
    client, _ = auth_client(is_commish=False)
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    team_a = scaffold_team(client, league_id, conference, division, "A1", "Alpha")
    team_b = scaffold_team(client, league_id, conference, division, "B1", "Beta")
    player_a = add_player(client, league_id, team_a, "Alice")

    # create a non-owner client
    other_client, _ = auth_client(is_commish=False)
    trade_url = reverse("league:trade-list-create", args=[league_id])
    payload = {"from_team": team_a, "to_team": team_b, "items": [{"player": player_a}]}
    resp = other_client.post(trade_url, payload, format="json")
    assert resp.status_code == 403
