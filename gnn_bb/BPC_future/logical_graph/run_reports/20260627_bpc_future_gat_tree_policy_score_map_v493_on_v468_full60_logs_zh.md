# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v492_tree_policy_event_dataset_20260627/gat_tree_policy_v492.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v493_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 0.03927913308143616
score_max = 0.5182689428329468
score_mean = 0.3317457394270443
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[3, 14] score=0.518269
- instance=apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=0 depth=0 pair=[1, 17] score=0.516107
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[1, 14] score=0.515920
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[3, 6] score=0.515299
- instance=apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=0 depth=0 pair=[2, 17] score=0.514503
- instance=apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=0 depth=0 pair=[1, 15] score=0.513265
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=1 depth=1 pair=[4, 20] score=0.513222
- instance=apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=0 depth=0 pair=[2, 15] score=0.512401
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 pair=[1, 18] score=0.512307
- instance=apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=1 depth=1 pair=[5, 19] score=0.512037
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 pair=[1, 6] score=0.511956
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=1 depth=1 pair=[1, 15] score=0.511613

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
