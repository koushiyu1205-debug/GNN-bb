# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v508_tree_policy_priority_neutral_dataset_20260627/gat_tree_policy_v509_priority_neutral.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v510_priority_neutral_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 0.0008604127215221524
score_max = 0.9235090613365173
score_mean = 0.3274689296932308
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[17, 19] score=0.923509
- instance=apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json node=2 depth=1 pair=[19, 20] score=0.907355
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[13, 16] score=0.903988
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[11, 19] score=0.900972
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=21 depth=5 pair=[18, 20] score=0.895547
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[10, 19] score=0.894033
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[13, 14] score=0.893278
- instance=apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json node=2 depth=1 pair=[14, 20] score=0.891691
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=21 depth=5 pair=[16, 19] score=0.888102
- instance=apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json node=2 depth=1 pair=[13, 20] score=0.887093
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=7 depth=3 pair=[10, 17] score=0.882724
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=14 depth=4 pair=[16, 19] score=0.881740

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
