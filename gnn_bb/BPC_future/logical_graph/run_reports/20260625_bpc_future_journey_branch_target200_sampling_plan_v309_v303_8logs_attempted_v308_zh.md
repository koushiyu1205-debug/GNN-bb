# Journey Branch Target-200 Sampling Plan

日期：2026-06-25

## 目的

按 V244 readiness 缺口为 branch/action GAT 选择下一批 target-200 正例采样 context。该计划只生成命令，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
raw_result_count = 60
all_context_count = 60
actionable_context_count = 22
selected_context_count = 12
target_wall = 200.0
near_wall = 360.0
known_target200_instance_count = 3
known_target200_family_count = 2
known_target200_families = ['greedy-anchor', 'sector-wave']
known_target200_terrain_count = 2
attempted_context_count = 11
all_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 7, 'COLLECT_BRANCH_CANDIDATE_DIAG_LOG': 15, 'ROUTE_TO_ROOT_PRICING_TAIL': 4, 'SKIP_ALREADY_ATTEMPTED_CONTEXT': 11, 'SKIP_ALREADY_WITHIN_TARGET': 20, 'SKIP_KNOWN_TARGET200_INSTANCE': 3}
selected_action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 7, 'COLLECT_BRANCH_CANDIDATE_DIAG_LOG': 5}
selected_family_counts = {'greedy-anchor': 8, 'sector-wave': 4}
commands_path = BPC_future/results/journey_branch_target200_sampling_plan_v309_v303_8logs_attempted_v308_20260625/commands.sh
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
```

## 推荐 context

- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=133.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61414, status=TIME_LIMIT, wall=555.746155, nodes=13, candidate_events=4, branch_events=4, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=greedy-anchor, terrain=apollo15_20km, seed=61410, status=EXTERNAL_TIME_LIMIT, wall=600.017398, nodes=0, candidate_events=2, branch_events=2, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61206, status=EXTERNAL_TIME_LIMIT, wall=600.0174, nodes=0, candidate_events=6, branch_events=6, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61311, status=EXTERNAL_TIME_LIMIT, wall=600.01741, nodes=0, candidate_events=16, branch_events=16, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61104, status=EXTERNAL_TIME_LIMIT, wall=600.017583, nodes=0, candidate_events=11, branch_events=11, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=sector-wave, terrain=tranquillitatis_balmer_like_20km, seed=61410, status=EXTERNAL_TIME_LIMIT, wall=600.017678, nodes=0, candidate_events=14, branch_events=14, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json
- action=BUILD_CHILD_PROBE_RUNBOOK, reason=candidate_log_available, priority=110.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61103, status=EXTERNAL_TIME_LIMIT, wall=600.01778, nodes=0, candidate_events=6, branch_events=6, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=apollo15_20km, seed=61103, status=EXTERNAL_TIME_LIMIT, wall=600.017874, nodes=0, candidate_events=0, branch_events=13, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=sector-wave, terrain=apollo15_20km, seed=61000, status=EXTERNAL_TIME_LIMIT, wall=600.017988, nodes=0, candidate_events=0, branch_events=25, instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61635, status=EXTERNAL_TIME_LIMIT, wall=600.018033, nodes=0, candidate_events=0, branch_events=31, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=tranquillitatis_balmer_like_20km, seed=61744, status=EXTERNAL_TIME_LIMIT, wall=600.018373, nodes=0, candidate_events=0, branch_events=8, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json
- action=COLLECT_BRANCH_CANDIDATE_DIAG_LOG, reason=branch_events_without_candidate_log, priority=82.0, family=greedy-anchor, terrain=apollo15_20km, seed=61512, status=EXTERNAL_TIME_LIMIT, wall=600.018607, nodes=0, candidate_events=0, branch_events=6, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json

## 边界

推荐 context 只是采样入口；只有后续 child-probe / full replay / counterfactual delta 闭环后，才能产生 target-200 positive 或 hard negative 训练标签。
`ROUTE_TO_ROOT_PRICING_TAIL` / `ROUTE_TO_PRICING_TAIL` 表示已有 top200 日志没有 branch event，该实例不应继续占用 branch-pair 采样预算。
