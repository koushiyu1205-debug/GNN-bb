# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 3
coverage_confidence_ready_epoch_count = 5
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 5, 'false_delay_safe_but_low_coverage': 3}
primary = no_epoch_satisfies_coverage_and_false_delay_constraints
checkpoint_selection_is_primary_blocker = false
recommended_next_step = not_a_checkpoint_selection_problem_collect_context_local_hard_negatives
production_ready = false
selector_can_certificate = false
```

## Best Epochs

```json
{
  "best_coverage_ready_epoch": {
    "accepted_batch_count": 73,
    "accepted_batch_roi": 14.827644570028944,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 6,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 14.855041830302918,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.027972027972027972,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9888111888111888,
    "high_priority_precision_point_pass": true,
    "min_confidence_all_success_count": 35,
    "nonfinite_skipped_update_rate": 0.0,
    "required_stage3_fields_missing": [
      "high_priority_precision_ci_low",
      "safe_precision_ci_low",
      "accepted_batch_roi_ci_low",
      "false_safe_rate_union",
      "accepted_batch_rate"
    ],
    "roi_point_pass": true,
    "safe_precision": 1.0,
    "safe_precision_point_pass": true,
    "selected_batch_threshold": 0.5750119090080261,
    "selected_candidate_threshold": 0.13086483743795738,
    "selected_threshold": 0.5750119090080261,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 3.9667692670701924,
    "validation_loss": 4.4071231538068805
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 18,
    "accepted_batch_roi": 31.299914128250546,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 31.313803017139435,
    "false_delay_safe": true,
    "false_high_priority_on_delay": 0.0,
    "false_safe_union_safe": false,
    "high_priority_precision": 1.0,
    "high_priority_precision_point_pass": true,
    "min_confidence_all_success_count": 35,
    "nonfinite_skipped_update_rate": 0.0,
    "required_stage3_fields_missing": [
      "high_priority_precision_ci_low",
      "safe_precision_ci_low",
      "accepted_batch_roi_ci_low",
      "false_safe_rate_union",
      "accepted_batch_rate"
    ],
    "roi_point_pass": true,
    "safe_precision": 1.0,
    "safe_precision_point_pass": true,
    "selected_batch_threshold": 0.5714261531829834,
    "selected_candidate_threshold": 0.1830359476019988,
    "selected_threshold": 0.5714261531829834,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.094136975613415,
    "validation_loss": 5.788629904690657
  },
  "best_overall_epoch": {
    "accepted_batch_count": 18,
    "accepted_batch_roi": 31.299914128250546,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 31.313803017139435,
    "false_delay_safe": true,
    "false_high_priority_on_delay": 0.0,
    "false_safe_union_safe": false,
    "high_priority_precision": 1.0,
    "high_priority_precision_point_pass": true,
    "min_confidence_all_success_count": 35,
    "nonfinite_skipped_update_rate": 0.0,
    "required_stage3_fields_missing": [
      "high_priority_precision_ci_low",
      "safe_precision_ci_low",
      "accepted_batch_roi_ci_low",
      "false_safe_rate_union",
      "accepted_batch_rate"
    ],
    "roi_point_pass": true,
    "safe_precision": 1.0,
    "safe_precision_point_pass": true,
    "selected_batch_threshold": 0.5714261531829834,
    "selected_candidate_threshold": 0.1830359476019988,
    "selected_threshold": 0.5714261531829834,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.094136975613415,
    "validation_loss": 5.788629904690657
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 18 | 31.299914 | 0.000000 | 1.000000 | 1.000000 | 5.788630 |
| 2 | false_delay_safe_but_low_coverage | 9 | 14.004474 | 0.000000 | 1.000000 | 1.000000 | 4.425679 |
| 3 | false_delay_safe_but_low_coverage | 10 | 12.996939 | 0.000000 | 1.000000 | 1.000000 | 4.304973 |
| 4 | coverage_ready_but_false_delay_unsafe | 98 | 11.282522 | 0.045455 | 0.981586 | 1.000000 | 4.476790 |
| 5 | coverage_ready_but_false_delay_unsafe | 37 | 12.804107 | 0.017483 | 0.988208 | 1.000000 | 4.559236 |
| 6 | coverage_ready_but_false_delay_unsafe | 73 | 14.827645 | 0.027972 | 0.988811 | 1.000000 | 4.407123 |
| 7 | coverage_ready_but_false_delay_unsafe | 111 | 9.964126 | 0.041958 | 0.983217 | 1.000000 | 4.417689 |
| 8 | coverage_ready_but_false_delay_unsafe | 87 | 12.663871 | 0.066434 | 0.976040 | 1.000000 | 4.827897 |

## Interpretation

- 若存在 `coverage_ready_and_false_delay_safe`，才说明 checkpoint selection 可能漏选了可行 epoch；
- 若同时存在 `false_delay_safe_but_low_coverage` 和 `coverage_ready_but_false_delay_unsafe`，说明问题更像 coverage / false-delay tradeoff，而不是单纯 checkpoint selection；
- 当前 epoch history 若缺少 CI / false-safe / family holdout 字段，不能直接证明 Stage 4 candidate，只能证明趋势。

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
