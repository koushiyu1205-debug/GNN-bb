# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v515_tree_policy_top200_context_competitor_dataset_20260627/gat_tree_policy_v516_top200_context_competitor.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v517_top200_context_competitor_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 3.937479162163804e-11
score_max = 0.07750241458415985
score_mean = 0.0013881786800685274
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[1, 3] score=0.077502
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[1, 6] score=0.074032
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[1, 14] score=0.070782
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[3, 6] score=0.070461
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[3, 14] score=0.066378
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=2 depth=1 pair=[1, 2] score=0.038129
- instance=apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json node=0 depth=0 pair=[2, 5] score=0.036974
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=2 depth=1 pair=[1, 8] score=0.035825
- instance=apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json node=0 depth=0 pair=[5, 13] score=0.035160
- instance=apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json node=0 depth=0 pair=[2, 13] score=0.034853
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=2 depth=1 pair=[1, 10] score=0.034011
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=1 depth=1 pair=[4, 7] score=0.032923

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
