# BPC_future Exact-context Capture Status 审计

日期：2026-06-13

## 目标

本报告只审计当前 exact-context capture / replay 数据是否足够进入
selector calibration。它不运行 BPC，不改变求解路径，不产生 certificate，也不证明
production speedup。

## 结论

```text
exact_context_capture_and_replay_dataset = ready_for_selector_calibration_attempt
addition_before_selector = calibrated_candidate_available_not_production_validated
production_candidate_ab = blocked_until_selector_holdout_and_20_speedup
```

解释：

- observational replay candidates 最初不是 replay-ready；
- 现在 planned capture targets 已经形成 exact coverage；
- replay dataset 中同时存在 high-impact 与 noop candidates；
- 因此可以进入 calibration-only selector 工作；
- 但还没有 production-validated selector，也没有 20-task wall-time speedup 证据。

## 关键数字

```text
initial_ready_candidate_count = 0
target_count = 3
initial_exact_covered = 2
after_target002_exact_covered = 3
after_target002_uncovered = 0
ready_case_count = 70
candidate_row_count = 202
high_impact_candidate_count = 143
noop_candidate_count = 59
full_batch_improved_count = 61
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
selector_false_positive_count = 22
selector_false_negative_count = 31
production_validated_selector = False
```

## 当前边界

这一关最多证明：

> capture/replay 数据已经足够支持下一轮 calibration-only selector attempt。

它不能证明：

- selector 可以上线；
- worker 可以默认启用；
- certificate gate 可以打开；
- 5/10 不退化；
- 20 wall-time / gap / status / final-judge tail 已改善。

## 下一步门槛

```text
calibration_only_until_selector_passes = true
required_selector_holdouts = context / instance / dataset
selector_feature_scope = addition_before_only
```

只有 addition-before selector 同时通过这些 holdout 后，才允许进入 full BPC A/B。
