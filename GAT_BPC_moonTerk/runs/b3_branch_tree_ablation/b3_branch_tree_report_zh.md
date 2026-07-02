# B3 Branch-and-Price Tree 消融报告

## Artifacts

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/b3_branch_tree_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_branch_tree_ablation/b3_branch_tree_summary.json`

## Superseding 20-scale Closure Sweep

本矩阵中的 `20-scale selected direct20 probe / B3B_seeded_branch_price_tree` 行来自旧实现，当时 B3B 先进入 B2B_R3 tail 并被 `row_time_limit_sec=60` 截断，显示为 0/5。

新的 B3 complete-universe branch RC audit 路径已在 full20 sweep 中验证：

- full20 report: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_full20_sweep/b3_full20_sweep_report_zh.md`
- selected5 report: `/home/kai/work/GAT_BPC_moonTerk/runs/b3_20_tree_closure_probe/b3_20_tree_closure_probe_report_zh.md`
- result: 20-scale full20 B3B `BPC_TREE_OPTIMAL = 20/20`
- max B3 wall time: `123.490706`
- max node count: `7`
- max open / incomplete node count: `0 / 0`
- max `|B3 incumbent - B0 objective|`: `1e-06`, within `TREE_OBJECTIVE_TOLERANCE=5e-06`

因此，下面旧矩阵里的 20-scale B3B timeout 行只保留为历史诊断，不代表当前 B3 实现的 20-scale 闭合能力。

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
| 10 | 10-scale full | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.157817 | 0 | 0 |
| 10 | 10-scale full | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 20 | 0 | 1.1071 | 0 | 0 |
| 10 | 10-scale full | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.155207 | 0 | 0 |
| 10 | 10-scale full | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.002559 | 0 | 0 |
| 10 | 10-scale full | B3B_seeded_branch_price_tree | 20 | 20 | 20 | 0 | 2.247478 | 1 | 0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.020024 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.009116 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.009445 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.008177 | 0 | 0 |
| 20 | 20-scale fail-closed guard | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.009698 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B0_pure_direct_dp | 5 | 0 | 0 | 0 | 10.022164 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2B_R3_true_dual_negative_search_worker | 5 | 0 | 0 | 5 | 44.426126 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B2_PRODUCT_EXACT_SOLVER | 5 | 0 | 0 | 0 | 10.10064 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B3A_full_universe_branch_audit | 5 | 0 | 0 | 5 | 0.014672 | 0 | 0 |
| 20 | 20-scale selected direct20 probe | B3B_seeded_branch_price_tree | 5 | 0 | 0 | 5 | 60.005655 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0.047568 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 0 | 20 | 0.021328 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 20 | 0.020741 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3A_full_universe_branch_audit | 20 | 0 | 0 | 20 | 0.019519 | 0 | 0 |
| 30 | 30-scale fail-closed diagnostic | B3B_seeded_branch_price_tree | 20 | 0 | 0 | 20 | 0.022189 | 0 | 0 |
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 0 | 0 | 0 | 0.00581 | 0 | 0 |
| 5 | 5-scale full | B2B_R3_true_dual_negative_search_worker | 20 | 0 | 20 | 0 | 0.312911 | 0 | 0 |
| 5 | 5-scale full | B2_PRODUCT_EXACT_SOLVER | 20 | 0 | 0 | 0 | 0.005837 | 0 | 0 |
| 5 | 5-scale full | B3A_full_universe_branch_audit | 20 | 0 | 20 | 0 | 0.203863 | 1 | 0 |
| 5 | 5-scale full | B3B_seeded_branch_price_tree | 20 | 20 | 20 | 0 | 0.6282 | 1 | 0 |

## B3 Accepted?

- B3B accepted: True.
- 5-scale full B3B BPC_TREE_OPTIMAL: 20/20.
- 10-scale selected no-regression vs B2B_R3: True (regressions=0, runs=20).
- 20-scale selected direct20 clean diagnostics: True (unique instances=5).
- Can enter B4: True.

## Notes

- B3 runner is serial by default to avoid concurrent branch/final-judge memory spikes.
- B3B uses B2B_R3 node pricing; B3A full-universe branch audit is diagnostic only.
- 20-scale selected direct20 probe defaults to 5 instances; use --scale20-probe-limit 0 only for a skipped diagnostic.
- 20-scale fail-closed guard uses max_direct_tasks below 20; fail-closed is expected.
- 20-scale selected direct20 probe used 5 instance(s).
- 30-scale diagnostic is expected to fail closed unless an explicit larger exact-pricing limit is selected.
