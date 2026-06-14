# Next Evidence Protocol Catalog 报告

日期：2026-06-14

## 目的

本报告从 evidence ledger 抽取下一步证据协议。它只读 `summary.json`，
不运行 solver，也不改变 pricing / worker / certificate。

## 机器字段

```text
next_evidence_protocol_catalog = current
next_evidence_protocol_status = calibration_only_until_selector_passes
current_stage = calibration_only_selector_holdout
gate_order = exact_context_capture_and_replay_dataset,addition_before_selector,production_candidate_ab
exact_context_capture_and_replay_dataset_passed = true
addition_before_selector_passed = true
addition_before_selector_status = calibrated_candidate_available_not_production_validated
production_selector_validated = false
production_candidate_ab_passed = false
production_candidate_ab_status = blocked_until_production_selector_and_20_speedup_pass
selector_feature_scope = addition_before_only
required_selector_holdouts = context/instance/dataset
forbidden_shortcuts = post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect
require_5_10_no_regression_gate_before_production = true
require_selected_20_hard_repeat_ab_before_production = true
all_checks_pass = true
```

## 结论

当前下一步协议不是 production A/B，也不是默认启用 worker。可继续的是 calibration-only selector holdout：只使用 addition-before features，并且必须通过 context / instance / dataset holdout。通过后才允许进入 5/10 no-regression 与 selected 20 hard repeat A/B。
