# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v29_v24_v25_alt01_alt02_alt07_to_alt10_20260624
runbook_entry_count = 12
matched_counterfactual_count = 6
forced_pair_matched_count = 6
label_positive_counts = {'y_counterfactual_proof_cost_improved': 1, 'y_counterfactual_regression': 4, 'y_counterfactual_wall_improved': 2}
status_pair_counts = {'OPTIMAL->OPTIMAL': 6}
wall_improvement_positive_count = 2
counterfactual_training_ready = true
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 边界

这些 delta row 只能训练或评估 branch 候选排序；不能作为剪枝依据、no-negative certificate、official bound 或 exact pricing 替代品。

## 关键 delta

```text
entry 01: [2,5] -> [3,18], wall_time_delta = -89.781081s, exact_pricing_calls_delta = -18, node_count_delta = -4, pricing_calls_delta = -29, child_negative_pricing_events_delta = 0, y_counterfactual_wall_improved = 1, y_counterfactual_proof_cost_improved = 1
entry 02: [2,5] -> [5,8],  wall_time_delta = +140.922309s, exact_pricing_calls_delta = +35, node_count_delta = +8, pricing_calls_delta = +49, child_negative_pricing_events_delta = -3, y_counterfactual_regression = 1
entry 07: [1,2] -> [1,18], wall_time_delta = -4.178415s, exact_pricing_calls_delta = 0, node_count_delta = 0, pricing_calls_delta = 0, child_negative_pricing_events_delta = +1, y_counterfactual_wall_improved = 1
entry 08: [1,2] -> [1,4],  wall_time_delta = +11.479765s, exact_pricing_calls_delta = +6, node_count_delta = +2, pricing_calls_delta = +7, child_negative_pricing_events_delta = -5, y_counterfactual_regression = 1
entry 09: [5,6] -> [6,7],  wall_time_delta = +65.673870s, exact_pricing_calls_delta = +13, node_count_delta = +4, pricing_calls_delta = +18, child_negative_pricing_events_delta = -2, y_counterfactual_regression = 1
entry 10: [5,6] -> [7,11], wall_time_delta = +78.788880s, exact_pricing_calls_delta = +13, node_count_delta = +4, pricing_calls_delta = +18, child_negative_pricing_events_delta = -2, y_counterfactual_regression = 1
```

## 判断

同一个 greedy root baseline `[2,5]` 下已经形成强正/强负候选对：`[3,18]` 明显加速，`[5,8]` 明显退化。尤其是 `[5,8]` 的局部 child negative pricing events 更少，但全局 exact pricing、node 和 wall-time 都更差。因此 branch-impact 排序标签必须使用同 parent context 的 counterfactual proof-cost / wall delta，不能用 child negative count、pool width 或 absolute tail class 代替。
