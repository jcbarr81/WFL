from collections import defaultdict
from typing import Dict, List

from league.models import Game, Season, Team


def compute_standings(season: Season) -> List[Dict]:
    records = defaultdict(lambda: {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0})

    games = Game.objects.filter(week__season=season, status="completed").select_related("home_team", "away_team")
    for g in games:
        if g.winner_id == g.home_team_id:
            records[g.home_team_id]["wins"] += 1
            records[g.away_team_id]["losses"] += 1
        elif g.winner_id == g.away_team_id:
            records[g.away_team_id]["wins"] += 1
            records[g.home_team_id]["losses"] += 1
        records[g.home_team_id]["points_for"] += g.home_score
        records[g.home_team_id]["points_against"] += g.away_score
        records[g.away_team_id]["points_for"] += g.away_score
        records[g.away_team_id]["points_against"] += g.home_score

    # Build list with team info
    teams = Team.objects.filter(id__in=records.keys()).select_related("conference", "division")
    standings = []
    for team in teams:
        rec = records[team.id]
        standings.append(
            {
                "team_id": team.id,
                "abbreviation": team.abbreviation,
                "wins": rec["wins"],
                "losses": rec["losses"],
                "points_for": rec["points_for"],
                "points_against": rec["points_against"],
                "conference": team.conference.name,
                "division": team.division.name,
            }
        )

    # Simple sort by wins then PF as placeholder
    standings.sort(key=lambda x: (-x["wins"], -x["points_for"]))
    return standings
