# B3 Branch-and-Price Tree 消融报告

## Objective Boundary

- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。
- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective 的 exact optimum，不证明 makespan-in-objective optimum。

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/smoke/b3_scale005_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/smoke/b3_scale005_summary.json`

## Redlines

| metric | value | required |
| --- | ---: | ---: |
| root_bound_gt_B0_violation_count | 0 | 0 |
| tree_incumbent_diff_vs_B0_count | 0 | 0 |
| certificate_scope_regression_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |
| branch_pricing_audit_fail_count | 0 | 0 |
| proof_debt_unreleased_certified_count | 0 | 0 |
| selected_harvest_addability_fail_count | 0 | 0 |
| direct_dp_certificate_leak_count | 0 | 0 |
| NO_FRACTIONAL_RF_PAIR_treated_as_integral_count | 0 | 0 |
| open_node_but_tree_optimal_count | 0 | 0 |
| incomplete_node_but_tree_optimal_count | 0 | 0 |

## Summary

| scale | group | mode | runs | BPC tree | BPC node LP | fail-closed | mean wall | mean nodes | incomplete nodes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale full normalized objective | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.005566 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2B_R3_true_dual_negative_search_worker | 1 | 0 | 1 | 0 | 0.15799 | 0 | 0 |
| 5 | 5-scale full normalized objective | B2_PRODUCT_EXACT_SOLVER | 1 | 0 | 0 | 0 | 0.005507 | 0 | 0 |
| 5 | 5-scale full normalized objective | B3A_full_universe_branch_audit | 1 | 0 | 1 | 0 | 0.098401 | 1 | 0 |
| 5 | 5-scale full normalized objective | B3B_seeded_branch_price_tree | 1 | 1 | 1 | 0 | 0.168977 | 1 | 0 |

## B3 Accepted?

- B3B accepted: False.
- 5-scale full B3B BPC_TREE_OPTIMAL: 0/0.
- 10-scale selected no-regression vs B2B_R3: False (regressions=0, runs=0).
- 20-scale selected direct20 clean diagnostics: False (unique instances=0).
- Can enter B4: False.

## Notes

