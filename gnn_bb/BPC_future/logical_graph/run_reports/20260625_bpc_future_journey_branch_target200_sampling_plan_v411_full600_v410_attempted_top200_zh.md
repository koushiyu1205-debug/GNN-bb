# Journey Branch Target-200 Sampling Plan

日期：2026-06-25

## 目的

按 V244 readiness 缺口为 branch/action GAT 选择下一批 target-200 正例采样 context。该计划只生成命令，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
raw_result_count = 60
all_context_count = 60
actionable_context_count = 5
selected_context_count = 5
target_wall = 200.0
near_wall = 360.0
known_target200_instance_count = 5
known_target200_family_count = 3
known_target200_families = ['greedy-anchor', 'random-wave', 'sector-wave']
known_target200_terrain_count = 2
attempted_context_count = 5
max_attempted_probe_entries_per_instance = 8
all_action_counts = {'COLLECT_LONG_TOP200_DIAG_LOG': 1, 'COLLECT_TOP200_DIAG_LOG': 4, 'DEFER_HARD_TIMEOUT_CONTEXT': 30, 'SKIP_ALREADY_WITHIN_TARGET': 20, 'SKIP_KNOWN_TARGET200_INSTANCE': 5}
selected_action_counts = {'COLLECT_LONG_TOP200_DIAG_LOG': 1, 'COLLECT_TOP200_DIAG_LOG': 4}
selected_family_counts = {'greedy-anchor': 2, 'random-wave': 1, 'sector-wave': 2}
commands_path = BPC_future/results/journey_branch_target200_sampling_plan_v411_full600_v410_attempted_top200_20260625/commands.sh
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
```

## 推荐 context

- action=COLLECT_TOP200_DIAG_LOG, reason=near_target_nonoptimal_missing_candidate_log, priority=174.966617, family=random-wave, terrain=apollo15_20km, seed=61102, status=TIME_LIMIT, wall=240.133531, nodes=1, candidate_events=0, branch_events=0, instance=apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json
- action=COLLECT_TOP200_DIAG_LOG, reason=near_target_optimal_missing_candidate_log, priority=171.50688, family=greedy-anchor, terrain=apollo15_20km, seed=61921, status=OPTIMAL, wall=213.97248, nodes=1, candidate_events=0, branch_events=0, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json
- action=COLLECT_TOP200_DIAG_LOG, reason=near_target_optimal_missing_candidate_log, priority=160.08005, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61308, status=OPTIMAL, wall=287.679798, nodes=7, candidate_events=0, branch_events=0, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
- action=COLLECT_TOP200_DIAG_LOG, reason=near_target_nonoptimal_missing_candidate_log, priority=125.585307, family=greedy-anchor, terrain=apollo15_20km, seed=61205, status=TIME_LIMIT, wall=357.658772, nodes=1, candidate_events=0, branch_events=0, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
- action=COLLECT_LONG_TOP200_DIAG_LOG, reason=slow_optimal_missing_candidate_log, priority=95.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61821, status=OPTIMAL, wall=522.147389, nodes=51, candidate_events=0, branch_events=0, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json

## 边界

推荐 context 只是采样入口；只有后续 child-probe / full replay / counterfactual delta 闭环后，才能产生 target-200 positive 或 hard negative 训练标签。
`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有 top200 日志没有 branch event，该实例不应继续占用 branch-pair 采样预算。
