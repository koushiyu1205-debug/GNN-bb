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
roi_class_counts = {'missing_result': 1, 'no_observed_roi': 4, 'positive_primal_roi': 1}
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
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "c488c428ee5822de",
    "generated_sequences_delta": 1733,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo20_sector_wave_c488c428_target_20_17_16",
    "official_bound_effect": false,
    "primal_improvement": 0.9636629999999968,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_columns": 259,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 739.158736,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "7e0afd09753effed",
    "generated_sequences_delta": 121,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_sequence": [
      19
    ],
    "worker_columns": 257,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 740.122399,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "a3b5b5263e1cfe17",
    "generated_sequences_delta": 9,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->14:low_time:0",
      "14->5:low_risk:2",
      "5->8:low_time:0",
      "8->18:low_risk:2",
      "18->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      5,
      8,
      18,
      12
    ],
    "worker_columns": 257,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 740.122399,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 752.490126,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "de2c1d84615d5c71",
    "generated_sequences_delta": -115,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->6:low_risk:2",
      "6->1:low_risk:2",
      "1->20:low_time:0",
      "20->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      6,
      1,
      20,
      9
    ],
    "worker_columns": 395,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 752.490126,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 395,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": true,
    "baseline_primal": 752.490126,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "157f03afc868de3b",
    "generated_sequences_delta": 75,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_sequence": [
      13
    ],
    "worker_columns": 395,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_auto_candidates_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 752.490126,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": true,
    "baseline_primal": 740.122399,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": null,
    "exact_pricing_calls_delta": null,
    "expected_context_hash": "c488c428ee5822de",
    "generated_sequences_delta": null,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16",
    "official_bound_effect": false,
    "primal_improvement": null,
    "roi_class": "missing_result",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_columns": null,
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20roi_smoke_auto_20260614/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16_target_priority_worker/results.csv",
    "worker_csv_exists": false,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": null,
    "worker_primal": null,
    "worker_status": null
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
