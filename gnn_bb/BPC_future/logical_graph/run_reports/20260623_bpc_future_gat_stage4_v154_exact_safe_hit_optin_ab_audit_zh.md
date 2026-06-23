# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 3
roi_class_counts = {'negative_primal_roi': 2, 'no_observed_roi': 1}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = false
```

## Records

```json
[
  {
    "baseline_columns": 252,
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 639.119548,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 59.251771,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 18,
    "exact_pricing_calls_delta": 2,
    "expected_context_hash": "dd1c3812ce457e30",
    "generated_sequences_delta": -8694,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": -50.52744699999994,
    "rmp_solves_delta": -1,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": -0.8795560000000009,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->2:low_time:0",
      "2->3:low_time:0",
      "3->18:low_energy:1",
      "18->0:low_time:0"
    ],
    "target_sequence": [
      8,
      2,
      3,
      18,
      8,
      3,
      2
    ],
    "worker_columns": 270,
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 9,
    "worker_pricing_calls": 16,
    "worker_primal": 689.646995,
    "worker_rmp_solves": 8,
    "worker_solving_time": 58.372215,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 218,
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 13,
    "baseline_primal": 744.848595,
    "baseline_rmp_solves": 6,
    "baseline_solving_time": 52.3257,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -36,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "b095fbae18116443",
    "generated_sequences_delta": 63,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4",
    "official_bound_effect": false,
    "pricing_calls_delta": 0,
    "primal_improvement": 0.0,
    "rmp_solves_delta": 0,
    "roi_class": "no_observed_roi",
    "solving_time_delta": -0.06512000000000029,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->8:low_risk:2",
      "8->3:low_risk:2",
      "3->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_sequence": [
      20,
      8,
      3,
      18,
      20,
      8,
      6,
      18,
      20,
      8,
      3,
      20,
      8,
      6
    ],
    "worker_columns": 182,
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 13,
    "worker_primal": 744.848595,
    "worker_rmp_solves": 6,
    "worker_solving_time": 52.26058,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 252,
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_pricing_calls": 16,
    "baseline_primal": 639.119548,
    "baseline_rmp_solves": 9,
    "baseline_solving_time": 59.025268,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -35,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "ea2f1344458c548f",
    "generated_sequences_delta": 8530,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2",
    "official_bound_effect": false,
    "pricing_calls_delta": 2,
    "primal_improvement": -4.358571999999981,
    "rmp_solves_delta": 2,
    "roi_class": "negative_primal_roi",
    "solving_time_delta": 0.9624740000000003,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_sequence": [
      1,
      11,
      11,
      1
    ],
    "worker_columns": 217,
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_pricing_calls": 18,
    "worker_primal": 643.47812,
    "worker_rmp_solves": 11,
    "worker_solving_time": 59.987742,
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
