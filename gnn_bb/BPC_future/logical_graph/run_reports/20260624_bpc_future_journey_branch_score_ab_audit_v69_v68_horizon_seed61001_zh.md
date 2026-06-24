# Journey Branch Score A/B Audit

日期：2026-06-24

## 目的

汇总 branch-score opt-in A/B 的实际分支选择和 proof-cost 差异。该脚本只读已完成的 CSV / JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
paired_instance_count = 1
both_optimal_count = 0
selected_pair_changed_count = 1
branch_score_used_count = 1
wall_improved_count = 1
wall_regressed_count = 0
wall_time_delta_sum = -50.270936
exact_pricing_calls_delta_sum = 31.0
node_count_delta_sum = 7.0
production_ready = False
official_bound_effect = False
```

## Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json, baseline_selected=[2, 18], optin_selected=[7, 11], score=2.061865917, source=node:0:depth:0:7,11, wall_delta=-50.270936, exact_delta=31.0, node_delta=7.0

## 人工判断

V68 使用 `journey_branch_candidate_priority=branch_score_horizon` 和 V61 score map，没有手工设置 `journey_branch_fractionality_tie_tolerance=0.2`。root 日志显示基础 `tie_tolerance=0.0`，`effective_tie_tolerance=0.2`，候选从 `12` 个扩大到 `30` 个，并选择 score 最高的 `[7,11]`。

因此 V69 证明的是 horizon-aware branch-score opt-in 链路：score map 可以在显式 opt-in 下自动打开必要 candidate horizon，并复现 V63 的 169s `OPTIMAL`。它仍不是 random-TW 20 全量 200s gate 证据，也不改变 official bound / certificate。

## 边界

该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。
