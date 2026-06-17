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
roi_class_counts = {'columns_only_roi': 1, 'negative_retry_roi': 1, 'no_observed_roi': 2}
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
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.582754,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 10,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": 2812,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "columns_only_roi",
    "solving_time_delta": 0.5108129999999989,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      16,
      19
    ],
    "worker_columns": 228,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 14,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 7,
    "worker_solving_time": 53.093567,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": true,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.582754,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -23,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": -101,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.09194700000000466,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->2:low_risk:2",
      "2->8:low_time:0",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      1,
      2,
      8
    ],
    "worker_columns": 195,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 13,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 6,
    "worker_solving_time": 52.490807,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": true,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.582754,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -21,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": -21,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.06839000000000084,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      5,
      19
    ],
    "worker_columns": 197,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 13,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 6,
    "worker_solving_time": 52.514364,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": true,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.582754,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 22,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": 2774,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb4_5_13_20",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.44166299999999836,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->13:low_risk:1",
      "13->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      5,
      13,
      20
    ],
    "worker_columns": 240,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb4_5_13_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 15,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 7,
    "worker_solving_time": 53.024417,
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
