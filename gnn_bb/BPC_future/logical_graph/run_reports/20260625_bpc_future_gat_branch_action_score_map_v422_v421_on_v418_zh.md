# GAT Branch/Action Score Map

日期：2026-06-25

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v421_v417_plus_v418_failclosed_20260625/gat_branch_action_v421.pt
resolved_log_file_count = 18
score_row_count = 5076
score_instance_count = 18
solver_score_path = BPC_future/results/gat_branch_action_score_map_v422_v421_on_v418_20260625/journey_branch_score_rows.json
score_min = 0.03350634500384331
score_max = 0.8475534915924072
score_mean = 0.3370894494454007
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[6, 15] score=0.847553
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[11, 15] score=0.846272
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[2, 9] score=0.842401
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[7, 9] score=0.839882
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[8, 15] score=0.837299
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[2, 20] score=0.833609
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[14, 18] score=0.833032
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node=2 depth=1 pair=[14, 16] score=0.831669
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node=2 depth=1 pair=[7, 14] score=0.831318
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[4, 15] score=0.829307
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[8, 14] score=0.829297
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node=0 depth=0 pair=[17, 18] score=0.827901

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
