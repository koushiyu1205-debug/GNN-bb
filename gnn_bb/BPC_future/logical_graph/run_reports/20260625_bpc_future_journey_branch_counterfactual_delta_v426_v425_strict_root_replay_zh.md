# V426 strict root replay counterfactual delta

日期：2026-06-26

```text
row_count = 16
label_type_counts = {'strong_positive': 9, 'regression': 5, 'unknown_right_censored': 2}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->OPTIMAL': 2, 'OPTIMAL->OPTIMAL': 10, 'TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1, 'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 2, 'OPTIMAL->TIME_LIMIT': 1}
usable_for_counterfactual_training_count = 14
mean_capped_delta = -19.733818625000005
```

## Best replay deltas

- -269.649s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json` OPTIMAL 327.746s -> OPTIMAL 58.097s, pair=[3, 4], label=strong_positive
- -253.780s: `apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json` EXTERNAL_TIME_LIMIT 600.022s -> OPTIMAL 346.220s, pair=[12, 20], label=strong_positive
- -141.222s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json` EXTERNAL_TIME_LIMIT 600.018s -> OPTIMAL 458.778s, pair=[6, 15], label=strong_positive
- -71.893s: `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json` OPTIMAL 173.764s -> OPTIMAL 101.872s, pair=[8, 16], label=strong_positive
- -60.472s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json` OPTIMAL 522.147s -> OPTIMAL 461.675s, pair=[3, 6], label=strong_positive
- -42.762s: `apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json` OPTIMAL 188.584s -> OPTIMAL 145.822s, pair=[4, 14], label=strong_positive
- -37.238s: `apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json` OPTIMAL 220.161s -> OPTIMAL 182.922s, pair=[2, 4], label=strong_positive
- -8.809s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json` OPTIMAL 42.301s -> OPTIMAL 33.492s, pair=[2, 18], label=strong_positive

## Worst replay deltas

- +309.476s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json` OPTIMAL 287.680s -> TIME_LIMIT 597.156s, pair=[2, 13], label=regression
- +144.938s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json` OPTIMAL 144.821s -> OPTIMAL 289.759s, pair=[5, 11], label=regression
- +46.951s: `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json` OPTIMAL 253.704s -> OPTIMAL 300.655s, pair=[2, 16], label=regression
- +44.254s: `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json` TIME_LIMIT 555.746s -> EXTERNAL_TIME_LIMIT 600.017s, pair=[11, 12], label=regression
- +31.198s: `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json` OPTIMAL 129.364s -> OPTIMAL 160.562s, pair=[5, 19], label=regression
- +0.000s: `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json` EXTERNAL_TIME_LIMIT 600.022s -> EXTERNAL_TIME_LIMIT 600.018s, pair=[12, 14], label=unknown_right_censored
- +0.000s: `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json` EXTERNAL_TIME_LIMIT 600.017s -> EXTERNAL_TIME_LIMIT 600.019s, pair=[2, 3], label=unknown_right_censored
- +-6.735s: `apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json` OPTIMAL 198.987s -> OPTIMAL 192.252s, pair=[6, 11], label=strong_positive
