"""Capacity planning: reps needed, ramp, attrition, hiring plan."""
from __future__ import annotations
import math


def pipeline_required(bookings_target: float, win_rate: float) -> float:
    return bookings_target / win_rate


def coverage_ratio(pipeline: float, remaining_quota: float) -> float:
    return pipeline / remaining_quota if remaining_quota > 0 else float("inf")


def effective_capacity(tenure_months: int, ramp_months: int = 6) -> float:
    """Linear ramp from 0 to 1 over ramp_months."""
    return min(1.0, max(0.0, tenure_months / ramp_months))


def reps_needed(bookings_target: float, quota_per_ramped_rep: float, expected_attainment: float,
                attrition_rate: float, ramp_months: int = 6, horizon_months: int = 12) -> int:
    """Headcount to carry at the start of the horizon.

    Productive output per rep = quota * expected attainment. Attrition removes reps part way
    through the year, and replacements lose ramp time: drag = attrition * (ramp / horizon / 2 + 0.5).
    """
    drag = attrition_rate * (ramp_months / horizon_months / 2 + 0.5)
    per_rep = quota_per_ramped_rep * expected_attainment * (1 - drag)
    return math.ceil(bookings_target / per_rep)


def hiring_plan(start_reps: int, target_reps: int, months: int = 12, attrition_rate: float = 0.2,
                ramp_months: int = 6, hires_per_month: int = 1) -> list[dict]:
    """Month-by-month headcount and ramped-equivalent capacity. Deterministic expected-value model."""
    cohorts = [(0, float(start_reps))]  # (hire month, headcount); start reps are fully ramped
    monthly_att = attrition_rate / 12
    out = []
    for m in range(1, months + 1):
        cohorts = [(h, n * (1 - monthly_att)) for h, n in cohorts]
        total = sum(n for _, n in cohorts)
        gap = target_reps - total
        hires = min(hires_per_month, max(0, math.ceil(gap)))
        if hires:
            cohorts.append((m, float(hires)))
        total = sum(n for _, n in cohorts)
        ramped = sum(n * (1.0 if h == 0 else effective_capacity(m - h, ramp_months)) for h, n in cohorts)
        out.append({"month": m, "headcount": round(total, 2), "ramped_equivalent": round(ramped, 2), "hired": hires})
    return out
