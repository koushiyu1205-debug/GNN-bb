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
roi_class_counts = {'negative_retry_roi': 1, 'no_observed_roi': 2, 'positive_primal_roi': 1}
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
    "baseline_columns": 427,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 508.184986,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 69.597056,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -3,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "d8b85dff55093cb1",
    "generated_sequences_delta": 4917,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 6.251426999999978,
    "rmp_solves_delta": 1,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 4.835832000000011,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_time:0",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      6,
      20,
      3,
      7
    ],
    "worker_columns": 424,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 27,
    "worker_primal": 501.933559,
    "worker_rmp_solves": 21,
    "worker_solving_time": 74.432888,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 376,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 571.707652,
    "baseline_rmp_solves": 16,
    "baseline_solving_time": 68.99778,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "ddb0ce64af10976a",
    "generated_sequences_delta": 2408,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "negative_retry_roi",
    "solving_time_delta": 0.39353099999999586,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->5:low_risk:2",
      "5->0:low_time:0"
    ],
    "target_sequence": [
      19,
      5,
      13,
      9
    ],
    "worker_columns": 375,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_ddb0ce64af10976a_19_5_13_9_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_pricing_calls": 27,
    "worker_primal": 571.707652,
    "worker_rmp_solves": 17,
    "worker_solving_time": 69.391311,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 63,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 85.063008,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "37e3048dada58785",
    "generated_sequences_delta": -30835,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 2,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.9947939999999988,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->6:low_risk:1",
      "6->12:low_time:0",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_sequence": [
      2,
      6,
      12,
      13,
      8,
      17
    ],
    "worker_columns": 314,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_8_17_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 65,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 58,
    "worker_solving_time": 84.068214,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 63,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 85.067119,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "07e693c5f161a590",
    "generated_sequences_delta": -39911,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.9967280000000045,
    "target_arc_option_sequence": [
      "0->18:low_time:0",
      "18->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_sequence": [
      18,
      5,
      4,
      11
    ],
    "worker_columns": 314,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v20_positive_yield_parallel2_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 64,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 57,
    "worker_solving_time": 84.070391,
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
