# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 4
roi_class_counts = {'negative_primal_roi': 1, 'negative_retry_roi': 3}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = false
```

## Records

```json
[
  {
    "baseline_columns": 406,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_20_17_10_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 633.782745,
    "baseline_rmp_solves": 8,
    "baseline_solving_time": 72.631824,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "da555dc83edc174c",
    "generated_sequences_delta": 13332,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_20_17_10_13",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 4.111049000000008,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->10:low_risk:2",
      "10->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_sequence": [
      20,
      17,
      10,
      13
    ],
    "worker_columns": 401,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_20_17_10_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 17,
    "worker_primal": 633.782745,
    "worker_rmp_solves": 9,
    "worker_solving_time": 76.742873,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.01496,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 4,
    "expected_context_hash": "e897b76f2888f822",
    "generated_sequences_delta": 8374,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9",
    "official_bound_effect": false,
    "pricing_calls_delta": 7,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 3,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 13.885815999999991,
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_sequence": [
      17,
      11,
      14,
      9
    ],
    "worker_columns": 382,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 12,
    "worker_pricing_calls": 22,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 10,
    "worker_solving_time": 67.900776,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 253,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_1b5a36a64a700b58_2_4_7_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 609.458605,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 82.842026,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -4,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "1b5a36a64a700b58",
    "generated_sequences_delta": 6827,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_1b5a36a64a700b58_2_4_7_12",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -0.08149199999991197,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 2.80151699999999,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      2,
      4,
      7,
      12
    ],
    "worker_columns": 249,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_1b5a36a64a700b58_2_4_7_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 25,
    "worker_primal": 609.540097,
    "worker_rmp_solves": 17,
    "worker_solving_time": 85.643543,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.080594,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 4,
    "expected_context_hash": "08b8d772e2ab9623",
    "generated_sequences_delta": 7379,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18",
    "official_bound_effect": false,
    "pricing_calls_delta": 7,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 3,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 11.721286,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->16:low_risk:2",
      "16->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_sequence": [
      8,
      16,
      11,
      15,
      18
    ],
    "worker_columns": 379,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v14_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 12,
    "worker_pricing_calls": 22,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 10,
    "worker_solving_time": 65.80188,
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
