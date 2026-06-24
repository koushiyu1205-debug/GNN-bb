# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v30_v24_v25_alt01_alt02_alt07_to_alt12_20260624
runbook_entry_count = 12
matched_counterfactual_count = 8
forced_pair_matched_count = 8
label_positive_counts = {'y_counterfactual_proof_cost_improved': 1, 'y_counterfactual_regression': 5, 'y_counterfactual_wall_improved': 2}
status_pair_counts = {'OPTIMAL->OPTIMAL': 8}
wall_improvement_positive_count = 2
counterfactual_training_ready = true
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
