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
coverage_confidence_ready_epoch_count = 4
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 4, 'false_delay_safe_but_low_coverage': 3, 'low_coverage_and_false_delay_unsafe': 1}
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
    "accepted_batch_count": 36,
    "accepted_batch_roi": 8.336969392581118,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 8,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 8.364747170358896,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.5384615384615384,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.8908145580589255,
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
    "selected_batch_threshold": 0.5083305835723877,
    "selected_candidate_threshold": 0.15425032320414545,
    "selected_threshold": 0.5083305835723877,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.310299091966024,
    "validation_loss": 6.972434124550419
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 6,
    "accepted_batch_roi": 1.0424414624770482,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 5,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 1.084108129143715,
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
    "selected_batch_threshold": 0.6208584308624268,
    "selected_candidate_threshold": 0.3438438694400645,
    "selected_threshold": 0.6208584308624268,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.394013189074312,
    "validation_loss": 5.3761827575291505
  },
  "best_overall_epoch": {
    "accepted_batch_count": 3,
    "accepted_batch_roi": 32.52320988972982,
    "attempted_update_count": 401,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 3,
    "epoch_signal_class": "low_coverage_and_false_delay_unsafe",
    "expected_trajectory_utility": 32.52320988972982,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.0425531914893617,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.3333333333333333,
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
    "selected_batch_threshold": 0.47844576835632324,
    "selected_candidate_threshold": 0.19717147624284692,
    "selected_threshold": 0.47844576835632324,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 6.8091609757068445,
    "validation_loss": 4.720333590507695
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 6 | 0.759492 | 0.000000 | 1.000000 | 1.000000 | 5.606461 |
| 2 | false_delay_safe_but_low_coverage | 9 | 0.889054 | 0.000000 | 1.000000 | 1.000000 | 4.959888 |
| 3 | low_coverage_and_false_delay_unsafe | 3 | 32.523210 | 0.042553 | 0.333333 | 1.000000 | 4.720334 |
| 4 | coverage_ready_but_false_delay_unsafe | 46 | 6.560289 | 0.446809 | 0.923451 | 1.000000 | 6.318642 |
| 5 | false_delay_safe_but_low_coverage | 6 | 1.042441 | 0.000000 | 1.000000 | 1.000000 | 5.376183 |
| 6 | coverage_ready_but_false_delay_unsafe | 38 | 7.882191 | 0.446809 | 0.841709 | 1.000000 | 6.040967 |
| 7 | coverage_ready_but_false_delay_unsafe | 57 | 5.102844 | 0.460993 | 0.937620 | 1.000000 | 6.304507 |
| 8 | coverage_ready_but_false_delay_unsafe | 36 | 8.336969 | 0.538462 | 0.890815 | 1.000000 | 6.972434 |

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
