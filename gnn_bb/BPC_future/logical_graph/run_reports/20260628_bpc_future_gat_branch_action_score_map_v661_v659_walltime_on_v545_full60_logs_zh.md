# GAT Branch/Action Score Map

日期：2026-06-28

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v658_all_counterfactual_delta_rows_20260628/gat_branch_action_v659_branchcls_seed29.pt
resolved_log_file_count = 60
score_row_count = 18823
score_instance_count = 42
solver_score_path = BPC_future/results/gat_branch_action_v661_v659_walltime_on_v545_full60_logs_20260628/journey_branch_score_rows.json
score_mode = walltime_gain
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
state_key_row_count = 18823
branch_state_count = 515
score_min = 0.4910910427570343
score_max = 0.6993146538734436
score_mean = 0.5000856858298419
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[3, 10] score=0.699315
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[2, 5] score=0.698779
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[2, 8] score=0.697076
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[3, 7] score=0.694256
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[4, 10] score=0.691368
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[4, 7] score=0.690392
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[2, 3] score=0.689358
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[3, 5] score=0.687210
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[3, 8] score=0.684722
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[5, 7] score=0.682725
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node=0 depth=0 state=root pair=[5, 10] score=0.682557
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node=0 depth=0 state=root pair=[5, 13] score=0.676217

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
