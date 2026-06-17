# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-16

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = checkpoint_training_history
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 4
coverage_confidence_ready_epoch_count = 4
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 4, 'false_delay_safe_but_low_coverage': 4}
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
    "accepted_batch_count": 35,
    "accepted_batch_roi": 8.351436269629215,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 8,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 8.371436269629214,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.4489795918367347,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.8508474576271187,
    "high_priority_precision_point_pass": false,
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
    "selected_batch_threshold": 0.45603272318840027,
    "selected_candidate_threshold": 0.1531489953101488,
    "selected_threshold": 0.45603272318840027,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.513963507028515,
    "validation_loss": 6.4187900180966215
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 3,
    "accepted_batch_roi": 1.0162206888198853,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 1.0495540221532187,
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
    "selected_batch_threshold": 0.47887441515922546,
    "selected_candidate_threshold": 0.27164855283571043,
    "selected_threshold": 0.47887441515922546,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 8.135401246170431,
    "validation_loss": 6.8049683949714215
  },
  "best_overall_epoch": {
    "accepted_batch_count": 35,
    "accepted_batch_roi": 8.351436269629215,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 8,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 8.371436269629214,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.4489795918367347,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.8508474576271187,
    "high_priority_precision_point_pass": false,
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
    "selected_batch_threshold": 0.45603272318840027,
    "selected_candidate_threshold": 0.1531489953101488,
    "selected_threshold": 0.45603272318840027,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.513963507028515,
    "validation_loss": 6.4187900180966215
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 3 | 1.016221 | 0.000000 | 1.000000 | 1.000000 | 6.804968 |
| 2 | false_delay_safe_but_low_coverage | 4 | 0.794640 | 0.000000 | 1.000000 | 1.000000 | 6.252271 |
| 3 | false_delay_safe_but_low_coverage | 9 | 0.813192 | 0.000000 | 1.000000 | 1.000000 | 5.974783 |
| 4 | false_delay_safe_but_low_coverage | 9 | 0.813192 | 0.000000 | 1.000000 | 1.000000 | 6.262749 |
| 5 | coverage_ready_but_false_delay_unsafe | 55 | 5.411594 | 0.540816 | 0.943436 | 1.000000 | 6.477388 |
| 6 | coverage_ready_but_false_delay_unsafe | 50 | 6.017736 | 0.368852 | 0.943038 | 1.000000 | 6.630926 |
| 7 | coverage_ready_but_false_delay_unsafe | 55 | 5.411594 | 0.459184 | 0.951717 | 1.000000 | 6.496329 |
| 8 | coverage_ready_but_false_delay_unsafe | 35 | 8.351436 | 0.448980 | 0.850847 | 1.000000 | 6.418790 |

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
