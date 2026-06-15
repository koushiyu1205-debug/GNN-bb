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
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 1, 'negative_retry_roi': 2, 'positive_primal_roi': 3, 'positive_retry_roi': 1}
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
    "baseline_columns": 336,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 561.030445,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 63.03761,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "048e5f66efcd12df",
    "generated_sequences_delta": 95,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.0032860000000027867,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_sequence": [
      2,
      10,
      19,
      9,
      1
    ],
    "worker_columns": 339,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 26,
    "worker_primal": 561.030445,
    "worker_rmp_solves": 20,
    "worker_solving_time": 63.034324,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.602168,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -108,
    "exact_pricing_calls_delta": -3,
    "expected_context_hash": "3d1bd8618099b573",
    "generated_sequences_delta": 23300,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 5,
    "primal_improvement": -1.4553480000000718,
    "rmp_solves_delta": 8,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -3.261802000000003,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      8,
      11,
      10,
      17
    ],
    "worker_columns": 223,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 23,
    "worker_primal": 632.69392,
    "worker_rmp_solves": 17,
    "worker_solving_time": 62.340366,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.515561,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -28,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 3156,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -7.6552970000000045,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      19,
      10,
      17
    ],
    "worker_columns": 303,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 631.238572,
    "worker_rmp_solves": 10,
    "worker_solving_time": 57.860264,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 63,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 85.06122,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "7fcd171c2901efb5",
    "generated_sequences_delta": 18492,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.0037540000000007012,
    "target_arc_option_sequence": [
      "0->6:low_energy:1",
      "6->12:low_energy:1",
      "12->13:low_time:0",
      "13->8:low_time:0",
      "8->15:low_energy:1",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_sequence": [
      6,
      12,
      13,
      8,
      15,
      3
    ],
    "worker_columns": 315,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 65,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 57,
    "worker_solving_time": 85.064974,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 446,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 38,
    "baseline_primal": 537.830843,
    "baseline_rmp_solves": 32,
    "baseline_solving_time": 85.076165,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 11,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "generated_sequences_delta": 39531,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19",
    "official_bound_effect": false,
    "pricing_calls_delta": 10,
    "primal_improvement": 2.650588999999968,
    "rmp_solves_delta": 9,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": -15.741459000000006,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_sequence": [
      18,
      3,
      13,
      6,
      19
    ],
    "worker_columns": 457,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 48,
    "worker_primal": 535.180254,
    "worker_rmp_solves": 41,
    "worker_solving_time": 69.334706,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.517889,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 11,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "17ccb5dc2e9bbac0",
    "generated_sequences_delta": 2887,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "columns_only_roi",
    "solving_time_delta": -5.873436999999996,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->5:low_energy:1",
      "5->0:low_energy:1"
    ],
    "target_sequence": [
      20,
      5,
      6,
      3
    ],
    "worker_columns": 342,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 19,
    "worker_primal": 631.238572,
    "worker_rmp_solves": 10,
    "worker_solving_time": 59.644452,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 446,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 38,
    "baseline_primal": 537.830843,
    "baseline_rmp_solves": 32,
    "baseline_solving_time": 85.102402,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "fd0697a8f685dbe7",
    "generated_sequences_delta": -34988,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 2.650588999999968,
    "rmp_solves_delta": 0,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": -12.420783999999998,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->15:low_time:0",
      "15->1:low_time:0",
      "1->7:low_time:0",
      "7->17:low_time:0",
      "17->0:low_time:0"
    ],
    "target_sequence": [
      12,
      15,
      1,
      7,
      17,
      14
    ],
    "worker_columns": 446,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 40,
    "worker_primal": 535.180254,
    "worker_rmp_solves": 32,
    "worker_solving_time": 72.681618,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 325,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 20,
    "baseline_primal": 568.697653,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 64.186636,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "02259d538b5f4b8d",
    "generated_sequences_delta": 4404,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 10.185688999999911,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 1.403359000000009,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      8,
      13,
      3,
      9,
      15
    ],
    "worker_columns": 325,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 23,
    "worker_primal": 558.511964,
    "worker_rmp_solves": 14,
    "worker_solving_time": 65.589995,
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
