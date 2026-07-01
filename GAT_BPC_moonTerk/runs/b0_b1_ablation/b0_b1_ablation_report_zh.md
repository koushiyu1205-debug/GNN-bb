# B0/B1 proof-safe 消融报告

## 完成范围

- B0 accepted evidence: 5-scale full、10-scale selected direct-DP、20-scale selected direct20 probe。
- B1 accepted: 5-scale proof-safe root closure。
- B1 not yet accepted: 10/20 root closure；当前 selected 10 与 selected direct20 仍由 row timeout fail-closed。
- B2 entry purpose: target 10-scale B1 timeout / pricing-tail / addability / final judge cost，不声称 B1 已在 10/20 完成。
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
- 20-scale selected direct20 probe modes: B0_pure_direct_dp, B1A_full_universe_root_audit, B1B_seeded_root_CG。
- 30-scale fail-closed diagnostic: 20 instances。
- 20-scale fail-closed guard 中的 B0 optimal=0 是预期行为；该组不测试 direct20 能力，只测试 task_count > max_direct_tasks 时是否 fail-closed。

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
| 5 | 5-scale full | B0_pure_direct_dp | 20 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0.005092 | 0.006737 | 0.0 | 0.0 |
| 5 | 5-scale full | B1A_full_universe_root_audit | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0.193752 | 0.262727 | 0.0 | 1.0 |
| 5 | 5-scale full | B1B_seeded_root_CG | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0.270378 | 0.378473 | 20.05 | 3.25 |
| 10 | 10-scale selected5 | B0_pure_direct_dp | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0.086853 | 0.116999 | 0.0 | 0.0 |
| 10 | 10-scale selected5 | B1A_full_universe_root_audit | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 30.002423 | 30.002542 | 0.0 | 0.0 |
| 10 | 10-scale selected5 | B1B_seeded_root_CG | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 30.008418 | 30.01604 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.000895 | 0.0012 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B1A_full_universe_root_audit | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.000905 | 0.000968 | 0.0 | 0.0 |
| 20 | 20-scale fail-closed guard | B1B_seeded_root_CG | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.000877 | 0.001134 | 0.0 | 0.0 |
| 20 | 20-scale selected direct20 probe | B0_pure_direct_dp | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 6.419588 | 6.419588 | 0.0 | 0.0 |
| 20 | 20-scale selected direct20 probe | B1A_full_universe_root_audit | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 61.525156 | 61.525156 | 0.0 | 0.0 |
| 20 | 20-scale selected direct20 probe | B1B_seeded_root_CG | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 60.007804 | 60.007804 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B0_pure_direct_dp | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.001943 | 0.002438 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B1A_full_universe_root_audit | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.001931 | 0.002261 | 0.0 | 0.0 |
| 30 | 30-scale fail-closed diagnostic | B1B_seeded_root_CG | 20 | 0 | 0 | 20 | 0 | 0 | 0 | 0 | 0.003112 | 0.002794 | 0.0 | 0.0 |

## 20-scale direct20 对照

- `lunar_ice_sp50_020_004_seed829004` B0 direct-DP: DIRECT_DP_BASELINE_OPTIMAL / DIRECT_DP_FIXED_GRAPH_OPTIMAL，wall=6.419588s。
- `lunar_ice_sp50_020_004_seed829004` B1A full-universe root audit: BPC_INCOMPLETE_PRICING / FEASIBLE_INCUMBENT_ONLY，wall=61.525156s，reason=row_time_limit_sec=60.0 exceeded at max_direct_tasks=20。
- `lunar_ice_sp50_020_004_seed829004` B1B seeded-CG: BPC_INCOMPLETE_PRICING / FEASIBLE_INCUMBENT_ONLY，wall=60.007804s，reason=row_time_limit_sec=60.0 exceeded at max_direct_tasks=20。
- 结论：同一 selected direct20 instance 上 direct-DP integer oracle 能闭合；当前瓶颈是 B1 root pricing closure / final judge 成本。

## B1B seeded-CG 说明

- B1B rows: 66; added_column_count > 0 rows: 20; added_column_count = 0 rows: 46。
- 0-add 且一轮闭合 rows: 0，解释为 seed pool 已足够或 root already closed。
- 0-add 且 task_count 超过 max_direct_tasks rows: 40，解释为 fail-closed guard。
- 0-add 且触发行超时 rows: 6，解释为 direct exhaustive pricing 成本过高，本轮不能声称 B1B closure。
- 0-add 且其他未闭合 rows: 0，需查看 fail_closed_reason，不能解释为 B1B CG 成功。

## 备注

- 10-scale ran selected 5/20 first; run full after this gate if wall time is acceptable.
- 20-scale fail-closed guard deliberately sets max_direct_tasks below 20; B0 optimal=0 in that group is an expected skip, not evidence that direct20 B0 fails.
- 20-scale direct20 probe used 1 selected instance(s), modes B0/B1A/B1B, with per-row timeout 60.0s.

## 结论边界

- B0 pure 路径不得产生 true-dual BPC certificate。
- B1A/B1B 只有 true-dual final judge closure、manual RC audit、pricing RC audit、proof debt gate 全通过时，才允许 `BPC_NODE_LP_CERTIFIED`。
- `direct_fixed_graph_root_lp` 只允许作为 diagnostic audit，不允许进入 official BPC bound。
- B1A full-universe 若未来加入 `full_universe_membership_rc_audit`，必须先证明 initial columns 等于 complete fixed pricing universe；否则仍必须走 true-dual final judge。
