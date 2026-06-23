# GAT Batch Impact Epoch Selector 审计报告

日期：2026-06-22

## 结论

本报告只审计训练 epoch history 中的 Stage 3 constrained selector 轨迹，
不运行 BPC、pricing、RMP、worker 或 certificate。

```text
epoch_count = 8
history_source = training_summary
min_confidence_all_success_count = 35
false_delay_safe_epoch_count = 1
coverage_confidence_ready_epoch_count = 7
coverage_and_false_delay_safe_epoch_count = 0
epoch_signal_class_counts = {'coverage_ready_but_false_delay_unsafe': 7, 'false_delay_safe_but_low_coverage': 1}
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
    "accepted_batch_count": 121,
    "accepted_batch_roi": 4.129276014370973,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": true,
    "epoch": 5,
    "epoch_signal_class": "coverage_ready_but_false_delay_unsafe",
    "expected_trajectory_utility": 4.1652264275941135,
    "false_delay_safe": false,
    "false_high_priority_on_delay": 0.04895104895104895,
    "false_safe_union_safe": false,
    "high_priority_precision": 0.9923455440131219,
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
    "selected_batch_threshold": 0.49680593609809875,
    "selected_candidate_threshold": 0.21407111110843918,
    "selected_threshold": 0.49680593609809875,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 2.985153358512665,
    "validation_loss": 5.929726594733684
  },
  "best_false_delay_safe_epoch": {
    "accepted_batch_count": 9,
    "accepted_batch_roi": 4.253915467196041,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 4.287248800529373,
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
    "selected_batch_threshold": 0.5902580618858337,
    "selected_candidate_threshold": 0.24076682309219216,
    "selected_threshold": 0.5902580618858337,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 5.045340280245756,
    "validation_loss": 5.345573652507208
  },
  "best_overall_epoch": {
    "accepted_batch_count": 9,
    "accepted_batch_roi": 4.253915467196041,
    "attempted_update_count": 1982,
    "checkpoint_gate_pass": false,
    "coverage_confidence_ready": false,
    "epoch": 1,
    "epoch_signal_class": "false_delay_safe_but_low_coverage",
    "expected_trajectory_utility": 4.287248800529373,
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
    "selected_batch_threshold": 0.5902580618858337,
    "selected_candidate_threshold": 0.24076682309219216,
    "selected_threshold": 0.5902580618858337,
    "skipped_update_count": 0,
    "stage3_full_gate_auditable": false,
    "threshold_local_gate_pass": false,
    "train_loss": 5.045340280245756,
    "validation_loss": 5.345573652507208
  }
}
```

## Epoch Rows

| epoch | class | accepted | ROI | false-delay | HP precision | safe precision | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 9 | 4.253915 | 0.000000 | 1.000000 | 1.000000 | 5.345574 |
| 2 | coverage_ready_but_false_delay_unsafe | 54 | 3.795432 | 0.017483 | 0.993873 | 1.000000 | 5.326231 |
| 3 | coverage_ready_but_false_delay_unsafe | 125 | 1.059460 | 0.038462 | 0.993268 | 1.000000 | 5.228565 |
| 4 | coverage_ready_but_false_delay_unsafe | 74 | 4.125824 | 0.066434 | 0.986778 | 1.000000 | 5.079018 |
| 5 | coverage_ready_but_false_delay_unsafe | 121 | 4.129276 | 0.048951 | 0.992346 | 1.000000 | 5.929727 |
| 6 | coverage_ready_but_false_delay_unsafe | 128 | 1.110663 | 0.111888 | 0.984398 | 1.000000 | 6.769804 |
| 7 | coverage_ready_but_false_delay_unsafe | 139 | 1.678225 | 0.048951 | 0.994073 | 1.000000 | 9.693823 |
| 8 | coverage_ready_but_false_delay_unsafe | 117 | 3.585444 | 0.062937 | 0.990441 | 1.000000 | 16.042081 |

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
