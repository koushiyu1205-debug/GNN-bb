# v431 v430 Score-Gated Smoke Branch Counterfactual Rows

日期：2026-06-26

## 机器字段

```text
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v431_v430_score_gated_smoke20_20260626
row_count = 12
counterfactual_label_type_counts = {'regression': 1, 'strong_positive': 1, 'unknown_right_censored': 10}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 8, 'EXTERNAL_TIME_LIMIT->TIME_LIMIT': 1, 'OPTIMAL->OPTIMAL': 2, 'TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1}
walltime_gain_gt30_count = 1
walltime_loss_gt30_count = 1
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 明细

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> TIME_LIMIT 293.9s, capped_gain=0.0s, pair [1, 4] -> [2, 19], score=0.714, width=1172, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [5, 9] -> [1, 6], score=0.689, width=746, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json`: TIME_LIMIT 555.7s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [13, 16] -> [1, 12], score=0.686, width=777, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json`: OPTIMAL 327.7s -> OPTIMAL 60.6s, capped_gain=267.1s, pair [2, 18] -> [3, 12], score=0.671, width=684, label=strong_positive
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [1, 13] -> [2, 11], score=0.667, width=811, label=unknown_right_censored
- `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [1, 2] -> [4, 16], score=0.665, width=743, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json`: OPTIMAL 144.8s -> OPTIMAL 208.4s, capped_gain=-63.6s, pair [2, 5] -> [2, 16], score=0.663, width=734, label=regression
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [4, 7] -> [6, 11], score=0.656, width=641, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [1, 9] -> [1, 12], score=0.654, width=681, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [10, 15] -> [1, 4], score=0.640, width=558, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [5, 14] -> [1, 2], score=0.639, width=543, label=unknown_right_censored
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json`: EXTERNAL_TIME_LIMIT 600.0s -> EXTERNAL_TIME_LIMIT 600.0s, capped_gain=0.0s, pair [8, 13] -> [8, 19], score=0.637, width=533, label=unknown_right_censored

## 判断

- 这些 rows 只来自 v430 score-gated smoke 的实际闭环结果，用于训练/诊断，不代表 production-ready。
- `unknown_right_censored` 不进入主训练正负标签；`strong_positive` 与 `regression` 可进入下一轮 v431 训练。
