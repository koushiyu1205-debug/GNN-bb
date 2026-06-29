# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v453_v437_plus_v447_v449_v452_walltime_20260627/gat_branch_action_v453_weighted.pt
resolved_log_file_count = 12
score_row_count = 463
score_instance_count = 12
solver_score_path = BPC_future/results/gat_branch_action_v453_weighted_walltime_20260627/score_map_v453_v438logs_hybrid_diag/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.3949973791837692
score_max = 0.5816259384155273
score_mean = 0.4864467421180486
skipped_counts = {'max_events_per_log_reached': 11}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 16] score=0.581626
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 16] score=0.577560
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[19, 20] score=0.576319
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[5, 16] score=0.570049
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[18, 20] score=0.567891
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 11] score=0.564935
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node=0 depth=0 pair=[11, 15] score=0.564444
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node=0 depth=0 pair=[13, 15] score=0.563948
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[13, 19] score=0.562633
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node=0 depth=0 pair=[11, 13] score=0.562329
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 9] score=0.561600
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[7, 13] score=0.560774

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
