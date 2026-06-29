# Journey Paired Probe Summary

日期：2026-06-29

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 8
paired_group_count = 2
baseline_entry_count = 2
alternative_entry_count = 6
result_available_entry_count = 4
missing_result_entry_count = 4
observed_alternative_entry_count = 3
valid_observed_alternative_entry_count = 3
target_not_replayed_entry_count = 0
target_pair_not_selected_entry_count = 0
label_counts = {'missing_result': 3, 'neutral_proxy': 3}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n5__sel_13,14`
  baseline = None / None
  best_alt = None / None
  gains = wall None, profile None, child_cb_retry None
  target = hit 0, not_replayed 0, pair_not_selected 0
  labels = {'missing_result': 3}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n6__sel_13,14`
  baseline = [13, 14] / 005_candidate_selected_d2_n6_13_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [3, 19] / 006_candidate_alt_d2_n6_r1_3_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 0.740418, profile 0.0, child_cb_retry 0.0
  target = hit 4, not_replayed 0, pair_not_selected 0
  labels = {'neutral_proxy': 3}
