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
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 52.448273,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ac056820151e9ad7",
    "generated_sequences_delta": 2230,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.290461999999998,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_sequence": [
      20,
      16
    ],
    "worker_columns": 233,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 16,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 10,
    "worker_solving_time": 52.738735,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 52.463403,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ac056820151e9ad7",
    "generated_sequences_delta": 2228,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.3212860000000006,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->5:low_risk:2",
      "5->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      15,
      5,
      16,
      7,
      3
    ],
    "worker_columns": 237,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 16,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 10,
    "worker_solving_time": 52.784689,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 236,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 14,
    "baseline_primal": 632.987632,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 52.39186,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 35,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ac056820151e9ad7",
    "generated_sequences_delta": 4468,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.6696079999999967,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_sequence": [
      15,
      20
    ],
    "worker_columns": 271,
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 17,
    "worker_primal": 632.987632,
    "worker_rmp_solves": 11,
    "worker_solving_time": 53.061468,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.101694,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 11,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -26.085125999999946,
    "rmp_solves_delta": 0,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -1.768607000000003,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 18,
    "worker_primal": 694.775986,
    "worker_rmp_solves": 11,
    "worker_solving_time": 56.333087,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.087761,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 1662,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": -26.085125999999946,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -1.8476050000000015,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 19,
    "worker_primal": 694.775986,
    "worker_rmp_solves": 12,
    "worker_solving_time": 56.240156,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 161,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 668.69086,
    "baseline_rmp_solves": 11,
    "baseline_solving_time": 58.232087,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "79fde658840fe2b8",
    "generated_sequences_delta": 3280,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": 3.898953000000006,
    "rmp_solves_delta": 2,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 2.372822999999997,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 21,
    "worker_primal": 664.791907,
    "worker_rmp_solves": 13,
    "worker_solving_time": 60.60491,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.339166,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -20,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 2934,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -2.609062999999992,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -4.955869000000007,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 633.847635,
    "worker_rmp_solves": 10,
    "worker_solving_time": 60.383297,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.330254,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -28,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 2947,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -7.6623539999999934,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 631.238572,
    "worker_rmp_solves": 10,
    "worker_solving_time": 57.6679,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 331,
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 18,
    "baseline_primal": 631.238572,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 65.355102,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -24,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "generated_sequences_delta": 2995,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -3.5236019999999826,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -6.284799,
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
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_pricing_calls": 18,
    "worker_primal": 634.762174,
    "worker_rmp_solves": 10,
    "worker_solving_time": 59.070303,
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
