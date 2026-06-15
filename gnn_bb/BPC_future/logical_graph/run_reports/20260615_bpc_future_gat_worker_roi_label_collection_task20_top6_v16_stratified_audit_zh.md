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
roi_class_counts = {'negative_primal_roi': 2, 'negative_retry_roi': 3, 'no_observed_roi': 1}
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
    "baseline_columns": 253,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 609.458605,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 85.361103,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4575716b3939cb89",
    "generated_sequences_delta": 4877,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.14538399999999285,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->19:low_energy:1",
      "19->9:low_risk:2",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      3,
      19,
      9,
      12
    ],
    "worker_columns": 250,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 25,
    "worker_primal": 609.458605,
    "worker_rmp_solves": 17,
    "worker_solving_time": 85.215719,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 253,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 609.458605,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 85.207747,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ff6827bb236f4831",
    "generated_sequences_delta": -925,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -11.519689999999969,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.14479199999999537,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->18:low_time:0",
      "18->8:low_risk:2",
      "8->7:low_time:0",
      "7->9:low_energy:1",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ],
    "worker_columns": 254,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 25,
    "worker_primal": 620.978295,
    "worker_rmp_solves": 17,
    "worker_solving_time": 85.352539,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.024115,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 4,
    "expected_context_hash": "9eb0dc7839bf91ec",
    "generated_sequences_delta": 8177,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18",
    "official_bound_effect": false,
    "pricing_calls_delta": 7,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 3,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 10.218017999999994,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      2,
      17,
      16,
      13,
      18
    ],
    "worker_columns": 384,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 12,
    "worker_pricing_calls": 22,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 10,
    "worker_solving_time": 64.242133,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 401,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 17,
    "baseline_primal": 633.782745,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 76.571246,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "ec59d1f203f1630c",
    "generated_sequences_delta": 1891,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.0752080000000035,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      15,
      1,
      13
    ],
    "worker_columns": 401,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 17,
    "worker_primal": 633.782745,
    "worker_rmp_solves": 9,
    "worker_solving_time": 76.496038,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 68.898148,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -24,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "67925c0d2fd4abde",
    "generated_sequences_delta": 8762,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": -1.1302819999999656,
    "rmp_solves_delta": 4,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.33304599999999596,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->16:low_risk:2",
      "16->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16,
      1,
      7
    ],
    "worker_columns": 352,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 28,
    "worker_primal": 572.837934,
    "worker_rmp_solves": 20,
    "worker_solving_time": 69.231194,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 336,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 561.030445,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 62.933416,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "f4e732e2cfdeea6e",
    "generated_sequences_delta": 102,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.01775100000000407,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      12,
      18,
      17
    ],
    "worker_columns": 339,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top6_v16_stratified_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 26,
    "worker_primal": 561.030445,
    "worker_rmp_solves": 20,
    "worker_solving_time": 62.915665,
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
