from django.db.models import Sum, Count

from league.models import PlayerGameStat, Season, TeamGameStat


def player_season_stats(season: Season):
    stats = (
        PlayerGameStat.objects.filter(game__week__season=season)
        .values("player_id", "player__first_name", "player__last_name", "team__abbreviation", "position")
        .annotate(
            games=Count("id"),
            pass_att=Sum("pass_att"),
            pass_cmp=Sum("pass_cmp"),
            pass_yds=Sum("pass_yds"),
            pass_td=Sum("pass_td"),
            pass_int=Sum("pass_int"),
            rush_att=Sum("rush_att"),
            rush_yds=Sum("rush_yds"),
            rush_td=Sum("rush_td"),
            rec=Sum("rec"),
            rec_yds=Sum("rec_yds"),
            rec_td=Sum("rec_td"),
            tackles=Sum("tackles"),
            sacks=Sum("sacks"),
            interceptions=Sum("interceptions"),
            fumbles=Sum("fumbles"),
        )
    )
    # normalize output keys
    results = []
    for row in stats:
        results.append(
            {
                "player_id": row["player_id"],
                "player_name": f"{row['player__first_name']} {row['player__last_name']}",
                "team_abbr": row["team__abbreviation"],
                "position": row["position"],
                **{k: row.get(k) or 0 for k in [
                    "games","pass_att","pass_cmp","pass_yds","pass_td","pass_int",
                    "rush_att","rush_yds","rush_td","rec","rec_yds","rec_td",
                    "tackles","sacks","interceptions","fumbles"
                ]}
            }
        )
    return results


def player_leaders(season: Season, stat: str, limit: int = 10):
    allowed = {
        "pass_yds",
        "pass_td",
        "rush_yds",
        "rush_td",
        "rec_yds",
        "rec_td",
        "tackles",
        "sacks",
        "interceptions",
    }
    if stat not in allowed:
        return []
    agg = player_season_stats(season)
    sorted_list = sorted(agg, key=lambda x: x.get(stat, 0), reverse=True)
    return sorted_list[:limit]


def team_season_stats(season: Season):
    stats = (
        TeamGameStat.objects.filter(game__week__season=season)
        .values("team_id", "team__abbreviation")
        .annotate(
            games=Count("id"),
            total_yards=Sum("total_yards"),
            pass_yards=Sum("pass_yards"),
            rush_yards=Sum("rush_yards"),
            turnovers=Sum("turnovers"),
        )
    )
    results = []
    for row in stats:
        results.append(
            {
                "team_id": row["team_id"],
                "team_abbr": row["team__abbreviation"],
                "games": row.get("games") or 0,
                "total_yards": row.get("total_yards") or 0,
                "pass_yards": row.get("pass_yards") or 0,
                "rush_yards": row.get("rush_yards") or 0,
                "turnovers": row.get("turnovers") or 0,
            }
        )
    return results
