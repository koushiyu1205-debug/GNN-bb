# GAT Branch Action v438 Proof-Risk Overlay Score Map

日期：2026-06-26

## 目的

在 v433 scoped score map 上叠加 v436 已观测 proof-risk：保留严格正例，压低 changed 后仍 600s timeout 的 root pair。该产物只影响 opt-in branch 排序，不提供 official bound/certificate。

## 机器字段

```text
base_score_rows = BPC_future/results/gat_branch_action_v430_randomtw60_20260626/score_map_v433_v421_depth01_top200_hybrid_scoped/journey_branch_score_rows.json
output_dir = BPC_future/results/gat_branch_action_v437_randomtw60_20260626/score_map_v438_v433_plus_v436_proofrisk_overlay
score_row_count = 3322
positive_overlay_keys = 2
negative_overlay_keys = 6
overlay_counts = {'suppress_negative': 6, 'boost_positive': 2}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## Overlay Rows

- suppress_negative: apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,20 0.647296->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:3,12 0.671354->0.680000, gain=268.935, OPTIMAL->OPTIMAL
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json node:0:depth:0:1,4 0.639845->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json node:0:depth:0:6,11 0.655633->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json node:0:depth:0:8,19 0.636824->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json node:0:depth:0:1,12 0.654412->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- suppress_negative: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json node:0:depth:0:1,2 0.639369->0.050000, gain=0.000, EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT
- boost_positive: tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json node:0:depth:0:13,20 0.626996->0.680000, gain=194.759, EXTERNAL_TIME_LIMIT->OPTIMAL
