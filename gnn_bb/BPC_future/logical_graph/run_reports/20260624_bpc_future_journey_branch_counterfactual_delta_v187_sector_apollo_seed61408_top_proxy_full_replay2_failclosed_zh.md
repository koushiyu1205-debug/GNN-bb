# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v187_v184_sector_apollo_seed61408_top_proxy_full_replay2_failclosed_20260624
runbook_entry_count = 6
matched_counterfactual_count = 2
forced_pair_matched_count = 2
usable_counterfactual_training_count = 2
right_censored_counterfactual_count = 0
timeout_resolved_count = 0
timeout_regression_count = 2
label_positive_counts = {'y_counterfactual_regression': 2, 'y_counterfactual_timeout_regression': 2}
status_pair_counts = {'OPTIMAL->EXTERNAL_TIME_LIMIT': 1, 'OPTIMAL->TIME_LIMIT': 1}
wall_improvement_positive_count = 0
counterfactual_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
