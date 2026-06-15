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
roi_class_counts = {'negative_primal_roi': 1, 'no_observed_roi': 1, 'positive_primal_roi': 1, 'positive_retry_roi': 1}
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
    "baseline_columns": 302,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 23,
    "baseline_primal": 579.577707,
    "baseline_rmp_solves": 18,
    "baseline_solving_time": 62.049466,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -1,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "bec78bfc0baddb44",
    "generated_sequences_delta": 2609,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2",
    "official_bound_effect": false,
    "pricing_calls_delta": 3,
    "primal_improvement": -2.2324689999999237,
    "rmp_solves_delta": 1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 4.430933000000003,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->3:low_risk:1",
      "3->0:low_risk:2"
    ],
    "target_sequence": [
      15,
      3,
      8,
      16,
      2
    ],
    "worker_columns": 301,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 26,
    "worker_primal": 581.810176,
    "worker_rmp_solves": 19,
    "worker_solving_time": 66.480399,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 427,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 25,
    "baseline_primal": 508.184986,
    "baseline_rmp_solves": 20,
    "baseline_solving_time": 69.761886,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -2,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "77bc967e4038b08b",
    "generated_sequences_delta": 4955,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": 6.251426999999978,
    "rmp_solves_delta": 1,
    "roi_class": "positive_primal_roi",
    "solving_time_delta": 0.8524910000000006,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_risk:2",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_sequence": [
      4,
      6,
      20,
      18,
      2,
      10
    ],
    "worker_columns": 425,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_pricing_calls": 27,
    "worker_primal": 501.933559,
    "worker_rmp_solves": 21,
    "worker_solving_time": 70.614377,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 315,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 63,
    "baseline_primal": 506.923489,
    "baseline_rmp_solves": 56,
    "baseline_solving_time": 85.062222,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -15,
    "exact_pricing_calls_delta": -2,
    "expected_context_hash": "b36178f6655c5f75",
    "generated_sequences_delta": -177909,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 3,
    "roi_class": "positive_retry_roi",
    "solving_time_delta": -15.538142000000008,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->12:low_risk:1",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->15:low_time:0",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "worker_columns": 300,
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 5,
    "worker_pricing_calls": 64,
    "worker_primal": 506.923489,
    "worker_rmp_solves": 59,
    "worker_solving_time": 69.52408,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 241,
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 684.895069,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 75.347745,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -31,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "0df8d5cea7864e69",
    "generated_sequences_delta": 7336,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10",
    "official_bound_effect": false,
    "pricing_calls_delta": 1,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 1,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -3.5869849999999985,
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
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top4_v19_positive_yield_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 17,
    "worker_primal": 684.895069,
    "worker_rmp_solves": 10,
    "worker_solving_time": 71.76076,
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
