# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v505_tree_policy_rehydrated_top_dataset_20260627/gat_tree_policy_v506_rehydrated_top.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v507_rehydrated_top_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 0.0
score_max = 0.41730839014053345
score_mean = 0.010689869808955733
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[12, 17] score=0.417308
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[15, 16] score=0.417265
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[17, 18] score=0.417122
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[11, 15] score=0.417119
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[12, 18] score=0.416469
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[13, 18] score=0.416393
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[6, 13] score=0.416337
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[14, 18] score=0.416302
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[2, 15] score=0.416190
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[3, 11] score=0.416152
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node=0 depth=0 pair=[14, 19] score=0.416140
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[3, 12] score=0.415949

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
