# GAT Branch/Action Score Map

日期：2026-06-26

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626/gat_branch_action_v437.pt
resolved_log_file_count = 12
score_row_count = 6729
score_instance_count = 12
solver_score_path = BPC_future/results/gat_branch_action_v437_randomtw60_20260626/score_map_v437_v436logs_walltime_top200/journey_branch_score_rows.json
score_mode = walltime_gain
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.4962797164916992
score_max = 0.9943912625312805
score_mean = 0.5198067626028009
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[6, 9] score=0.994391
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[6, 12] score=0.993739
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node=0 depth=0 pair=[11, 15] score=0.993594
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[6, 7] score=0.993480
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[2, 6] score=0.993383
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 5] score=0.992991
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 9] score=0.992881
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[6, 8] score=0.992790
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 16] score=0.992663
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[4, 12] score=0.992463
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node=0 depth=0 pair=[11, 12] score=0.992235
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 16] score=0.991223

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
