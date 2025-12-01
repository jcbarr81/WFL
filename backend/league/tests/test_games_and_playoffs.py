import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from league.models import Conference, Division, Game, Season, Team
from users.models import User

pytestmark = pytest.mark.django_db


def auth_client():
    user = User.objects.create_user(email="commish@example.com", password="password123", is_commissioner=True)
    client = APIClient()
    client.post(reverse("users:login"), {"email": user.email, "password": "password123"}, format="json")
    return client


def create_league_and_teams(client):
    resp = client.post(reverse("league:league-list-create"), {"name": "League"}, format="json")
    league_id = resp.json()["id"]
    conference = Conference.objects.filter(league_id=league_id).first()
    division = Division.objects.filter(conference=conference).first()
    team_a = client.post(
        reverse("league:team-create", args=[league_id]),
        {
            "name": "Alpha",
            "city": "Alpha",
            "nickname": "A",
            "abbreviation": "A1",
            "primary_color": "#111111",
            "secondary_color": "#eeeeee",
            "conference": conference.id,
            "division": division.id,
        },
        format="json",
    ).json()["id"]
    team_b = client.post(
        reverse("league:team-create", args=[league_id]),
        {
            "name": "Beta",
            "city": "Beta",
            "nickname": "B",
            "abbreviation": "B1",
            "primary_color": "#111111",
            "secondary_color": "#eeeeee",
            "conference": conference.id,
            "division": division.id,
        },
        format="json",
    ).json()["id"]
    return league_id, team_a, team_b


def test_complete_game_and_seedings():
    client = auth_client()
    league_id, team_a, team_b = create_league_and_teams(client)

    # create season and game manually
    season = Season.objects.create(league_id=league_id, year=2025)
    week = season.weeks.create(number=1, is_playoffs=False)
    game = Game.objects.create(week=week, home_team_id=team_a, away_team_id=team_b, status="scheduled")

    complete_url = reverse("league:game-complete", args=[game.id])
    resp = client.put(complete_url, {"home_score": 21, "away_score": 14}, format="json")
    assert resp.status_code == 200
    game.refresh_from_db()
    assert game.status == "completed"
    assert game.winner_id == team_a

    standings_url = reverse("league:standings", args=[league_id, 2025])
    standings = client.get(standings_url).json()
    assert standings[0]["wins"] == 1

    seeds_url = reverse("league:playoff-seeds", args=[league_id, 2025])
    seeds = client.get(seeds_url).json()
    assert seeds[0]["seed"] == 1
