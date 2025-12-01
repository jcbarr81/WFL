import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division, WaiverClaim
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


def test_waiver_release_and_claim():
    client = auth_client()
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    team_a = scaffold_team(client, league_id, conference, division, "A1", "Alpha")
    team_b = scaffold_team(client, league_id, conference, division, "B1", "Beta")
    player_id = add_player(client, league_id, team_a, "Wally")

    release_url = reverse("league:waiver-release", args=[league_id])
    release_resp = client.post(release_url, {"player_id": player_id, "team_id": team_a}, format="json")
    assert release_resp.status_code == 201
    claim_id = release_resp.json()["id"]

    claim = WaiverClaim.objects.get(pk=claim_id)
    assert claim.status == "pending"
    assert claim.player_id == player_id

    claim_url = reverse("league:waiver-claim", args=[claim_id])
    claim_resp = client.put(claim_url, {"team_id": team_b}, format="json")
    assert claim_resp.status_code == 200
    claim.refresh_from_db()
    assert claim.status == "awarded"
    assert claim.claimed_by_id == team_b

    roster_b = client.get(reverse("league:team-roster", args=[league_id, team_b])).json()
    assert any(p["id"] == player_id for p in roster_b)
