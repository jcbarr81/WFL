from collections import deque
from typing import List

from league.models import Game, League, Season, Team, Week


def _round_robin_pairings(team_ids: List[int]) -> List[List[tuple[int, int]]]:
    teams = list(team_ids)
    if len(teams) % 2 != 0:
        teams.append(None)  # bye slot
    n = len(teams)
    half = n // 2
    rotation = deque(teams[1:])
    rounds = []

    for _ in range(n - 1):
        left = [teams[0]] + list(rotation)[: half - 1]
        right = list(rotation)[half - 1 :]
        pairings = []
        for home, away in zip(left, reversed(right)):
            if home is None or away is None:
                continue
            pairings.append((home, away))
        rounds.append(pairings)
        rotation.rotate(1)

    return rounds


def generate_regular_season_schedule(league: League, year: int) -> Season:
    teams = list(league.teams.all())
    if len(teams) < 2:
        raise ValueError("At least two teams are required to generate a schedule.")

    season, _ = Season.objects.get_or_create(league=league, year=year)
    # Clear existing weeks/games for a regenerate
    season.weeks.all().delete()

    team_ids = [t.id for t in teams]
    rounds = _round_robin_pairings(team_ids)

    week_objs = []
    for idx, matchups in enumerate(rounds, start=1):
        week = Week.objects.create(season=season, number=idx, is_playoffs=False)
        week_objs.append(week)
        for home_id, away_id in matchups:
            # Alternate home/away each week for fairness
            if idx % 2 == 0:
                home_id, away_id = away_id, home_id
            Game.objects.create(
                week=week,
                home_team_id=home_id,
                away_team_id=away_id,
            )

    return season
