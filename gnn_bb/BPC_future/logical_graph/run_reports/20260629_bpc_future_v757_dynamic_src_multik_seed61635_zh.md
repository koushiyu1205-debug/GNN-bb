# Journey Dynamic SRC Audit Summary

日期：2026-06-29

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 1
candidate_row_count = 22
cut_dual_diagnostic_count = 55
cut_dual_nonzero_event_count = 29
max_nonzero_cut_dual_count = 5
max_subset_row_nonzero_dual_count = 5
max_binding_nonzero_cut_count = 5
max_cut_dual_abs_sum = 21.985862615
global_task_hubs = [{'task': 2, 'count': 34}, {'task': 10, 'count': 34}, {'task': 18, 'count': 33}, {'task': 6, 'count': 23}, {'task': 8, 'count': 23}, {'task': 17, 'count': 19}, {'task': 19, 'count': 19}, {'task': 14, 'count': 18}, {'task': 11, 'count': 17}, {'task': 15, 'count': 13}]
global_route_region_task_hubs = [{'task': 2, 'weighted_violation': 6.683333333}, {'task': 10, 'weighted_violation': 5.566666667}, {'task': 17, 'weighted_violation': 4.433333333}, {'task': 18, 'weighted_violation': 3.866666666}, {'task': 6, 'weighted_violation': 2.75}, {'task': 8, 'weighted_violation': 2.75}, {'task': 16, 'weighted_violation': 2.333333333}, {'task': 11, 'weighted_violation': 1.666666667}, {'task': 14, 'weighted_violation': 1.333333333}, {'task': 19, 'weighted_violation': 1.0}]
global_route_region_pair_hubs = [{'tasks': [2, 17], 'weighted_violation': 3.583333333}, {'tasks': [2, 14], 'weighted_violation': 3.333333333}, {'tasks': [2, 6], 'weighted_violation': 2.75}, {'tasks': [2, 8], 'weighted_violation': 2.75}, {'tasks': [2, 16], 'weighted_violation': 2.333333333}, {'tasks': [2, 18], 'weighted_violation': 2.333333333}, {'tasks': [14, 17], 'weighted_violation': 2.0}, {'tasks': [14, 16], 'weighted_violation': 1.333333333}, {'tasks': [16, 18], 'weighted_violation': 1.0}, {'tasks': [11, 18], 'weighted_violation': 1.0}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260629_v757_guided_src_multik_seed61635_180::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=45, added=36, max_best_violation=0.5, max_active_cuts=37
  route_region_guided generated/violated=5016/33
  cut_dual_diag nonzero_events=29/55, max_nonzero=5, max_subset_nonzero=5, max_binding_nonzero=5, max_abs_sum=21.985862615
  gate pass/block=4/2
  task_hubs=[{'task': 2, 'count': 34}, {'task': 10, 'count': 34}, {'task': 18, 'count': 33}, {'task': 6, 'count': 23}, {'task': 8, 'count': 23}, {'task': 17, 'count': 19}, {'task': 19, 'count': 19}, {'task': 14, 'count': 18}]
  route_region_events=6, route_region_task_hubs=[{'task': 2, 'weighted_violation': 6.683333333}, {'task': 10, 'weighted_violation': 5.566666667}, {'task': 17, 'weighted_violation': 4.433333333}, {'task': 18, 'weighted_violation': 3.866666666}, {'task': 6, 'weighted_violation': 2.75}, {'task': 8, 'weighted_violation': 2.75}, {'task': 16, 'weighted_violation': 2.333333333}, {'task': 11, 'weighted_violation': 1.666666667}]
