import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division, Game, Season
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


def test_generate_schedule_round_robin():
    client, _ = auth_client()
    league_id = create_league(client)
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()

    for idx, abbr in enumerate(["T1", "T2", "T3", "T4"], start=1):
        scaffold_team(client, league_id, conference, division, abbr, f"Team {idx}")

    url = reverse("league:season-generate", args=[league_id])
    resp = client.post(url, {"year": 2025}, format="json")
    assert resp.status_code == 201

    season = Season.objects.get(league_id=league_id, year=2025)
    weeks = season.weeks.order_by("number").all()
    assert weeks.count() == 3  # 4 teams -> 3 weeks single round robin
    games = Game.objects.filter(week__season=season)
    assert games.count() == 6  # n*(n-1)/2

    schedule_resp = client.get(reverse("league:season-schedule", args=[league_id, 2025]))
    assert schedule_resp.status_code == 200
    data = schedule_resp.json()
    assert len(data["weeks"]) == 3
    assert all("games" in week for week in data["weeks"])


def test_generate_schedule_requires_two_teams():
    client, _ = auth_client()
    league_id = create_league(client)
    url = reverse("league:season-generate", args=[league_id])
    resp = client.post(url, {"year": 2025}, format="json")
    assert resp.status_code == 400
    assert "At least two teams" in resp.json()["detail"]
