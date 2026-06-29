# Journey Paired Probe Summary

日期：2026-06-28

## Boundary

This report only summarizes already completed paired replay probes. It does not run BPC / pricing / RMP, and it does not create official bounds or certificates.

## Summary

```text
entry_count = 72
paired_group_count = 24
baseline_entry_count = 24
alternative_entry_count = 48
result_available_entry_count = 72
missing_result_entry_count = 0
observed_alternative_entry_count = 48
label_counts = {'neutral_proxy': 33, 'positive_proxy': 2, 'hard_negative_proxy': 13}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## Groups

- `apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_12,20`
  baseline = [12, 20] / 025_candidate_selected_d0_n0_12_20_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph
  best_alt = [6, 9] / 026_candidate_alt_d0_n0_r4_6_9_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph
  gains = wall 0.001301, profile 0.0, child_cb_retry -3.0
  labels = {'neutral_proxy': 1, 'hard_negative_proxy': 1}
- `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph__d1__n2__sel_4,12`
  baseline = [4, 12] / 043_candidate_selected_d1_n2_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph
  best_alt = [12, 16] / 045_candidate_alt_d1_n2_r8_12_16_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph
  gains = wall -5.86095, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph__d0__n0__sel_4,7`
  baseline = [4, 7] / 016_candidate_selected_d0_n0_4_7_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph
  best_alt = [1, 4] / 018_candidate_alt_d0_n0_r9_1_4_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph
  gains = wall 0.251898, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph__d0__n0__sel_4,19`
  baseline = [4, 19] / 046_candidate_selected_d0_n0_4_19_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph
  best_alt = [2, 6] / 047_candidate_alt_d0_n0_r7_2_6_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph
  gains = wall -12.12342, profile 0.0, child_cb_retry 0.0
  labels = {'hard_negative_proxy': 2}
- `apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph__d0__n0__sel_4,12`
  baseline = [4, 12] / 028_candidate_selected_d0_n0_4_12_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph
  best_alt = [6, 15] / 030_candidate_alt_d0_n0_r3_6_15_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph
  gains = wall 102.684275, profile 0.0, child_cb_retry 6.0
  labels = {'hard_negative_proxy': 1, 'positive_proxy': 1}
- `apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph__d0__n0__sel_8,18`
  baseline = [8, 18] / 007_candidate_selected_d0_n0_8_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph
  best_alt = [17, 18] / 008_candidate_alt_d0_n0_r3_17_18_apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph
  gains = wall 33.891568, profile 0.0, child_cb_retry 5.0
  labels = {'positive_proxy': 1, 'neutral_proxy': 1}
- `apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph__d1__n2__sel_5,8`
  baseline = [5, 8] / 001_candidate_selected_d1_n2_5_8_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph
  best_alt = [8, 15] / 003_candidate_alt_d1_n2_r1_8_15_apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph
  gains = wall 21.773378, profile 0.0, child_cb_retry 5.0
  labels = {'neutral_proxy': 2}
- `apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph__d0__n0__sel_2,5`
  baseline = [2, 5] / 067_candidate_selected_d0_n0_2_5_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph
  best_alt = [4, 9] / 068_candidate_alt_d0_n0_r5_4_9_apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph
  gains = wall 0.156469, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph__d1__n2__sel_3,5`
  baseline = [3, 5] / 034_candidate_selected_d1_n2_3_5_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph
  best_alt = [10, 14] / 036_candidate_alt_d1_n2_r3_10_14_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph
  gains = wall 0.000768, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph__d1__n1__sel_1,2`
  baseline = [1, 2] / 013_candidate_selected_d1_n1_1_2_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph
  best_alt = [3, 15] / 014_candidate_alt_d1_n1_r12_3_15_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph
  gains = wall 20.249882, profile 0.0, child_cb_retry 5.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph__d1__n2__sel_1,4`
  baseline = [1, 4] / 022_candidate_selected_d1_n2_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph
  best_alt = [4, 5] / 024_candidate_alt_d1_n2_r5_4_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph
  gains = wall 20.761374, profile 0.0, child_cb_retry 5.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph__d0__n0__sel_5,9`
  baseline = [5, 9] / 031_candidate_selected_d0_n0_5_9_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph
  best_alt = [5, 14] / 033_candidate_alt_d0_n0_r4_5_14_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph
  gains = wall 19.322706, profile 0.0, child_cb_retry 0.0
  labels = {'hard_negative_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph__d0__n0__sel_6,20`
  baseline = [6, 20] / 055_candidate_selected_d0_n0_6_20_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph
  best_alt = [13, 16] / 056_candidate_alt_d0_n0_r3_13_16_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph
  gains = wall -140.280573, profile 0.0, child_cb_retry -14.0
  labels = {'hard_negative_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph__d0__n0__sel_4,7`
  baseline = [4, 7] / 010_candidate_selected_d0_n0_4_7_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph
  best_alt = [7, 8] / 011_candidate_alt_d0_n0_r4_7_8_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph
  gains = wall 19.082443, profile 0.0, child_cb_retry 5.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph__d2__n5__sel_2,5`
  baseline = [2, 5] / 004_candidate_selected_d2_n5_2_5_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph
  best_alt = [2, 12] / 005_candidate_alt_d2_n5_r1_2_12_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph
  gains = wall 29.792059, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph__d0__n0__sel_1,4`
  baseline = [1, 4] / 037_candidate_selected_d0_n0_1_4_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph
  best_alt = [2, 19] / 038_candidate_alt_d0_n0_r6_2_19_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph
  gains = wall 0.36628, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph__d1__n1__sel_2,17`
  baseline = [2, 17] / 049_candidate_selected_d1_n1_2_17_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph
  best_alt = [3, 18] / 050_candidate_alt_d1_n1_r3_3_18_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph
  gains = wall 10.367869, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 1, 'hard_negative_proxy': 1}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph__d1__n1__sel_3,6`
  baseline = [3, 6] / 052_candidate_selected_d1_n1_3_6_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph
  best_alt = [3, 19] / 053_candidate_alt_d1_n1_r2_3_19_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph
  gains = wall 0.047303, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph__d0__n0__sel_1,2`
  baseline = [1, 2] / 061_candidate_selected_d0_n0_1_2_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph
  best_alt = [1, 18] / 062_candidate_alt_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph
  gains = wall 4.135092, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph__d2__n6__sel_1,3`
  baseline = [1, 3] / 058_candidate_selected_d2_n6_1_3_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph
  best_alt = [7, 11] / 060_candidate_alt_d2_n6_r4_7_11_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph
  gains = wall 15.302147, profile 0.0, child_cb_retry 5.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph__d2__n4__sel_6,10`
  baseline = [6, 10] / 019_candidate_selected_d2_n4_6_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph
  best_alt = [8, 10] / 020_candidate_alt_d2_n4_r4_8_10_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph
  gains = wall 4.854934, profile 0.0, child_cb_retry 2.0
  labels = {'hard_negative_proxy': 2}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph__d0__n0__sel_12,13`
  baseline = [12, 13] / 064_candidate_selected_d0_n0_12_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph
  best_alt = [9, 13] / 066_candidate_alt_d0_n0_r2_9_13_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph
  gains = wall -105.714978, profile 0.0, child_cb_retry -8.0
  labels = {'hard_negative_proxy': 2}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph__d2__n4__sel_6,20`
  baseline = [6, 20] / 070_candidate_selected_d2_n4_6_20_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph
  best_alt = [4, 7] / 071_candidate_alt_d2_n4_r2_4_7_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph
  gains = wall 3.206217, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
- `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph__d2__n3__sel_1,8`
  baseline = [1, 8] / 040_candidate_selected_d2_n3_1_8_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph
  best_alt = [1, 17] / 042_candidate_alt_d2_n3_r2_1_17_tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph
  gains = wall 0.819134, profile 0.0, child_cb_retry 0.0
  labels = {'neutral_proxy': 2}
