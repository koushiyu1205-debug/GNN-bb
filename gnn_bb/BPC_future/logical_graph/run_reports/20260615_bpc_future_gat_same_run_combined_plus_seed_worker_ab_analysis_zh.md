# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 16
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 3, 'no_observed_roi': 6, 'positive_primal_roi': 6}
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
  },
  {
    "baseline_columns": 337,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": true,
    "baseline_primal": 523.233925,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "8bd56cf157d96aaa",
    "generated_sequences_delta": 2901,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->20:low_time:0",
      "20->0:low_risk:2"
    ],
    "target_sequence": [
      18,
      20,
      11,
      1,
      17
    ],
    "worker_columns": 337,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_8bd56cf157d96aaa_18_20_11_1_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 523.233925,
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
    "columns_delta": -1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "085044441345625f",
    "generated_sequences_delta": 4327,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      20,
      14,
      13
    ],
    "worker_columns": 251,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_085044441345625f_20_14_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 639.119548,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 231,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 569.184782,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 9,
    "exact_pricing_calls_delta": 5,
    "expected_context_hash": "5704f305b764baf5",
    "generated_sequences_delta": 23702,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      1,
      14
    ],
    "worker_columns": 240,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 11,
    "worker_primal": 569.184782,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 231,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 569.184782,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "9d086dc2401550f2",
    "generated_sequences_delta": 11047,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->3:low_risk:2",
      "3->10:low_risk:2",
      "10->11:low_risk:1",
      "11->0:low_risk:2"
    ],
    "target_sequence": [
      9,
      3,
      10,
      11
    ],
    "worker_columns": 225,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_9d086dc2401550f2_9_3_10_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 569.184782,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 231,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_5704f305b764baf5_20_1_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 569.184782,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -13,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "6465dff938f298e1",
    "generated_sequences_delta": 15378,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->1:low_risk:2",
      "1->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      9,
      1,
      12
    ],
    "worker_columns": 218,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_10_seed61919_6465dff938f298e1_9_1_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 569.184782,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 191,
    "baseline_csv": "BPC_future/results/gat_same_run_target_priority_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 677.673076,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "eb76f8c2c929ecb9",
    "generated_sequences_delta": 1000,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5",
    "official_bound_effect": false,
    "primal_improvement": -0.33462499999996,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->0:low_risk:2"
    ],
    "target_sequence": [
      7,
      4,
      5
    ],
    "worker_columns": 185,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_eb76f8c2c929ecb9_7_4_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 678.007701,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 535,
    "baseline_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 14,
    "baseline_fallback_used": false,
    "baseline_primal": 616.937219,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -53,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "8c83e7f0dc9171d5",
    "generated_sequences_delta": -3214,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17",
    "official_bound_effect": false,
    "primal_improvement": 1.4517819999999801,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_sequence": [
      3,
      5,
      10,
      8,
      17
    ],
    "worker_columns": 482,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 13,
    "worker_primal": 615.485437,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 535,
    "baseline_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 14,
    "baseline_fallback_used": true,
    "baseline_primal": 616.937219,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 5,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "12cfa32e4756fd37",
    "generated_sequences_delta": 9067,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10",
    "official_bound_effect": false,
    "primal_improvement": 0.3330320000000029,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->9:low_time:0",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      3,
      9,
      4,
      2,
      10
    ],
    "worker_columns": 540,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 13,
    "worker_primal": 616.604187,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 535,
    "baseline_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 14,
    "baseline_fallback_used": true,
    "baseline_primal": 616.937219,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -5,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "c4004463c80918b5",
    "generated_sequences_delta": 8716,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10",
    "official_bound_effect": false,
    "primal_improvement": 0.3330320000000029,
    "roi_class": "positive_primal_roi",
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
      4,
      2,
      10
    ],
    "worker_columns": 530,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 14,
    "worker_primal": 616.604187,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 535,
    "baseline_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 14,
    "baseline_fallback_used": true,
    "baseline_primal": 616.937219,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -41,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "4d45ffb07ab7073b",
    "generated_sequences_delta": -8016,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_4d45ffb07ab7073b_12_13_4_10_17",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      12,
      13,
      4,
      10,
      17
    ],
    "worker_columns": 494,
    "worker_csv": "BPC_future/results/gat_same_run_seed_apollo_high_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_4d45ffb07ab7073b_12_13_4_10_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 13,
    "worker_primal": 616.937219,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
