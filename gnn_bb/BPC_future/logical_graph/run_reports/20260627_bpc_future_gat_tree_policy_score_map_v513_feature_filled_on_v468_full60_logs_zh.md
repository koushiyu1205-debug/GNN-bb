# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v511_tree_policy_feature_filled_dataset_20260627/gat_tree_policy_v512_feature_filled.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v513_feature_filled_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 5.4068573263066355e-06
score_max = 0.695824921131134
score_mean = 0.10705135762635298
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node=1 depth=1 pair=[17, 20] score=0.695825
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node=1 depth=1 pair=[16, 20] score=0.688555
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[15, 19] score=0.688023
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[16, 19] score=0.685918
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=2 depth=1 pair=[18, 20] score=0.683770
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=2 depth=1 pair=[17, 20] score=0.677502
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node=6 depth=2 pair=[18, 19] score=0.677018
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=2 depth=1 pair=[16, 19] score=0.669893
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[9, 20] score=0.664584
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[17, 18] score=0.662565
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[14, 18] score=0.662363
- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node=0 depth=0 pair=[15, 16] score=0.658971

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
