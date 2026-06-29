# GAT Branch/Action Score Map

日期：2026-06-26

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v430_randomtw60_branch_replay_20260626/gat_branch_action_v430.pt
resolved_log_file_count = 60
score_row_count = 1581
score_instance_count = 41
solver_score_path = BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map_v421_root_top50_hybrid/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
max_candidates_per_event = 50
score_min = 0.36739524900913234
score_max = 0.7135628640651702
score_mean = 0.5840927210715962
skipped_counts = {'candidate_rank_above_cap': 128, 'max_events_per_log_reached': 39}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 19] score=0.713563
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 4] score=0.710179
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 4] score=0.709966
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 6] score=0.709954
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 19] score=0.709811
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[1, 6] score=0.707990
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[5, 12] score=0.701567
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 10] score=0.701384
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[10, 19] score=0.701060
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[3, 11] score=0.700750
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[2, 15] score=0.700521
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=0 depth=0 pair=[11, 19] score=0.698629

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
