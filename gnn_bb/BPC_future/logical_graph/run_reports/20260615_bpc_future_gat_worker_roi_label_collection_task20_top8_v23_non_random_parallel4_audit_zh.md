# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 8
roi_class_counts = {'negative_primal_roi': 3, 'negative_retry_roi': 2, 'positive_primal_roi': 3}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Records

```json
[
  {
    "baseline_columns": 446,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 38,
    "baseline_primal": 537.830843,
    "baseline_rmp_solves": 32,
    "baseline_solving_time": 85.078908,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -7,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "7db256d4f7224cc6",
    "generated_sequences_delta": 8441,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 2.650588999999968,
    "rmp_solves_delta": 1,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": -0.010661999999996397,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->20:low_risk:1",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      12,
      20,
      5,
      3,
      6,
      4
    ],
    "worker_columns": 439,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 40,
    "worker_primal": 535.180254,
    "worker_rmp_solves": 33,
    "worker_solving_time": 85.068246,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 325,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 20,
    "baseline_primal": 568.697653,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 63.970947,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -80,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "9fadf4f7b39742a2",
    "generated_sequences_delta": 2786,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10",
    "official_bound_effect": false,
    "pricing_calls_delta": -1,
    "primal_improvement": 9.56736699999999,
    "rmp_solves_delta": 1,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": -8.168598000000003,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_sequence": [
      1,
      7,
      20,
      4,
      10
    ],
    "worker_columns": 245,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 19,
    "worker_primal": 559.130286,
    "worker_rmp_solves": 13,
    "worker_solving_time": 55.802349,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 325,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 20,
    "baseline_primal": 568.697653,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 64.059496,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -36,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "1f855fbf33f8155e",
    "generated_sequences_delta": 5474,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 9.88040199999989,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 1.2429360000000003,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      8,
      1,
      3,
      9,
      15
    ],
    "worker_columns": 289,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 22,
    "worker_primal": 558.817251,
    "worker_rmp_solves": 14,
    "worker_solving_time": 65.302432,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 334,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 27,
    "baseline_primal": 479.023574,
    "baseline_rmp_solves": 22,
    "baseline_solving_time": 85.059446,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -11,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "eb102a126dd0d5e3",
    "generated_sequences_delta": 15659,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": -3.6722750000000133,
    "rmp_solves_delta": 2,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -0.005668999999997482,
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->10:low_risk:2",
      "10->4:low_time:0",
      "4->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_sequence": [
      9,
      10,
      4,
      14,
      1
    ],
    "worker_columns": 323,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 31,
    "worker_primal": 482.695849,
    "worker_rmp_solves": 24,
    "worker_solving_time": 85.053777,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 293,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 28,
    "baseline_primal": 516.980503,
    "baseline_rmp_solves": 21,
    "baseline_solving_time": 85.604785,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "22dec9cfc13bb3d6",
    "generated_sequences_delta": 7530,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.07910700000000759,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->8:low_risk:2",
      "8->20:low_risk:2",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      7,
      8,
      20,
      3
    ],
    "worker_columns": 291,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 30,
    "worker_primal": 516.980503,
    "worker_rmp_solves": 22,
    "worker_solving_time": 85.525678,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 399,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 27,
    "baseline_primal": 563.295017,
    "baseline_rmp_solves": 21,
    "baseline_solving_time": 84.064907,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "84ae11479ed592d4",
    "generated_sequences_delta": -10817,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -1.8228649999999789,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.9836169999999953,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_sequence": [
      13,
      17,
      11,
      4,
      10
    ],
    "worker_columns": 396,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 27,
    "worker_primal": 565.117882,
    "worker_rmp_solves": 21,
    "worker_solving_time": 85.048524,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 334,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 27,
    "baseline_primal": 479.023574,
    "baseline_rmp_solves": 22,
    "baseline_solving_time": 85.05129,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "39d7643d5a478407",
    "generated_sequences_delta": 8850,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.010358000000010747,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_sequence": [
      7,
      14,
      3,
      5
    ],
    "worker_columns": 334,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 29,
    "worker_primal": 479.023574,
    "worker_rmp_solves": 23,
    "worker_solving_time": 85.061648,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 399,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 27,
    "baseline_primal": 563.295017,
    "baseline_rmp_solves": 21,
    "baseline_solving_time": 84.182406,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4c81d9ecf77097c9",
    "generated_sequences_delta": 44805,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": -0.8322979999999234,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.883931000000004,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->13:low_risk:2",
      "13->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_sequence": [
      3,
      13,
      17,
      8,
      4,
      10
    ],
    "worker_columns": 396,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 28,
    "worker_primal": 564.127315,
    "worker_rmp_solves": 21,
    "worker_solving_time": 85.066337,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `positive_retry_roi` / `positive_pricing_roi` 表示 primal 不变差且后续 pricing/retry 负担下降；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
