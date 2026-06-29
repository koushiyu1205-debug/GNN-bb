# GAT Branch/Action Score Map

日期：2026-06-27

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v531_tree_policy_v530_dataset_20260627/gat_tree_policy_v532_v530_plus_v525.pt
resolved_log_file_count = 60
score_row_count = 19859
score_instance_count = 42
solver_score_path = BPC_future/results/gat_tree_policy_score_map_v533_v532_on_v468_full60_logs_20260627/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
state_key_row_count = 1787
branch_state_count = 1
score_min = 3.1941508899652193e-12
score_max = 0.06825084984302521
score_mean = 0.0023579200630508986
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[7, 18] score=0.068251
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[9, 17] score=0.066653
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[11, 18] score=0.066493
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[6, 18] score=0.066183
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json node=0 depth=0 state=root pair=[17, 20] score=0.065527
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[7, 17] score=0.065266
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node=0 depth=0 state=root pair=[3, 14] score=0.064764
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[10, 17] score=0.064639
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json node=0 depth=0 state=root pair=[13, 18] score=0.064254
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[6, 17] score=0.063955
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=1 depth=1 state=None pair=[8, 20] score=0.063565
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json node=0 depth=0 state=root pair=[4, 18] score=0.061306

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
