# GAT Branch/Action Score Map

日期：2026-06-28

## 目的

用已训练的 branch/action GAT checkpoint 对既有 `journey_branch_candidates` 日志离线打分，导出 solver 可 opt-in 读取的 branch score rows。

## 机器字段

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v612_v607_plus_v610_failure_hardneg_20260628/gat_branch_action_v612.pt
resolved_log_file_count = 60
score_row_count = 18823
score_instance_count = 42
solver_score_path = BPC_future/results/gat_branch_action_v612_v607_plus_v610_failure_hardneg_20260628/score_map_v612_on_v545_full60_hybrid_top200/journey_branch_score_rows.json
score_mode = hybrid
has_walltime_regression_head = True
has_tree_policy_head = True
max_candidates_per_event = 200
state_key_row_count = 18823
branch_state_count = 515
score_min = 0.8656017482280731
score_max = 0.9276563346385955
score_mean = 0.8895343156652674
skipped_counts = {}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
pricing_oracle = False
branching_oracle = False
production_ready = False
```

## Top Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[13, 19] score=0.927656
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[5, 19] score=0.927355
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[13, 14] score=0.927275
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=34 depth=3 state=RF(5,9)=separate_vehicle;RF(4,6)=separate_vehicle;RF(2,5)=separate_vehicle pair=[18, 19] score=0.927250
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[5, 12] score=0.927236
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=34 depth=3 state=RF(5,9)=separate_vehicle;RF(4,6)=separate_vehicle;RF(2,5)=separate_vehicle pair=[16, 20] score=0.927188
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[13, 15] score=0.927160
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[10, 19] score=0.927085
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[1, 19] score=0.927003
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[13, 16] score=0.926982
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node=34 depth=3 state=RF(5,9)=separate_vehicle;RF(4,6)=separate_vehicle;RF(2,5)=separate_vehicle pair=[16, 19] score=0.926947
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node=12 depth=4 state=RF(1,4)=separate_vehicle;RF(1,20)=separate_vehicle;RF(1,3)=separate_vehicle;RF(3,4)=separate_vehicle pair=[13, 20] score=0.926852

## 使用边界

`solver_score_path` 应作为 `journey_branch_candidate_score_path` 使用；不要使用无上下文聚合 map 作为生产配置。
这些分数只改变 opt-in 的 Ryan-Foster pair 排序；所有下界、剪枝和 OPTIMAL 证书仍由 exact pricing / BPC 逻辑产生。
