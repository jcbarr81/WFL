from typing import List, Dict, Tuple, Optional

from django.db import models

from league.models import Season, Team, Game, Week
from league.services.standings import compute_standings


def generate_playoff_seeds(season: Season, seeds: int = 7) -> List[Dict]:
    """
    Return top seeds per conference (NFL-style 7 per conference by default).
    """
    standings = compute_standings(season)
    grouped = {}
    for record in standings:
        conf = record.get("conference") or "Conference"
        grouped.setdefault(conf, []).append(record)
    seeded: List[Dict] = []
    for conf_name, records in grouped.items():
        top = records[:seeds]
        for idx, rec in enumerate(top, start=1):
            rec = dict(rec)
            rec["seed"] = idx
            rec["conference_name"] = conf_name
            seeded.append(rec)
    # keep deterministic order by conference then seed
    seeded.sort(key=lambda r: (r.get("conference_name", ""), r.get("seed", 99)))
    return seeded


def _conference_bracket(seed_list: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """
    Build a simple bracket for a single conference.
    Uses 7 seeds (1 bye) by default; falls back to top/bottom pairing.
    """
    if not seed_list:
        return []
    seed_list = sorted(seed_list, key=lambda s: s.get("seed", 99))
    if len(seed_list) == 7:
        # Wild card: 2v7,3v6,4v5; 1 seed bye
        return [
          (seed_list[1], seed_list[6]),
          (seed_list[2], seed_list[5]),
          (seed_list[3], seed_list[4]),
          (seed_list[0], None),
        ]
    # Generic pairing highest vs lowest
    result = []
    left = 0
    right = len(seed_list) - 1
    while left < right:
        result.append((seed_list[left], seed_list[right]))
        left += 1
        right -= 1
    if left == right:
        result.append((seed_list[left], None))
    return result


def generate_bracket(season: Season, seeds: int = 7) -> List[Tuple[Dict, Dict, str]]:
    """
    Return a list of matchup tuples (higher_seed, lower_seed, conference).
    For NFL-style 7 seeds per conference: seed 1 gets a bye; 2v7,3v6,4v5.
    """
    seeds_all = generate_playoff_seeds(season, seeds)
    if not seeds_all:
        return []
    # Group by conference
    by_conf: Dict[str, List[Dict]] = {}
    for seed in seeds_all:
        conf = seed.get("conference_name") or "Conference"
        by_conf.setdefault(conf, []).append(seed)
    bracket = []
    for conf_name, conf_seeds in by_conf.items():
        matchups = _conference_bracket(conf_seeds[:seeds])
        for higher, lower in matchups:
            bracket.append((higher, lower, conf_name))
    return bracket


def _find_game(season: Season, team_a_id: int, team_b_id: int) -> Optional[Game]:
    return (
        Game.objects.filter(week__season=season, week__is_playoffs=True)
        .filter(
            (models.Q(home_team_id=team_a_id, away_team_id=team_b_id))
            | (models.Q(home_team_id=team_b_id, away_team_id=team_a_id))
        )
        .order_by("-week__number", "-id")
        .first()
    )


def _winner(game: Game) -> Optional[Team]:
    if not game or game.status != "completed":
        return None
    if game.home_score is None or game.away_score is None:
        return None
    if game.home_score == game.away_score:
        return None
    return game.home_team if game.home_score > game.away_score else game.away_team


def playoff_progress(season: Season, seeds: int = 7):
    """
    Compute playoff rounds with advancing winners (reseeding each round).
    Returns a structure with rounds and matchup status (pending/in-progress/final).
    """
    seeds_all = generate_playoff_seeds(season, seeds)
    if not seeds_all:
        return {"rounds": []}

    by_conf: Dict[str, List[Dict]] = {}
    for seed in seeds_all:
        conf = seed.get("conference_name") or "Conference"
        by_conf.setdefault(conf, []).append(seed)

    rounds = []
    conf_champs = []

    for conf_name, conf_seeds in by_conf.items():
        conf_seeds = sorted(conf_seeds, key=lambda s: s.get("seed", 99))
        seed_map = {s["seed"]: s for s in conf_seeds}

        # Wildcard round
        wc_pairs = [(2, 7), (3, 6), (4, 5)]
        wc_matchups = []
        wc_winners: List[Tuple[int, Dict]] = []
        for a, b in wc_pairs:
            if a not in seed_map or b not in seed_map:
                continue
            ga = seed_map[a]
            gb = seed_map[b]
            game = _find_game(season, ga["team_id"], gb["team_id"])
            winner_team = _winner(game)
            winner_seed = None
            if winner_team:
                winner_seed = a if winner_team.id == ga["team_id"] else b
                wc_winners.append((winner_seed, seed_map[winner_seed]))
            wc_matchups.append(
                {
                    "round": "Wildcard",
                    "conference": conf_name,
                    "higher_seed": ga,
                    "lower_seed": gb,
                    "game_id": getattr(game, "id", None),
                    "status": getattr(game, "status", "pending") if game else "pending",
                    "winner_seed": winner_seed,
                }
            )
        # Seed 1 bye auto-advances
        if 1 in seed_map:
            wc_winners.append((1, seed_map[1]))

        # Divisional: 1 vs lowest remaining, other two face
        div_matchups = []
        div_winners: List[Tuple[int, Dict]] = []
        remaining = sorted(wc_winners, key=lambda x: x[0])
        if len(remaining) >= 2:
            top_seed, top_team = remaining[0]
            bye_seed, bye_team = (1, seed_map[1]) if 1 in seed_map else (None, None)
            if bye_seed and bye_seed != top_seed:
                # 1 vs lowest remaining
                low_seed, low_team = remaining[0]
                game = _find_game(season, bye_team["team_id"], low_team["team_id"]) if bye_team else None
                winner_team = _winner(game)
                winner_seed = None
                if winner_team:
                    winner_seed = bye_seed if winner_team.id == bye_team["team_id"] else low_seed
                    div_winners.append((winner_seed, seed_map[winner_seed]))
                div_matchups.append(
                    {
                        "round": "Divisional",
                        "conference": conf_name,
                        "higher_seed": bye_team,
                        "lower_seed": low_team,
                        "game_id": getattr(game, "id", None),
                        "status": getattr(game, "status", "pending") if game else "pending",
                        "winner_seed": winner_seed,
                    }
                )
                others = [pair for pair in remaining if pair[0] not in (bye_seed, low_seed)]
            else:
                others = remaining
        else:
            others = remaining

        if len(others) >= 2:
            a_seed, a_team = others[0]
            b_seed, b_team = others[1]
            game = _find_game(season, a_team["team_id"], b_team["team_id"])
            winner_team = _winner(game)
            winner_seed = None
            if winner_team:
                winner_seed = a_seed if winner_team.id == a_team["team_id"] else b_seed
                div_winners.append((winner_seed, seed_map[winner_seed]))
            div_matchups.append(
                {
                    "round": "Divisional",
                    "conference": conf_name,
                    "higher_seed": a_team,
                    "lower_seed": b_team,
                    "game_id": getattr(game, "id", None),
                    "status": getattr(game, "status", "pending") if game else "pending",
                    "winner_seed": winner_seed,
                }
            )

        rounds.extend(wc_matchups + div_matchups)

        # Conference championship
        cc_matchups = []
        if len(div_winners) >= 2:
            div_sorted = sorted(div_winners, key=lambda x: x[0])
            a_seed, a_team = div_sorted[0]
            b_seed, b_team = div_sorted[1]
            game = _find_game(season, a_team["team_id"], b_team["team_id"])
            winner_team = _winner(game)
            winner_seed = None
            champ = None
            if winner_team:
                winner_seed = a_seed if winner_team.id == a_team["team_id"] else b_seed
                champ = seed_map[winner_seed]
                conf_champs.append((conf_name, champ))
            cc_matchups.append(
                {
                    "round": "Conference",
                    "conference": conf_name,
                    "higher_seed": a_team,
                    "lower_seed": b_team,
                    "game_id": getattr(game, "id", None),
                    "status": getattr(game, "status", "pending") if game else "pending",
                    "winner_seed": winner_seed,
                }
            )
        elif len(div_winners) == 1:
            # Only one team advanced; they are the champ
            champ = div_winners[0][1]
            conf_champs.append((conf_name, champ))
        rounds.extend(cc_matchups)

    # Championship (Super Bowl) between conference champs, if two exist
    if len(conf_champs) >= 2:
        a_conf, a_team = conf_champs[0]
        b_conf, b_team = conf_champs[1]
        game = _find_game(season, a_team["team_id"], b_team["team_id"])
        winner_team = _winner(game)
        winner_conf = None
        if winner_team:
            winner_conf = a_conf if winner_team.id == a_team["team_id"] else b_conf
        rounds.append(
            {
                "round": "Championship",
                "conference": f"{a_conf} vs {b_conf}",
                "higher_seed": a_team,
                "lower_seed": b_team,
                "game_id": getattr(game, "id", None),
                "status": getattr(game, "status", "pending") if game else "pending",
                "winner_conference": winner_conf,
            }
        )

    return {"rounds": rounds}


ROUND_ORDER = ["Wildcard", "Divisional", "Conference", "Championship"]


def advance_playoff_rounds(season: Season, seeds: int = 7) -> List[int]:
    """
    Create playoff games for the next rounds based on existing results.
    Returns list of created game IDs.
    """
    progress = playoff_progress(season, seeds)
    created: List[int] = []
    if not progress.get("rounds"):
        return created

    max_regular = season.weeks.filter(is_playoffs=False).aggregate(models.Max("number")).get("number__max") or 0

    for idx, round_name in enumerate(ROUND_ORDER, start=1):
        matchups = [m for m in progress["rounds"] if m.get("round") == round_name]
        if not matchups:
            continue
        week_number = max_regular + idx
        week, _ = Week.objects.get_or_create(season=season, number=week_number, is_playoffs=True)
        for m in matchups:
            higher = m.get("higher_seed")
            lower = m.get("lower_seed")
            if not higher or not lower:
                # bye or no opponent; skip scheduling
                continue
            home_id = higher.get("team_id")
            away_id = lower.get("team_id")
            if not home_id or not away_id:
                continue
            exists = Game.objects.filter(week=week).filter(
                (models.Q(home_team_id=home_id, away_team_id=away_id))
                | (models.Q(home_team_id=away_id, away_team_id=home_id))
            )
            if exists.exists():
                continue
            home = Team.objects.get(id=home_id)
            away = Team.objects.get(id=away_id)
            game = Game.objects.create(week=week, home_team=home, away_team=away, status="scheduled")
            created.append(game.id)
    return created
