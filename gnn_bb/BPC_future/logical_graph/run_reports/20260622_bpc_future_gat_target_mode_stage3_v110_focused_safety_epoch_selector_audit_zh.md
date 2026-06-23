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
    "accepted_batch_count": 101,
    "accepted_batch_roi": 4.480919954080554,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 5,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 4.51755361744689,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.04195804195804196,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9929988331388565,
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
    "selected_batch_threshold": 0.5856167674064636,
    "selected_candidate_threshold": 0.18894951152091136,
    "selected_threshold": 0.5856167674064636,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.4928309243267286,
    "validation_loss": 3.102272393723029
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 11,
    "accepted_batch_roi": 11.667098435488613,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 8,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 11.685280253670431,
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
    "selected_batch_threshold": 0.7114347219467163,
    "selected_candidate_threshold": 0.45149831826078507,
    "selected_threshold": 0.7114347219467163,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.199237736493246,
    "validation_loss": 3.4082596505207845
  },
  "best_overall_epoch": {
    "accepted_batch_count": 11,
    "accepted_batch_roi": 11.667098435488613,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 8,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 11.685280253670431,
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
    "selected_batch_threshold": 0.7114347219467163,
    "selected_candidate_threshold": 0.45149831826078507,
    "selected_threshold": 0.7114347219467163,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.199237736493246,
    "validation_loss": 3.4082596505207845
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 25 | 6.418822 | 0.000000 | 1.000000 | 1.000000 | 4.055039 |
| 2 | false_delay_safe_but_low_coverage | 17 | 9.131482 | 0.000000 | 1.000000 | 1.000000 | 3.152942 |
| 3 | false_delay_safe_but_low_coverage | 17 | 9.131482 | 0.000000 | 1.000000 | 1.000000 | 3.009320 |
| 4 | false_delay_safe_but_low_coverage | 12 | 7.632101 | 0.000000 | 1.000000 | 1.000000 | 2.983236 |
| 5 | coverage_ready_but_false_delay_unsafe | 101 | 4.480920 | 0.041958 | 0.992999 | 1.000000 | 3.102272 |
| 6 | false_delay_safe_but_low_coverage | 12 | 7.632101 | 0.000000 | 1.000000 | 1.000000 | 3.657798 |
| 7 | false_delay_safe_but_low_coverage | 15 | 9.648632 | 0.000000 | 1.000000 | 1.000000 | 3.615839 |
| 8 | false_delay_safe_but_low_coverage | 11 | 11.667098 | 0.000000 | 1.000000 | 1.000000 | 3.408260 |

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
