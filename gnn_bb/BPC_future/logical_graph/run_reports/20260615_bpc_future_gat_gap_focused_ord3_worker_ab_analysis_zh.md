# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 1
roi_class_counts = {'no_observed_roi': 1}
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
    "baseline_columns": 196,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord3_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 537.218772,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "6fe9dc2c7bd2affb",
    "generated_sequences_delta": 5698,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      4,
      16,
      3,
      7
    ],
    "worker_columns": 195,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord3_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 537.218772,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
