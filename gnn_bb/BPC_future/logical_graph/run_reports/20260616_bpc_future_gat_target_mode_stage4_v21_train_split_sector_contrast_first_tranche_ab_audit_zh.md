# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 9
roi_class_counts = {'negative_primal_roi': 2, 'negative_retry_roi': 2, 'no_observed_roi': 1, 'positive_primal_roi': 1, 'positive_retry_roi': 3}
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
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 684.895069,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 75.668526,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -51,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "0df8d5cea7864e69",
    "generated_sequences_delta": 78220,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18",
    "official_bound_effect": false,
    "pricing_calls_delta": 10,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 9,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 9.428541999999993,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_sequence": [
      1,
      18
    ],
    "worker_columns": 190,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb1_1_18_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 26,
    "worker_primal": 684.895069,
    "worker_rmp_solves": 18,
    "worker_solving_time": 85.097068,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 684.895069,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 75.72781,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -31,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "0df8d5cea7864e69",
    "generated_sequences_delta": 7336,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -3.641690000000011,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->5:low_risk:2",
      "5->12:low_time:0",
      "12->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      5,
      12,
      10
    ],
    "worker_columns": 210,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb2_16_5_12_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 17,
    "worker_primal": 684.895069,
    "worker_rmp_solves": 10,
    "worker_solving_time": 72.08612,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 684.895069,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 75.572948,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -56,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "0df8d5cea7864e69",
    "generated_sequences_delta": 177650,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 11,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 9,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 9.475721000000007,
    "target_arc_option_sequence": [
      "0->16:low_risk:2",
      "16->3:low_time:0",
      "3->2:low_risk:2",
      "2->10:low_time:0",
      "10->0:low_risk:2"
    ],
    "target_sequence": [
      16,
      3,
      2,
      10
    ],
    "worker_columns": 185,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_mb3_16_3_2_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 27,
    "worker_primal": 684.895069,
    "worker_rmp_solves": 18,
    "worker_solving_time": 85.048669,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 205,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb1_13_20_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 714.637579,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 59.090234,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -15,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "b9550ffc9a42531a",
    "generated_sequences_delta": 14387,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb1_13_20_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 5,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -2.5120180000000047,
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_sequence": [
      13,
      20,
      7
    ],
    "worker_columns": 190,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb1_13_20_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 22,
    "worker_primal": 714.637579,
    "worker_rmp_solves": 15,
    "worker_solving_time": 56.578216,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 205,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb2_5_4_6_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 714.637579,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 59.141467,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -4,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "b9550ffc9a42531a",
    "generated_sequences_delta": 30,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb2_5_4_6_11",
    "official_bound_effect": false,
    "pricing_calls_delta": -1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -5.192014999999998,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_sequence": [
      5,
      4,
      6,
      11
    ],
    "worker_columns": 201,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb2_5_4_6_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 17,
    "worker_primal": 714.637579,
    "worker_rmp_solves": 10,
    "worker_solving_time": 53.949452,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 205,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb3_5_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 714.637579,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 59.208927,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -9,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "b9550ffc9a42531a",
    "generated_sequences_delta": 393,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb3_5_19",
    "official_bound_effect": false,
    "pricing_calls_delta": -2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -5.0815100000000015,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      19
    ],
    "worker_columns": 196,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_mb3_5_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 16,
    "worker_primal": 714.637579,
    "worker_rmp_solves": 10,
    "worker_solving_time": 54.127417,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb1_11_4_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 673.976604,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 51.97056,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4e481a6307fca228",
    "generated_sequences_delta": 2609,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb1_11_4_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 0.11635799999999108,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 0.6975180000000023,
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->4:low_energy:1",
      "4->7:low_energy:1",
      "7->0:low_energy:1"
    ],
    "target_sequence": [
      11,
      4,
      7
    ],
    "worker_columns": 255,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb1_11_4_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 16,
    "worker_primal": 673.860246,
    "worker_rmp_solves": 9,
    "worker_solving_time": 52.668078,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb2_10_11_7_3_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 673.976604,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 52.104904,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -21,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "4e481a6307fca228",
    "generated_sequences_delta": 23,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb2_10_11_7_3_14",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -71.10362000000009,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -0.14987699999999649,
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->11:low_risk:1",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      10,
      11,
      7,
      3,
      14
    ],
    "worker_columns": 236,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb2_10_11_7_3_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 13,
    "worker_primal": 745.080224,
    "worker_rmp_solves": 7,
    "worker_solving_time": 51.955027,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 257,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb3_11_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 673.976604,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 52.069993,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -11,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "4e481a6307fca228",
    "generated_sequences_delta": 1257,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb3_11_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -71.10362000000009,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.2661210000000054,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_sequence": [
      11,
      7
    ],
    "worker_columns": 246,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_mb3_11_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 15,
    "worker_primal": 745.080224,
    "worker_rmp_solves": 8,
    "worker_solving_time": 52.336114,
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
