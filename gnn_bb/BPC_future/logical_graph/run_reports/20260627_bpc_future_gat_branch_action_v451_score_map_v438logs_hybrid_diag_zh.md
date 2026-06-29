# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v450_v437_plus_v447_v449_walltime_20260627/gat_branch_action_v451_weighted.pt
resolved_log_file_count = 12
score_row_count = 463
score_instance_count = 12
solver_score_path = BPC_future/results/gat_branch_action_v451_weighted_v450_walltime_20260627/score_map_v451_v438logs_hybrid_diag/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.28087724149227145
score_max = 0.7282622456550597
score_mean = 0.5459141274733111
skipped_counts = {'max_events_per_log_reached': 11}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[15, 16] score=0.728262
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[12, 15] score=0.725566
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[6, 12] score=0.718539
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[12, 13] score=0.717263
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[4, 15] score=0.714848
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[4, 16] score=0.713958
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[12, 15] score=0.711716
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[13, 15] score=0.710315
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[4, 12] score=0.709946
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 16] score=0.709550
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[13, 16] score=0.704519
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 11] score=0.704182

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
