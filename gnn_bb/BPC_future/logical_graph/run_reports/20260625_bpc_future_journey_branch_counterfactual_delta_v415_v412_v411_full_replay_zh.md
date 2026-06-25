# Journey Branch Counterfactual Delta Audit

日期：2026-06-25

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v415_v412_v411_full_replay
runbook_entry_count = 9
matched_counterfactual_count = 9
forced_pair_matched_count = 9
usable_counterfactual_training_count = 6
right_censored_counterfactual_count = 3
timeout_resolved_count = 1
timeout_regression_count = 2
label_positive_counts = {'y_counterfactual_local_improved_but_whole_run_not': 3, 'y_counterfactual_proof_cost_improved': 3, 'y_counterfactual_proof_cost_proxy_improved': 7, 'y_counterfactual_regression': 2, 'y_counterfactual_right_censored': 3, 'y_counterfactual_timeout_regression': 2, 'y_counterfactual_timeout_resolved': 1, 'y_counterfactual_wall_improved': 3}
counterfactual_label_type_counts = {'local_only_hard_negative': 3, 'regression': 2, 'strong_positive': 4}
status_pair_counts = {'OPTIMAL->EXTERNAL_TIME_LIMIT': 2, 'OPTIMAL->OPTIMAL': 3, 'TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1, 'TIME_LIMIT->OPTIMAL': 1, 'TIME_LIMIT->TIME_LIMIT': 2}
wall_improvement_positive_count = 3
budget_dominant_improvement_count = 0
local_improved_but_whole_run_not_count = 3
minimal_counterfactual_signal_ready = true
strict_counterfactual_training_ready = false
strong_positive_count = 4
strong_positive_context_count = 2
strong_positive_instance_count = 2
strong_positive_time_window_family_count = 1
positive_holdout_context_count = 0
counterfactual_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
