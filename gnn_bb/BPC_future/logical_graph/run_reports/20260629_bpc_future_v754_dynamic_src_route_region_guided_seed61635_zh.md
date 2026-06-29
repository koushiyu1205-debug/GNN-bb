# Journey Dynamic SRC Audit Summary

日期：2026-06-29

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 1
candidate_row_count = 15
global_task_hubs = [{'task': 2, 'count': 24}, {'task': 19, 'count': 18}, {'task': 13, 'count': 9}, {'task': 10, 'count': 8}, {'task': 4, 'count': 7}, {'task': 1, 'count': 7}, {'task': 12, 'count': 6}, {'task': 3, 'count': 6}, {'task': 16, 'count': 4}, {'task': 20, 'count': 4}]
global_route_region_task_hubs = [{'task': 2, 'weighted_violation': 3.363636364}, {'task': 19, 'weighted_violation': 3.0}, {'task': 10, 'weighted_violation': 1.5}, {'task': 13, 'weighted_violation': 1.5}, {'task': 1, 'weighted_violation': 1.324675325}, {'task': 16, 'weighted_violation': 0.5}, {'task': 18, 'weighted_violation': 0.5}, {'task': 3, 'weighted_violation': 0.324675325}, {'task': 4, 'weighted_violation': 0.324675325}, {'task': 6, 'weighted_violation': 0.25}]
global_route_region_pair_hubs = [{'tasks': [2, 19], 'weighted_violation': 2.0}, {'tasks': [10, 19], 'weighted_violation': 1.25}, {'tasks': [13, 19], 'weighted_violation': 1.25}, {'tasks': [1, 19], 'weighted_violation': 1.0}, {'tasks': [4, 19], 'weighted_violation': 1.0}, {'tasks': [2, 16], 'weighted_violation': 0.5}, {'tasks': [2, 18], 'weighted_violation': 0.5}, {'tasks': [16, 18], 'weighted_violation': 0.5}, {'tasks': [2, 6], 'weighted_violation': 0.25}, {'tasks': [2, 7], 'weighted_violation': 0.25}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260629_v754_route_region_guided_src_seed61635_180::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=22, added=17, max_best_violation=0.5, max_active_cuts=18
  route_region_guided generated/violated=1516/4
  gate pass/block=3/3
  task_hubs=[{'task': 2, 'count': 24}, {'task': 19, 'count': 18}, {'task': 13, 'count': 9}, {'task': 10, 'count': 8}, {'task': 4, 'count': 7}, {'task': 1, 'count': 7}, {'task': 12, 'count': 6}, {'task': 3, 'count': 6}]
  route_region_events=6, route_region_task_hubs=[{'task': 2, 'weighted_violation': 3.363636364}, {'task': 19, 'weighted_violation': 3.0}, {'task': 10, 'weighted_violation': 1.5}, {'task': 13, 'weighted_violation': 1.5}, {'task': 1, 'weighted_violation': 1.324675325}, {'task': 16, 'weighted_violation': 0.5}, {'task': 18, 'weighted_violation': 0.5}, {'task': 3, 'weighted_violation': 0.324675325}]
