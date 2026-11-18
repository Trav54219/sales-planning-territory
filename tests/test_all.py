import math
import pytest
from salesplan import territory, quota, capacity, comp, report, forecast
from salesplan.data import make_accounts, make_reps, make_deals, Deal


def test_territory_covers_every_account_once():
    a = make_accounts(200)
    t = territory.design(a, 8)
    ids = [x.id for tt in t for x in tt]
    assert sorted(ids) == sorted(x.id for x in a)


def test_rebalance_improves_or_keeps_spread():
    a = make_accounts(200)
    k = 8
    seeded = territory.design(a, k, rebalance_iters=0)
    before = territory.fairness([list(t) for t in seeded])["max_min_ratio"]
    after = territory.fairness(territory.design(a, k))["max_min_ratio"]
    assert after <= before + 1e-9


def test_territories_reasonably_balanced():
    f = territory.fairness(territory.design(make_accounts(300), 10))
    assert f["potential_cv"] < 0.25


def test_gini_extremes():
    assert territory.gini([5, 5, 5]) == 0
    assert territory.gini([0, 0, 10]) > 0.6


def test_bad_k():
    with pytest.raises(ValueError):
        territory.design(make_accounts(5), 9)


def test_top_down_sums_to_target():
    assert math.isclose(sum(quota.top_down(1000, [1, 2, 3])), 1000)


def test_reconcile_blend_and_gap():
    r = quota.reconcile([100, 100], [60, 60], blend=0.5)
    assert r["final"] == [80, 80] and r["gap"] == 80


def test_attainment_monotonic_in_expectation():
    lo = quota.simulate_attainment([1] * 5, 0.7)["pct_at_or_above_100"]
    hi = quota.simulate_attainment([1] * 5, 1.1)["pct_at_or_above_100"]
    assert hi > lo


def test_pipeline_math():
    assert capacity.pipeline_required(1_000_000, 0.25) == 4_000_000
    assert capacity.coverage_ratio(3, 1) == 3


def test_reps_needed_rises_with_attrition():
    base = capacity.reps_needed(12e6, 1e6, 0.85, 0.0)
    assert capacity.reps_needed(12e6, 1e6, 0.85, 0.3) > base
    assert base == math.ceil(12e6 / 0.85e6)


def test_hiring_plan_ramp_lags_headcount():
    p = capacity.hiring_plan(5, 10)
    assert all(r["ramped_equivalent"] <= r["headcount"] + 1e-9 for r in p)
    assert p[-1]["headcount"] > p[0]["headcount"]


def test_comp_at_target_pays_target_variable():
    p = comp.Plan()
    assert math.isclose(comp.variable_pay(p, p.quota), p.variable_at_target)


def test_accelerator_and_cap():
    p = comp.Plan()
    # 125% attainment: 100% at 1x + 25% at 1.5x
    assert math.isclose(comp.variable_pay(p, 1.25 * p.quota), p.variable_at_target * (1 + 0.25 * 1.5))
    assert comp.variable_pay(p, 10 * p.quota) == p.variable_at_target * p.cap_multiple


def test_threshold_gate():
    p = comp.Plan(threshold=0.5)
    assert comp.variable_pay(p, 0.4 * p.quota) == 0


def test_clawback_prorates_and_expires():
    assert comp.clawback(0.1, 100_000, 0) == 10_000
    assert comp.clawback(0.1, 100_000, 3) == 5_000
    assert comp.clawback(0.1, 100_000, 6) == 0


def test_total_comp_with_spiff_and_clawback():
    p = comp.Plan()
    t = comp.total_comp(p, p.quota, spiffs=1000, clawbacks=500)
    assert t["total"] == p.base + p.variable_at_target + 500


def test_scenario_table_monotonic():
    rows = comp.scenario_table(comp.Plan())
    tot = [r["total"] for r in rows]
    assert tot == sorted(tot)


def _deal(**kw):
    base = dict(id=1, rep="A", amount=100, stage="Negotiation", close_month=1, days_since_activity=2,
                has_next_step=True, champion=True, economic_buyer=True, slipped_count=0)
    base.update(kw)
    return Deal(**base)


def test_commit_requires_all_rules():
    assert forecast.categorize(_deal()) == "Commit"
    assert forecast.categorize(_deal(economic_buyer=False)) == "Best Case"
    assert forecast.categorize(_deal(days_since_activity=20)) == "Best Case"
    assert forecast.categorize(_deal(slipped_count=2)) == "Best Case"
    assert forecast.categorize(_deal(stage="Proposal")) == "Best Case"
    assert forecast.categorize(_deal(stage="Discovery")) == "Pipeline"


def test_rollup_totals_match():
    deals = make_deals(make_reps())
    r = forecast.rollup(deals)
    assert math.isclose(sum(r["TOTAL"].values()), sum(d.amount for d in deals))


def test_call_template_labels_synthetic():
    deals = make_deals(make_reps())
    assert "synthetic" in forecast.call_template(deals).lower()


def test_rep_report_flags():
    d = [_deal(rep="A", amount=100)]
    rows = report.rep_report({"A": 1000}, {"A": 100}, d)
    assert "coverage gap" in rows[0]["flag"] and "behind pace" in rows[0]["flag"]
