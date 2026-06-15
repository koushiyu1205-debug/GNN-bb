# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 3
roi_class_counts = {'no_observed_roi': 3}
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
    "baseline_columns": 470,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_96c5f5928a47fe72_16_4_19_12_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 548.335796,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -52,
    "exact_pricing_calls_delta": -3,
    "expected_context_hash": "96c5f5928a47fe72",
    "generated_sequences_delta": 74757,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_96c5f5928a47fe72_16_4_19_12_20",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->4:low_time:0",
      "4->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      4,
      19,
      12,
      20
    ],
    "worker_columns": 418,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_96c5f5928a47fe72_16_4_19_12_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 548.335796,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 470,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_fc8f27326a163867_16_15_19_6_12_11_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 548.335796,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -39,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "fc8f27326a163867",
    "generated_sequences_delta": 21030,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_fc8f27326a163867_16_15_19_6_12_11_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->16:low_risk:1",
      "16->15:low_risk:2",
      "15->19:low_time:0",
      "19->6:low_energy:1",
      "6->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      15,
      19,
      6,
      12,
      11,
      13
    ],
    "worker_columns": 431,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_fc8f27326a163867_16_15_19_6_12_11_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 548.335796,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 470,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 548.335796,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "55a386bc49af1dda",
    "generated_sequences_delta": -6896,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->16:low_risk:1",
      "16->4:low_risk:2",
      "4->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_sequence": [
      16,
      4,
      14,
      11,
      13
    ],
    "worker_columns": 450,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord7_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_07_seed61615_55a386bc49af1dda_16_4_14_11_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
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
