# sales-planning-territory

A small Python model of the planning side of sales operations: territory design, quota setting, capacity planning, comp plan modeling, rep/pipeline reporting, and a forecast call template.

**All data is synthetic**, generated from seeded random numbers in `salesplan/data.py`. Nothing here is real company, customer, or personal data, and nothing here reports real results. This is a modeling exercise, not a claim of carrying a quota or running a sales org.

## What is in it

| Module | Models |
|---|---|
| `territory.py` | Greedy assignment by potential plus a geo penalty, local rebalance, fairness metrics (CV, max/min, Gini, geo radius) |
| `quota.py` | Top-down vs bottom-up quotas, blended reconciliation with the gap, Monte Carlo attainment distribution |
| `capacity.py` | Pipeline required from win rate, coverage ratio, reps needed with attrition and ramp drag, month-by-month hiring plan |
| `comp.py` | Base/variable, tiered accelerators, cap, threshold, SPIFs, prorated clawbacks, scenario table |
| `report.py` | Rep attainment, pace, pipeline coverage, flags |
| `forecast.py` | Commit / Best Case roll-up where Commit must pass inspection rules; markdown call template |

## Run

```
python -m salesplan        # prints every model on synthetic data
python -m pytest           # tests
```

Python 3.10+, standard library only (pytest for tests).

## Assumptions to know

- Territory algorithm is a heuristic (greedy + single-move rebalance), not an optimal solver.
- Attainment simulation uses a lognormal noise assumption; it shows how quota level changes the shape, not what will happen.
- Capacity and comp parameters (win rate, ramp, attrition, tiers) are illustrative defaults you should replace.
