# GAT Branch Action Proof-Risk Overlay

日期：2026-06-27

## 目的

把已完成 branch-score 实验中的整实例正负 evidence 叠加到 score rows：严格收益分支 boost，changed 后仍非最优的分支 suppress。该脚本只读完成结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/score_map_v471_on_branchonly60_hybrid_diag/journey_branch_score_rows.json
analysis_paths = ['BPC_future/results/gat_branch_action_v457_weighted_walltime_20260627/analysis_v459_conservative_delta_overlay_input.json', 'BPC_future/results/gat_branch_action_v466_weighted_walltime_20260627/analysis_v467_v465_overlay_input.json', 'BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/analysis_v472_v470_overlay_input.json', 'BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/analysis_v473_v472_smoke_overlay_input.json']
output_dir = BPC_future/results/gat_branch_action_v471_weighted_walltime_20260627/score_map_v473_conservative_overlay_with_smoke_suppress_on_branchonly60
score_row_count = 2255
positive_overlay_keys = 12
negative_overlay_keys = 93
overlay_counts = {'boost_positive': 10, 'suppress_negative': 76}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- boost_positive: apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:12,20 0.349460->0.740000, gain=253.802, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,20 0.333536->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:4,16 0.323275->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:13,15 0.297226->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:2,5 0.296277->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,16 0.257547->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:14,18 0.196226->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json node:0:depth:0:5,16 0.311856->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json node:0:depth:0:5,11 0.286652->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,17 0.350260->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,16 0.345522->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:7,15 0.334932->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json node:0:depth:0:1,7 0.328606->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:7,12 0.307208->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:12,16 0.307081->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:1,8 0.292304->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json node:0:depth:0:1,4 0.291639->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:4,19 0.341324->0.740000, gain=257.123, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:9,10 0.311027->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json node:0:depth:0:1,6 0.270537->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,12 0.350795->0.740000, gain=268.935, OPTIMAL->OPTIMAL
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,4 0.309865->0.740000, gain=269.649, OPTIMAL->OPTIMAL
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:6,15 0.279148->0.740000, gain=141.240, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:8,14 0.270870->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,4 0.264631->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,19 0.202732->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:7,19 0.319017->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:2,16 0.310463->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:11,17 0.302570->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:18,20 0.294098->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,9 0.286542->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,5 0.281967->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node:0:depth:0:12,18 0.308136->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node:0:depth:0:4,12 0.301030->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json node:0:depth:0:8,16 0.280773->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:6,20 0.388223->0.740000, gain=459.734, TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:16,17 0.376808->0.050000, gain=-14.688, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:13,17 0.373833->0.050000, gain=128.610, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:10,18 0.338235->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:13,15 0.321990->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,10 0.316149->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,9 0.315199->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:4,8 0.314324->0.050000, gain=0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:11,15 0.268228->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:1,12 0.358599->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:6,14 0.352699->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:8,14 0.349210->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:9,10 0.332370->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json node:0:depth:0:1,9 0.324424->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:1,20 0.943876->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:9,12 0.678801->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:10,15 0.554169->0.050000, gain=196.276, EXTERNAL_TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:9,20 0.326488->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:12,20 0.320421->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:4,18 0.528700->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:12,16 0.273325->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:15,18 0.271857->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:8,15 0.265538->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:14,18 0.257720->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json node:0:depth:0:5,13 0.355757->0.740000, gain=126.933, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json node:0:depth:0:3,17 0.290131->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json node:0:depth:0:3,5 0.269015->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:5,7 0.757967->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,16 0.527246->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:7,19 0.398786->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,19 0.314482->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:10,19 0.270524->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json node:0:depth:0:2,5 0.355852->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:1,12 0.324406->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:3,10 0.306278->0.740000, gain=550.376, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:12,14 0.298774->0.050000, gain=0.004, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,10 0.270291->0.740000, gain=258.555, EXTERNAL_TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,4 0.263704->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json node:0:depth:0:5,12 0.853589->0.050000, gain=0.002, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json node:0:depth:0:5,12 0.863731->0.050000, gain=0.002, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:2,18 0.881975->0.050000, gain=-0.002, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:7,10 0.336729->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:12,16 0.335740->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:1,2 0.315339->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:11,18 0.309640->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:6,10 0.906210->0.050000, gain=-0.002, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node:0:depth:0:4,20 0.864323->0.050000, gain=-0.004, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json node:0:depth:0:2,3 0.675142->0.050000, gain=-0.003, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json node:0:depth:0:4,7 0.918277->0.050000, gain=-0.001, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json node:0:depth:0:1,14 0.887984->0.050000, gain=-71.333, OPTIMAL->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node:0:depth:0:13,20 0.331925->0.740000, gain=194.759, EXTERNAL_TIME_LIMIT->OPTIMAL

## 边界

输出只用于 opt-in branch ordering。它不能剪枝，不能替代 exact pricing closure，也不能作为 official lower bound。
