# B3 Branch-and-Price Tree 消融报告

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/b3_branch_tree_no20probe_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/b3_branch_tree_no20probe_summary.json`

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
| 10 | 10-scale selected5 | B0_pure_direct_dp | 5 | 0 | 0 | 0 | 0.123815 | 0 | 0 |
| 10 | 10-scale selected5 | B2B_R3_true_dual_negative_search_worker | 5 | 0 | 5 | 0 | 0.832551 | 0 | 0 |
| 10 | 10-scale selected5 | B2_PRODUCT_EXACT_SOLVER | 5 | 0 | 0 | 0 | 0.126815 | 0 | 0 |
| 10 | 10-scale selected5 | B3A_full_universe_branch_audit | 5 | 0 | 0 | 5 | 0.002158 | 0 | 0 |
| 10 | 10-scale selected5 | B3B_seeded_branch_price_tree | 5 | 5 | 5 | 0 | 1.692163 | 1 | 0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.018838 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.008796 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.008698 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.007981 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.009526 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.043322 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.019406 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.020077 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.018242 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.02168 | 0 | 0 |
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.00582 | 0 | 0 |
| 5 | 5-scale full | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 20 | 0 | 0.309727 | 0 | 0 |
| 5 | 5-scale full | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.006016 | 0 | 0 |
| 5 | 5-scale full | B3A_full_universe_branch_audit | 20 | 0 | 20 | 0 | 0.203011 | 1 | 0 |
| 5 | 5-scale full | B3B_seeded_branch_price_tree | 20 | 20 | 20 | 0 | 0.653332 | 1 | 0 |

## B3 Accepted?

- B3B accepted: False.
- 5-scale full B3B BPC_TREE_OPTIMAL: 20/20.
- 10-scale selected no-regression vs B2B_R3: True (regressions=0, runs=5).
- 20-scale selected direct20 clean diagnostics: False (unique instances=0).
- Can enter B4: False.

## Notes

- B3 runner is serial by default to avoid concurrent branch/final-judge memory spikes.
- B3B uses B2B_R3 node pricing; B3A full-universe branch audit is diagnostic only.
- 20-scale selected direct20 probe defaults to 5 instances; use --scale20-probe-limit 0 only for a skipped diagnostic.
- 10-scale ran selected 5/20 first; full run is deferred.
- 20-scale fail-closed guard uses max_direct_tasks below 20; fail-closed is expected.
- 30-scale diagnostic is expected to fail closed unless an explicit larger exact-pricing limit is selected.
