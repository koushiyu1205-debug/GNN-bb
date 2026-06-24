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
wall_time_delta_sum = -50.742462
exact_pricing_calls_delta_sum = 31.0
node_count_delta_sum = 7.0
production_ready = False
official_bound_effect = False
```

## Rows

- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json, baseline_selected=[2, 18], optin_selected=[7, 11], score=2.061865917, source=node:0:depth:0:7,11, wall_delta=-50.742462, exact_delta=31.0, node_delta=7.0

## 人工判断

V63 通过 `journey_branch_candidate_priority=branch_score` 和 `journey_branch_fractionality_tie_tolerance=0.2`，让 V61 的最高分 pair `[7,11]` 进入 root 分支选择。V44 baseline 是 220s external timeout，内部 proof-cost 字段为空；因此本报告中 `exact_delta` / `node_delta` 不能按两个完整 optimal run 的同口径差分解读。

可靠结论是：同一 canonical random-TW 20 实例上，baseline root `[2,18]` 在 220.026983s 外部超时；V63 root `[7,11]` 在 169.284521s 返回 `OPTIMAL`。这是 in-sample branch-score 链路复现，不是 random-TW 20 全量 200s gate 证据。

## 边界

该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。
