# BPC_future 20规模 random-TW 60-instance 全量600秒并行测试

日期：2026-06-24

## 测试口径

- 实例集：`BPC_future/logical_graph/tasks_020` 下全量 60 个 `*_logical_graph.json`
- 配置：`BPC_future/configs/moon_trek_20_smoke.yaml`
- 单实例预算：600 秒
- 并行度：`--max-workers 4`
- 结果 CSV：`BPC_future/results/20260624_full600_randomtw60_tasks20_parallel4.csv`
- 日志目录：`BPC_future/results/run_logs_20260624_full600_randomtw60_tasks20_parallel4`
- solution 目录：`BPC_future/results/solutions_20260624_full600_randomtw60_tasks20_parallel4`

## 总体结果

60 个实例全部完成落盘。

| 指标 | 数值 |
|---|---:|
| OPTIMAL | 26 / 60 |
| OPTIMAL 且 wall <= 200s | 20 / 60 |
| OPTIMAL 但 wall > 200s | 6 / 60 |
| 非最优 | 34 / 60 |
| EXTERNAL_TIME_LIMIT | 30 / 60 |
| 内部 TIME_LIMIT | 4 / 60 |
| 全部实例平均 wall | 381.784s |
| 全部实例 median wall | 577.881s |
| 最优实例平均 wall | 123.382s |
| 最优实例 median wall | 53.782s |
| 最慢最优 wall | 522.147s |

结论：当前版本距离“20规模 random-TW 60-instance 全部 200 秒内最优”差距很大。只有 20/60 达到 200 秒内最优；即使把预算放宽到 600 秒，也只有 26/60 得到 OPTIMAL。

## 分组结果

| 分组 | OPTIMAL | <=200s OPTIMAL | >200s OPTIMAL | EXTERNAL_TIME_LIMIT | TIME_LIMIT |
|---|---:|---:|---:|---:|---:|
| greedy-anchor/apollo15_20km | 2 | 0 | 2 | 6 | 2 |
| greedy-anchor/tranquillitatis_balmer_like_20km | 3 | 2 | 1 | 6 | 1 |
| random-wave/apollo15_20km | 6 | 6 | 0 | 3 | 1 |
| random-wave/tranquillitatis_balmer_like_20km | 5 | 5 | 0 | 5 | 0 |
| sector-wave/apollo15_20km | 6 | 5 | 1 | 4 | 0 |
| sector-wave/tranquillitatis_balmer_like_20km | 4 | 2 | 2 | 6 | 0 |

## 慢最优样本

| instance | wall |
|---|---:|
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json` | 522.147s |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json` | 327.746s |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json` | 287.680s |
| `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json` | 253.704s |
| `apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json` | 220.161s |
| `apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json` | 213.972s |

## 判断

1. 当前性能不是“少数坏 seed”问题。greedy 两组和 sector/tranquillitatis 都有明显长尾。
2. 200 秒目标当前只覆盖 20/60；还差 40 个实例，其中 34 个在 600 秒内都没有证明最优。
3. 放宽到 600 秒只能暴露更多证明长尾，不能让当前版本达到可接受状态。
4. 后续优化应继续以 random-TW 60-instance 为唯一验收口径，重点盯住 `greedy-anchor/*` 和 `sector-wave/tranquillitatis_balmer_like_20km` 的证明失败。

## 后续审计

本轮日志上的 Tail Action Controller 审计得到 `row_count=0`。原因不是 60 个实例没有 A/B/C/D 节点，而是当时 canonical `moon_trek_20_smoke.yaml` 没有打开 corrected-bound / tail-action audit 行，solver 日志中缺少 `journey_corrected_node_bound_audit` 事件。

已补诊断修正：新增并在 canonical 20-task 配置中打开 `journey_tail_action_audit_enabled`。该开关只写 Tail Action Controller 分类日志，不开启 `journey_corrected_node_bound_fathom_enabled`，也不开启 tail-action early branch。

同时 canonical 20-task 配置已打开 `journey_branch_candidate_log_top_n=12`。这只记录 `journey_branch_candidates` top-N 特征，不改变实际 branch priority；下一轮 full600 会同时具备 tail-action 分类和 branch-impact 候选特征。

Late-negative tail 审计仍然有效。150 秒以后解析到：

| 指标 | 数值 |
|---|---:|
| tail_event_count | 999 |
| true_negative_event_count | 947 |
| weak_false_negative_event_count | 52 |
| true_negative_active_support_changing | 59 |
| true_negative_inactive_only | 570 |
| true_negative_no_addition_observed | 318 |

含义：当前 20 规模长尾主要不是“只有 weak/profile 假负列噪声”，而是后段仍有大量 true-RC negative materialization，其中多数是 inactive-only，对当前 LP support 的实际推进很弱。下一轮 benchmark 必须同时采集 tail-action 行、branch-candidate 行和 late-negative 行，才能判断节点应继续 CG、提前分支、调整 branch pair，还是进入 refinement/fallback。
