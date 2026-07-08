# B3 Branch-and-Price Tree 消融报告

## Objective Boundary

- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。
- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。
- `BPC_TREE_OPTIMAL` 只证明 normalized additive objective 的 exact optimum，不证明 makespan-in-objective optimum。

## Artifacts

- CSV rows: `runs/objective_normalized_cost_risk_completion_full/b3_scale010_rows.csv`
- JSON summary: `runs/objective_normalized_cost_risk_completion_full/b3_scale010_summary.json`

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
| 10 | 10-scale full normalized objective | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.28815 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 18 | 2 | 1.831933 | 0 | 0 |
| 10 | 10-scale full normalized objective | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.290036 | 0 | 0 |
| 10 | 10-scale full normalized objective | B3A_full_universe_branch_audit | 20 | 0 | 20 | 0 | 1.345573 | 1 | 0 |
| 10 | 10-scale full normalized objective | B3B_seeded_branch_price_tree | 20 | 20 | 30 | 0 | 2.491146 | 1.5 | 0 |

## Acceptance Scope

- Cross-scale B3 acceptance is not evaluated in this artifact; this report may contain only one scale or one batch.
- Local B3B BPC_TREE_OPTIMAL: 20/20.
- Local B3B all tree optimal: True.
- Use the master normalized objective report for cross-scale B0/B3B alignment and final acceptance boundaries.

## Notes

