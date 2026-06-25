# Journey Branch Holdout Sampling Plan

日期：2026-06-24

该计划只读 benchmark / label / log 文件，生成下一批 holdout-oriented 采样建议；不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## Machine Fields

```text
candidate_context_count = 40
selected_context_count = 12
known_strict_positive_instance_count = 3
known_strict_positive_family_count = 2
candidate_log_top_n = 200
action_counts = {'COLLECT_TOP200_DIAG_LOG': 1, 'COLLECT_LONG_TOP200_DIAG_LOG': 1, 'COLLECT_ROOT_TAIL_TOP200_DIAG_LOG': 1, 'ALREADY_HAS_STRICT_POSITIVE': 3, 'DEFER_NONOPTIMAL_CONTEXT': 6}
official_bound_effect = false
certificate_effect = false
```

## Rows

- action=COLLECT_TOP200_DIAG_LOG, reason=near_threshold_missing_candidate_log, priority=139.76798, wall=287.679798, nodes=7, family=sector-wave, seed=61308, known_positive=False, candidates=0, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json
- action=COLLECT_LONG_TOP200_DIAG_LOG, reason=slow_optimal_missing_candidate_log, priority=123.785261, wall=522.147389, nodes=51, family=sector-wave, seed=61821, known_positive=False, candidates=0, instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json
- action=COLLECT_ROOT_TAIL_TOP200_DIAG_LOG, reason=near_threshold_root_tail_no_branch_candidates, priority=85.397248, wall=213.97248, nodes=1, family=greedy-anchor, seed=61921, known_positive=False, candidates=0, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json
- action=ALREADY_HAS_STRICT_POSITIVE, reason=instance_already_has_strict_positive, priority=49.774582, wall=327.745824, nodes=13, family=greedy-anchor, seed=61001, known_positive=True, candidates=0, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=43.013353, wall=240.133531, nodes=1, family=random-wave, seed=61102, known_positive=False, candidates=0, instance=apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=39.765877, wall=357.658772, nodes=1, family=greedy-anchor, seed=61205, known_positive=False, candidates=0, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json
- action=ALREADY_HAS_STRICT_POSITIVE, reason=instance_already_has_strict_positive, priority=34.370378, wall=253.703779, nodes=5, family=greedy-anchor, seed=61716, known_positive=True, candidates=0, instance=apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=33.425384, wall=555.746155, nodes=13, family=greedy-anchor, seed=61414, known_positive=False, candidates=0, instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json
- action=ALREADY_HAS_STRICT_POSITIVE, reason=instance_already_has_strict_positive, priority=33.016081, wall=220.160814, nodes=7, family=sector-wave, seed=61408, known_positive=True, candidates=0, instance=apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=30.998336, wall=600.016641, nodes=0, family=random-wave, seed=61309, known_positive=False, candidates=0, instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=30.998293, wall=600.017072, nodes=0, family=random-wave, seed=61717, known_positive=False, candidates=0, instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json
- action=DEFER_NONOPTIMAL_CONTEXT, reason=full600_not_optimal, priority=30.998282, wall=600.017177, nodes=0, family=random-wave, seed=61408, known_positive=False, candidates=0, instance=apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json

## 边界

该计划用于减少盲扫；推荐命令仍需实际运行并通过 strict counterfactual delta 才能产生训练正例。
