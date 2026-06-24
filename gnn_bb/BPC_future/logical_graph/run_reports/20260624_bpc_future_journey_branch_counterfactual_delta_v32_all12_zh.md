# Journey Branch Counterfactual Delta Audit

日期：2026-06-24

## 目的

把 baseline branch 选择与 forced-pair alternative replay 按同实例、同节点、同 depth 对齐，生成 wall/proof-cost delta 标签。该脚本只读既有 CSV 和审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_counterfactual_delta = current
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v32_v24_v25_all12_20260624
runbook_entry_count = 12
matched_counterfactual_count = 12
forced_pair_matched_count = 12
label_positive_counts = {'y_counterfactual_proof_cost_improved': 1, 'y_counterfactual_regression': 9, 'y_counterfactual_wall_improved': 2}
status_pair_counts = {'OPTIMAL->OPTIMAL': 12}
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
entry 01: [2,5] -> [3,18],  wall_time_delta = -89.781081s, exact_pricing_calls_delta = -18, node_count_delta = -4, pricing_calls_delta = -29, child_negative_pricing_events_delta = 0, y_counterfactual_wall_improved = 1, y_counterfactual_proof_cost_improved = 1
entry 02: [2,5] -> [5,8],   wall_time_delta = +140.922309s, exact_pricing_calls_delta = +35, node_count_delta = +8, pricing_calls_delta = +49, child_negative_pricing_events_delta = -3, y_counterfactual_regression = 1
entry 03: [2,17] -> [8,18], wall_time_delta = +77.206493s, exact_pricing_calls_delta = +21, node_count_delta = +4, pricing_calls_delta = +30, child_negative_pricing_events_delta = -4, y_counterfactual_regression = 1
entry 04: [2,17] -> [8,17], wall_time_delta = +111.093631s, exact_pricing_calls_delta = +28, node_count_delta = +4, pricing_calls_delta = +39, child_negative_pricing_events_delta = +2, y_counterfactual_regression = 1
entry 05: [3,17] -> [3,18], wall_time_delta = +1.015413s, exact_pricing_calls_delta = +2, node_count_delta = 0, pricing_calls_delta = +4, child_negative_pricing_events_delta = +4, y_counterfactual_regression = 1
entry 06: [3,17] -> [13,18], wall_time_delta = +41.544674s, exact_pricing_calls_delta = +14, node_count_delta = +4, pricing_calls_delta = +20, child_negative_pricing_events_delta = -2, y_counterfactual_regression = 1
entry 07: [1,2] -> [1,18],  wall_time_delta = -4.178415s, exact_pricing_calls_delta = 0, node_count_delta = 0, pricing_calls_delta = 0, child_negative_pricing_events_delta = +1, y_counterfactual_wall_improved = 1
entry 08: [1,2] -> [1,4],   wall_time_delta = +11.479765s, exact_pricing_calls_delta = +6, node_count_delta = +2, pricing_calls_delta = +7, child_negative_pricing_events_delta = -5, y_counterfactual_regression = 1
entry 09: [5,6] -> [6,7],   wall_time_delta = +65.673870s, exact_pricing_calls_delta = +13, node_count_delta = +4, pricing_calls_delta = +18, child_negative_pricing_events_delta = -2, y_counterfactual_regression = 1
entry 10: [5,6] -> [7,11],  wall_time_delta = +78.788880s, exact_pricing_calls_delta = +13, node_count_delta = +4, pricing_calls_delta = +18, child_negative_pricing_events_delta = -2, y_counterfactual_regression = 1
entry 11: [5,7] -> [7,10],  wall_time_delta = +1.666250s, exact_pricing_calls_delta = 0, node_count_delta = 0, pricing_calls_delta = 0, child_negative_pricing_events_delta = 0, y_counterfactual_regression = 1
entry 12: [5,7] -> [6,7],   wall_time_delta = -0.255814s, exact_pricing_calls_delta = 0, node_count_delta = 0, pricing_calls_delta = 0, child_negative_pricing_events_delta = 0, below 1s improvement threshold
```

## 判断

V25 runbook 已完整闭环：12 条 alternative 全部 OPTIMAL，全部 forced pair matched，可以作为第一批 branch-impact ranking 标签。标签分布是 2 条 wall improved、1 条 proof-cost improved、9 条 regression；真正强正例只有 entry 01，entry 07 只是弱 wall 正例。

当前 `priority_top` 直接采样多数产生 regression，说明它适合暴露 hard negative，但不足以提供大量强正例。下一步应继续在 canonical random-TW 20 上扩大同 parent counterfactual 采样，并改进候选生成，使 GAT 学到“减少全局 proof cost 的 branch pair”，而不是只学会避开局部 child negative count 或 pool width proxy。
