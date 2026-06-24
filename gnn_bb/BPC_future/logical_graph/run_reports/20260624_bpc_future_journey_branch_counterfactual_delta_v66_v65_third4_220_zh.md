# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v66_v65_third4_220_20260624
runbook_entry_count = 12
matched_counterfactual_count = 4
forced_pair_matched_count = 4
usable_counterfactual_training_count = 0
right_censored_counterfactual_count = 4
timeout_resolved_count = 0
timeout_regression_count = 0
label_positive_counts = {'y_counterfactual_proof_cost_proxy_improved': 4, 'y_counterfactual_right_censored': 4}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 4}
wall_improvement_positive_count = 0
counterfactual_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 人工判断

V66 的 4 条 counterfactual 全部是 `EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT`，`timeout_resolved_count=0`，`usable_counterfactual_training_count=0`。虽然 `y_counterfactual_proof_cost_proxy_improved=4`，但全部 right-censored，且 wall delta 只有约 `-0.02s`，实质上是 timeout 抖动，不能作为正式 branch ranking 正例。

相对 baseline `[8,18]`：

```text
[3,17]:  wall_delta=-0.022767, child_cb_retries_delta=-4, child_negative_delta=+4, right_censored
[10,17]: wall_delta=-0.020530, child_cb_retries_delta=-4, child_negative_delta=-3, right_censored
[10,20]: wall_delta=-0.017246, child_cb_retries_delta=-4, child_negative_delta=-4, right_censored
[2,13]:  wall_delta=-0.022012, child_cb_retries_delta=-4, child_negative_delta=+3, right_censored
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。
