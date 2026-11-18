from .data import make_accounts, make_reps, make_deals
from . import territory, quota, capacity, comp, report, forecast


def main() -> None:
    print("ALL DATA BELOW IS SYNTHETIC. Output of a planning model, not results.\n")
    accts = make_accounts()
    reps = make_reps()
    terr = territory.design(accts, len(reps))
    print("Territory fairness:", territory.fairness(terr))
    pot = [sum(a.potential for a in t) for t in terr]
    td = quota.top_down(12_000_000, pot)
    bu = quota.bottom_up(pot, 0.85 * 12_000_000 / sum(pot))  # assumed capture rate
    rec = quota.reconcile(td, bu)
    print("Quota gap (top-down vs bottom-up):", f"{rec['gap']:,.0f} ({rec['gap_pct']:.1%})")
    print("Attainment sim:", quota.simulate_attainment(rec["final"]))
    print("Reps needed:", capacity.reps_needed(12_000_000, 1_000_000, 0.85, 0.2))
    for row in comp.scenario_table(comp.Plan()):
        print({k: round(v, 2) for k, v in row.items()})
    deals = make_deals(reps)
    quotas = {r["name"]: q for r, q in zip(reps, rec["final"])}
    booked = {r["name"]: q * 0.4 * r["skill"] for r, q in zip(reps, rec["final"])}
    for r in report.rep_report(quotas, booked, deals):
        print(r)
    print()
    print(forecast.call_template(deals, quotas))


main()
