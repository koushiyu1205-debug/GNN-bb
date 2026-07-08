# B0/B1 proof-safe 消融报告

## 完成范围

- B0 accepted evidence: 5-scale full、10-scale selected direct-DP、20-scale selected direct20 probe。
- B1 accepted: 5-scale proof-safe root closure。
- B1 not yet accepted: 10/20 root closure；当前 selected 10 与 selected direct20 仍由 row timeout fail-closed。
- B2 entry purpose: target 10-scale B1 timeout / pricing-tail / addability / final judge cost，不声称 B1 已在 10/20 完成。
- B2/B3/B4/B5 文件若存在，仅视为 scaffold / preliminary module，不纳入当前完成状态。
- 本报告不启用 harvesting、GAT、cuts 或 full branch tree。

## Objective Boundary

- Official objective: `1.0 * normalized_operating_cost + 1.0 * normalized_risk + 0.4 * normalized_weighted_completion_time`。
- `makespan` 只作为 report/evaluation metric，不进入 pricing objective 或 reduced cost。
- CSV 中 `objective_*` 为 per-instance reference；`solution_*` 为 incumbent/direct-DP 解的 raw/normalized 分解。
- `solution_normalized_objective`/`solution_official_objective` 是本轮 official objective；`solution_raw_objective_unscaled_weighted_sum` 只用于尺度诊断，不参与 reduced cost 或证书判定。

## 产物

- CSV rows: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s/b0b1_scale030_rows.csv`
- JSON summary: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s/b0b1_scale030_summary.json`

## 矩阵

- max_workers: 1。
- 5-scale full: 0 instances。
- 10-scale: 0/0 instances。
- 10-scale row timeout: None 秒。
- 20-scale fail-closed guard: 0 instances。
- 20-scale selected direct20 probe: 0 instances。
- 20-scale selected direct20 probe modes: 。
- 30-scale fail-closed diagnostic: 0 instances。
- 20-scale fail-closed guard 中的 B0 optimal=0 是预期行为；该组不测试 direct20 能力，只测试 task_count > max_direct_tasks 时是否 fail-closed。

## 红线

| metric | value | required |
| --- | ---: | ---: |
| root_bound_gt_B0_violation_count | 0 | 0 |
| direct_root_official_leak_count | 0 | 0 |
| manual_rc_fail_count | 1 | 0 |
| pricing_rc_fail_count | 1 | 0 |

## 汇总

| scale | group | mode | runs | B0 optimal | BPC node LP | fail-closed | bound>B0 | manual RC fail | pricing RC fail | direct-root leak | mean wall | p90 wall | mean added | mean rounds |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 30-scale full normalized objective | B0_pure_direct_dp | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 50.111255 | 50.111255 | 0.0 | 0.0 |
| 30 | 30-scale full normalized objective | B1A_full_universe_root_audit | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 30 | 30-scale full normalized objective | B1B_seeded_root_CG | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 50.120424 | 50.120424 | 0.0 | 1.0 |

## B1B seeded-CG 说明

- B1B rows: 1; added_column_count > 0 rows: 0; added_column_count = 0 rows: 1。
- 0-add 且一轮闭合 rows: 0，解释为 seed pool 已足够或 root already closed。
- 0-add 且 task_count 超过 max_direct_tasks rows: 0，解释为 fail-closed guard。
- 0-add 且触发行超时 rows: 0，解释为 direct exhaustive pricing 成本过高，本轮不能声称 B1B closure。
- 0-add 且其他未闭合 rows: 1，需查看 fail_closed_reason，不能解释为 B1B CG 成功。

## 结论边界

- B0 pure 路径不得产生 true-dual BPC certificate。
- B1A/B1B 只有 true-dual final judge closure、manual RC audit、pricing RC audit、proof debt gate 全通过时，才允许 `BPC_NODE_LP_CERTIFIED`。
- `direct_fixed_graph_root_lp` 只允许作为 diagnostic audit，不允许进入 official BPC bound。
- B1A full-universe 若未来加入 `full_universe_membership_rc_audit`，必须先证明 initial columns 等于 complete fixed pricing universe；否则仍必须走 true-dual final judge。
