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
roi_class_counts = {'negative_primal_roi': 1, 'no_observed_roi': 1}
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
    "baseline_columns": 231,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_b96b7ed8e3d18bbd_5_6_17_8_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 702.537472,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -15,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "b96b7ed8e3d18bbd",
    "generated_sequences_delta": 34509,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_b96b7ed8e3d18bbd_5_6_17_8",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->6:low_risk:2",
      "6->0:low_time:0"
    ],
    "target_sequence": [
      5,
      6,
      17,
      8
    ],
    "worker_columns": 216,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_b96b7ed8e3d18bbd_5_6_17_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 702.537472,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 266,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_b89320d8a5148225_5_7_1_16_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 552.21958,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -12,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b89320d8a5148225",
    "generated_sequences_delta": 2,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_b89320d8a5148225_5_7_1_16_3",
    "official_bound_effect": false,
    "primal_improvement": -10.643286000000103,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->7:low_risk:2",
      "7->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      7,
      1,
      16,
      3
    ],
    "worker_columns": 254,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_b89320d8a5148225_5_7_1_16_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 562.862866,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
