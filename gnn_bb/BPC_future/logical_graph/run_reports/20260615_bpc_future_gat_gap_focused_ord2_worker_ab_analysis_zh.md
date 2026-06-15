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
roi_class_counts = {'negative_primal_roi': 2, 'positive_primal_roi': 4}
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
    "baseline_columns": 419,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 594.368004,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 1,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "35a4908dfecb7ff3",
    "generated_sequences_delta": 17657,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13",
    "official_bound_effect": false,
    "primal_improvement": 13.686776000000009,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->18:low_time:0",
      "18->10:low_risk:1",
      "10->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      18,
      10,
      8,
      13
    ],
    "worker_columns": 420,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 580.681228,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 419,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 594.368004,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 33,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "7fc1de982db572be",
    "generated_sequences_delta": 16252,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13",
    "official_bound_effect": false,
    "primal_improvement": 4.700892000000067,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->10:low_risk:1",
      "10->0:low_time:0"
    ],
    "target_sequence": [
      18,
      10,
      12,
      4,
      13
    ],
    "worker_columns": 452,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_primal": 589.667112,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 365,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 472.611976,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -16,
    "exact_pricing_calls_delta": 3,
    "expected_context_hash": "8f2fd95e2f03ec41",
    "generated_sequences_delta": 28095,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13",
    "official_bound_effect": false,
    "primal_improvement": 2.3322950000000446,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->7:low_energy:1",
      "7->20:low_energy:1",
      "20->1:low_risk:2",
      "1->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_sequence": [
      12,
      7,
      20,
      1,
      5,
      13
    ],
    "worker_columns": 349,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 470.279681,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 365,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 472.611976,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 0,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "1625c1776efc58ed",
    "generated_sequences_delta": 19058,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4",
    "official_bound_effect": false,
    "primal_improvement": 1.7684980000000223,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->7:low_risk:2",
      "7->2:low_risk:2",
      "2->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_sequence": [
      12,
      7,
      2,
      1,
      10,
      4
    ],
    "worker_columns": 365,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 470.843478,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 450,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 546.898087,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -24,
    "exact_pricing_calls_delta": 3,
    "expected_context_hash": "355f0684d6e275df",
    "generated_sequences_delta": 181793,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8",
    "official_bound_effect": false,
    "primal_improvement": -2.594432999999981,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->17:low_time:0",
      "17->3:low_time:0",
      "3->9:low_time:0",
      "9->4:low_risk:2",
      "4->8:low_time:0",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      17,
      3,
      9,
      4,
      8
    ],
    "worker_columns": 426,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_355f0684d6e275df_5_17_3_9_4_8_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_primal": 549.49252,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 284,
    "baseline_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 596.911574,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "aa78e15d40fb733a",
    "generated_sequences_delta": 5652,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13",
    "official_bound_effect": false,
    "primal_improvement": -6.702342000000044,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->9:low_risk:1",
      "9->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      9,
      1,
      13
    ],
    "worker_columns": 282,
    "worker_csv": "BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_aa78e15d40fb733a_20_9_1_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 8,
    "worker_primal": 603.613916,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
