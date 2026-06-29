# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v488_tree_policy_event_dataset_20260627/gat_tree_policy_v488.pt
resolved_log_file_count = 6
score_row_count = 392
score_instance_count = 5
solver_score_path = BPC_future/results/gat_tree_policy_v488_score_map_on_v485_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 20
score_min = 0.2452465146780014
score_max = 0.5109182000160217
score_mean = 0.4314830667358272
skipped_counts = {'candidate_rank_above_cap': 309, 'max_events_per_log_reached': 5}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[2, 10] score=0.510918
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[2, 19] score=0.509614
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[2, 9] score=0.508404
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[2, 20] score=0.508040
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[2, 13] score=0.507494
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[3, 10] score=0.507333
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[3, 11] score=0.504737
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[10, 20] score=0.499601
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[10, 19] score=0.499304
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[11, 20] score=0.498829
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[9, 11] score=0.497142
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node=0 depth=0 pair=[10, 13] score=0.496911

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
