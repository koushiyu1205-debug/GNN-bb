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
roi_class_counts = {'columns_only_roi': 2, 'no_observed_roi': 2}
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
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_primal": 619.142683,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "d519291840dd7000",
    "generated_sequences_delta": 90402,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_time:0",
      "18->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "worker_columns": 241,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 13,
    "worker_primal": 619.142683,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_primal": 619.142683,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -8,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "67c11b5ec80925ec",
    "generated_sequences_delta": 44995,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->15:low_time:0",
      "15->3:low_time:0",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      1,
      15,
      3
    ],
    "worker_columns": 232,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 12,
    "worker_primal": 619.142683,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_primal": 568.523092,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ddcb5387bef3bf63",
    "generated_sequences_delta": 5114,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->8:low_energy:1",
      "8->4:low_time:0",
      "4->5:low_time:0",
      "5->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      8,
      4,
      5,
      16
    ],
    "worker_columns": 365,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 568.523092,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_primal": 568.523092,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "5c522ff2995f86be",
    "generated_sequences_delta": 7119,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->11:low_energy:1",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      11,
      1,
      13,
      20
    ],
    "worker_columns": 386,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 568.523092,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
