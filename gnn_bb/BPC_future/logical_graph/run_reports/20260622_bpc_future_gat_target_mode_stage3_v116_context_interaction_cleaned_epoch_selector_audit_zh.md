# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 2
coverage_confidence_ready_epoch_count = 7
coverage_and_false_delay_safe_epoch_count = 1
epoch_signal_class_counts = {'coverage_ready_and_false_delay_safe': 1, 'coverage_ready_but_false_delay_unsafe': 6, 'false_delay_safe_but_low_coverage': 1}
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
    "accepted_batch_count": 36,
    "accepted_batch_roi": 4.602682617492974,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 1,
    "epoch_signal_class": "coverage_ready_and_false_delay_safe",
    "expected_trajectory_utility": 4.6401826174929734,
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
    "selected_batch_threshold": 0.65,
    "selected_candidate_threshold": 0.18986651552497125,
    "selected_threshold": 0.65,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": true,
    "train_loss": 5.086885346531093,
    "validation_loss": 5.3154436632383515
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 8,
    "accepted_batch_roi": 14.827931880950928,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 6,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 14.827931880950928,
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
    "selected_batch_threshold": 0.85,
    "selected_candidate_threshold": 0.5226738406398548,
    "selected_threshold": 0.85,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.719890202427365,
    "validation_loss": 6.3387491250725185
  },
  "best_overall_epoch": {
    "accepted_batch_count": 8,
    "accepted_batch_roi": 14.827931880950928,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 6,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 14.827931880950928,
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
    "selected_batch_threshold": 0.85,
    "selected_candidate_threshold": 0.5226738406398548,
    "selected_threshold": 0.85,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.719890202427365,
    "validation_loss": 6.3387491250725185
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | coverage_ready_and_false_delay_safe | 36 | 4.602683 | 0.000000 | 1.000000 | 1.000000 | 5.315444 |
| 2 | coverage_ready_but_false_delay_unsafe | 90 | 1.164655 | 0.013986 | 0.997273 | 1.000000 | 4.647985 |
| 3 | coverage_ready_but_false_delay_unsafe | 90 | 1.175881 | 0.017483 | 0.996535 | 1.000000 | 4.364541 |
| 4 | coverage_ready_but_false_delay_unsafe | 95 | 1.798745 | 0.055944 | 0.990794 | 1.000000 | 4.482638 |
| 5 | coverage_ready_but_false_delay_unsafe | 134 | 1.393417 | 0.087413 | 0.984644 | 1.000000 | 6.225640 |
| 6 | false_delay_safe_but_low_coverage | 8 | 14.827932 | 0.000000 | 1.000000 | 1.000000 | 6.338749 |
| 7 | coverage_ready_but_false_delay_unsafe | 115 | 1.604034 | 0.031469 | 0.995047 | 1.000000 | 6.436293 |
| 8 | coverage_ready_but_false_delay_unsafe | 113 | 2.737115 | 0.069930 | 0.987326 | 1.000000 | 13.597285 |

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
