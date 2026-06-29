# GAT Tree Policy Strict Overlay

日期：2026-06-27

## 目的

把 strict tree-policy replay / controlled replay 标签叠加到 branch score rows。该步骤只读离线日志和标签，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_tree_policy_score_map_v537_v536_controlled_weighted_on_v468_full60_logs_20260627/journey_branch_score_rows.json
event_rows = ['BPC_future/data/gat_branch_action_sanity/v529_tree_policy_v504_plus_v525_strict_events_20260627/tree_policy_event_rows.jsonl']
output_dir = BPC_future/results/gat_tree_policy_strict_overlay_v538_v537_plus_v529_20260627
solver_score_path = BPC_future/results/gat_tree_policy_strict_overlay_v538_v537_plus_v529_20260627/journey_branch_score_rows.json
score_row_count = 19862
events_seen = 84
boost_score = 0.91
suppress_score = 0.01
min_positive_gain = 30.0
require_state_for_depth_gt0 = True
overlay_counts = {'appended_overlay_row': 3, 'boost_positive': 5, 'skipped_missing_state_for_deep_event': 70, 'suppress_negative': 9}
production_ready = False
official_bound_effect = False
certificate_effect = False
```

## Touched Rows

- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:0:depth:0:2,5 state=root score=0.0007253460353240371->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:0:depth:0:3,19 state=root score=0.0002543272858019918->0.91 gain=239.816 label=strong_positive
- suppress_negative instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json key=node:0:depth:0:4,12 state=root score=3.770552939386107e-05->3.770552939386107e-05 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json key=node:0:depth:0:3,4 state=root score=3.2082519973997137e-10->3.2082519973997137e-10 gain=-0.023 label=hard_negative
- suppress_negative instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json key=node:0:depth:0:1,10 state=root score=2.5995952455559745e-05->2.5995952455559745e-05 gain=-0.018 label=hard_negative
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:0:depth:0:5,19 state=root score=0.0007412786944769323->0.91 gain=46.502 label=strong_positive
- suppress_negative instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json key=node:0:depth:0:2,10 state=root score=0.0002264434442622587->0.0002264434442622587 gain=-0.019 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json key=node:0:depth:0:1,20 state=root score=0.00022158237698022276->0.00022158237698022276 gain=-0.021 label=hard_negative
- suppress_negative instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json key=node:0:depth:0:1,20 state=root score=3.1981413485482335e-05->3.1981413485482335e-05 gain=0.000 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:0:depth:0:8,16 state=root score=0.00036831441684626043->0.00036831441684626043 gain=-46.502 label=hard_negative
- suppress_negative instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json key=node:0:depth:0:2,19 state=root score=0.00041263876482844353->0.00041263876482844353 gain=0.000 label=hard_negative
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:1:depth:1:8,12 state=RF(5,19)=same_vehicle score=None->0.91 gain=90.515 label=controlled_replay_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:1:depth:1:12,13 state=RF(5,19)=same_vehicle score=None->0.91 gain=98.546 label=controlled_replay_positive
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:1:depth:1:2,5 state=RF(5,19)=same_vehicle score=None->0.01 gain=-0.010 label=controlled_replay_hard_negative

## 使用边界

`journey_branch_score_rows.json` 只影响 Ryan-Foster pair 排序；必须配合 exact pricing closure，不能提供 bound、certificate 或剪枝依据。
带 `branch_state_key` 的 deep rows 应配合 `journey_branch_candidate_score_require_state_key=True` 使用，避免把某个子树中的正例泄漏到其他分支状态。
