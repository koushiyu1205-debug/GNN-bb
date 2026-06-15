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
roi_class_counts = {'no_observed_roi': 2, 'positive_primal_roi': 2}
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
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 551.221675,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -21,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "301df9ab59b370e5",
    "generated_sequences_delta": 8880,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14",
    "official_bound_effect": false,
    "primal_improvement": 1.1993049999999812,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_sequence": [
      3,
      8,
      9,
      14
    ],
    "worker_columns": 603,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 550.02237,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 624,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_19_10_18_1_11_12_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 551.221675,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -13,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "10d0ac41456ac922",
    "generated_sequences_delta": 18776,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_19_10_18_1_11_12_5",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->13:low_risk:1",
      "13->19:low_time:0",
      "19->10:low_risk:2",
      "10->18:low_time:0",
      "18->1:low_time:0",
      "1->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      13,
      19,
      10,
      18,
      1,
      11,
      12,
      5
    ],
    "worker_columns": 611,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_10d0ac41456ac922_13_19_10_18_1_11_12_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 551.221675,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 367,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 649.843765,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -7,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "1bb852f9988a595e",
    "generated_sequences_delta": 2178,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12",
    "official_bound_effect": false,
    "primal_improvement": 68.56680099999994,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_risk:2"
    ],
    "target_sequence": [
      6,
      8,
      12
    ],
    "worker_columns": 360,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 581.276964,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 292,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_20_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 17,
    "baseline_fallback_used": false,
    "baseline_primal": 551.211298,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -10,
    "exact_pricing_calls_delta": -6,
    "expected_context_hash": "4716509a0e100011",
    "generated_sequences_delta": -152063,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_20",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->2:low_risk:1",
      "2->14:low_time:0",
      "14->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_sequence": [
      15,
      2,
      14,
      20
    ],
    "worker_columns": 282,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_remaining_high_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_09_seed61817_4716509a0e100011_15_2_14_20_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 11,
    "worker_primal": 551.211298,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
