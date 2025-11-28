import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import AuditLog, Conference, Division
from users.models import User

pytestmark = pytest.mark.django_db


def auth_client():
    user = User.objects.create_user(email="owner@example.com", password="password123")
    client = APIClient()
    client.post(reverse("users:login"), {"email": user.email, "password": "password123"}, format="json")
    return client, user


def create_league(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League"}, format="json")
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


def test_audit_logs_on_create_and_roster_actions():
    client, _ = auth_client()
    league_id = create_league(client)
    conference, division = get_scaffold_ids(league_id)
    team_id = create_team(client, league_id, conference, division)

    roster_url = reverse("league:team-roster-add", args=[league_id, team_id])
    resp = client.post(
        roster_url,
        {"first_name": "John", "last_name": "Doe", "position": "QB", "age": 25},
        format="json",
    )
    assert resp.status_code == 201
    player_id = resp.json()["id"]

    release_url = reverse("league:team-roster-release", args=[league_id, team_id, player_id])
    release_resp = client.delete(release_url)
    assert release_resp.status_code == 204

    actions = list(AuditLog.objects.values_list("action", flat=True))
    assert "league.create" in actions
    assert "team.create" in actions
    assert "roster.add" in actions
    assert "roster.release" in actions


def test_release_removes_contract():
    client, _ = auth_client()
    league_id = create_league(client)
    conference, division = get_scaffold_ids(league_id)
    team_id = create_team(client, league_id, conference, division)
    roster_url = reverse("league:team-roster-add", args=[league_id, team_id])

    resp = client.post(
        roster_url,
        {
            "first_name": "Cap",
            "last_name": "Hold",
            "position": "WR",
            "age": 26,
            "contract": {"salary": 1000, "bonus": 1000, "years": 1, "start_year": 2025},
        },
        format="json",
    )
    assert resp.status_code == 201
    player_id = resp.json()["id"]

    from league.models import Contract, Player

    player = Player.objects.get(pk=player_id)
    assert hasattr(player, "contract")

    release_url = reverse("league:team-roster-release", args=[league_id, team_id, player_id])
    release_resp = client.delete(release_url)
    assert release_resp.status_code == 204

    assert Contract.objects.filter(player_id=player_id).count() == 0
    player.refresh_from_db()
    assert player.team is None
