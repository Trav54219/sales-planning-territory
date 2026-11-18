"""Rep performance and pipeline coverage report."""
from __future__ import annotations
from collections import defaultdict
from .data import Deal
from .capacity import coverage_ratio


def rep_report(quotas: dict[str, float], booked: dict[str, float], deals: list[Deal],
               elapsed_fraction: float = 0.5, target_coverage: float = 3.0) -> list[dict]:
    open_pipe: dict[str, float] = defaultdict(float)
    for d in deals:
        open_pipe[d.rep] += d.amount
    rows = []
    for rep, q in quotas.items():
        b = booked.get(rep, 0.0)
        remaining = max(q - b, 0.0)
        cov = coverage_ratio(open_pipe[rep], remaining)
        pace = b / (q * elapsed_fraction) if q and elapsed_fraction else 0.0
        flag = "ok"
        if cov < target_coverage and remaining > 0:
            flag = "coverage gap"
        if pace < 0.7:
            flag = "behind pace" if flag == "ok" else flag + " + behind pace"
        rows.append({"rep": rep, "quota": q, "booked": b, "attainment": b / q if q else 0.0,
                     "pace": pace, "open_pipeline": open_pipe[rep], "coverage": cov, "flag": flag})
    return sorted(rows, key=lambda r: -r["attainment"])
