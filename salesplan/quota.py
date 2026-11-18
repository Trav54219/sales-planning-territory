"""Quota setting: top-down vs bottom-up, reconciliation, attainment distribution."""
from __future__ import annotations
import random


def top_down(company_target: float, weights: list[float]) -> list[float]:
    """Allocate a company target proportional to territory weights (e.g. potential)."""
    total = sum(weights)
    return [company_target * w / total for w in weights]


def bottom_up(potentials: list[float], capture_rate: float, ramp_factors: list[float] | None = None) -> list[float]:
    """Each rep's quota = potential * capture_rate * ramp factor (1.0 = fully ramped)."""
    ramp = ramp_factors or [1.0] * len(potentials)
    return [p * capture_rate * r for p, r in zip(potentials, ramp)]


def reconcile(top: list[float], bottom: list[float], blend: float = 0.5) -> dict:
    """Blend the two views; report the gap the planning team has to explain."""
    if len(top) != len(bottom):
        raise ValueError("length mismatch")
    final = [blend * t + (1 - blend) * b for t, b in zip(top, bottom)]
    return {"final": final, "top_total": sum(top), "bottom_total": sum(bottom),
            "gap": sum(top) - sum(bottom), "gap_pct": (sum(top) - sum(bottom)) / sum(top)}


def simulate_attainment(quotas: list[float], expected_pct: float = 0.9, sigma: float = 0.3,
                        seed: int = 1, trials: int = 1000) -> dict:
    """Monte Carlo of attainment (bookings/quota) with lognormal noise around expected_pct.
    Model assumption only: not a prediction."""
    rng = random.Random(seed)
    att = []
    for _ in range(trials):
        for _q in quotas:
            att.append(expected_pct * rng.lognormvariate(0, sigma))
    att.sort()
    n = len(att)
    q = lambda p: att[min(n - 1, int(p * n))]  # noqa: E731
    return {"pct_at_or_above_100": sum(a >= 1 for a in att) / n, "p10": q(0.1), "median": q(0.5),
            "p90": q(0.9), "pct_below_50": sum(a < 0.5 for a in att) / n}
