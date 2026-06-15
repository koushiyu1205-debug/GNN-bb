# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 9
roi_class_counts = {'columns_only_roi': 1, 'negative_retry_roi': 3, 'no_observed_roi': 1, 'positive_primal_roi': 3, 'positive_retry_roi': 1}
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
    "baseline_columns": 324,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 19,
    "baseline_primal": 469.31962,
    "baseline_rmp_solves": 14,
    "baseline_solving_time": 59.051289,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -8,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "577b70605147a3cd",
    "generated_sequences_delta": 3525,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 4.959271999999999,
    "target_arc_option_sequence": [
      "0->15:low_time:0",
      "15->0:low_time:0"
    ],
    "target_sequence": [
      15,
      9,
      10,
      1
    ],
    "worker_columns": 316,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 23,
    "worker_primal": 469.31962,
    "worker_rmp_solves": 16,
    "worker_solving_time": 64.010561,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 205,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 714.637579,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 59.257715,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -15,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "b9550ffc9a42531a",
    "generated_sequences_delta": 14079,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 5,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -2.796369999999996,
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_sequence": [
      13,
      20,
      7
    ],
    "worker_columns": 190,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 22,
    "worker_primal": 714.637579,
    "worker_rmp_solves": 15,
    "worker_solving_time": 56.461345,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 843.939853,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 64.803382,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -36,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "476979944ba39894",
    "generated_sequences_delta": 49085,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2",
    "official_bound_effect": false,
    "pricing_calls_delta": 7,
    "primal_improvement": 56.48128899999995,
    "rmp_solves_delta": 6,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 5.908870000000007,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->2:low_risk:2",
      "2->0:low_risk:2"
    ],
    "target_sequence": [
      12,
      2
    ],
    "worker_columns": 125,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 23,
    "worker_primal": 787.458564,
    "worker_rmp_solves": 17,
    "worker_solving_time": 70.712252,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 843.939853,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 64.623328,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 9,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "95e9afaf1ecbdc5e",
    "generated_sequences_delta": 20006,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": 61.28254700000002,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 2.787993,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->13:low_time:0",
      "13->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      13,
      5
    ],
    "worker_columns": 170,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 20,
    "worker_primal": 782.657306,
    "worker_rmp_solves": 13,
    "worker_solving_time": 67.411321,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 52.827276,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ac056820151e9ad7",
    "generated_sequences_delta": 2227,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.24530299999999983,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      20,
      16
    ],
    "worker_columns": 233,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 16,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 10,
    "worker_solving_time": 53.072579,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 673.976604,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 52.197816,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4e481a6307fca228",
    "generated_sequences_delta": 2395,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 0.11635799999999108,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 0.6577709999999968,
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->4:low_energy:1",
      "4->7:low_energy:1",
      "7->0:low_energy:1"
    ],
    "target_sequence": [
      11,
      4,
      7
    ],
    "worker_columns": 255,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 16,
    "worker_primal": 673.860246,
    "worker_rmp_solves": 9,
    "worker_solving_time": 52.855587,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.819205,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 10,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": 2900,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "columns_only_roi",
    "solving_time_delta": 0.4278890000000004,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      16,
      19
    ],
    "worker_columns": 228,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 14,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 7,
    "worker_solving_time": 53.247094,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.709084,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -39,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b095fbae18116443",
    "generated_sequences_delta": 1,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.09563099999999736,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->8:low_risk:2",
      "8->3:low_risk:2",
      "3->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_sequence": [
      20,
      8,
      3,
      18
    ],
    "worker_columns": 179,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 13,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 6,
    "worker_solving_time": 52.613453,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.680833,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 17,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "a4f29d238b2963df",
    "generated_sequences_delta": 2929,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.4626700000000028,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_risk:1"
    ],
    "target_sequence": [
      2,
      20,
      8,
      3
    ],
    "worker_columns": 235,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 15,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 7,
    "worker_solving_time": 53.143503,
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
