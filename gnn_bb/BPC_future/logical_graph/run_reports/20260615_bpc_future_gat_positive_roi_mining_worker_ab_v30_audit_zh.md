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
roi_class_counts = {'negative_primal_roi': 2, 'negative_retry_roi': 1, 'no_observed_roi': 2, 'positive_primal_roi': 1, 'positive_retry_roi': 2}
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
    "baseline_columns": 594,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 39,
    "baseline_primal": 608.525827,
    "baseline_rmp_solves": 31,
    "baseline_solving_time": 76.108989,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "33c54245da27321e",
    "generated_sequences_delta": -143399,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -7.52860299999999,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->17:low_risk:2",
      "17->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      16,
      17,
      19
    ],
    "worker_columns": 594,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33c54245da27321e_16_17_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 39,
    "worker_primal": 608.525827,
    "worker_rmp_solves": 31,
    "worker_solving_time": 68.580386,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 594,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 39,
    "baseline_primal": 608.525827,
    "baseline_rmp_solves": 31,
    "baseline_solving_time": 75.948719,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -12,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "7390856b04698300",
    "generated_sequences_delta": -116624,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20",
    "official_bound_effect": false,
    "pricing_calls_delta": -4,
    "primal_improvement": -3.3248969999999645,
    "rmp_solves_delta": -6,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 9.974443000000008,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      12,
      8,
      16,
      9,
      20
    ],
    "worker_columns": 582,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_12_8_16_9_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 35,
    "worker_primal": 611.850724,
    "worker_rmp_solves": 25,
    "worker_solving_time": 85.923162,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 594,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 39,
    "baseline_primal": 608.525827,
    "baseline_rmp_solves": 31,
    "baseline_solving_time": 76.028383,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "33788d6b7bdf8387",
    "generated_sequences_delta": -161537,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20",
    "official_bound_effect": false,
    "pricing_calls_delta": -3,
    "primal_improvement": -1.8813429999999016,
    "rmp_solves_delta": -3,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -9.674937,
    "target_arc_option_sequence": [
      "0->13:low_energy:1",
      "13->12:low_time:0",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      13,
      12,
      8,
      16,
      9,
      20
    ],
    "worker_columns": 589,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_8_16_9_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 36,
    "worker_primal": 610.40717,
    "worker_rmp_solves": 28,
    "worker_solving_time": 66.353446,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 62,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 84.070453,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "b1fb77954b949bf0",
    "generated_sequences_delta": -76766,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 4.500000000007276e-05,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->12:low_time:0",
      "12->13:low_time:0",
      "13->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_sequence": [
      6,
      12,
      13,
      7,
      17,
      14
    ],
    "worker_columns": 315,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_13_7_17_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 64,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 57,
    "worker_solving_time": 84.070498,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 26,
    "baseline_primal": 565.117882,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 85.059917,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "84ae11479ed592d4",
    "generated_sequences_delta": -51310,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": 0.0073330000000026985,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      13,
      17,
      11,
      5
    ],
    "worker_columns": 389,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 26,
    "worker_primal": 565.117882,
    "worker_rmp_solves": 20,
    "worker_solving_time": 85.06725,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 26,
    "baseline_primal": 565.117882,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 85.117114,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4c81d9ecf77097c9",
    "generated_sequences_delta": 7385,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 1.8199919999999565,
    "rmp_solves_delta": 1,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": -0.06046999999999514,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->4:low_time:0",
      "4->10:low_time:0",
      "10->0:low_energy:1"
    ],
    "target_sequence": [
      8,
      4,
      10
    ],
    "worker_columns": 396,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_8_4_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 28,
    "worker_primal": 563.29789,
    "worker_rmp_solves": 21,
    "worker_solving_time": 85.056644,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 397,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 28,
    "baseline_primal": 505.797935,
    "baseline_rmp_solves": 21,
    "baseline_solving_time": 65.788501,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -43,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "7079ec06a2d9eab3",
    "generated_sequences_delta": 2826,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": 0.19768200000000036,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_time:0"
    ],
    "target_sequence": [
      7,
      12
    ],
    "worker_columns": 354,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_7_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 28,
    "worker_primal": 505.797935,
    "worker_rmp_solves": 22,
    "worker_solving_time": 65.986183,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 69.312627,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "67925c0d2fd4abde",
    "generated_sequences_delta": 14095,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6",
    "official_bound_effect": false,
    "pricing_calls_delta": 5,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 6,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": 0.8238789999999909,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->15:low_risk:2",
      "15->0:low_risk:2"
    ],
    "target_sequence": [
      11,
      15,
      6
    ],
    "worker_columns": 356,
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v30_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 30,
    "worker_primal": 571.707652,
    "worker_rmp_solves": 22,
    "worker_solving_time": 70.136506,
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
