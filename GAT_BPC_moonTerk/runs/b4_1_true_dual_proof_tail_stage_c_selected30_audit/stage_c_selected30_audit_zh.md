# B4.1 Stage C Selected 30-scale Audit

## Boundary

- Selected 5-instance diagnostic only; no certificate upgrade is allowed.
- V4 compact formulation is used because Stage B showed the strongest frontier-bound improvement.

## Input Probes

| instance | active cols | added | rounds | state | elapsed s |
|---|---:|---:|---:|---|---:|
| lunar_ice_sp50_030_001_seed929001 | 37 | 3 | 3 | INCOMPLETE_LIMIT | 301.312432 |
| lunar_ice_sp50_030_002_seed929002 | 39 | 5 | 2 | INCOMPLETE_LIMIT | 301.673772 |
| lunar_ice_sp50_030_003_seed929003 | 36 | 2 | 3 | INCOMPLETE_LIMIT | 301.512277 |
| lunar_ice_sp50_030_004_seed929004 | 40 | 6 | 3 | INCOMPLETE_LIMIT | 301.22934 |
| lunar_ice_sp50_030_005_seed929005 | 39 | 5 | 2 | INCOMPLETE_LIMIT | 301.781144 |

## V4 Diagnostic Result

| instance | best frontier LB | negative rows | phases |
|---|---:|---:|---|
| lunar_ice_sp50_030_001_seed929001 | -0.891977561 | 2 | negative_feasibility:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-0.894535244, optimization_proof:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-0.891977561 |
| lunar_ice_sp50_030_002_seed929002 | -1.033680555 | 2 | negative_feasibility:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-1.033680555, optimization_proof:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-1.092151812 |
| lunar_ice_sp50_030_003_seed929003 | -0.770056922 | 2 | negative_feasibility:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-0.790056906, optimization_proof:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-0.770056922 |
| lunar_ice_sp50_030_004_seed929004 | -1.127205592 | 2 | negative_feasibility:COMPACT_HIGHS_PRICING_OPTIMAL:neg1:lb-1.127205592, optimization_proof:COMPACT_HIGHS_PRICING_OPTIMAL:neg1:lb-1.127205592 |
| lunar_ice_sp50_030_005_seed929005 | -2.758521188 | 1 | negative_feasibility:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg1:lb-2.760247654, optimization_proof:COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED:neg0:lb-2.758521188 |

## Conclusion

- Stage C rows: `10`; diagnostic rows only: `True`.
- Any no-negative certificate claimed: `False`.
- Best selected frontier LB: `-0.770056922`.
- All selected 30-scale instances still have negative frontier bounds under 60s V4 diagnostic.
- Stage C confirms the proof-tail bottleneck generalizes beyond instance001.
