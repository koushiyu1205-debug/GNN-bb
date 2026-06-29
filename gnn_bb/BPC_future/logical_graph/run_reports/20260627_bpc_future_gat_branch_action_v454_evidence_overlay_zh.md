# GAT Branch Action v454 Evidence Overlay

日期：2026-06-27

## Summary

```text
base_score_rows = BPC_future/results/gat_branch_action_v453_weighted_walltime_20260627/score_map_v453_v438logs_hybrid_diag/journey_branch_score_rows.json
output_dir = BPC_future/results/gat_branch_action_v453_weighted_walltime_20260627/score_map_v454_evidence_overlay_v438logs
positive_keys = 4
negative_keys = 17
overlay_counts = {'suppress_negative': 17, 'boost_positive': 4}
score_row_count = 463
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Touched Rows

- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,16 0.551558->0.050000, source=v452_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,20 0.482527->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,12 0.525097->0.720000, source=v436_positive, gain=268.935, OPTIMAL->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:15,19 0.417952->0.050000, source=v447_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,4 0.394997->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,9 0.431768->0.050000, source=v449_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json node:0:depth:0:3,5 0.418955->0.050000, source=v449_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:6,20 0.538401->0.740000, source=v452_strong_positive, gain=459.734, TIME_LIMIT->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:16,17 0.507793->0.050000, source=v449_negative, gain=-14.688, TIME_LIMIT->TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json node:0:depth:0:13,17 0.504859->0.690000, source=v447_walltime_gain, gain=128.610, TIME_LIMIT->TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:6,11 0.552556->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:4,8 0.518366->0.050000, source=v447_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:8,9 0.517458->0.050000, source=v449_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json node:0:depth:0:12,15 0.509521->0.050000, source=v452_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,19 0.541913->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,16 0.503057->0.050000, source=v449_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:1,12 0.495600->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:2,4 0.493889->0.050000, source=v449_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:11,18 0.551395->0.050000, source=v452_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:1,2 0.450388->0.050000, source=v436_negative, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node:0:depth:0:13,20 0.428222->0.720000, source=v436_positive, gain=194.759, EXTERNAL_TIME_LIMIT->OPTIMAL

## Boundary

该 overlay 只改变 opt-in branch ordering 分数；不提供 official bound、certificate、pricing oracle 或剪枝依据。
