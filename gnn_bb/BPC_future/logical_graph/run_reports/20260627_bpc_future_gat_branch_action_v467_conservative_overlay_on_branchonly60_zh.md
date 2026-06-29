# GAT Branch Action Proof-Risk Overlay

日期：2026-06-27

## 目的

把已完成 branch-score 实验中的整实例正负 evidence 叠加到 score rows：严格收益分支 boost，changed 后仍非最优的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/score_map_v466_on_branchonly60_hybrid_diag/journey_branch_score_rows.json
analysis_paths = ['BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/analysis_v459_conservative_delta_overlay_input.json', 'BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/analysis_v467_v465_overlay_input.json']
output_dir = BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/score_map_v467_conservative_overlay_on_branchonly60
score_row_count = 2255
positive_overlay_keys = 12
negative_overlay_keys = 78
overlay_counts = {'boost_positive': 10, 'suppress_negative': 62}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- boost_positive: apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:12,20 0.311972->0.740000, gain=253.802, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,16 0.393832->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:13,15 0.369644->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:14,18 0.360470->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:4,16 0.351499->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,20 0.339333->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:2,5 0.290661->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json node:0:depth:0:5,16 0.221534->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json node:0:depth:0:5,11 0.209608->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,16 0.552519->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,15 0.548646->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,17 0.544071->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:1,7 0.526530->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:12,16 0.419369->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:7,12 0.398131->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:1,8 0.380570->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:1,4 0.376666->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:9,10 0.314169->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:4,19 0.300038->0.740000, gain=257.123, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:1,6 0.289546->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,4 0.604338->0.740000, gain=269.649, OPTIMAL->OPTIMAL
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,12 0.596395->0.740000, gain=268.935, OPTIMAL->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,19 0.271374->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:8,14 0.259148->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:6,15 0.254560->0.740000, gain=141.240, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,4 0.230668->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:18,20 0.385623->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:11,17 0.383492->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:2,16 0.356963->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,9 0.353517->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,5 0.348918->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:7,19 0.324304->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node:0:depth:0:12,18 0.428582->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node:0:depth:0:4,12 0.376119->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:16,17 0.686458->0.050000, gain=-14.688, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:13,17 0.677344->0.050000, gain=128.610, TIME_LIMIT->TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:6,20 0.659830->0.740000, gain=459.734, TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:13,15 0.571318->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:11,15 0.570428->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,10 0.564602->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,9 0.545416->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:4,8 0.542268->0.050000, gain=0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:8,14 0.429726->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:6,14 0.419801->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:1,9 0.390532->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:1,12 0.386171->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:10,15 0.609472->0.050000, gain=196.276, EXTERNAL_TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:9,12 0.606329->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:12,20 0.564300->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:9,20 0.525892->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:1,20 0.475426->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:12,16 0.286313->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:4,18 0.280213->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:15,18 0.276693->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:14,18 0.267533->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json node:0:depth:0:5,13 0.329155->0.740000, gain=126.933, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json node:0:depth:0:3,5 0.205373->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json node:0:depth:0:3,17 0.202647->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,16 0.583145->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,19 0.569094->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:7,19 0.566911->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:12,14 0.562437->0.050000, gain=0.004, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:3,10 0.523324->0.740000, gain=550.376, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:1,12 0.519952->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,4 0.517696->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,10 0.512550->0.740000, gain=258.555, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:12,16 0.509528->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:11,18 0.502814->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:1,2 0.443567->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node:0:depth:0:2,3 0.344066->0.050000, gain=-0.003, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node:0:depth:0:1,14 0.563040->0.050000, gain=-71.333, OPTIMAL->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node:0:depth:0:13,20 0.366333->0.740000, gain=194.759, EXTERNAL_TIME_LIMIT->OPTIMAL

## 边界

输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。
