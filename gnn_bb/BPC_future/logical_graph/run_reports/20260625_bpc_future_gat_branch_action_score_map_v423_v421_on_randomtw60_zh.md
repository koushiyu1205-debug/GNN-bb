# GAT Branch/Action Score Map

日期：2026-06-25

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v421_v417_plus_v418_failclosed_20260625/gat_branch_action_v421.pt
resolved_log_file_count = 60
score_row_count = 9258
score_instance_count = 39
solver_score_path = BPC_future/results/gat_branch_action_score_map_v423_v421_on_randomtw60_20260625/journey_branch_score_rows.json
score_min = 0.03350634500384331
score_max = 0.9032425880432129
score_mean = 0.3464414033395769
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 16] score=0.903243
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 20] score=0.902253
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[1, 13] score=0.893539
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 16] score=0.887544
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[2, 9] score=0.886893
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 11] score=0.886446
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[16, 20] score=0.885747
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[9, 20] score=0.884523
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[4, 20] score=0.884399
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[5, 11] score=0.883690
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[5, 16] score=0.883353
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=0 depth=0 pair=[4, 18] score=0.882557

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
