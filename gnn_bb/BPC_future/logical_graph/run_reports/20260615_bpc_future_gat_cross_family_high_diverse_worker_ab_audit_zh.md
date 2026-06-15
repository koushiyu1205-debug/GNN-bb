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
roi_class_counts = {'columns_only_roi': 1, 'no_observed_roi': 1, 'positive_primal_roi': 2}
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
    "baseline_columns": 249,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 11,
    "baseline_fallback_used": false,
    "baseline_primal": 584.981747,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": -3,
    "expected_context_hash": "01430159f79364bf",
    "generated_sequences_delta": -189997,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->10:low_risk:1",
      "10->13:low_risk:1",
      "13->0:low_risk:1"
    ],
    "target_sequence": [
      3,
      10,
      13,
      7,
      19
    ],
    "worker_columns": 249,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_01_seed61000_01430159f79364bf_3_10_13_7_19_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 584.981747,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 367,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 649.843765,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -14,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "f567a0928007db23",
    "generated_sequences_delta": 10101,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5",
    "official_bound_effect": false,
    "primal_improvement": 44.82507999999996,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_sequence": [
      14,
      19,
      5
    ],
    "worker_columns": 353,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 605.018685,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 189,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 670.585418,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "5c5a1e3be100b071",
    "generated_sequences_delta": -13376,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2",
    "official_bound_effect": false,
    "primal_improvement": 7.742461000000048,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->20:low_risk:2",
      "20->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_sequence": [
      12,
      20,
      2
    ],
    "worker_columns": 188,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_01_seed61000_5c5a1e3be100b071_12_20_2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 662.842957,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 301,
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 10,
    "baseline_fallback_used": false,
    "baseline_primal": 690.693243,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "084e39c1f4a0fc67",
    "generated_sequences_delta": 1915,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->20:low_time:0",
      "20->0:low_energy:1"
    ],
    "target_sequence": [
      1,
      20,
      4
    ],
    "worker_columns": 303,
    "worker_csv": "BPC_future/results/gat_same_run_cross_family_high_diverse_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_01_seed61001_084e39c1f4a0fc67_1_20_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 11,
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
