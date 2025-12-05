import random
from typing import List, Dict

from django.db import transaction
from django.utils import timezone

from league.models import Game, PlayLog, TeamGameStat, PlayerGameStat


def _team_power(team) -> float:
    players = list(team.players.all())
    if not players:
        return 60.0
    # Blend overall and core ratings if present
    totals = []
    for p in players:
        core = getattr(p, "rating_speed", None)
        if core is not None:
            avg_core = (
                p.rating_speed
                + p.rating_accel
                + p.rating_agility
                + p.rating_strength
                + p.rating_hands
                + p.rating_endurance
                + p.rating_intelligence
                + p.rating_discipline
            ) / 8
            totals.append(0.6 * p.overall_rating + 0.4 * avg_core)
        else:
            totals.append(p.overall_rating)
    return sum(totals) / len(totals)


def _skill_groups(team):
    qbs = list(team.players.filter(position="QB").order_by("-overall_rating")[:1])
    rbs = list(team.players.filter(position="RB").order_by("-overall_rating")[:2])
    wrs = list(team.players.filter(position="WR").order_by("-overall_rating")[:3])
    tes = list(team.players.filter(position="TE").order_by("-overall_rating")[:1])
    return {"QB": qbs, "RB": rbs, "WR": wrs, "TE": tes}


def _generate_player_stats(game: Game, home_yards: int, away_yards: int):
    home_groups = _skill_groups(game.home_team)
    away_groups = _skill_groups(game.away_team)

    def gen_side(groups, yards, is_home: bool):
        pass_yds = int(yards * 0.6)
        rush_yds = yards - pass_yds
        qb = groups["QB"][0] if groups["QB"] else None
        if qb:
            PlayerGameStat.objects.update_or_create(
                game=game,
                player=qb,
                defaults={
                    "team": game.home_team if is_home else game.away_team,
                    "position": "QB",
                    "pass_att": 25,
                    "pass_cmp": 16,
                    "pass_yds": pass_yds,
                    "pass_td": random.randint(0, 3),
                    "pass_int": random.randint(0, 2),
                },
            )
        rushers = (groups["RB"] + groups["QB"][:1])[:2]
        if rushers:
            split = _split_yards(rush_yds, len(rushers))
            for idx, p in enumerate(rushers):
                PlayerGameStat.objects.update_or_create(
                    game=game,
                    player=p,
                    defaults={
                        "team": game.home_team if is_home else game.away_team,
                        "position": p.position,
                        "rush_att": 12 if p.position == "RB" else 4,
                        "rush_yds": split[idx],
                        "rush_td": 1 if idx == 0 and rush_yds > 80 else 0,
                    },
                )
        receivers = (groups["WR"] + groups["TE"])[:3]
        if receivers:
            split = _split_yards(pass_yds, len(receivers))
            for idx, p in enumerate(receivers):
                PlayerGameStat.objects.update_or_create(
                    game=game,
                    player=p,
                    defaults={
                        "team": game.home_team if is_home else game.away_team,
                        "position": p.position,
                        "rec": 4 + idx,
                        "rec_yds": split[idx],
                        "rec_td": 1 if idx == 0 and pass_yds > 120 else 0,
                    },
                )

    gen_side(home_groups, home_yards, True)
    gen_side(away_groups, away_yards, False)


def _split_yards(total: int, parts: int) -> list[int]:
    if parts <= 0:
        return []
    base = max(0, total // parts)
    result = [base for _ in range(parts)]
    remain = total - base * parts
    idx = 0
    while remain > 0:
        result[idx % parts] += 1
        idx += 1
        remain -= 1
    return result


def simulate_game(game: Game) -> Dict:
    """
    Simple ratings-driven sim that produces play-by-play and team stats.
    """
    home_power = _team_power(game.home_team)
    away_power = _team_power(game.away_team)
    home_score = 0
    away_score = 0
    plays: List[Dict] = []
    play_index = 1
    quarters = [900, 900, 900, 900]
    for q_idx, q_time in enumerate(quarters, start=1):
        clock = q_time
        # ~12 plays per quarter
        for _ in range(12):
            clock = max(0, clock - random.randint(15, 45))
            # determine possession by relative power
            if random.random() < home_power / (home_power + away_power):
                offense = "home"
                defense = "away"
            else:
                offense = "away"
                defense = "home"
            base = home_power if offense == "home" else away_power
            def_base = away_power if offense == "home" else home_power
            yard = int(random.gauss((base - def_base) * 0.2 + 4, 8))
            yard = max(-10, min(80, yard))
            result = "run" if random.random() < 0.45 else "pass"
            summary = f"{offense.upper()} {result} for {yard} yards"
            # scoring
            if yard >= 20 and random.random() < 0.15:
                score_add = 7
                if offense == "home":
                    home_score += score_add
                else:
                    away_score += score_add
                summary = f"{offense.upper()} TD on a {result} ({score_add} pts)"
            elif yard >= 3 and random.random() < 0.25:
                score_add = 3
                if offense == "home":
                    home_score += score_add
                else:
                    away_score += score_add
                summary = f"{offense.upper()} FG ({score_add} pts)"
            elif yard < -5 and random.random() < 0.1:
                # turnover
                summary = f"{offense.upper()} turnover"
                if offense == "home":
                    away_score += 0
                else:
                    home_score += 0
            plays.append(
                {
                    "play_index": play_index,
                    "quarter": q_idx,
                    "clock_seconds": clock,
                    "summary": summary,
                    "home_score": home_score,
                    "away_score": away_score,
                }
            )
            play_index += 1
    # final outcome
    status = "completed"
    winner = None
    loser = None
    if home_score > away_score:
        winner = game.home_team
        loser = game.away_team
    elif away_score > home_score:
        winner = game.away_team
        loser = game.home_team
    return {
        "home_score": home_score,
        "away_score": away_score,
        "status": status,
        "winner": winner,
        "loser": loser,
        "plays": plays,
        "home_power": home_power,
        "away_power": away_power,
    }


@transaction.atomic
def persist_sim_result(game: Game, sim_result: Dict):
    game.home_score = sim_result["home_score"]
    game.away_score = sim_result["away_score"]
    game.status = sim_result["status"]
    game.winner = sim_result["winner"]
    game.loser = sim_result["loser"]
    game.save(update_fields=["home_score", "away_score", "status", "winner", "loser"])
    # Clear previous logs/stats
    game.plays.all().delete()
    game.team_stats.all().delete()
    plays = sim_result.get("plays", [])
    for play in plays:
        PlayLog.objects.create(game=game, **play)
    # Simple team stats derived from power
    home_yards = int(sim_result["home_score"] * 10 + random.randint(180, 360))
    away_yards = int(sim_result["away_score"] * 10 + random.randint(180, 360))
    TeamGameStat.objects.create(
        game=game,
        team=game.home_team,
        total_yards=home_yards,
        pass_yards=int(home_yards * 0.6),
        rush_yards=int(home_yards * 0.4),
        turnovers=random.randint(0, 2),
    )

    # Generate coarse player stats shares
    _generate_player_stats(game, home_yards, away_yards)
    TeamGameStat.objects.create(
        game=game,
        team=game.away_team,
        total_yards=away_yards,
        pass_yards=int(away_yards * 0.6),
        rush_yards=int(away_yards * 0.4),
        turnovers=random.randint(0, 2),
    )
