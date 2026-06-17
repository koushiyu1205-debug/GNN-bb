# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 5
roi_class_counts = {'negative_primal_roi': 2, 'negative_retry_roi': 1, 'no_observed_roi': 2}
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
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_batch3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 53.481376,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ac056820151e9ad7",
    "generated_sequences_delta": 2176,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_batch3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": -0.5870439999999988,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      20,
      16,
      15,
      5,
      16,
      7,
      3,
      15,
      20
    ],
    "worker_columns": 238,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_batch3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 16,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 10,
    "worker_solving_time": 52.894332,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_batch3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.631167,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -17,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b6d808ebac2a6dd8",
    "generated_sequences_delta": 2974,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_batch3",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "no_observed_roi",
    "solving_time_delta": 0.29584000000000543,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_sequence": [
      16,
      19,
      1,
      2,
      8,
      5,
      19
    ],
    "worker_columns": 201,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_batch3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 14,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 7,
    "worker_solving_time": 52.927007,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_batch3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.314239,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": -608,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_batch3",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -26.085125999999946,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -2.022658,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      1,
      15,
      17,
      12,
      4,
      13,
      5,
      12,
      4,
      19,
      13
    ],
    "worker_columns": 160,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_batch3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 18,
    "worker_primal": 694.775986,
    "worker_rmp_solves": 11,
    "worker_solving_time": 56.291581,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_batch3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.590897,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -35,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 2912,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_batch3",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -1.0817230000000109,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -6.344839999999998,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      16,
      17,
      15,
      4,
      19,
      10,
      17,
      4,
      10,
      17,
      7
    ],
    "worker_columns": 296,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_batch3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 632.320295,
    "worker_rmp_solves": 10,
    "worker_solving_time": 59.246057,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_batch3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 52.48967,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "7b430465c7ae76b3",
    "generated_sequences_delta": 0,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_batch3",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.0033219999999971606,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->1:low_risk:2",
      "1->0:low_energy:1"
    ],
    "target_sequence": [
      5,
      1,
      15,
      17,
      19,
      9,
      1,
      9
    ],
    "worker_columns": 236,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/context_batch_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_batch3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 5,
    "worker_pricing_calls": 14,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 9,
    "worker_solving_time": 52.486348,
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
