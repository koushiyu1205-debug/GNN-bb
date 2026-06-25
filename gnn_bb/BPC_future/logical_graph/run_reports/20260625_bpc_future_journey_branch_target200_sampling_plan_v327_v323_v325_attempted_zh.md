# Journey Branch Target-200 Sampling Plan

日期：2026-06-25

## 目的

按 V244 readiness 缺口为 branch/action GAT 选择下一批 target-200 正例采样 context。该计划只生成命令，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
raw_result_count = 60
all_context_count = 60
actionable_context_count = 11
selected_context_count = 11
target_wall = 200.0
near_wall = 360.0
known_target200_instance_count = 4
known_target200_family_count = 2
known_target200_families = ['greedy-anchor', 'sector-wave']
known_target200_terrain_count = 2
attempted_context_count = 21
all_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 2, 'COLLECT_BRANCH_CANDIDATE_DIAG_LOG': 9, 'ROUTE_TO_ROOT_PRICING_TAIL': 4, 'SKIP_ALREADY_ATTEMPTED_CONTEXT': 21, 'SKIP_ALREADY_WITHIN_TARGET': 20, 'SKIP_KNOWN_TARGET200_INSTANCE': 4}
selected_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 2, 'COLLECT_BRANCH_CANDIDATE_DIAG_LOG': 9}
selected_family_counts = {'greedy-anchor': 7, 'sector-wave': 4}
commands_path = BPC_future/results/journey_branch_target200_sampling_plan_v327_v323_v325_attempted_20260625/commands.sh
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
```

## 推荐 context

- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=greedy-anchor, terrain=apollo15_20km, seed=61410, status=EXTERNAL_TIME_LIMIT, wall=600.017398, nodes=0, candidate_events=2, branch_events=2, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61744, status=EXTERNAL_TIME_LIMIT, wall=600.018373, nodes=0, candidate_events=1, branch_events=1, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61520, status=EXTERNAL_TIME_LIMIT, wall=600.01864, nodes=0, candidate_events=0, branch_events=30, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61718, status=EXTERNAL_TIME_LIMIT, wall=600.019624, nodes=0, candidate_events=0, branch_events=62, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61206, status=EXTERNAL_TIME_LIMIT, wall=600.019706, nodes=0, candidate_events=0, branch_events=20, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=apollo15_20km, seed=61308, status=EXTERNAL_TIME_LIMIT, wall=600.020566, nodes=0, candidate_events=0, branch_events=3, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=apollo15_20km, seed=61614, status=EXTERNAL_TIME_LIMIT, wall=600.020646, nodes=0, candidate_events=0, branch_events=6, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61923, status=EXTERNAL_TIME_LIMIT, wall=600.021381, nodes=0, candidate_events=0, branch_events=14, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=apollo15_20km, seed=61000, status=EXTERNAL_TIME_LIMIT, wall=600.022151, nodes=0, candidate_events=0, branch_events=5, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=sector-wave, terrain=apollo15_20km, seed=61612, status=EXTERNAL_TIME_LIMIT, wall=600.022716, nodes=0, candidate_events=0, branch_events=11, instance=apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=sector-wave, terrain=apollo15_20km, seed=61102, status=EXTERNAL_TIME_LIMIT, wall=600.04953, nodes=0, candidate_events=0, branch_events=3, instance=apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json

## 边界

推荐 context 只是采样入口；只有后续 child-probe / full replay / counterfactual delta 闭环后，才能产生 target-200 positive 或 hard negative 训练标签。
`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有 top200 日志没有 branch event，该实例不应继续占用 branch-pair 采样预算。
