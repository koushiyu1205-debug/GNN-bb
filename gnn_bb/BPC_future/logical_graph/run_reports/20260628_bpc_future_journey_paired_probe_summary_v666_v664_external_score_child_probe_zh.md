# Journey Paired Probe Summary

日期：2026-06-28

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 24
paired_group_count = 15
baseline_entry_count = 10
alternative_entry_count = 14
result_available_entry_count = 24
missing_result_entry_count = 0
observed_alternative_entry_count = 14
label_counts = {'neutral_proxy': 7, 'missing_baseline': 5, 'hard_negative_proxy': 2}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12`
  baseline = None / None
  best_alt = [3, 8] / 013_candidate_alt_d0_n0_r69_3_8_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph
  gains = wall None, profile None, child_cb_retry None
  labels = {'missing_baseline': 1}
- `apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18`
  baseline = None / None
  best_alt = [3, 18] / 007_candidate_alt_d0_n0_r36_3_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph
  gains = wall None, profile None, child_cb_retry None
  labels = {'missing_baseline': 1}
- `apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph__d0__n0__sel_3,7`
  baseline = [3, 7] / 020_candidate_selected_d0_n0_3_7_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph
  best_alt = [1, 18] / 021_candidate_alt_d0_n0_r56_1_18_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph
  gains = wall 7.280904, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph__d0__n0__sel_1,12`
  baseline = [1, 12] / 009_candidate_selected_d0_n0_1_12_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph
  best_alt = [2, 18] / 010_candidate_alt_d0_n0_r48_2_18_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph
  gains = wall 14.421054, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph__d0__n0__sel_5,6`
  baseline = [5, 6] / 018_candidate_selected_d0_n0_5_6_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph
  best_alt = [1, 18] / 019_candidate_alt_d0_n0_r31_1_18_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph
  gains = wall 19.261906, profile 0.0, child_cb_retry 0.0
  labels = {'hard_negative_proxy': 1}
- `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d0__n0__sel_4,8`
  baseline = [4, 8] / 016_candidate_selected_d0_n0_4_8_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph
  best_alt = [5, 18] / 017_candidate_alt_d0_n0_r45_5_18_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph
  gains = wall -9.259593, profile 0.0, child_cb_retry 0.0
  labels = {'hard_negative_proxy': 1}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph__d0__n0__sel_5,9`
  baseline = None / None
  best_alt = [2, 16] / 012_candidate_alt_d0_n0_r67_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph
  gains = wall None, profile None, child_cb_retry None
  labels = {'missing_baseline': 1}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph__d0__n0__sel_6,20`
  baseline = None / None
  best_alt = [2, 16] / 008_candidate_alt_d0_n0_r13_2_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph
  gains = wall None, profile None, child_cb_retry None
  labels = {'missing_baseline': 1}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph__d0__n0__sel_5,19`
  baseline = [5, 19] / 001_candidate_selected_d0_n0_5_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph
  best_alt = [3, 10] / 002_candidate_alt_d0_n0_r7_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph
  gains = wall -6.223003, profile 0.0, child_cb_retry -5.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph__d0__n0__sel_3,10`
  baseline = [3, 10] / 014_candidate_selected_d0_n0_3_10_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph
  best_alt = [5, 20] / 015_candidate_alt_d0_n0_r34_5_20_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph
  gains = wall 3.100485, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d0__n0__sel_5,14`
  baseline = [5, 14] / 005_candidate_selected_d0_n0_5_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph
  best_alt = [2, 14] / 006_candidate_alt_d0_n0_r27_2_14_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph
  gains = wall -4.356974, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph__d0__n0__sel_12,13`
  baseline = None / None
  best_alt = [3, 19] / 011_candidate_alt_d0_n0_r76_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph
  gains = wall None, profile None, child_cb_retry None
  labels = {'missing_baseline': 1}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_3,6`
  baseline = [3, 6] / 022_candidate_selected_d0_n0_3_6_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph
  best_alt = [3, 10] / 023_candidate_alt_d0_n0_r20_3_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph
  gains = wall 7.651044, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph__d0__n0__sel_3,19`
  baseline = [3, 19] / 003_candidate_selected_d0_n0_3_19_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph
  best_alt = [2, 5] / 004_candidate_alt_d0_n0_r44_2_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph
  gains = wall 0.042015, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph__d0__n0__sel_3,5`
  baseline = [3, 5] / 024_candidate_selected_d0_n0_3_5_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph
  best_alt = None / None
  gains = wall None, profile None, child_cb_retry None
  labels = {}
