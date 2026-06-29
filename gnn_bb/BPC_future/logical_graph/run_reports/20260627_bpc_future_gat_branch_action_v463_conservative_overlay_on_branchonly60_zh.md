# GAT Branch Action Proof-Risk Overlay

日期：2026-06-27

## 目的

把已完成 branch-score 实验中的整实例正负 evidence 叠加到 score rows：严格收益分支 boost，changed 后仍非最优的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/score_map_v462_on_branchonly60_hybrid_diag/journey_branch_score_rows.json
analysis_paths = ['BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/analysis_v459_conservative_delta_overlay_input.json']
output_dir = BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/score_map_v463_conservative_overlay_on_branchonly60
score_row_count = 2255
positive_overlay_keys = 10
negative_overlay_keys = 34
overlay_counts = {'boost_positive': 8, 'suppress_negative': 26}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- boost_positive: apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:12,20 0.530090->0.740000, gain=253.802, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,20 0.535869->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,16 0.535262->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:4,16 0.533471->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,12 0.539895->0.740000, gain=268.935, OPTIMAL->OPTIMAL
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,4 0.538553->0.740000, gain=269.649, OPTIMAL->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,19 0.534534->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:6,15 0.532760->0.740000, gain=141.240, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:8,14 0.531908->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,4 0.524988->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:2,16 0.538330->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,9 0.533351->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,5 0.532570->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:6,20 0.545326->0.740000, gain=459.734, TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:13,17 0.543169->0.050000, gain=128.610, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:16,17 0.542973->0.050000, gain=-14.688, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:11,15 0.539484->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,9 0.536306->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:4,8 0.534929->0.050000, gain=0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:9,12 0.552168->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,19 0.538647->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:7,19 0.538203->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,16 0.537832->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:12,14 0.541314->0.050000, gain=0.004, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:3,10 0.540031->0.740000, gain=550.376, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:1,12 0.539281->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,4 0.538762->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,10 0.537370->0.740000, gain=258.555, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:11,18 0.538874->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:12,16 0.537960->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:1,2 0.531093->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node:0:depth:0:2,3 0.527742->0.050000, gain=-0.003, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node:0:depth:0:1,14 0.536069->0.050000, gain=-71.333, OPTIMAL->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node:0:depth:0:13,20 0.533219->0.740000, gain=194.759, EXTERNAL_TIME_LIMIT->OPTIMAL

## 边界

输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。
