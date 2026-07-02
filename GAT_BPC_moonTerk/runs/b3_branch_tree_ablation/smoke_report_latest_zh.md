# B3 Branch-and-Price Tree 消融报告

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/smoke_rows_latest.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/smoke_summary_latest.json`

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
| 10 | 10-scale selected5 | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.059511 | 0 | 0 |
| 10 | 10-scale selected5 | B2B_R3_true_dual_negative_search_worker | 1 | 0 | 0 | 0 | 0.743711 | 0 | 0 |
| 10 | 10-scale selected5 | B2_PRODUCT_EXACT_SOLVER | 1 | 0 | 0 | 0 | 0.059763 | 0 | 0 |
| 10 | 10-scale selected5 | B3A_full_universe_branch_audit | 1 | 0 | 0 | 1 | 0.002022 | 0 | 0 |
| 10 | 10-scale selected5 | B3B_seeded_branch_price_tree | 1 | 1 | 1 | 0 | 1.53215 | 1 | 0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.019687 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.008959 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.008712 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.007838 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.009256 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.045463 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.020787 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.019972 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.01867 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.021442 | 0 | 0 |
| 5 | 5-scale selected | B0_pure_direct_dp | 1 | 0 | 0 | 0 | 0.004604 | 0 | 0 |
| 5 | 5-scale selected | B2B_R3_true_dual_negative_search_worker | 1 | 0 | 0 | 0 | 0.157522 | 0 | 0 |
| 5 | 5-scale selected | B2_PRODUCT_EXACT_SOLVER | 1 | 0 | 0 | 0 | 0.004525 | 0 | 0 |
| 5 | 5-scale selected | B3A_full_universe_branch_audit | 1 | 0 | 0 | 0 | 0.084673 | 1 | 0 |
| 5 | 5-scale selected | B3B_seeded_branch_price_tree | 1 | 1 | 1 | 0 | 0.313229 | 1 | 0 |

## B3 Accepted?

- B3B accepted: False.
- 5-scale full B3B BPC_TREE_OPTIMAL: 0/0.
- 10-scale selected no-regression vs B2B_R3: False (regressions=0, runs=1).
- 20-scale selected direct20 clean diagnostics: False (unique instances=0).
- Can enter B4: False.

## Notes

- B3 runner is serial by default to avoid concurrent branch/final-judge memory spikes.
- B3B uses B2B_R3 node pricing; B3A full-universe branch audit is diagnostic only.
- 20-scale selected direct20 probe defaults to 5 instances; use --scale20-probe-limit 0 only for a skipped diagnostic.
- 10-scale ran selected 1/20 first; full run is deferred.
- 20-scale fail-closed guard uses max_direct_tasks below 20; fail-closed is expected.
- 30-scale diagnostic is expected to fail closed unless an explicit larger exact-pricing limit is selected.
