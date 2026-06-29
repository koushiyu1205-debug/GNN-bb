# GAT Branch/Action Score Map

日期：2026-06-28

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v607_tree_policy_walltime_v534_plus_v562_20260628/gat_branch_action_v608_tree_walltime.pt
resolved_log_file_count = 60
score_row_count = 18823
score_instance_count = 42
solver_score_path = BPC_future/results/gat_branch_action_v608_tree_walltime_20260628/score_map_v608_on_v545_full60_treepolicy_top200/journey_branch_score_rows.json
score_mode = tree_policy
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
state_key_row_count = 18823
branch_state_count = 515
score_min = 0.0013918423792347312
score_max = 0.0393509678542614
score_mean = 0.015131261571471166
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[3, 8] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[4, 7] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[4, 10] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[4, 15] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[4, 16] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[4, 19] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[6, 10] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[6, 15] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[6, 16] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[7, 8] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[8, 11] score=0.039351
- instance=apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json node=1 depth=1 state=RF(3,7)=same_vehicle pair=[8, 12] score=0.039351

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
