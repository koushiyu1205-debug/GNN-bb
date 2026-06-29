# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v471_v466_plus_v470_hard_negative_20260627/gat_branch_action_v471_weighted.pt
resolved_log_file_count = 60
score_row_count = 2255
score_instance_count = 51
solver_score_path = BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/score_map_v471_on_branchonly60_hybrid_diag/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.1558355956338346
score_max = 0.9495536506175994
score_mean = 0.3610130761204052
skipped_counts = {'max_events_per_log_reached': 42}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[4, 15] score=0.949554
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 10] score=0.948399
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 11] score=0.947556
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 15] score=0.947114
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 19] score=0.946273
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 19] score=0.944067
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 20] score=0.943876
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 20] score=0.942435
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 15] score=0.942312
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json node=0 depth=0 pair=[4, 18] score=0.941370
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 17] score=0.941179
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[6, 15] score=0.941082

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
