# B0/B1 proof-safe 消融报告

## 完成范围

- 当前 accepted baseline layers: B0, B1。
- B2/B3/B4/B5 文件若存在，仅视为 scaffold / preliminary module，不纳入当前完成状态。
- 本报告不启用 harvesting、GAT、cuts 或 full branch tree。

## 产物

- CSV rows: `runs/b0_b1_ablation/b0_b1_ablation_rows.csv`
- JSON summary: `runs/b0_b1_ablation/b0_b1_ablation_summary.json`

## 矩阵

- max_workers: 4。
- 5-scale full: 20 instances。
- 10-scale: 5/20 instances。
- 10-scale row timeout: 30.0 秒。
- 20-scale fail-closed guard: 20 instances。
- 20-scale selected direct20 probe: 1 instances。
- 30-scale fail-closed diagnostic: 20 instances。

## 红线

| metric | value | required |
| --- | ---: | ---: |
| root_bound_gt_B0_violation_count | 0 | 0 |
| direct_root_official_leak_count | 0 | 0 |
| manual_rc_fail_count | 0 | 0 |
| pricing_rc_fail_count | 0 | 0 |

## 汇总

| scale | group | mode | runs | B0 optimal | BPC node LP | fail-closed | bound>B0 | manual RC fail | pricing RC fail | direct-root leak | mean wall | p90 wall | mean added | mean rounds |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0.004994 | 0.006984 | 0.0 | 0.0 |
| 5 | 5-scale full | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0.195587 | 0.276082 | 0.0 | 1.0 |
| 5 | 5-scale full | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0.272076 | 0.372019 | 20.05 | 3.25 |
| 10 | 10-scale selected5 | B0_pure_direct_dp | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0.086574 | 0.114281 | 0.0 | 0.0 |
| 10 | 10-scale selected5 | B1A_full_universe_root_audit | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 30.002423 | 30.002416 | 0.0 | 0.0 |
| 10 | 10-scale selected5 | B1B_seeded_root_CG | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 30.002495 | 30.002621 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.001067 | 0.001431 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B1A_full_universe_root_audit | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.000948 | 0.001137 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B1B_seeded_root_CG | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.000862 | 0.001012 | 0.0 | 0.0 |
| 20 | 20-scale selected direct20 probe | B1A_full_universe_root_audit | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 61.452989 | 61.452989 | 0.0 | 0.0 |
| 20 | 20-scale selected direct20 probe | B1B_seeded_root_CG | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 60.007956 | 60.007956 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.002317 | 0.00327 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B1A_full_universe_root_audit | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.00217 | 0.003104 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B1B_seeded_root_CG | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.002044 | 0.002405 | 0.0 | 0.0 |

## B1B seeded-CG 说明

- B1B rows: 66; added_column_count > 0 rows: 20; added_column_count = 0 rows: 46。
- 0-add 且一轮闭合 rows: 0，解释为 seed pool 已足够或 root already closed。
- 0-add 且 task_count 超过 max_direct_tasks rows: 40，解释为 fail-closed guard。
- 0-add 且触发行超时 rows: 6，解释为 direct exhaustive pricing 成本过高，本轮不能声称 B1B closure。
- 0-add 且其他未闭合 rows: 0，需查看 fail_closed_reason，不能解释为 B1B CG 成功。

## 备注

- 10-scale ran selected 5/20 first; run full after this gate if wall time is acceptable.
- 20-scale direct20 probe used 1 selected instance(s) with per-row timeout 60.0s.

## 结论边界

- B0 pure 路径不得产生 true-dual BPC certificate。
- B1A/B1B 只有 true-dual final judge closure、manual RC audit、pricing RC audit、proof debt gate 全通过时，才允许 `BPC_NODE_LP_CERTIFIED`。
- `direct_fixed_graph_root_lp` 只允许作为 diagnostic audit，不允许进入 official BPC bound。
