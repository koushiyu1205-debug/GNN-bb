# Journey Paired Probe Summary

日期：2026-06-28

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 16
paired_group_count = 4
baseline_entry_count = 4
alternative_entry_count = 12
result_available_entry_count = 16
missing_result_entry_count = 0
observed_alternative_entry_count = 12
label_counts = {'hard_negative_proxy': 5, 'neutral_proxy': 7}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_1,3`
  baseline = [1, 3] / 001_candidate_selected_d1_n1_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [1, 10] / 003_candidate_alt_d1_n1_r2_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 0.016004, profile 0.0, child_cb_retry 5.0
  labels = {'hard_negative_proxy': 3}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_1,3`
  baseline = [1, 3] / 005_candidate_selected_d1_n2_1_3_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [1, 15] / 007_candidate_alt_d1_n2_r2_1_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 0.912465, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 3}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n3__sel_1,10`
  baseline = [1, 10] / 009_candidate_selected_d2_n3_1_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [3, 10] / 010_candidate_alt_d2_n3_r1_3_10_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 0.499836, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 3}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d2__n4__sel_1,13`
  baseline = [1, 13] / 013_candidate_selected_d2_n4_1_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [5, 8] / 015_candidate_alt_d2_n4_r2_5_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 21.507233, profile 0.0, child_cb_retry 5.0
  labels = {'hard_negative_proxy': 2, 'neutral_proxy': 1}
