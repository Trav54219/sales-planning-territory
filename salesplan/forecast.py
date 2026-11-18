"""Forecast call template: commit / best case roll-up with inspection rules."""
from __future__ import annotations
from collections import defaultdict
from .data import Deal

# Inspection rules a deal must pass to stay in Commit.
RULES = {
    "activity within 7 days": lambda d: d.days_since_activity <= 7,
    "next step scheduled": lambda d: d.has_next_step,
    "economic buyer engaged": lambda d: d.economic_buyer,
    "champion identified": lambda d: d.champion,
    "slipped fewer than 2 times": lambda d: d.slipped_count < 2,
}
COMMIT_STAGES = {"Negotiation", "Verbal"}
BEST_CASE_STAGES = {"Proposal"} | COMMIT_STAGES


def failed_rules(d: Deal) -> list[str]:
    return [name for name, fn in RULES.items() if not fn(d)]


def categorize(d: Deal) -> str:
    """Commit = late stage AND passes all rules. Late-stage failures drop to Best Case.
    Proposal stage = Best Case. Anything earlier = Pipeline (not forecast)."""
    if d.stage in COMMIT_STAGES:
        return "Commit" if not failed_rules(d) else "Best Case"
    if d.stage in BEST_CASE_STAGES:
        return "Best Case"
    return "Pipeline"


def rollup(deals: list[Deal], month: int | None = None) -> dict[str, dict[str, float]]:
    """Per-rep and total sums by category. Best Case is cumulative on top of Commit in the call view."""
    by_rep: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for d in deals:
        if month is not None and d.close_month != month:
            continue
        by_rep[d.rep][categorize(d)] += d.amount
        by_rep["TOTAL"][categorize(d)] += d.amount
    return {r: dict(v) for r, v in by_rep.items()}


def call_template(deals: list[Deal], quotas: dict[str, float] | None = None, month: int = 1) -> str:
    roll = rollup(deals, month)
    lines = [f"# Forecast call, month {month} (synthetic data)", "",
             "| Rep | Commit | Best Case (added) | Commit + Best Case | Quota |", "|---|---:|---:|---:|---:|"]
    for rep in sorted(k for k in roll if k != "TOTAL") + ["TOTAL"]:
        if rep not in roll:
            continue
        c, b = roll[rep].get("Commit", 0), roll[rep].get("Best Case", 0)
        q = (quotas or {}).get(rep) if rep != "TOTAL" else (sum(quotas.values()) if quotas else None)
        lines.append(f"| {rep} | {c:,.0f} | {b:,.0f} | {c + b:,.0f} | {f'{q:,.0f}' if q else '-'} |")
    lines += ["", "## Inspect before the number is accepted", ""]
    for d in sorted((d for d in deals if d.close_month == month and d.stage in BEST_CASE_STAGES),
                    key=lambda d: -d.amount):
        fails = failed_rules(d)
        if fails:
            lines.append(f"- {d.rep} deal {d.id} ({d.stage}, {d.amount:,.0f}) -> {categorize(d)}: "
                         + "; ".join(fails))
    lines += ["", "## Questions for each Commit deal", "",
              "1. What is the mutual close plan and the next dated step?",
              "2. Who signs, and have we spoken to them directly?",
              "3. What would make this slip, and what is the fallback date?"]
    return "\n".join(lines)
