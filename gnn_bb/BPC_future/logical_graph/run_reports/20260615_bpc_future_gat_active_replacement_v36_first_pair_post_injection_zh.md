# GAT Fixed Worker Post-Injection Trajectory Audit 报告

日期：2026-06-15

## 目的

只读分析固定 worker 注入目标列之后的 trajectory 后效。该脚本不运行 BPC、pricing 或 worker，
只读取已有 JSONL/CSV。

## 机器字段

```text
gat_fixed_worker_post_injection_trajectory_audit = current
status = audited
allow_partial = true
runbook_candidate_count = 9
record_count = 1
skipped_missing_log_count = 8
target_injection_success_count = 1
target_returned_journeys_sum = 4.0
target_active_changed_task_set_sum = 1.0
target_inactive_changed_task_set_sum = 3.0
immediate_objective_improved_count = 1
immediate_vs_baseline_same_iter_improved_count = 0
worker_next_objective_delta_sum = -8.219276
worker_next_dual_l1_delta_mean = 11.157344
worker_next_objective_vs_baseline_same_iter_delta_sum = 133.604914
followup_pricing_event_sum = 20.0
followup_exact_event_sum = 10.0
followup_completion_retry_event_sum = 2.0
context_mismatch_skip_sum = 8.0
final_positive_roi_count = 1
final_negative_roi_count = 0
next_decision = fit_trajectory_gate_on_positive_long_horizon_cases
all_checks_pass = true
```

## 核心发现

注入后一轮 RMP 虽可能本地下降，但相对 baseline 同迭代没有优势，需要把标签改成 post-injection trajectory impact。

## 结论

- `target_returned_journeys_sum` 衡量 GAT/worker 是否真的注入了 true-RC negative 列；
- `target_active_changed_task_set_sum` 衡量这些列是否立刻进入 active support；
- `worker_next_objective_delta_sum` 衡量注入后一轮 RMP 目标改善；
- `worker_next_dual_l1_delta_mean` 衡量注入后 dual 震荡；
- `context_mismatch_skip_sum` 衡量注入后 context 是否快速漂移；
- 最终 ROI 仍以 status / wall time / pricing / exact 调用数为准。

## Records

```json
[
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 11,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 23,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 346.229826,
    "baseline_same_iter_objective": 748.758409,
    "baseline_same_iter_objective_delta": -141.82419,
    "baseline_solving_time": 71.26332,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 4,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [
      [
        8,
        11
      ],
      [
        2,
        4
      ],
      [
        2,
        3,
        18,
        11
      ],
      [
        5,
        1,
        2,
        15
      ]
    ],
    "certificate_effect": false,
    "exact_pricing_calls_delta": 0.0,
    "expected_context_hash": "d519291840dd7000",
    "final_roi_class": "positive_pricing_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4",
    "official_bound_effect": false,
    "pricing_calls_delta": -1.0,
    "rmp_solves_delta": -1.0,
    "solving_time_delta": 18.81804600000001,
    "target_active_changed_task_set_count": 1,
    "target_added_journeys": 4,
    "target_addition_productivity_class": "active_replacement_task_set",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_best_rc": -7.660825,
    "target_cg_iter": 1,
    "target_context_hash": "d519291840dd7000",
    "target_inactive_changed_task_set_count": 3,
    "target_injection_success": true,
    "target_new_journeys": 2,
    "target_replacement_journeys": 2,
    "target_returned_journeys": 4,
    "target_sequence": [
      8,
      11
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 8,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 11,
    "worker_followup_completion_retry_events": 2,
    "worker_followup_exact_pricing_events": 10,
    "worker_followup_pricing_events": 20,
    "worker_followup_worker_events": 8,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "46c65721781b361f",
    "worker_next_cg_iter": 2,
    "worker_next_dual_l1_delta": 11.157344,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": -335.072482,
    "worker_next_objective": 882.363323,
    "worker_next_objective_delta": -8.219276,
    "worker_next_objective_vs_baseline_same_iter_delta": 133.604914,
    "worker_pricing_calls": 22,
    "worker_rmp_solves": 11,
    "worker_solving_time": 90.081366,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 边界

- 该分析不产生 certificate；
- 该分析不改变任何求解结果；
- 后续训练标签应优先使用 long-horizon trajectory ROI，而不是仅使用 true-RC negative。
