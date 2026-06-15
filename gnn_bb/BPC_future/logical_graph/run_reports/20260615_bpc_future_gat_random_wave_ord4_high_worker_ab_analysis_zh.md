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
roi_class_counts = {'negative_primal_roi': 2}
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
    "baseline_columns": 266,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_d40675f8eea857f5_14_8_7_1_16_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 552.21958,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -9,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "d40675f8eea857f5",
    "generated_sequences_delta": 2250,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_d40675f8eea857f5_14_8_7_1_16_3",
    "official_bound_effect": false,
    "primal_improvement": -10.643286000000103,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->8:low_time:0",
      "8->7:low_time:0",
      "7->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      14,
      8,
      7,
      1,
      16,
      3
    ],
    "worker_columns": 257,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_d40675f8eea857f5_14_8_7_1_16_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 562.862866,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 266,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_97834be69e3ad8f3_20_15_1_16_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 552.21958,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "97834be69e3ad8f3",
    "generated_sequences_delta": 2253,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_97834be69e3ad8f3_20_15_1_16_3",
    "official_bound_effect": false,
    "primal_improvement": -10.643286000000103,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->15:low_time:0",
      "15->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      15,
      1,
      16,
      3
    ],
    "worker_columns": 260,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_04_seed61309_97834be69e3ad8f3_20_15_1_16_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
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
