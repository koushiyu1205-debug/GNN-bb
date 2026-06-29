# Journey Paired Probe Summary

日期：2026-06-28

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 6
paired_group_count = 3
baseline_entry_count = 3
alternative_entry_count = 3
result_available_entry_count = 6
missing_result_entry_count = 0
observed_alternative_entry_count = 3
label_counts = {'neutral_proxy': 2, 'positive_proxy': 1}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_3,4`
  baseline = [3, 4] / 001_candidate_selected_d0_n0_3_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph
  best_alt = [3, 12] / 002_candidate_alt_d0_n0_r1_3_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph
  gains = wall 0.014463, profile -0.018624, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d1__n1__sel_8,12`
  baseline = [8, 12] / 005_candidate_selected_d1_n1_8_12_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph
  best_alt = [12, 13] / 006_candidate_alt_d1_n1_r1_12_13_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph
  gains = wall 1.260352, profile 1.195685, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph__d0__n0__sel_2,10`
  baseline = [2, 10] / 003_candidate_selected_d0_n0_2_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph
  best_alt = [3, 10] / 004_candidate_alt_d0_n0_r1_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph
  gains = wall -0.021741, profile -1.878292, child_cb_retry 0.0
  labels = {'positive_proxy': 1}
