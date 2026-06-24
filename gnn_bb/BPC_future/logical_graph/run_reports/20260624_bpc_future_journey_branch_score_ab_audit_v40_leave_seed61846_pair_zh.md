# Journey Branch Score A/B Audit

日期：2026-06-24

## 目的

汇总 branch-score opt-in A/B 的实际分支选择和 proof-cost 差异。该脚本只读已完成的 CSV / JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
paired_instance_count = 1
both_optimal_count = 1
selected_pair_changed_count = 0
branch_score_used_count = 0
wall_improved_count = 1
wall_regressed_count = 0
wall_time_delta_sum = -29.421475
exact_pricing_calls_delta_sum = 0.0
node_count_delta_sum = 0.0
production_ready = False
official_bound_effect = False
```

## Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json, baseline_selected=[2, 5], optin_selected=[2, 5], score=None, source=None, wall_delta=-29.421475, exact_delta=0.0, node_delta=0.0

## 边界

该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。
