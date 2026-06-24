# Journey Tail-Action Counterfactual Delta

日期：2026-06-24

## 机器字段

```text
journey_tail_action_counterfactual_delta = current
matched_counterfactual_count = 5
local_tail_improved_count = 5
whole_run_improved_count = 0
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Label Counts

- `y_local_improved_but_whole_run_not`: 5
- `y_local_tail_improved`: 5
- `y_right_censored_counterfactual`: 5

## Rows

- 02_tail_action_alt_pair_d1_n1_r9_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph: pair [4, 7] -> [1, 10], status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, local_delta=-42.35, wall_delta=-0.002188, labels={'y_local_tail_improved': 1.0, 'y_whole_run_improved': 0.0, 'y_local_improved_but_whole_run_not': 1.0, 'y_timeout_resolved': 0.0, 'y_timeout_regression': 0.0, 'y_right_censored_counterfactual': 1.0}
- 03_tail_action_alt_pair_d1_n1_r17_4_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph: pair [4, 7] -> [4, 11], status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, local_delta=-32.95, wall_delta=-0.00199, labels={'y_local_tail_improved': 1.0, 'y_whole_run_improved': 0.0, 'y_local_improved_but_whole_run_not': 1.0, 'y_timeout_resolved': 0.0, 'y_timeout_regression': 0.0, 'y_right_censored_counterfactual': 1.0}
- 08_tail_action_alt_pair_d2_n3_r1_1_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph: pair [1, 10] -> [1, 15], status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, local_delta=-17.85, wall_delta=-0.001213, labels={'y_local_tail_improved': 1.0, 'y_whole_run_improved': 0.0, 'y_local_improved_but_whole_run_not': 1.0, 'y_timeout_resolved': 0.0, 'y_timeout_regression': 0.0, 'y_right_censored_counterfactual': 1.0}
- 09_tail_action_alt_pair_d2_n3_r4_2_15_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph: pair [1, 10] -> [2, 15], status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, local_delta=-19.95, wall_delta=-0.000693, labels={'y_local_tail_improved': 1.0, 'y_whole_run_improved': 0.0, 'y_local_improved_but_whole_run_not': 1.0, 'y_timeout_resolved': 0.0, 'y_timeout_regression': 0.0, 'y_right_censored_counterfactual': 1.0}
- 12_tail_action_alt_pair_d2_n4_r11_1_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph: pair [4, 11] -> [1, 10], status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, local_delta=-3.25, wall_delta=0.013423, labels={'y_local_tail_improved': 1.0, 'y_whole_run_improved': 0.0, 'y_local_improved_but_whole_run_not': 1.0, 'y_timeout_resolved': 0.0, 'y_timeout_regression': 0.0, 'y_right_censored_counterfactual': 1.0}

## 边界

这些 rows 只用于离线反事实诊断和 hard-negative/positive gap 标注；不能作为 branch oracle、pricing oracle、official bound 或 certificate。
