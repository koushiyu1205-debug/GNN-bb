# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v501_tree_policy_context_competitor_dataset_20260627/gat_tree_policy_v502_context_competitor.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v503_context_competitor_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 0.0
score_max = 0.4652724862098694
score_mean = 0.023563592409087303
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node=3 depth=2 pair=[15, 20] score=0.465272
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=13 depth=3 pair=[13, 19] score=0.462288
- instance=apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=1 depth=1 pair=[11, 12] score=0.461922
- instance=apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=1 depth=1 pair=[11, 16] score=0.461220
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node=5 depth=2 pair=[3, 20] score=0.460304
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node=5 depth=2 pair=[6, 20] score=0.459103
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[15, 19] score=0.457779
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[10, 15] score=0.457587
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node=3 depth=2 pair=[5, 13] score=0.457373
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json node=0 depth=0 pair=[12, 13] score=0.456684
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json node=0 depth=0 pair=[4, 12] score=0.456673
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node=4 depth=2 pair=[3, 17] score=0.456052

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
