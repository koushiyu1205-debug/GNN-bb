# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v457_v453_plus_v456_walltime_20260627/gat_branch_action_v457_weighted.pt
resolved_log_file_count = 12
score_row_count = 463
score_instance_count = 12
solver_score_path = BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/score_map_v457_v455logs_hybrid_diag/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 200
score_min = 0.5255834400653838
score_max = 0.5472497433423995
score_mean = 0.5374576923785406
skipped_counts = {'max_events_per_log_reached': 10}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 20] score=0.547250
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[19, 20] score=0.547150
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[18, 19] score=0.546967
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[7, 19] score=0.546787
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 19] score=0.546707
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[18, 20] score=0.546481
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[17, 19] score=0.546405
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[15, 17] score=0.546210
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[12, 20] score=0.546090
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[6, 20] score=0.546073
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 19] score=0.546071
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[10, 15] score=0.545919

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
