# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-16

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 3
coverage_confidence_ready_epoch_count = 3
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 3, 'false_delay_safe_but_low_coverage': 3, 'low_coverage_and_false_delay_unsafe': 2}
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
    "accepted_batch_count": 39,
    "accepted_batch_roi": 7.661404526195465,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 8,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 7.690891705682644,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.417910447761194,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9086460032626428,
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
    "selected_batch_threshold": 0.4925599992275238,
    "selected_candidate_threshold": 0.19138971363514834,
    "selected_threshold": 0.4925599992275238,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.193720512196626,
    "validation_loss": 6.76071464822407
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 8,
    "accepted_batch_roi": 4.255639676004648,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 4,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 4.293139676004648,
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
    "selected_batch_threshold": 0.5228214859962463,
    "selected_candidate_threshold": 0.2776198979179778,
    "selected_threshold": 0.5228214859962463,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.526053922730463,
    "validation_loss": 6.148751474790946
  },
  "best_overall_epoch": {
    "accepted_batch_count": 10,
    "accepted_batch_roi": 23.265176677703856,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 3,
    "epoch_signal_class": "low_coverage_and_false_delay_unsafe",
    "expected_trajectory_utility": 23.275176677703858,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.09701492537313433,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.43478260869565216,
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
    "selected_batch_threshold": 0.4938751757144928,
    "selected_candidate_threshold": 0.22083025307323823,
    "selected_threshold": 0.4938751757144928,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.748102001808677,
    "validation_loss": 5.689555021519099
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 20 | 1.922835 | 0.000000 | 1.000000 | 1.000000 | 6.622838 |
| 2 | false_delay_safe_but_low_coverage | 4 | 0.794640 | 0.000000 | 1.000000 | 1.000000 | 5.990555 |
| 3 | low_coverage_and_false_delay_unsafe | 10 | 23.265177 | 0.097015 | 0.434783 | 1.000000 | 5.689555 |
| 4 | false_delay_safe_but_low_coverage | 8 | 4.255640 | 0.000000 | 1.000000 | 1.000000 | 6.148751 |
| 5 | coverage_ready_but_false_delay_unsafe | 46 | 6.367897 | 0.418182 | 0.942500 | 1.000000 | 6.166661 |
| 6 | coverage_ready_but_false_delay_unsafe | 49 | 6.342413 | 0.425373 | 0.905473 | 1.000000 | 6.585526 |
| 7 | low_coverage_and_false_delay_unsafe | 17 | 7.405960 | 0.082090 | 0.970109 | 1.000000 | 6.736951 |
| 8 | coverage_ready_but_false_delay_unsafe | 39 | 7.661405 | 0.417910 | 0.908646 | 1.000000 | 6.760715 |

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
