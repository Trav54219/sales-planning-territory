"""Synthetic data generators. Everything here is random, seeded, and fictional."""
from __future__ import annotations
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    id: int
    x: float          # synthetic map coordinates, 0-100
    y: float
    employees: int
    potential: float  # estimated annual revenue opportunity, USD


@dataclass(frozen=True)
class Deal:
    id: int
    rep: str
    amount: float
    stage: str        # Discovery, Evaluation, Proposal, Negotiation, Verbal
    close_month: int  # 1-12
    days_since_activity: int
    has_next_step: bool
    champion: bool
    economic_buyer: bool
    slipped_count: int


STAGES = ["Discovery", "Evaluation", "Proposal", "Negotiation", "Verbal"]


def make_accounts(n: int = 300, seed: int = 7) -> list[Account]:
    rng = random.Random(seed)
    centers = [(20, 25), (75, 20), (50, 70), (85, 80)]
    out = []
    for i in range(n):
        cx, cy = rng.choice(centers)
        x = min(100, max(0, rng.gauss(cx, 12)))
        y = min(100, max(0, rng.gauss(cy, 12)))
        employees = int(math.exp(rng.gauss(5.0, 1.2)))
        potential = round(employees * rng.uniform(40, 120) * rng.uniform(0.6, 1.4), 2)
        out.append(Account(i, x, y, max(employees, 10), potential))
    return out


def make_reps(n: int = 12, seed: int = 11) -> list[dict]:
    """Rep roster with tenure (months) and a synthetic attainment-driving skill factor."""
    rng = random.Random(seed)
    return [
        {"name": f"Rep {i + 1:02d}", "tenure_months": rng.choice([2, 5, 9, 14, 20, 30, 40]),
         "skill": rng.uniform(0.6, 1.4)}
        for i in range(n)
    ]


def make_deals(reps: list[dict], per_rep: int = 8, seed: int = 21) -> list[Deal]:
    rng = random.Random(seed)
    deals, did = [], 0
    for r in reps:
        for _ in range(per_rep):
            stage = rng.choices(STAGES, weights=[30, 25, 20, 15, 10])[0]
            deals.append(Deal(
                id=did, rep=r["name"], amount=round(rng.uniform(15_000, 180_000), -2),
                stage=stage, close_month=rng.randint(1, 3),
                days_since_activity=rng.choice([1, 2, 3, 5, 8, 12, 20, 35]),
                has_next_step=rng.random() > 0.25, champion=rng.random() > 0.3,
                economic_buyer=rng.random() > 0.45, slipped_count=rng.choice([0, 0, 0, 1, 2, 3]),
            ))
            did += 1
    return deals
