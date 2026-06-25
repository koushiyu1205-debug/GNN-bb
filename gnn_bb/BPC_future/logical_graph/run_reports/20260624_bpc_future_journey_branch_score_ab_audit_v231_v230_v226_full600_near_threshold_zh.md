# Journey Branch Score A/B Audit

日期：2026-06-24

## 目的

汇总 branch-score opt-in A/B 的实际分支选择和 proof-cost 差异。该脚本只读已完成的 CSV / JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
paired_instance_count = 4
both_optimal_count = 4
selected_pair_changed_count = 4
branch_score_used_count = 4
wall_improved_count = 3
wall_regressed_count = 1
wall_time_delta_sum = -321.351138
exact_pricing_calls_delta_sum = -50.0
node_count_delta_sum = -10.0
production_ready = False
official_bound_effect = False
```

## Rows

- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json, baseline_selected=[4, 12], optin_selected=[12, 15], score=3.4249861, source=node:0:depth:0:12,15, wall_delta=-88.249791, exact_delta=-5.0, node_delta=-2.0
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json, baseline_selected=[2, 18], optin_selected=[2, 6], score=2.547759323, source=node:0:depth:0:2,6, wall_delta=-221.884479, exact_delta=-38.0, node_delta=-8.0
- instance=apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json, baseline_selected=[1, 6], optin_selected=[6, 16], score=1.985119013, source=node:0:depth:0:6,16, wall_delta=-34.436572, exact_delta=-4.0, node_delta=0.0
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json, baseline_selected=[12, 13], optin_selected=[2, 5], score=0.04228335, source=node:0:depth:0:2,5, wall_delta=23.219704, exact_delta=-3.0, node_delta=0.0

## 边界

该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。
