# Journey Dynamic SRC Audit Summary

日期：2026-06-29

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 1
candidate_row_count = 15
global_task_hubs = [{'task': 2, 'count': 14}, {'task': 19, 'count': 10}, {'task': 4, 'count': 9}, {'task': 3, 'count': 8}, {'task': 13, 'count': 7}, {'task': 1, 'count': 7}, {'task': 10, 'count': 6}, {'task': 12, 'count': 4}, {'task': 5, 'count': 3}, {'task': 16, 'count': 2}]
global_route_region_task_hubs = [{'task': 2, 'weighted_violation': 1.727272728}, {'task': 19, 'weighted_violation': 1.5}, {'task': 1, 'weighted_violation': 1.006493507}, {'task': 10, 'weighted_violation': 1.0}, {'task': 13, 'weighted_violation': 1.0}, {'task': 3, 'weighted_violation': 0.506493507}, {'task': 4, 'weighted_violation': 0.506493507}, {'task': 16, 'weighted_violation': 0.5}, {'task': 18, 'weighted_violation': 0.5}, {'task': 12, 'weighted_violation': 0.363636364}]
global_route_region_pair_hubs = [{'tasks': [10, 19], 'weighted_violation': 0.75}, {'tasks': [13, 19], 'weighted_violation': 0.75}, {'tasks': [2, 16], 'weighted_violation': 0.5}, {'tasks': [2, 18], 'weighted_violation': 0.5}, {'tasks': [16, 18], 'weighted_violation': 0.5}, {'tasks': [1, 19], 'weighted_violation': 0.5}, {'tasks': [2, 19], 'weighted_violation': 0.5}, {'tasks': [3, 5], 'weighted_violation': 0.5}, {'tasks': [1, 2], 'weighted_violation': 0.363636364}, {'tasks': [2, 3], 'weighted_violation': 0.363636364}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260629_v753_route_region_audit_seed61635_180::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=18, added=9, max_best_violation=0.5, max_active_cuts=10
  gate pass/block=2/4
  task_hubs=[{'task': 2, 'count': 14}, {'task': 19, 'count': 10}, {'task': 4, 'count': 9}, {'task': 3, 'count': 8}, {'task': 13, 'count': 7}, {'task': 1, 'count': 7}, {'task': 10, 'count': 6}, {'task': 12, 'count': 4}]
  route_region_events=6, route_region_task_hubs=[{'task': 2, 'weighted_violation': 1.727272728}, {'task': 19, 'weighted_violation': 1.5}, {'task': 1, 'weighted_violation': 1.006493507}, {'task': 10, 'weighted_violation': 1.0}, {'task': 13, 'weighted_violation': 1.0}, {'task': 3, 'weighted_violation': 0.506493507}, {'task': 4, 'weighted_violation': 0.506493507}, {'task': 16, 'weighted_violation': 0.5}]
