# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v466_v457_plus_v465_walltime_20260627/gat_branch_action_v466_weighted.pt
resolved_log_file_count = 60
score_row_count = 2255
score_instance_count = 51
solver_score_path = BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/score_map_v466_on_branchonly60_hybrid_diag/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.19886457175016403
score_max = 0.6864581286907196
score_mean = 0.37012181695212015
skipped_counts = {'max_events_per_log_reached': 42}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[16, 17] score=0.686458
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[17, 19] score=0.681979
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[16, 19] score=0.679314
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[13, 16] score=0.678232
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[13, 17] score=0.677344
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[19, 20] score=0.676478
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[12, 19] score=0.665346
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[12, 20] score=0.664278
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[6, 20] score=0.659830
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node=0 depth=0 pair=[6, 19] score=0.656951
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[13, 16] score=0.636428
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[12, 13] score=0.633859

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
