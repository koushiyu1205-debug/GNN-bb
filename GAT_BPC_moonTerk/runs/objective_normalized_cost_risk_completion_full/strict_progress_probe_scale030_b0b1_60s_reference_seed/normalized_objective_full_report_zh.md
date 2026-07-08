# 归一化成本-风险-完成时间目标 B0-B3 全量实验总报告

## 目标函数边界

- official objective: `normalized_operating_cost + normalized_risk + 0.4 * normalized_weighted_completion_time`。
- 所有 normalization references 均按 instance 写入 `objective_*` 字段。
- `solution_normalized_objective` / `solution_official_objective` 是本轮 official objective。
- `solution_raw_objective_unscaled_weighted_sum` 只用于尺度诊断，不参与 reduced cost 或证书判定。
- makespan 只作为 `solution_raw_makespan` / `solution_normalized_makespan_metric` 报告指标，不进入 pricing objective。

## 完成度边界

- 5/10/20-scale official objective/certificate 结果来自 distance-corrected full runs；30-scale candidate-pruning 优化后已做 5-scale B0 objective spot-check，目标值保持一致。
- 代码当前已修复 path-option dominance：distance 现在参与支配判断；若某个 scale/family 尚未在该修复后重跑，以 `completion_audit_zh.md` 的刷新边界为准。
- 20-scale B2/B3 的 diagnostic frontier rows 是实际 solver run 的诊断结果；它们不构成 official certificate，也不应解释为 B3B tree optimality gap。
- 20-scale 已补跑的 B1A/B2A/B3A full-universe active-RMP rows 会在 dense tableau memory precheck 超限时 fail-closed；这不是证书，而是避免重复触发 MemoryError 的安全边界。
- 30-scale rows 是 resource-guard fail-closed rows，不是实际跑满 3600s 的 solver rows，也不是 30-scale exact solve。
- 30-scale rows 的 `solution_*` 字段来自可行上界 incumbent，用于记录 objective 分解；它不表示对应 B0/B1/B2/B3 mode 已证明 optimal。
- 严格完成度审计见 `completion_audit_zh.md`。

## 覆盖汇总

| scale | family | rows | instances | solved/certified scopes | fail-closed rows | missing solution objective |
|---:|---|---:|---:|---|---:|---:|
| 5 | b0b1 | 0 | 0 | missing | 0 | 0 |
| 5 | b2 | 0 | 0 | missing | 0 | 0 |
| 5 | b3 | 0 | 0 | missing | 0 | 0 |
| 10 | b0b1 | 0 | 0 | missing | 0 | 0 |
| 10 | b2 | 0 | 0 | missing | 0 | 0 |
| 10 | b3 | 0 | 0 | missing | 0 | 0 |
| 20 | b0b1 | 0 | 0 | missing | 0 | 0 |
| 20 | b2 | 0 | 0 | missing | 0 | 0 |
| 20 | b3 | 0 | 0 | missing | 0 | 0 |
| 30 | b0b1 | 3 | 1 | FEASIBLE_INCUMBENT_ONLY:3 | 3 | 2 |
| 30 | b2 | 0 | 0 | missing | 0 | 0 |
| 30 | b3 | 0 | 0 | missing | 0 | 0 |

## 逐模式证书与耗时汇总

| scale | family | mode | rows | mean wall time (s) | certificate scopes | missing solution objective |
|---:|---|---|---:|---:|---|---:|
| 30 | b0b1 | `B0_pure_direct_dp` | 1 | 50.1177 | FEASIBLE_INCUMBENT_ONLY:1 | 1 |
| 30 | b0b1 | `B1A_full_universe_root_audit` | 1 | 0 | FEASIBLE_INCUMBENT_ONLY:1 | 0 |
| 30 | b0b1 | `B1B_seeded_root_CG` | 1 | 60.0001 | FEASIBLE_INCUMBENT_ONLY:1 | 1 |

## B0 与 B3B 对齐

| scale | compared instances | max abs(B3 global UB - B0 objective) | B3B tree optimal rows |
|---:|---:|---:|---:|
| 5 | 0 |  | 0/0 |
| 10 | 0 |  | 0/0 |
| 20 | 0 |  | 0/0 |
| 30 | 0 |  | 0/0 |

## 30-scale 说明

- 30-scale rows 是 fail-closed resource-guard rows，不表示 B0/BPC 已求得 30-scale 精确解。
- 优化前 300s probe 结果为 `DIRECT_DP_TIME_LIMIT`：在 `sortie_candidate_generation` 阶段超时，尚未进入 `fleet_set_partition`；`generated_sortie_count=417,487,274`，最大 RSS 约 4.7GB。
- 新增 exact-safe candidate pruning 与 30-scale bounded sortie cache 后，60s probe 仍在 `sortie_candidate_generation` 超时，但 `generated_sortie_count` 从同限时优化前的 90,643,490 降到 8,067,440，最大 RSS 约 0.6GB。
- 新增 reference-solution best-path upper bound、time-aware task-visit lower bound、endpoint path lower bound 与 outgoing/start future-tail lower bound 诊断；5/10/20 首实例 direct-DP objective 与无 reference 上界版本一致。30-scale 首实例 20s probe 得到 repaired reference upper bound `1.919465`，direct-DP root pruning bound `0.841965885`，active bound pruning 因下界太弱而关闭，`journey_label_bound_pruned_count=0`；当前仍不足以切掉 early candidate generation。
- B0/B1/B2/B3 runners 已把 row timeout 传入内部 direct-DP；B3B 在 B0 direct-DP 未给出 incumbent 时会先 fail-closed，不再继续枚举 representative universe。
- B3B fail-closed payload 现在会记录 instance `reference_solution` 修复得到的 feasible upper bound，但仍保持 `FEASIBLE_INCUMBENT_ONLY`，不会把 reference incumbent 当作 BPC certificate。30-scale reference incumbent audit 显示 20/20 实例可重建 feasible upper bound，mean objective `1.8890827`。
- Compact fixed-graph MILP 的 HiGHS backend 已在 5/10-scale 首实例与 B0 direct-DP 对齐；Gurobi backend 在本机从 10-scale 起被 size-limited license 拒绝。
- 30-scale 首实例 HiGHS compact 300s 探针已运行：无 warm-start 时没有 feasible incumbent；reference warm-start 后得到 incumbent `objective=1.9146`，lower bound `1.259623395`，gap 约 34.21%，RSS 峰值约 2.48GB。
- 新增可恢复 compact product probe runner；尚未发现 `compact_product_scale030_summary.json`，因此总报告未纳入 compact product row 统计。
- compact MILP 是 fixed-graph product exact oracle，不是 BPC root/tree certificate；30-scale 仍未实际闭合，且未跑 3600s full compact MILP。
- 因此当前 official BPC certificate 结果可用于 5/10/20；30-scale 需要后续设计新的 exact-safe pricing/certificate path，不能只依赖现有 direct universe 枚举。

## Artifact 路径

- index: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/index.json`
- per-family CSV/summary/report: `b0b1_*`, `b2_*`, `b3_*`。
- 30-scale B0 probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_b0_direct_dp_probe_300s_zh.md`
- 30-scale B0 post-pruning probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_b0_direct_dp_probe_60s_after_candidate_pruning_zh.md`
- 30-scale B0 reference-bound probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_b0_direct_dp_probe_20s_reference_bound_pruning_zh.md`
- 30-scale B3B safe-fail probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_b3b_safe_fail_probe_20s_zh.md`
- 30-scale reference incumbent audit: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale030_reference_incumbent_audit.md`
- 30-scale HiGHS compact probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_highs_compact_probe_300s_zh.md`
- 30-scale resumable compact product rows: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/compact_product_scale030_report_zh.md`
- 30-scale compact bound probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/compact_bound_probe_scale030_300s/compact_product_scale030_report_zh.md`
- 30-scale duration-lower-bound compact probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/compact_duration_lb_probe_scale030_60s/compact_product_scale030_report_zh.md`
- 30-scale tight big-M compact probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/compact_tight_m_probe_scale030_300s/compact_product_scale030_report_zh.md`
- 30-scale bound-gap diagnostic: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_bound_gap_diagnostic_zh.md`
- 30-scale direct bound-pruning threshold probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_direct_bound_pruning_threshold_probe_20s_zh.md`
- 30-scale B0/B1 strict-progress probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/scale30_b0b1_strict_progress_probe_60s_zh.md`
- compact oracle probe: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/gurobi_compact_oracle_probe_zh.md`
- completion audit: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/strict_progress_probe_scale030_b0b1_60s_reference_seed/completion_audit_zh.md`
