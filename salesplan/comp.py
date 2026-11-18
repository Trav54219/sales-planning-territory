"""Compensation plan calculator: base/variable, accelerators, SPIFs, clawbacks."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Plan:
    base: float = 90_000
    variable_at_target: float = 90_000   # OTE = base + variable
    quota: float = 1_000_000
    # (attainment threshold, rate multiplier applied to bookings above threshold)
    tiers: list[tuple[float, float]] = field(default_factory=lambda: [(0.0, 1.0), (1.0, 1.5), (1.25, 2.0)])
    cap_multiple: float | None = 3.0     # cap on variable as multiple of target variable; None = uncapped
    threshold: float = 0.0               # minimum attainment before variable pays

    @property
    def base_rate(self) -> float:
        """Commission rate on bookings at 1.0x multiplier."""
        return self.variable_at_target / self.quota


def variable_pay(plan: Plan, bookings: float) -> float:
    att = bookings / plan.quota
    if att < plan.threshold:
        return 0.0
    tiers = sorted(plan.tiers)
    pay = 0.0
    for i, (start, mult) in enumerate(tiers):
        end = tiers[i + 1][0] if i + 1 < len(tiers) else float("inf")
        in_tier = max(0.0, min(att, end) - start)
        pay += in_tier * plan.quota * plan.base_rate * mult
    if plan.cap_multiple is not None:
        pay = min(pay, plan.variable_at_target * plan.cap_multiple)
    return pay


def clawback(commission_rate_paid: float, churned_bookings: float, months_active: int, window_months: int = 6) -> float:
    """Full clawback of commission on bookings that churn inside the window, prorated linearly."""
    if months_active >= window_months:
        return 0.0
    return churned_bookings * commission_rate_paid * (1 - months_active / window_months)


def total_comp(plan: Plan, bookings: float, spiffs: float = 0.0, clawbacks: float = 0.0) -> dict:
    var = variable_pay(plan, bookings)
    total = plan.base + var + spiffs - clawbacks
    return {"attainment": bookings / plan.quota, "base": plan.base, "variable": var,
            "spiffs": spiffs, "clawbacks": clawbacks, "total": total,
            "cost_of_sale": (var + spiffs - clawbacks) / bookings if bookings else float("inf")}


def scenario_table(plan: Plan, attainments=(0.5, 0.75, 1.0, 1.25, 1.5, 2.0)) -> list[dict]:
    return [total_comp(plan, a * plan.quota) for a in attainments]
