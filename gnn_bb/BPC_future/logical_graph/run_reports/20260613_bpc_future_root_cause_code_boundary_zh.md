# BPC_future Root Cause Code Boundary 审计

日期：2026-06-13

## 目标

确认当前 root-cause 诊断相关改动没有默认接入 production effect。
本审计只读源码和测试名，不运行 BPC / pricing / Pulse / RMP。

## 结论

all_checks_pass = true

关键边界：

- counterfactual_capture_guarded_by_config = true
- counterfactual_capture_diagnostic_only = true
- counterfactual_capture_default_enabled = false
- counterfactual_capture_certificate_capable = false
- counterfactual_capture_official_bound_effect = false
- profile_priority_defaults_empty = true
- experimental_profiles_not_default = true
- mainline_unvalidated_effect_default_enabled = false

## 检查项

- calibrated_true_rc_profile_is_20_only = true
- capture_driver_smoke_test_exists = true
- counterfactual_capture_diagnostic_only = true
- counterfactual_capture_enabled_only_by_cli_flag = true
- counterfactual_capture_guarded_by_config = true
- default_benchmark_capture_disabled_by_test = true
- experimental_rcc_profile_is_named_experiment = true
- journey_driver_file_exists = true
- journey_pricing_file_exists = true
- profile_priority_mapping_test_exists = true
- profile_priority_min_returned_default_zero = true
- profile_priority_selection_falls_back_to_original_path = true
- profile_priority_task_masks_default_empty = true
- roi_calibration_file_exists = true
- roi_capture_opt_in_test_exists = true
- tests_file_exists = true

## 解释

这说明当前失败不是因为把未验证 selector / worker / certificate 逻辑默认接进主线。
现有改动主要用于离线诊断、counterfactual replay capture、或显式实验 profile。

因此 root-cause 结论仍是：问题不是“没有负列”或“Pulse wiring 本身”，
而是 returned batch 与 RMP active-basis / dual / pricing trajectory 的耦合，
且当前 addition-before selector 还没有通过 production holdout 和 20-task wall-time A/B。
