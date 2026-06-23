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
coverage_confidence_ready_epoch_count = 2
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 2, 'false_delay_safe_but_low_coverage': 6}
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
    "accepted_batch_count": 158,
    "accepted_batch_roi": 7.169939013298661,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 7,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 7.2015845829189145,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.03496503496503497,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9948400412796697,
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
    "selected_batch_threshold": 0.607864260673523,
    "selected_candidate_threshold": 0.2993163371035443,
    "selected_threshold": 0.607864260673523,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.8025256143821693,
    "validation_loss": 3.170040117337611
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 13,
    "accepted_batch_roi": 33.163724605853744,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 33.163724605853744,
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
    "selected_batch_threshold": 0.5830044746398926,
    "selected_candidate_threshold": 0.3149940616839544,
    "selected_threshold": 0.5830044746398926,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 4.816163308192468,
    "validation_loss": 4.4661149264239155
  },
  "best_overall_epoch": {
    "accepted_batch_count": 13,
    "accepted_batch_roi": 33.163724605853744,
    "attempted_update_count": 1979,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 33.163724605853744,
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
    "selected_batch_threshold": 0.5830044746398926,
    "selected_candidate_threshold": 0.3149940616839544,
    "selected_threshold": 0.5830044746398926,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 4.816163308192468,
    "validation_loss": 4.4661149264239155
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 13 | 33.163725 | 0.000000 | 1.000000 | 1.000000 | 4.466115 |
| 2 | false_delay_safe_but_low_coverage | 20 | 26.950305 | 0.000000 | 1.000000 | 1.000000 | 3.445097 |
| 3 | false_delay_safe_but_low_coverage | 18 | 26.401427 | 0.000000 | 1.000000 | 1.000000 | 3.256267 |
| 4 | false_delay_safe_but_low_coverage | 7 | 15.713709 | 0.000000 | 1.000000 | 1.000000 | 3.246889 |
| 5 | false_delay_safe_but_low_coverage | 8 | 13.815763 | 0.000000 | 1.000000 | 1.000000 | 3.356342 |
| 6 | false_delay_safe_but_low_coverage | 7 | 15.713709 | 0.000000 | 1.000000 | 1.000000 | 3.424351 |
| 7 | coverage_ready_but_false_delay_unsafe | 158 | 7.169939 | 0.034965 | 0.994840 | 1.000000 | 3.170040 |
| 8 | coverage_ready_but_false_delay_unsafe | 182 | 6.289559 | 0.146853 | 0.981457 | 1.000000 | 3.544146 |

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
