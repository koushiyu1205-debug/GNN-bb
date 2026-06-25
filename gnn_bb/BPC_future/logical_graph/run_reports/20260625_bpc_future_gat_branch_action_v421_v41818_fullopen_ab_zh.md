# GAT Branch Action V421 Full-open A/B

日期：2026-06-25

## 结论

- V421 GAT branch/action 模型能影响真实 20 规模求解路径；full-open 在 18 个 V418 覆盖实例中让 2 个从 baseline 600 秒超时变成 OPTIMAL。
- full-open 没有达到 20 规模 200 秒目标：`<=200s OPTIMAL = 0/18`。
- full-open 相比受限版保留了 2 个 OPTIMAL，并且共同 OPTIMAL 的实例上更快：291.71s vs 511.82s，466.14s vs 543.58s。
- 当前模型不是稳定的全局加速器；它提供了可学习信号，但训练数据量和覆盖仍不足。

## 机器字段

```text
baseline_status_counts = {'EXTERNAL_TIME_LIMIT': 18}
baseline_optimal_count = 0
baseline_optimal_under_200_count = 0
baseline_optimal_wall_times = []
limited_status_counts = {'EXTERNAL_TIME_LIMIT': 15, 'OPTIMAL': 2, 'TIME_LIMIT': 1}
limited_optimal_count = 2
limited_optimal_under_200_count = 0
limited_optimal_wall_times = [511.822729, 543.580975]
fullopen_status_counts = {'EXTERNAL_TIME_LIMIT': 16, 'OPTIMAL': 2}
fullopen_optimal_count = 2
fullopen_optimal_under_200_count = 0
fullopen_optimal_wall_times = [291.713493, 466.142748]
fullopen_optimal_gain_count_vs_baseline = 2
limited_optimal_gain_count_vs_baseline = 2
common_limited_fullopen_optimal_count = 2
fullopen_faster_than_limited_common_optimal_count = 2
audit_dir = BPC_future/results/gat_branch_action_v421_v41818_ab_audit_20260625
evaluation_semantics = non_OPTIMAL rows are all unsolved for primary comparison
```

## 逐实例重点

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: baseline=EXTERNAL_TIME_LIMIT 600.01778s, limited=OPTIMAL 511.822729s, fullopen=OPTIMAL 291.713493s
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json`: baseline=EXTERNAL_TIME_LIMIT 600.01681s, limited=OPTIMAL 543.580975s, fullopen=OPTIMAL 466.142748s

## 解释

这轮 full-open 不是通过 GAT 剪枝或给 bound 加速，而是让 GAT 更大范围地决定 Ryan-Foster 分支 pair 排序：`journey_branch_candidate_score_horizon_min_score=0.0`，`journey_branch_candidate_score_horizon_tie_tolerance=1.0`。因此 exact 性仍由原 BPC / exact pricing closure 保证。
从结果看，限制确实压住了部分效果：同一个实例 full-open 从受限版 511.82s 降到 291.71s。但这仍未到 200s，说明下一步重点不是再加 gate，而是扩大严格 full-replay 标签、补全 60-instance candidate-log 覆盖，并训练能在更多 context 上稳定选出好分支的模型。
