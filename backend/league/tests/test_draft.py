import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Draft, DraftPick, Conference, Division
from users.models import User

pytestmark = pytest.mark.django_db


def auth_client():
    user = User.objects.create_user(email="commish@example.com", password="password123", is_commissioner=True)
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


def test_draft_create_and_pick():
    client = auth_client()
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    team_a = scaffold_team(client, league_id, conference, division, "A1", "Alpha")
    team_b = scaffold_team(client, league_id, conference, division, "B1", "Beta")

    player_id = add_player(client, league_id, team_a, "Rookie")

    create_url = reverse("league:draft-create", args=[league_id])
    create_resp = client.post(create_url, {}, format="json")
    assert create_resp.status_code == 201
    draft_id = create_resp.json()["id"]

    draft = Draft.objects.get(pk=draft_id)
    assert draft.picks.count() == draft.rounds * 2  # two teams

    pick = DraftPick.objects.filter(draft=draft).order_by("overall_number").first()
    select_url = reverse("league:draft-pick-select", args=[pick.id])
    resp_select = client.put(select_url, {"player_id": player_id}, format="json")
    assert resp_select.status_code == 200
    pick.refresh_from_db()
    assert pick.player_id == player_id
    assert pick.is_selected is True
