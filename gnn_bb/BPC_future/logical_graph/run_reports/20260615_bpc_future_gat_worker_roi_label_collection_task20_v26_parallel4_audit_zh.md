# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 5
roi_class_counts = {'negative_primal_roi': 5}
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
    "baseline_columns": 180,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 30,
    "baseline_primal": 740.900563,
    "baseline_rmp_solves": 22,
    "baseline_solving_time": 85.475221,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -37,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "49e19467900df88b",
    "generated_sequences_delta": 19900,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 6,
    "primal_improvement": -1.1017359999999599,
    "rmp_solves_delta": 5,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -0.2963190000000111,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->11:low_risk:2",
      "11->5:low_risk:2",
      "5->10:low_risk:2",
      "10->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      19,
      11,
      5,
      10,
      3
    ],
    "worker_columns": 143,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_49e19467900df88b_19_11_5_10_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 36,
    "worker_primal": 742.002299,
    "worker_rmp_solves": 27,
    "worker_solving_time": 85.178902,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 180,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 30,
    "baseline_primal": 740.900563,
    "baseline_rmp_solves": 22,
    "baseline_solving_time": 85.447697,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -8,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "6190d8b37f2491c2",
    "generated_sequences_delta": -560,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": -0.849884999999972,
    "rmp_solves_delta": 2,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -0.24666299999999808,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->17:low_risk:2",
      "17->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      17,
      3
    ],
    "worker_columns": 172,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_6190d8b37f2491c2_4_17_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 33,
    "worker_primal": 741.750448,
    "worker_rmp_solves": 24,
    "worker_solving_time": 85.201034,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 706.229906,
    "baseline_rmp_solves": 17,
    "baseline_solving_time": 75.714055,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "9a11128d9256c3d8",
    "generated_sequences_delta": 10524,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -0.2681599999999662,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 4.016649000000001,
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->4:low_risk:1",
      "4->16:low_risk:2",
      "16->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_sequence": [
      13,
      4,
      16,
      5
    ],
    "worker_columns": 234,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_9a11128d9256c3d8_13_4_16_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 25,
    "worker_primal": 706.498066,
    "worker_rmp_solves": 18,
    "worker_solving_time": 79.730704,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 706.229906,
    "baseline_rmp_solves": 17,
    "baseline_solving_time": 75.629442,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -9,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "b6675887fb63db55",
    "generated_sequences_delta": 9972,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -1.7895300000000134,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 2.3378859999999975,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      1,
      9,
      5,
      14,
      2
    ],
    "worker_columns": 231,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_09_seed61817_b6675887fb63db55_1_9_5_14_2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 25,
    "worker_primal": 708.019436,
    "worker_rmp_solves": 18,
    "worker_solving_time": 77.967328,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 332,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 625.11877,
    "baseline_rmp_solves": 18,
    "baseline_solving_time": 85.055569,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -26,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "dbddb0163ebb7fd4",
    "generated_sequences_delta": 2305,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -2.856318999999985,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -3.4349060000000122,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_sequence": [
      6,
      18,
      3,
      7
    ],
    "worker_columns": 306,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v26_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_10_seed61923_dbddb0163ebb7fd4_6_18_3_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 25,
    "worker_primal": 627.975089,
    "worker_rmp_solves": 18,
    "worker_solving_time": 81.620663,
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
