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
roi_class_counts = {'no_observed_roi': 1, 'positive_primal_roi': 3}
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
