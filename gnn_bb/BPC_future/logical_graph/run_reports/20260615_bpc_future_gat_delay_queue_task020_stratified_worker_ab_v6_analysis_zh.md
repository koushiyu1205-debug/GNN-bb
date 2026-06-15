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
roi_class_counts = {'negative_primal_roi': 2, 'no_observed_roi': 2}
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
    "baseline_columns": 284,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3a059da228ba2c81_12_2_1_5_7_3_8_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 596.911574,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "3a059da228ba2c81",
    "generated_sequences_delta": 5907,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3a059da228ba2c81_12_2_1_5_7_3_8",
    "official_bound_effect": false,
    "primal_improvement": -1.2802720000000818,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->2:low_risk:1",
      "2->1:low_time:0",
      "1->5:low_time:0",
      "5->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_sequence": [
      12,
      2,
      1,
      5,
      7,
      3,
      8
    ],
    "worker_columns": 284,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3a059da228ba2c81_12_2_1_5_7_3_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 598.191846,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 445,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_805e5fc463a05fb8_2_11_13_3_9_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 546.898087,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -13,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "805e5fc463a05fb8",
    "generated_sequences_delta": -91016,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_805e5fc463a05fb8_2_11_13_3_9_12",
    "official_bound_effect": false,
    "primal_improvement": -1.9959629999999606,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->11:low_time:0",
      "11->13:low_time:0",
      "13->3:low_risk:1",
      "3->9:low_time:0",
      "9->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      2,
      11,
      13,
      3,
      9,
      12
    ],
    "worker_columns": 432,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_805e5fc463a05fb8_2_11_13_3_9_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 548.89405,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 432,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_38ffc02bc19f2143_13_8_11_9_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 515.705063,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -7,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "38ffc02bc19f2143",
    "generated_sequences_delta": -37,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_38ffc02bc19f2143_13_8_11_9_5",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->8:low_time:0",
      "8->11:low_energy:1",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      13,
      8,
      11,
      9,
      5
    ],
    "worker_columns": 425,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_38ffc02bc19f2143_13_8_11_9_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 515.705063,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_66de5b1da5c5614e_11_9_5_16_6_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 644.548686,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "66de5b1da5c5614e",
    "generated_sequences_delta": -33301,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_66de5b1da5c5614e_11_9_5_16_6_19",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->9:low_time:0",
      "9->5:low_time:0",
      "5->16:low_risk:1",
      "16->6:low_risk:2",
      "6->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      11,
      9,
      5,
      16,
      6,
      19
    ],
    "worker_columns": 329,
    "worker_csv": "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_66de5b1da5c5614e_11_9_5_16_6_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 644.548686,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
