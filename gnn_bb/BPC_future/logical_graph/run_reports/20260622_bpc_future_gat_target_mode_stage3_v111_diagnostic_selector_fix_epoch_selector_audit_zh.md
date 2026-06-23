# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
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
    "accepted_batch_count": 37,
    "accepted_batch_roi": 13.311626392441827,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 7,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 13.345410176225611,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.01048951048951049,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9950413223140496,
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
    "selected_batch_threshold": 0.6530526876449585,
    "selected_candidate_threshold": 0.28655569665742353,
    "selected_threshold": 0.6530526876449585,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.157070807248841,
    "validation_loss": 2.6069127389770945
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 9,
    "accepted_batch_roi": 12.659979475869072,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 4,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 12.67664614253574,
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
    "selected_batch_threshold": 0.6214677691459656,
    "selected_candidate_threshold": 0.3043908622247372,
    "selected_threshold": 0.6214677691459656,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.6010020472774302,
    "validation_loss": 2.838080947849634
  },
  "best_overall_epoch": {
    "accepted_batch_count": 37,
    "accepted_batch_roi": 13.311626392441827,
    "attempted_update_count": 2557,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 7,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 13.345410176225611,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.01048951048951049,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9950413223140496,
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
    "selected_batch_threshold": 0.6530526876449585,
    "selected_candidate_threshold": 0.28655569665742353,
    "selected_threshold": 0.6530526876449585,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.157070807248841,
    "validation_loss": 2.6069127389770945
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 22 | 12.614279 | 0.000000 | 1.000000 | 1.000000 | 4.016617 |
| 2 | coverage_ready_but_false_delay_unsafe | 51 | 6.024377 | 0.010490 | 0.997329 | 1.000000 | 3.204101 |
| 3 | false_delay_safe_but_low_coverage | 12 | 11.733326 | 0.000000 | 1.000000 | 1.000000 | 2.822710 |
| 4 | false_delay_safe_but_low_coverage | 9 | 12.659979 | 0.000000 | 1.000000 | 1.000000 | 2.838081 |
| 5 | false_delay_safe_but_low_coverage | 16 | 9.238649 | 0.000000 | 1.000000 | 1.000000 | 2.705304 |
| 6 | coverage_ready_but_false_delay_unsafe | 139 | 5.865574 | 0.048951 | 0.991706 | 1.000000 | 3.310569 |
| 7 | coverage_ready_but_false_delay_unsafe | 37 | 13.311626 | 0.010490 | 0.995041 | 1.000000 | 2.606913 |
| 8 | coverage_ready_but_false_delay_unsafe | 46 | 8.855629 | 0.013986 | 0.995881 | 1.000000 | 2.630493 |

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
