# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v518_tree_policy_top200_rankneutral_dataset_20260627/gat_tree_policy_v519_top200_rankneutral.pt
resolved_log_file_count = 60
score_row_count = 11135
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_v520_top200_rankneutral_score_map_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
score_min = 2.0723227578400838e-07
score_max = 0.09696654975414276
score_mean = 0.009647231379760042
skipped_counts = {'max_events_per_log_reached': 17}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 pair=[16, 17] score=0.096967
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=1 depth=1 pair=[17, 18] score=0.089072
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json node=0 depth=0 pair=[17, 20] score=0.085437
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json node=0 depth=0 pair=[17, 18] score=0.082374
- instance=apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json node=1 depth=1 pair=[18, 20] score=0.080814
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=1 depth=1 pair=[15, 17] score=0.077122
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=3 depth=2 pair=[15, 17] score=0.072970
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 pair=[13, 16] score=0.071388
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 pair=[16, 18] score=0.068250
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=2 depth=1 pair=[17, 19] score=0.066666
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json node=1 depth=1 pair=[17, 20] score=0.066296
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json node=0 depth=0 pair=[18, 19] score=0.060651

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
