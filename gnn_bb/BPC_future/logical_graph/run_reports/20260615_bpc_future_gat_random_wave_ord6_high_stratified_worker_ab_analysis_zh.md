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
roi_class_counts = {'columns_only_roi': 1, 'no_observed_roi': 1}
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
    "baseline_columns": 127,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_4bdbc33c25c0cc96_2_15_1_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 5,
    "baseline_fallback_used": false,
    "baseline_primal": 615.605876,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": 3,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "4bdbc33c25c0cc96",
    "generated_sequences_delta": 1304,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_4bdbc33c25c0cc96_2_15_1",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->15:low_risk:2",
      "15->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_sequence": [
      2,
      15,
      1
    ],
    "worker_columns": 130,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_4bdbc33c25c0cc96_2_15_1_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 5,
    "worker_primal": 615.605876,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_columns": 235,
    "baseline_csv": "BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_29abc7dcf4532844_14_5_18_4_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_dual_bound": null,
    "baseline_exact_pricing_calls": 7,
    "baseline_fallback_used": false,
    "baseline_primal": 675.557123,
    "baseline_status": "TIME_LIMIT",
    "certificate_effect": false,
    "columns_delta": -6,
    "exact_pricing_calls_delta": 0,
    "expected_context_hash": "29abc7dcf4532844",
    "generated_sequences_delta": -4,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_29abc7dcf4532844_14_5_18_4_13",
    "official_bound_effect": false,
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi",
    "target_arc_option_sequence": [
      "0->14:low_risk:1",
      "14->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_sequence": [
      14,
      5,
      18,
      4,
      13
    ],
    "worker_columns": 229,
    "worker_csv": "BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_29abc7dcf4532844_14_5_18_4_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_dual_bound": null,
    "worker_exact_pricing_calls": 7,
    "worker_primal": 675.557123,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 判断

- `positive_primal_roi` 表示 worker primal 严格优于同实例 baseline；
- `no_observed_roi` 表示 worker 与 baseline 没有可观测改善；
- 只要正负 ROI 同时存在，GAT HIGH_PRIORITY 就不能直接默认触发 worker；
- 所有结果都不能参与 no-negative certificate 或 official lower bound。
