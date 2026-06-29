# Journey Paired Probe Summary

日期：2026-06-28

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 12
paired_group_count = 4
baseline_entry_count = 4
alternative_entry_count = 8
result_available_entry_count = 12
missing_result_entry_count = 0
observed_alternative_entry_count = 8
valid_observed_alternative_entry_count = 6
target_not_replayed_entry_count = 3
target_pair_not_selected_entry_count = 0
label_counts = {'neutral_proxy': 6, 'target_not_replayed': 2}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n1__sel_5,13`
  baseline = [5, 13] / 007_candidate_selected_d1_n1_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [5, 19] / 008_candidate_alt_d1_n1_r1_5_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall 0.019639, profile 0.0, child_cb_retry 0.0
  target = hit 3, not_replayed 0, pair_not_selected 0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph__d1__n2__sel_5,13`
  baseline = [5, 13] / 010_candidate_selected_d1_n2_5_13_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  best_alt = [4, 20] / 012_candidate_alt_d1_n2_r2_4_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph
  gains = wall -12.106404, profile 0.0, child_cb_retry 0.0
  target = hit 3, not_replayed 0, pair_not_selected 0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d1__n1__sel_11,15`
  baseline = [11, 15] / 001_candidate_selected_d1_n1_11_15_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph
  best_alt = [15, 17] / 003_candidate_alt_d1_n1_r2_15_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph
  gains = wall 0.543908, profile 0.0, child_cb_retry 0.0
  target = hit 3, not_replayed 0, pair_not_selected 0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n4__sel_7,14`
  baseline = [7, 14] / 004_candidate_selected_d2_n4_7_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph
  best_alt = None / None
  gains = wall None, profile None, child_cb_retry None
  target = hit 0, not_replayed 3, pair_not_selected 0
  labels = {'target_not_replayed': 2}
