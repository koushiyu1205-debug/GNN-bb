# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v217_v215_random_apollo_seed61408_root2_replay_20260624
runbook_entry_count = 2
matched_counterfactual_count = 2
forced_pair_matched_count = 2
usable_counterfactual_training_count = 0
right_censored_counterfactual_count = 2
timeout_resolved_count = 0
timeout_regression_count = 0
label_positive_counts = {'y_counterfactual_local_improved_but_whole_run_not': 1, 'y_counterfactual_proof_cost_proxy_improved': 1, 'y_counterfactual_right_censored': 2}
counterfactual_label_type_counts = {'local_only_hard_negative': 1, 'unknown_right_censored': 1}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 2}
wall_improvement_positive_count = 0
budget_dominant_improvement_count = 0
local_improved_but_whole_run_not_count = 1
minimal_counterfactual_signal_ready = false
strict_counterfactual_training_ready = false
strong_positive_count = 0
strong_positive_context_count = 0
strong_positive_instance_count = 0
strong_positive_time_window_family_count = 0
positive_holdout_context_count = 0
counterfactual_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
