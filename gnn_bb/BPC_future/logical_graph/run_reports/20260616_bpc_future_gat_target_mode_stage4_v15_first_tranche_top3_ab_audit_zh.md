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
roi_class_counts = {'negative_primal_roi': 4, 'negative_retry_roi': 3, 'positive_primal_roi': 1, 'positive_retry_roi': 1}
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
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 68.284961,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 2774,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -2.609062999999992,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -7.445451999999996,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      16,
      17,
      15
    ],
    "worker_columns": 311,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 633.847635,
    "worker_rmp_solves": 10,
    "worker_solving_time": 60.839509,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.848407,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -28,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 3034,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -7.556666999999997,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      19,
      10,
      17
    ],
    "worker_columns": 303,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 631.238572,
    "worker_rmp_solves": 10,
    "worker_solving_time": 58.29174,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.832757,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -24,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 3008,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -3.5236019999999826,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -6.259926999999998,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      10,
      17,
      7
    ],
    "worker_columns": 307,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 634.762174,
    "worker_rmp_solves": 10,
    "worker_solving_time": 59.57283,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.422257,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 2,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -26.085125999999946,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -2.1083690000000033,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      1,
      15,
      17
    ],
    "worker_columns": 160,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 18,
    "worker_primal": 694.775986,
    "worker_rmp_solves": 11,
    "worker_solving_time": 56.313888,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.416048,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 1743,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": -26.085125999999946,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -1.9837160000000011,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_sequence": [
      12,
      4,
      13,
      5
    ],
    "worker_columns": 159,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 19,
    "worker_primal": 694.775986,
    "worker_rmp_solves": 12,
    "worker_solving_time": 56.432332,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.508456,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 3303,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 3.898953000000006,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 2.1174549999999996,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_sequence": [
      12,
      4,
      19,
      13
    ],
    "worker_columns": 162,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 21,
    "worker_primal": 664.791907,
    "worker_rmp_solves": 13,
    "worker_solving_time": 60.625911,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb1_2_19_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 633.106726,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 61.5656,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "45baa40751a0bf77",
    "generated_sequences_delta": 12747,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb1_2_19_14",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 2.411695999999999,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_sequence": [
      2,
      19,
      14
    ],
    "worker_columns": 241,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb1_2_19_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 18,
    "worker_primal": 633.106726,
    "worker_rmp_solves": 12,
    "worker_solving_time": 63.977296,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb2_1_3_19_15_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 633.106726,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 61.426799,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "45baa40751a0bf77",
    "generated_sequences_delta": 24482,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb2_1_3_19_15_12",
    "official_bound_effect": false,
    "pricing_calls_delta": 6,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 4,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 9.617273999999995,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_sequence": [
      1,
      3,
      19,
      15,
      12
    ],
    "worker_columns": 235,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb2_1_3_19_15_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 21,
    "worker_primal": 633.106726,
    "worker_rmp_solves": 14,
    "worker_solving_time": 71.044073,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb3_2_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 633.106726,
    "baseline_rmp_solves": 10,
    "baseline_solving_time": 61.397761,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "45baa40751a0bf77",
    "generated_sequences_delta": 7260,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb3_2_14",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 1.3182079999999985,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_risk:2"
    ],
    "target_sequence": [
      2,
      14
    ],
    "worker_columns": 242,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_45baa40751a0bf77_mb3_2_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 17,
    "worker_primal": 633.106726,
    "worker_rmp_solves": 11,
    "worker_solving_time": 62.715969,
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
