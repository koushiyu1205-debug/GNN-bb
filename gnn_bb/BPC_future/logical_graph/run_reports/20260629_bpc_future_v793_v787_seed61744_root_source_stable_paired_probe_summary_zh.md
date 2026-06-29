# Journey Paired Probe Summary

日期：2026-06-29

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 4
paired_group_count = 1
baseline_entry_count = 1
alternative_entry_count = 3
result_available_entry_count = 2
missing_result_entry_count = 2
observed_alternative_entry_count = 1
valid_observed_alternative_entry_count = 0
target_not_replayed_entry_count = 2
target_pair_not_selected_entry_count = 0
target_replay_reason_counts = {'source_node_not_replayed': 2, 'log_missing': 2}
label_counts = {'missing_result': 2, 'target_not_replayed': 1}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph__d0__n0__sel_3,6`
  baseline = [3, 6] / 001_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph
  best_alt = None / None
  gains = wall None, profile None, child_cb_retry None
  target = hit 0, not_replayed 2, pair_not_selected 0
  labels = {'missing_result': 2, 'target_not_replayed': 1}
