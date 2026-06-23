# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 6
coverage_confidence_ready_epoch_count = 3
coverage_and_false_delay_safe_epoch_count = 1
epoch_signal_class_counts = {'coverage_ready_and_false_delay_safe': 1, 'coverage_ready_but_false_delay_unsafe': 2, 'false_delay_safe_but_low_coverage': 5}
primary = epoch_history_missing_full_stage3_ci_fields
checkpoint_selection_is_primary_blocker = true
recommended_next_step = rerun_threshold_frontier_for_candidate_epoch_and_verify_full_stage3_gate
production_ready = false
selector_can_certificate = false
```

## Best Epochs

```json
{
  "best_coverage_ready_epoch": {
    "accepted_batch_count": 130,
    "accepted_batch_roi": 7.9323717752553,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 7,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 7.963525621409146,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.038461538461538464,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9938922820655192,
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
    "selected_batch_threshold": 0.6093875169754028,
    "selected_candidate_threshold": 0.2495091510937179,
    "selected_threshold": 0.6093875169754028,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.438944620212096,
    "validation_loss": 3.43880539482519
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 12,
    "accepted_batch_roi": 10.141976873079935,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 6,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 10.166976873079935,
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
    "selected_batch_threshold": 0.75,
    "selected_candidate_threshold": 0.44012893117211543,
    "selected_threshold": 0.75,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.634962795249118,
    "validation_loss": 3.4569424040802015
  },
  "best_overall_epoch": {
    "accepted_batch_count": 12,
    "accepted_batch_roi": 10.141976873079935,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 6,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 10.166976873079935,
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
    "selected_batch_threshold": 0.75,
    "selected_candidate_threshold": 0.44012893117211543,
    "selected_threshold": 0.75,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.634962795249118,
    "validation_loss": 3.4569424040802015
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | coverage_ready_and_false_delay_safe | 35 | 4.921133 | 0.000000 | 1.000000 | 1.000000 | 4.142489 |
| 2 | false_delay_safe_but_low_coverage | 15 | 9.904254 | 0.000000 | 1.000000 | 1.000000 | 3.328141 |
| 3 | false_delay_safe_but_low_coverage | 20 | 7.889833 | 0.000000 | 1.000000 | 1.000000 | 3.523332 |
| 4 | false_delay_safe_but_low_coverage | 11 | 8.000249 | 0.000000 | 1.000000 | 1.000000 | 3.147071 |
| 5 | false_delay_safe_but_low_coverage | 10 | 7.672612 | 0.000000 | 1.000000 | 1.000000 | 3.231184 |
| 6 | false_delay_safe_but_low_coverage | 12 | 10.141977 | 0.000000 | 1.000000 | 1.000000 | 3.456942 |
| 7 | coverage_ready_but_false_delay_unsafe | 130 | 7.932372 | 0.038462 | 0.993892 | 1.000000 | 3.438805 |
| 8 | coverage_ready_but_false_delay_unsafe | 103 | 7.701932 | 0.034965 | 0.991687 | 1.000000 | 4.760383 |

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
