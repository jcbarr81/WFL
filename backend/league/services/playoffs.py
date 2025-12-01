from typing import List, Dict, Tuple

from league.models import Season, Team
from league.services.standings import compute_standings


def generate_playoff_seeds(season: Season, seeds: int = 4) -> List[Dict]:
    standings = compute_standings(season)
    return standings[:seeds]


def generate_bracket(season: Season, seeds: int = 8) -> List[Tuple[Dict, Dict]]:
    """
    Return a list of matchup tuples (higher_seed, lower_seed). If odd count, last is a bye.
    """
    seeded = generate_playoff_seeds(season, seeds)
    if not seeded:
        return []
    # ensure sorted by seed asc
    seeded = sorted(seeded, key=lambda s: s.get("seed") or seeded.index(s) + 1)
    # apply seed numbers if not present
    for idx, seed in enumerate(seeded, start=1):
        seed.setdefault("seed", idx)
    result = []
    left = 0
    right = len(seeded) - 1
    while left < right:
        result.append((seeded[left], seeded[right]))
        left += 1
        right -= 1
    if left == right:
        result.append((seeded[left], None))
    return result
