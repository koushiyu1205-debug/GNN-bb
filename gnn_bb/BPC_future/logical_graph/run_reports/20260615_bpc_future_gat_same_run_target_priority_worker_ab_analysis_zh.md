# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 6
roi_class_counts = {'negative_primal_roi': 2, 'no_observed_roi': 1, 'positive_primal_roi': 3}
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
    "baseline_columns": 337,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 523.233925,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 4,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "587e2ac350a8619b",
    "generated_sequences_delta": 5424,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14",
    "official_bound_effect": false,
    "primal_improvement": 3.820515999999998,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_sequence": [
      3,
      9,
      11,
      14
    ],
    "worker_columns": 341,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 519.413409,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 252,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 639.119548,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -35,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "ea2f1344458c548f",
    "generated_sequences_delta": 8727,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11",
    "official_bound_effect": false,
    "primal_improvement": -4.358571999999981,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      1,
      11
    ],
    "worker_columns": 217,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 643.47812,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 252,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": true,
    "baseline_primal": 639.119548,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 7,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "09187873900ecefa",
    "generated_sequences_delta": 4206,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16",
    "official_bound_effect": false,
    "primal_improvement": 0.652150000000006,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      6,
      20,
      4,
      16
    ],
    "worker_columns": 259,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 638.467398,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 252,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": true,
    "baseline_primal": 639.119548,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "39ec05e43b291642",
    "generated_sequences_delta": 4380,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9",
    "official_bound_effect": false,
    "primal_improvement": -1.1803939999999784,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      20,
      1,
      16,
      9
    ],
    "worker_columns": 247,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 640.299942,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 191,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 677.673076,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b46cdc0f247ab6e3",
    "generated_sequences_delta": -143,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13",
    "official_bound_effect": false,
    "primal_improvement": 2.191962999999987,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_sequence": [
      7,
      8,
      2,
      13
    ],
    "worker_columns": 186,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 675.481113,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 157,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 740.299496,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "3a9af4966d4b91d5",
    "generated_sequences_delta": 4889,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      8,
      18,
      12
    ],
    "worker_columns": 156,
    "worker_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 740.299496,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
