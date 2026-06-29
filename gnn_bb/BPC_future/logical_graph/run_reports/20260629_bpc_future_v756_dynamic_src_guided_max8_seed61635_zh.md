# Journey Dynamic SRC Audit Summary

日期：2026-06-29

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 1
candidate_row_count = 21
cut_dual_diagnostic_count = 56
cut_dual_nonzero_event_count = 17
max_nonzero_cut_dual_count = 4
max_subset_row_nonzero_dual_count = 4
max_binding_nonzero_cut_count = 4
max_cut_dual_abs_sum = 21.2536988
global_task_hubs = [{'task': 2, 'count': 29}, {'task': 18, 'count': 26}, {'task': 10, 'count': 26}, {'task': 17, 'count': 20}, {'task': 6, 'count': 15}, {'task': 8, 'count': 15}, {'task': 14, 'count': 15}, {'task': 16, 'count': 11}, {'task': 13, 'count': 11}, {'task': 19, 'count': 10}]
global_route_region_task_hubs = [{'task': 2, 'weighted_violation': 6.35}, {'task': 10, 'weighted_violation': 5.566666667}, {'task': 17, 'weighted_violation': 4.1}, {'task': 18, 'weighted_violation': 3.533333333}, {'task': 6, 'weighted_violation': 2.75}, {'task': 8, 'weighted_violation': 2.75}, {'task': 16, 'weighted_violation': 2.0}, {'task': 11, 'weighted_violation': 1.666666667}, {'task': 14, 'weighted_violation': 1.0}, {'task': 19, 'weighted_violation': 1.0}]
global_route_region_pair_hubs = [{'tasks': [2, 17], 'weighted_violation': 3.25}, {'tasks': [2, 14], 'weighted_violation': 3.0}, {'tasks': [2, 6], 'weighted_violation': 2.75}, {'tasks': [2, 8], 'weighted_violation': 2.75}, {'tasks': [2, 16], 'weighted_violation': 2.0}, {'tasks': [2, 18], 'weighted_violation': 2.0}, {'tasks': [14, 17], 'weighted_violation': 2.0}, {'tasks': [16, 18], 'weighted_violation': 1.0}, {'tasks': [14, 16], 'weighted_violation': 1.0}, {'tasks': [10, 11], 'weighted_violation': 1.0}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260629_v756_guided_src_max8_seed61635_180::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=45, added=24, max_best_violation=0.5, max_active_cuts=25
  route_region_guided generated/violated=3016/34
  cut_dual_diag nonzero_events=17/56, max_nonzero=4, max_subset_nonzero=4, max_binding_nonzero=4, max_abs_sum=21.2536988
  gate pass/block=3/3
  task_hubs=[{'task': 2, 'count': 29}, {'task': 18, 'count': 26}, {'task': 10, 'count': 26}, {'task': 17, 'count': 20}, {'task': 6, 'count': 15}, {'task': 8, 'count': 15}, {'task': 14, 'count': 15}, {'task': 16, 'count': 11}]
  route_region_events=6, route_region_task_hubs=[{'task': 2, 'weighted_violation': 6.35}, {'task': 10, 'weighted_violation': 5.566666667}, {'task': 17, 'weighted_violation': 4.1}, {'task': 18, 'weighted_violation': 3.533333333}, {'task': 6, 'weighted_violation': 2.75}, {'task': 8, 'weighted_violation': 2.75}, {'task': 16, 'weighted_violation': 2.0}, {'task': 11, 'weighted_violation': 1.666666667}]
