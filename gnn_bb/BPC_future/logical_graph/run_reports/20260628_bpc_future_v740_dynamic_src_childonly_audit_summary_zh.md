# Journey Dynamic SRC Audit Summary

日期：2026-06-28

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 4
candidate_row_count = 60
global_task_hubs = [{'task': 3, 'count': 38}, {'task': 10, 'count': 38}, {'task': 8, 'count': 25}, {'task': 4, 'count': 25}, {'task': 2, 'count': 23}, {'task': 19, 'count': 22}, {'task': 12, 'count': 21}, {'task': 13, 'count': 19}, {'task': 15, 'count': 18}, {'task': 20, 'count': 16}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260628_v736_dynamic_src_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph`
  separations=6, violated=20, added=20, max_best_violation=0.5, max_active_cuts=21
  gate pass/block=4/2
  task_hubs=[{'task': 10, 'count': 16}, {'task': 8, 'count': 14}, {'task': 3, 'count': 12}, {'task': 4, 'count': 10}, {'task': 12, 'count': 10}, {'task': 13, 'count': 8}, {'task': 15, 'count': 8}, {'task': 16, 'count': 8}]
- `20260628_v736_dynamic_src_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=18, added=9, max_best_violation=0.5, max_active_cuts=10
  gate pass/block=2/4
  task_hubs=[{'task': 2, 'count': 14}, {'task': 19, 'count': 12}, {'task': 3, 'count': 9}, {'task': 4, 'count': 9}, {'task': 1, 'count': 9}, {'task': 10, 'count': 8}, {'task': 13, 'count': 8}, {'task': 5, 'count': 4}]
- `20260628_v740_dynamic_src_childonly_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph`
  separations=6, violated=17, added=9, max_best_violation=0.5, max_active_cuts=10
  gate pass/block=3/3
  task_hubs=[{'task': 3, 'count': 11}, {'task': 15, 'count': 10}, {'task': 8, 'count': 9}, {'task': 10, 'count': 9}, {'task': 12, 'count': 5}, {'task': 4, 'count': 4}, {'task': 20, 'count': 4}, {'task': 16, 'count': 4}]
- `20260628_v740_dynamic_src_childonly_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=9, added=6, max_best_violation=0.5, max_active_cuts=7
  gate pass/block=1/5
  task_hubs=[{'task': 3, 'count': 6}, {'task': 20, 'count': 6}, {'task': 2, 'count': 5}, {'task': 10, 'count': 5}, {'task': 16, 'count': 2}, {'task': 12, 'count': 2}, {'task': 13, 'count': 2}, {'task': 8, 'count': 2}]
