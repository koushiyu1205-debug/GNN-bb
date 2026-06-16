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
roi_class_counts = {'negative_primal_roi': 1, 'negative_retry_roi': 2, 'no_observed_roi': 2, 'positive_retry_roi': 4}
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
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb1_14_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 77.645206,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 43,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "d519291840dd7000",
    "generated_sequences_delta": 13538,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb1_14_10",
    "official_bound_effect": false,
    "pricing_calls_delta": -1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -9.364573000000007,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->10:low_time:0",
      "10->0:low_time:0"
    ],
    "target_sequence": [
      14,
      10
    ],
    "worker_columns": 283,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb1_14_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 23,
    "worker_primal": 619.142683,
    "worker_rmp_solves": 13,
    "worker_solving_time": 68.280633,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb2_5_1_2_18_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 77.578874,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "d519291840dd7000",
    "generated_sequences_delta": 56836,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb2_5_1_2_18_3",
    "official_bound_effect": false,
    "pricing_calls_delta": -5,
    "primal_improvement": -0.03082599999993363,
    "rmp_solves_delta": -3,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 7.536358000000007,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb2_5_1_2_18_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 19,
    "worker_primal": 619.173509,
    "worker_rmp_solves": 9,
    "worker_solving_time": 85.115232,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb3_8_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 77.556986,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "d519291840dd7000",
    "generated_sequences_delta": 59475,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb3_8_11",
    "official_bound_effect": false,
    "pricing_calls_delta": -4,
    "primal_improvement": 0.0,
    "rmp_solves_delta": -2,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": 7.548666000000011,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      8,
      11
    ],
    "worker_columns": 240,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_mb3_8_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 20,
    "worker_primal": 619.142683,
    "worker_rmp_solves": 10,
    "worker_solving_time": 85.105652,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb1_2_17_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.410306,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 4,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "ddcb5387bef3bf63",
    "generated_sequences_delta": 5535,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb1_2_17_16",
    "official_bound_effect": false,
    "pricing_calls_delta": 4,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 11.243460000000006,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      2,
      17,
      16
    ],
    "worker_columns": 389,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb1_2_17_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 19,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 9,
    "worker_solving_time": 65.653766,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb2_8_4_5_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.319333,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ddcb5387bef3bf63",
    "generated_sequences_delta": 5069,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb2_8_4_5_16",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 7.321362000000001,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb2_8_4_5_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 18,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 9,
    "worker_solving_time": 61.640695,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 385,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb3_10_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 8,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 15,
    "baseline_primal": 568.523092,
    "baseline_rmp_solves": 7,
    "baseline_solving_time": 54.285945,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -23,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "ddcb5387bef3bf63",
    "generated_sequences_delta": 2572,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb3_10_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "no_observed_roi",
    "solving_time_delta": 0.1556100000000029,
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      10,
      3
    ],
    "worker_columns": 362,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_mb3_10_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 16,
    "worker_primal": 568.523092,
    "worker_rmp_solves": 8,
    "worker_solving_time": 54.441555,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb1_19_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 77.600772,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -27,
    "exact_pricing_calls_delta": -3,
    "expected_context_hash": "67c11b5ec80925ec",
    "generated_sequences_delta": 43516,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb1_19_16",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 5,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -8.794880000000006,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->16:low_risk:2",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      19,
      16
    ],
    "worker_columns": 213,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb1_19_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 26,
    "worker_primal": 619.142683,
    "worker_rmp_solves": 17,
    "worker_solving_time": 68.805892,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb2_5_1_15_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 76.996334,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -8,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "67c11b5ec80925ec",
    "generated_sequences_delta": 45710,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb2_5_1_15_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 5,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 5,
    "roi_class": "no_observed_roi",
    "solving_time_delta": 1.0682219999999916,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb2_5_1_15_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 12,
    "worker_pricing_calls": 29,
    "worker_primal": 619.142683,
    "worker_rmp_solves": 17,
    "worker_solving_time": 78.064556,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 240,
    "baseline_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb3_5_1_2_18_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 12,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 24,
    "baseline_primal": 619.142683,
    "baseline_rmp_solves": 12,
    "baseline_solving_time": 77.539593,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -26,
    "exact_pricing_calls_delta": -3,
    "expected_context_hash": "67c11b5ec80925ec",
    "generated_sequences_delta": 42878,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb3_5_1_2_18_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 5,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -8.830840999999992,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_risk:2",
      "18->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "worker_columns": 214,
    "worker_csv": "BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_mb3_5_1_2_18_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 26,
    "worker_primal": 619.142683,
    "worker_rmp_solves": 17,
    "worker_solving_time": 68.708752,
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
