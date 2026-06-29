# Journey Dynamic SRC Audit Summary

日期：2026-06-28

## Boundary

This report summarizes existing dynamic SRC logs only. It does not run BPC / pricing / RMP and does not create official bounds or certificates.

## Summary

```text
run_count = 6
candidate_row_count = 170
global_task_hubs = [{'task': 2, 'count': 126}, {'task': 10, 'count': 91}, {'task': 3, 'count': 76}, {'task': 19, 'count': 75}, {'task': 4, 'count': 64}, {'task': 13, 'count': 63}, {'task': 8, 'count': 54}, {'task': 12, 'count': 52}, {'task': 5, 'count': 50}, {'task': 15, 'count': 48}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Runs

- `20260628_v734_dynamic_src_cuton_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph`
  separations=6, violated=20, added=20, max_best_violation=0.5, max_active_cuts=21
  gate pass/block=0/0
  task_hubs=[{'task': 10, 'count': 16}, {'task': 8, 'count': 14}, {'task': 3, 'count': 12}, {'task': 4, 'count': 10}, {'task': 12, 'count': 10}, {'task': 13, 'count': 8}, {'task': 15, 'count': 8}, {'task': 16, 'count': 8}]
- `20260628_v734_dynamic_src_cuton_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=22, added=22, max_best_violation=0.5, max_active_cuts=23
  gate pass/block=0/0
  task_hubs=[{'task': 2, 'count': 26}, {'task': 19, 'count': 16}, {'task': 10, 'count': 12}, {'task': 3, 'count': 10}, {'task': 4, 'count': 10}, {'task': 1, 'count': 10}, {'task': 13, 'count': 8}, {'task': 5, 'count': 8}]
- `20260628_v736_dynamic_src_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph`
  separations=6, violated=20, added=20, max_best_violation=0.5, max_active_cuts=21
  gate pass/block=4/2
  task_hubs=[{'task': 10, 'count': 16}, {'task': 8, 'count': 14}, {'task': 3, 'count': 12}, {'task': 4, 'count': 10}, {'task': 12, 'count': 10}, {'task': 13, 'count': 8}, {'task': 15, 'count': 8}, {'task': 16, 'count': 8}]
- `20260628_v736_dynamic_src_gated_hard2_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=6, violated=18, added=9, max_best_violation=0.5, max_active_cuts=10
  gate pass/block=2/4
  task_hubs=[{'task': 2, 'count': 14}, {'task': 19, 'count': 12}, {'task': 3, 'count': 9}, {'task': 4, 'count': 9}, {'task': 1, 'count': 9}, {'task': 10, 'count': 8}, {'task': 13, 'count': 8}, {'task': 5, 'count': 4}]
- `20260628_v737_dynamic_src_strong_seed61635_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=25, violated=49, added=49, max_best_violation=0.5, max_active_cuts=50
  gate pass/block=0/0
  task_hubs=[{'task': 2, 'count': 42}, {'task': 3, 'count': 22}, {'task': 10, 'count': 20}, {'task': 19, 'count': 18}, {'task': 13, 'count': 18}, {'task': 5, 'count': 16}, {'task': 15, 'count': 16}, {'task': 14, 'count': 14}]
- `20260628_v738_dynamic_src_depth2_gated_seed61635_600::tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph`
  separations=14, violated=41, added=39, max_best_violation=0.5, max_active_cuts=40
  gate pass/block=9/5
  task_hubs=[{'task': 2, 'count': 40}, {'task': 10, 'count': 19}, {'task': 19, 'count': 17}, {'task': 13, 'count': 13}, {'task': 4, 'count': 13}, {'task': 1, 'count': 13}, {'task': 14, 'count': 12}, {'task': 12, 'count': 12}]
