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
roi_class_counts = {'negative_primal_roi': 1, 'negative_retry_roi': 4, 'no_observed_roi': 1, 'positive_retry_roi': 2}
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
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 69.154576,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "2d1da4555bf67a8c",
    "generated_sequences_delta": 91,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -1.1480829999999997,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->12:low_risk:2",
      "12->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_sequence": [
      19,
      12,
      5,
      18
    ],
    "worker_columns": 376,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 25,
    "worker_primal": 571.707652,
    "worker_rmp_solves": 16,
    "worker_solving_time": 68.006493,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 302,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 579.577707,
    "baseline_rmp_solves": 18,
    "baseline_solving_time": 62.050537,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "7714263901aeb2ec",
    "generated_sequences_delta": 2480,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.4425560000000033,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_risk:2"
    ],
    "target_sequence": [
      3,
      20,
      16,
      17
    ],
    "worker_columns": 302,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 25,
    "worker_primal": 579.577707,
    "worker_rmp_solves": 19,
    "worker_solving_time": 62.493093,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 68.982041,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "5d9c7e881a00ee06",
    "generated_sequences_delta": 2465,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.4423129999999986,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      1,
      10,
      18,
      9
    ],
    "worker_columns": 371,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 27,
    "worker_primal": 571.707652,
    "worker_rmp_solves": 17,
    "worker_solving_time": 69.424354,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 69.014885,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "6cbf8d7c2c4fe23f",
    "generated_sequences_delta": 2380,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.5405269999999973,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      1,
      4,
      18,
      9
    ],
    "worker_columns": 376,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 27,
    "worker_primal": 571.707652,
    "worker_rmp_solves": 17,
    "worker_solving_time": 69.555412,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 480,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 34,
    "baseline_primal": 616.937219,
    "baseline_rmp_solves": 25,
    "baseline_solving_time": 85.06879,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 7,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "c4004463c80918b5",
    "generated_sequences_delta": -83440,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": -1.0682399999999461,
    "rmp_solves_delta": 3,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -1.0035250000000104,
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      9,
      3,
      20,
      11,
      4,
      8,
      10
    ],
    "worker_columns": 487,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 37,
    "worker_primal": 618.005459,
    "worker_rmp_solves": 28,
    "worker_solving_time": 84.065265,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 480,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 34,
    "baseline_primal": 616.937219,
    "baseline_rmp_solves": 25,
    "baseline_solving_time": 85.063194,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "12cfa32e4756fd37",
    "generated_sequences_delta": 1534,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.0013780000000025439,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->9:low_time:0",
      "9->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_sequence": [
      3,
      9,
      7,
      11,
      4,
      2,
      8
    ],
    "worker_columns": 479,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 36,
    "worker_primal": 616.937219,
    "worker_rmp_solves": 26,
    "worker_solving_time": 85.061816,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 63,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 85.062649,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "b1fb77954b949bf0",
    "generated_sequences_delta": -110235,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17",
    "official_bound_effect": false,
    "pricing_calls_delta": -2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": -1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -0.001409999999992806,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->12:low_time:0",
      "12->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_sequence": [
      6,
      12,
      7,
      16,
      17
    ],
    "worker_columns": 309,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 61,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 55,
    "worker_solving_time": 85.061239,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.564551,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -21,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "dfd68d5873b84183",
    "generated_sequences_delta": 10,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12",
    "official_bound_effect": false,
    "pricing_calls_delta": -1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -10.744606999999995,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      20,
      1,
      17,
      12
    ],
    "worker_columns": 310,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 17,
    "worker_primal": 631.238572,
    "worker_rmp_solves": 9,
    "worker_solving_time": 54.819944,
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
