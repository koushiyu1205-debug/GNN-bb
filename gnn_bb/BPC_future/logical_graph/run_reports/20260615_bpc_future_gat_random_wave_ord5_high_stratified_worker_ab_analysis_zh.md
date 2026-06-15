# GAT Target-Priority Worker A/B Audit 报告

日期：2026-06-14

## 目的

聚合 GAT target-priority worker A/B 的 CSV 结果，判断候选是否有真实 ROI。
该脚本只读 CSV，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_audit = current
status = audited
record_count = 2
roi_class_counts = {'negative_primal_roi': 1, 'positive_primal_roi': 1}
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
    "baseline_columns": 148,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_be1c1c2bb30bf3f2_20_17_1_16_4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 6,
    "baseline_fallback_used": false,
    "baseline_primal": 664.677377,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -8,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "be1c1c2bb30bf3f2",
    "generated_sequences_delta": -22314,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_be1c1c2bb30bf3f2_20_17_1_16_4",
    "official_bound_effect": false,
    "primal_improvement": -11.301099000000022,
    "roi_class": "negative_primal_roi",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->1:low_risk:1",
      "1->16:low_time:0",
      "16->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_sequence": [
      20,
      17,
      1,
      16,
      4
    ],
    "worker_columns": 140,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_be1c1c2bb30bf3f2_20_17_1_16_4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 6,
    "worker_primal": 675.978476,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 372,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 9,
    "baseline_fallback_used": false,
    "baseline_primal": 646.349246,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -12,
    "exact_pricing_calls_delta": 1,
    "expected_context_hash": "79c1e81dc9889c24",
    "generated_sequences_delta": 2522,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10",
    "official_bound_effect": false,
    "primal_improvement": 4.6900210000000015,
    "roi_class": "positive_primal_roi",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->6:low_risk:2",
      "6->10:low_energy:1",
      "10->0:low_risk:2"
    ],
    "target_sequence": [
      5,
      6,
      10
    ],
    "worker_columns": 360,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 10,
    "worker_primal": 641.659225,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
