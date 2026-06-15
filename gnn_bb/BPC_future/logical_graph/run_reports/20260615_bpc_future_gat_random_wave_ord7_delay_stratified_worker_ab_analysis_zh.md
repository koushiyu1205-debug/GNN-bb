# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 2
roi_class_counts = {'columns_only_roi': 1, 'no_observed_roi': 1}
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
    "baseline_columns": 160,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord7_delay_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_92c5b0ad3f98c8a5_17_18_14_5_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 642.358116,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "92c5b0ad3f98c8a5",
    "generated_sequences_delta": 39628,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_92c5b0ad3f98c8a5_17_18_14_5_3",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->17:low_risk:2",
      "17->18:low_risk:2",
      "18->14:low_risk:2",
      "14->5:low_risk:2",
      "5->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      17,
      18,
      14,
      5,
      3
    ],
    "worker_columns": 163,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_delay_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_92c5b0ad3f98c8a5_17_18_14_5_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 642.358116,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 470,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord7_delay_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_dc68e76c2134eaa8_16_4_15_19_12_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 548.335796,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "dc68e76c2134eaa8",
    "generated_sequences_delta": 7331,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_dc68e76c2134eaa8_16_4_15_19_12_11",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->4:low_risk:2",
      "4->15:low_risk:2",
      "15->19:low_time:0",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      4,
      15,
      19,
      12,
      11
    ],
    "worker_columns": 470,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_delay_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_dc68e76c2134eaa8_16_4_15_19_12_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_primal": 548.335796,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
