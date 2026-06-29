# Journey Paired Probe Summary

日期：2026-06-29

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 16
paired_group_count = 1
baseline_entry_count = 1
alternative_entry_count = 15
result_available_entry_count = 2
missing_result_entry_count = 14
observed_alternative_entry_count = 1
valid_observed_alternative_entry_count = 1
target_not_replayed_entry_count = 0
target_pair_not_selected_entry_count = 0
target_replay_reason_counts = {'target_pair_selected': 2, 'log_missing': 14}
label_counts = {'missing_result': 14, 'neutral_proxy': 1}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d0__n0__sel_2,16`
  baseline = [2, 16] / 001_candidate_selected_d0_n0_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [4, 12] / 005_candidate_alt_d0_n0_r3_4_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall -0.001163, profile 0.0, child_cb_retry 0.0
  target = hit 2, not_replayed 0, pair_not_selected 0
  labels = {'missing_result': 14, 'neutral_proxy': 1}
