# Journey Branch Score A/B Audit

日期：2026-06-24

## 目的

汇总 branch-score opt-in A/B 的实际分支选择和 proof-cost 差异。该脚本只读已完成的 CSV / JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
paired_instance_count = 6
both_optimal_count = 1
selected_pair_changed_count = 1
branch_score_used_count = 1
wall_improved_count = 6
wall_regressed_count = 0
wall_time_delta_sum = -63.607674
exact_pricing_calls_delta_sum = 31.0
node_count_delta_sum = 7.0
production_ready = False
official_bound_effect = False
```

## Rows

- instance=apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json, baseline_selected=[3, 7], optin_selected=[3, 7], score=None, source=None, wall_delta=-0.003881, exact_delta=0.0, node_delta=0.0
- instance=tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json, baseline_selected=[2, 18], optin_selected=[7, 11], score=2.061865917, source=node:0:depth:0:7,11, wall_delta=-51.111395, exact_delta=31.0, node_delta=7.0
- instance=apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json, baseline_selected=[8, 18], optin_selected=[8, 18], score=None, source=None, wall_delta=-0.023123, exact_delta=0.0, node_delta=0.0
- instance=tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json, baseline_selected=[8, 13], optin_selected=[8, 13], score=None, source=None, wall_delta=-0.001972, exact_delta=0.0, node_delta=0.0
- instance=apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json, baseline_selected=[2, 3], optin_selected=[2, 3], score=None, source=None, wall_delta=-0.001681, exact_delta=0.0, node_delta=0.0
- instance=tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json, baseline_selected=None, optin_selected=None, score=None, source=None, wall_delta=-12.465622, exact_delta=0.0, node_delta=0.0

## 边界

该审计只证明 opt-in 调度和已完成 run 的差异；不能作为 random-TW 全量加速、production GAT 泛化或 official certificate 证据。
