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
solver_score_path = BPC_future/results/gat_branch_action_v608_tree_walltime_20260628/score_map_v608_on_v545_full60_hybrid_top200/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
state_key_row_count = 18823
branch_state_count = 515
score_min = 0.5832910001277923
score_max = 0.9617350161075592
score_mean = 0.8525782756592498
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[13, 20] score=0.961735
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[14, 19] score=0.961710
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[12, 19] score=0.961462
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[13, 19] score=0.961402
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[11, 20] score=0.961175
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[11, 19] score=0.961082
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[9, 19] score=0.960616
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[11, 13] score=0.960551
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[8, 20] score=0.960449
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[6, 18] score=0.960040
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[11, 12] score=0.960017
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node=88 depth=8 state=RF(3,5)=separate_vehicle;RF(3,9)=separate_vehicle;RF(4,5)=separate_vehicle;RF(2,12)=separate_vehicle;RF(4,11)=separate_vehicle;RF(5,8)=separate_vehicle;RF(5,11)=same_vehicle;RF(4,7)=separate_vehicle pair=[8, 15] score=0.959880

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
