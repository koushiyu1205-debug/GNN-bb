# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v192_v190_greedy_apollo_seed61716_root_layered_replay4_20260624
runbook_entry_count = 6
matched_counterfactual_count = 4
forced_pair_matched_count = 4
usable_counterfactual_training_count = 4
right_censored_counterfactual_count = 0
timeout_resolved_count = 0
timeout_regression_count = 3
label_positive_counts = {'y_counterfactual_proof_cost_improved': 1, 'y_counterfactual_proof_cost_proxy_improved': 1, 'y_counterfactual_regression': 3, 'y_counterfactual_timeout_regression': 3, 'y_counterfactual_wall_improved': 1}
counterfactual_label_type_counts = {'regression': 3, 'strong_positive': 1}
status_pair_counts = {'OPTIMAL->EXTERNAL_TIME_LIMIT': 2, 'OPTIMAL->OPTIMAL': 1, 'OPTIMAL->TIME_LIMIT': 1}
wall_improvement_positive_count = 1
budget_dominant_improvement_count = 0
local_improved_but_whole_run_not_count = 0
minimal_counterfactual_signal_ready = true
strict_counterfactual_training_ready = false
strong_positive_count = 1
strong_positive_context_count = 1
strong_positive_instance_count = 1
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
