# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 7
coverage_confidence_ready_epoch_count = 1
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 1, 'false_delay_safe_but_low_coverage': 7}
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
    "accepted_batch_count": 131,
    "accepted_batch_roi": 1.3274868553561168,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 4,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 1.3641280767301627,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.06643356643356643,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9889470622454916,
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
    "selected_batch_threshold": 0.494320273399353,
    "selected_candidate_threshold": 0.18214086719609257,
    "selected_threshold": 0.494320273399353,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 3.083539075367155,
    "validation_loss": 5.829807798534068
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 8,
    "accepted_batch_roi": 14.403059124946594,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 2,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 14.403059124946594,
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
    "selected_batch_threshold": 0.37650904059410095,
    "selected_candidate_threshold": 0.20911908673282392,
    "selected_threshold": 0.37650904059410095,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 4.246908164817079,
    "validation_loss": 5.026445491471242
  },
  "best_overall_epoch": {
    "accepted_batch_count": 8,
    "accepted_batch_roi": 14.403059124946594,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 2,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 14.403059124946594,
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
    "selected_batch_threshold": 0.37650904059410095,
    "selected_candidate_threshold": 0.20911908673282392,
    "selected_threshold": 0.37650904059410095,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 4.246908164817079,
    "validation_loss": 5.026445491471242
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 12 | 1.444415 | 0.000000 | 1.000000 | 1.000000 | 5.449554 |
| 2 | false_delay_safe_but_low_coverage | 8 | 14.403059 | 0.000000 | 1.000000 | 1.000000 | 5.026445 |
| 3 | false_delay_safe_but_low_coverage | 20 | 5.435636 | 0.000000 | 1.000000 | 1.000000 | 5.424816 |
| 4 | coverage_ready_but_false_delay_unsafe | 131 | 1.327487 | 0.066434 | 0.988947 | 1.000000 | 5.829808 |
| 5 | false_delay_safe_but_low_coverage | 9 | 14.004474 | 0.000000 | 1.000000 | 1.000000 | 7.747203 |
| 6 | false_delay_safe_but_low_coverage | 9 | 14.004474 | 0.000000 | 1.000000 | 1.000000 | 7.261382 |
| 7 | false_delay_safe_but_low_coverage | 9 | 14.004474 | 0.000000 | 1.000000 | 1.000000 | 10.901749 |
| 8 | false_delay_safe_but_low_coverage | 8 | 11.542411 | 0.006993 | 0.988439 | 1.000000 | 20.615401 |

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
