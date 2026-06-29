# GAT Tree Policy Strict Overlay

日期：2026-06-27

## 目的

把 strict tree-policy replay / controlled replay 标签叠加到 branch score rows。该步骤只读离线日志和标签，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_tree_policy_score_map_v537_v536_controlled_weighted_on_v468_full60_logs_20260627/journey_branch_score_rows.json
event_rows = ['BPC_future/data/gat_branch_action_sanity/v529_tree_policy_v504_plus_v525_strict_events_20260627/tree_policy_event_rows.jsonl']
output_dir = BPC_future/results/gat_tree_policy_strict_overlay_v540_v537_plus_v529_state_rehydrated_20260627
solver_score_path = BPC_future/results/gat_tree_policy_strict_overlay_v540_v537_plus_v529_state_rehydrated_20260627/journey_branch_score_rows.json
score_row_count = 19931
events_seen = 84
boost_score = 0.91
suppress_score = 0.01
min_positive_gain = 30.0
require_state_for_depth_gt0 = True
overlay_counts = {'appended_overlay_row': 72, 'boost_positive': 31, 'suppress_negative': 53}
production_ready = False
official_bound_effect = False
certificate_effect = False
```

## Touched Rows

- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:0:depth:0:2,5 state=root score=0.0007253460353240371->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:1:depth:1:17,20 state=RF(2,5)=same_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:2:depth:1:17,20 state=RF(2,5)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:3:depth:2:12,18 state=RF(2,5)=same_vehicle;RF(17,20)=same_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:4:depth:2:17,18 state=RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:10:depth:3:16,20 state=RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:11:depth:4:12,18 state=RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle;RF(16,20)=same_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:12:depth:4:12,18 state=RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle;RF(16,20)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:5:depth:2:10,19 state=RF(2,5)=separate_vehicle;RF(17,20)=same_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:6:depth:2:17,18 state=RF(2,5)=separate_vehicle;RF(17,20)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:20:depth:3:1,14 state=RF(2,5)=separate_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:22:depth:4:1,7 state=RF(2,5)=separate_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle;RF(1,14)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:23:depth:5:3,10 state=RF(2,5)=separate_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle;RF(1,14)=separate_vehicle;RF(1,7)=same_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json key=node:26:depth:6:1,16 state=RF(2,5)=separate_vehicle;RF(17,20)=separate_vehicle;RF(17,18)=separate_vehicle;RF(1,14)=separate_vehicle;RF(1,7)=same_vehicle;RF(3,10)=separate_vehicle score=None->0.91 gain=131.481 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:0:depth:0:3,19 state=root score=0.0002543272858019918->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:1:depth:1:4,20 state=RF(3,19)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:3:depth:2:6,20 state=RF(3,19)=same_vehicle;RF(4,20)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:4:depth:2:6,20 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:5:depth:3:5,13 state=RF(3,19)=same_vehicle;RF(4,20)=same_vehicle;RF(6,20)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:7:depth:3:10,20 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:10:depth:4:7,13 state=RF(3,19)=same_vehicle;RF(4,20)=same_vehicle;RF(6,20)=same_vehicle;RF(5,13)=separate_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:11:depth:4:1,16 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle;RF(10,20)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:12:depth:4:4,5 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle;RF(10,20)=separate_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:18:depth:5:4,7 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle;RF(10,20)=separate_vehicle;RF(4,5)=separate_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:19:depth:6:13,16 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle;RF(10,20)=separate_vehicle;RF(4,5)=separate_vehicle;RF(4,7)=same_vehicle score=None->0.91 gain=239.816 label=strong_positive
- boost_positive instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json key=node:22:depth:7:1,9 state=RF(3,19)=same_vehicle;RF(4,20)=separate_vehicle;RF(6,20)=same_vehicle;RF(10,20)=separate_vehicle;RF(4,5)=separate_vehicle;RF(4,7)=same_vehicle;RF(13,16)=separate_vehicle score=None->0.91 gain=239.816 label=strong_positive
- suppress_negative instance=apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json key=node:0:depth:0:4,12 state=root score=3.770552939386107e-05->3.770552939386107e-05 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json key=node:0:depth:0:3,4 state=root score=3.2082519973997137e-10->3.2082519973997137e-10 gain=-0.023 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json key=node:1:depth:1:2,17 state=RF(3,4)=same_vehicle score=None->0.01 gain=-0.023 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json key=node:2:depth:1:2,17 state=RF(3,4)=separate_vehicle score=None->0.01 gain=-0.023 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json key=node:6:depth:2:6,10 state=RF(3,4)=separate_vehicle;RF(2,17)=separate_vehicle score=None->0.01 gain=-0.023 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:4:depth:2:17,18 state=RF(8,13)=same_vehicle;RF(3,7)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:12:depth:4:12,18 state=RF(8,13)=same_vehicle;RF(3,7)=separate_vehicle;RF(17,18)=separate_vehicle;RF(3,5)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:10:depth:4:12,18 state=RF(8,13)=same_vehicle;RF(3,7)=separate_vehicle;RF(17,18)=same_vehicle;RF(3,5)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:5:depth:2:12,18 state=RF(8,13)=separate_vehicle;RF(2,5)=same_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:6:depth:2:17,18 state=RF(8,13)=separate_vehicle;RF(2,5)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:30:depth:4:12,18 state=RF(8,13)=separate_vehicle;RF(2,5)=separate_vehicle;RF(17,18)=same_vehicle;RF(5,7)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:35:depth:5:3,10 state=RF(8,13)=separate_vehicle;RF(2,5)=separate_vehicle;RF(17,18)=separate_vehicle;RF(2,12)=separate_vehicle;RF(5,7)=same_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:37:depth:5:3,10 state=RF(8,13)=separate_vehicle;RF(2,5)=separate_vehicle;RF(17,18)=same_vehicle;RF(5,7)=same_vehicle;RF(1,9)=same_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- suppress_negative instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json key=node:38:depth:5:3,10 state=RF(8,13)=separate_vehicle;RF(2,5)=separate_vehicle;RF(17,18)=same_vehicle;RF(5,7)=same_vehicle;RF(1,9)=separate_vehicle score=None->0.01 gain=-0.022 label=hard_negative
- ... 44 rows omitted

## 使用边界

`journey_branch_score_rows.json` 只影响 Ryan-Foster pair 排序；必须配合 exact pricing closure，不能提供 bound、certificate 或剪枝依据。
带 `branch_state_key` 的 deep rows 应配合 `journey_branch_candidate_score_require_state_key=True` 使用，避免把某个子树中的正例泄漏到其他分支状态。
