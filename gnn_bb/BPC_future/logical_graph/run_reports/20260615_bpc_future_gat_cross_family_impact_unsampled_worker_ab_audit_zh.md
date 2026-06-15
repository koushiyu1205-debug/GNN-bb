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
roi_class_counts = {'negative_primal_roi': 1, 'no_observed_roi': 2, 'positive_primal_roi': 3}
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
    "baseline_columns": 624,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 551.221675,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 10,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "301df9ab59b370e5",
    "generated_sequences_delta": 13991,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5",
    "official_bound_effect": false,
    "primal_improvement": 1.1993049999999812,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:1",
      "13->0:low_risk:1"
    ],
    "target_sequence": [
      13,
      3,
      8,
      18,
      1,
      11,
      15,
      5
    ],
    "worker_columns": 634,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 550.02237,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 624,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_10_1_18_8_20_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 551.221675,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "10d0ac41456ac922",
    "generated_sequences_delta": 7433,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_10_1_18_8_20_5",
    "official_bound_effect": false,
    "primal_improvement": -1.1826379999999972,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:1",
      "13->10:low_time:0",
      "10->1:low_time:0",
      "1->18:low_time:0",
      "18->8:low_risk:1",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      13,
      10,
      1,
      18,
      8,
      20,
      5
    ],
    "worker_columns": 621,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_10_1_18_8_20_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 552.404313,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 367,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 649.843765,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "f567a0928007db23",
    "generated_sequences_delta": 2460,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5",
    "official_bound_effect": false,
    "primal_improvement": 68.56680099999994,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->7:low_risk:1",
      "7->9:low_time:0",
      "9->0:low_energy:1"
    ],
    "target_sequence": [
      2,
      7,
      9,
      15,
      1,
      5
    ],
    "worker_columns": 367,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 581.276964,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 367,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 649.843765,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "1bb852f9988a595e",
    "generated_sequences_delta": 2605,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11",
    "official_bound_effect": false,
    "primal_improvement": 68.56680099999994,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_sequence": [
      6,
      2,
      9,
      11
    ],
    "worker_columns": 365,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 581.276964,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 292,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_9_3_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 17,
    "baseline_fallback_used": false,
    "baseline_primal": 551.211298,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -10,
    "exact_pricing_calls_delta": -7,
    "expected_context_hash": "4716509a0e100011",
    "generated_sequences_delta": -198360,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_9_3_11",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->2:low_risk:1",
      "2->14:low_time:0",
      "14->9:low_time:0",
      "9->3:low_time:0",
      "3->11:low_energy:1",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      15,
      2,
      14,
      9,
      3,
      11
    ],
    "worker_columns": 282,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_9_3_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_primal": 551.211298,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 301,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_5_19_2_4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 10,
    "baseline_fallback_used": false,
    "baseline_primal": 690.693243,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -4,
    "exact_pricing_calls_delta": -1,
    "expected_context_hash": "084e39c1f4a0fc67",
    "generated_sequences_delta": -1525,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_5_19_2_4",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->19:low_risk:2",
      "19->2:low_time:0",
      "2->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      19,
      2,
      4
    ],
    "worker_columns": 297,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_5_19_2_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 690.693243,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
