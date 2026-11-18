"""Territory design: greedy assignment, local rebalance, fairness metrics."""
from __future__ import annotations
import math
from .data import Account


def _dist(a: Account, p: tuple[float, float]) -> float:
    return math.hypot(a.x - p[0], a.y - p[1])


def design(accounts: list[Account], k: int, geo_weight: float = 0.3, rebalance_iters: int = 500):
    """Return list of k territories (lists of accounts).

    Phase 1 greedy: seed centroids with farthest-point picks, then place accounts in
    descending potential on the territory minimizing
    (load / target) + geo_weight * (distance to centroid / 100).
    Phase 2 rebalance: move or swap accounts between heaviest and lightest territory
    while the potential spread (max - min) shrinks.
    """
    if k < 1 or k > len(accounts):
        raise ValueError("k must be between 1 and number of accounts")
    seeds = [max(accounts, key=lambda a: a.potential)]
    while len(seeds) < k:
        seeds.append(max(accounts, key=lambda a: min(math.hypot(a.x - s.x, a.y - s.y) for s in seeds)))
    centroids = [(s.x, s.y) for s in seeds]
    target = sum(a.potential for a in accounts) / k
    terr: list[list[Account]] = [[] for _ in range(k)]
    load = [0.0] * k
    for a in sorted(accounts, key=lambda a: -a.potential):
        best = min(range(k), key=lambda t: load[t] / target + geo_weight * _dist(a, centroids[t]) / 100)
        terr[best].append(a)
        load[best] += a.potential
    return rebalance(terr, rebalance_iters)


def rebalance(terr: list[list[Account]], iters: int = 500):
    loads = lambda: [sum(a.potential for a in t) for t in terr]  # noqa: E731
    for _ in range(iters):
        L = loads()
        hi, lo = L.index(max(L)), L.index(min(L))
        gap = L[hi] - L[lo]
        if hi == lo or gap <= 0:
            break
        # best single move from hi to lo: potential closest to gap/2, must not overshoot
        moves = [a for a in terr[hi] if a.potential < gap]
        if not moves:
            break
        a = min(moves, key=lambda a: abs(a.potential - gap / 2))
        terr[hi].remove(a)
        terr[lo].append(a)
    return terr


def gini(values: list[float]) -> float:
    v = sorted(values)
    n, s = len(v), sum(v)
    if n == 0 or s == 0:
        return 0.0
    return sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(v)) / (n * s)


def fairness(terr: list[list[Account]]) -> dict:
    pot = [sum(a.potential for a in t) for t in terr]
    mean = sum(pot) / len(pot)
    sd = math.sqrt(sum((p - mean) ** 2 for p in pot) / len(pot))
    spreads = []
    for t in terr:
        if t:
            cx = sum(a.x for a in t) / len(t)
            cy = sum(a.y for a in t) / len(t)
            spreads.append(sum(_dist(a, (cx, cy)) for a in t) / len(t))
    return {
        "potential_cv": sd / mean if mean else 0.0,
        "max_min_ratio": max(pot) / min(pot) if min(pot) else float("inf"),
        "gini": gini(pot),
        "account_count_range": (min(len(t) for t in terr), max(len(t) for t in terr)),
        "avg_geo_radius": sum(spreads) / len(spreads),
    }
