# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 5
raw_ranking_pair_row_count = 5
include_child_probe = False
raw_child_probe_row_count = 0
child_probe_row_count = 0
child_probe_branch_row_count = 0
filtered_out_child_probe_row_count = 0
filtered_out_row_count = 0
branch_score_row_count = 4
branch_score_map_entry_count = 4
instance_count = 1
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
include_child_probe_log_contains = []
exclude_child_probe_log_contains = []
solver_priority_mode = branch_score
solver_score_path = BPC_future/results/journey_branch_score_map_v194_v193_greedy_apollo_seed61716_root_layered_replay4_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=node:0:depth:0:12,15 pair=[12, 15] score=3.4249861 wins=3 losses=0 comparisons=3
- key=node:0:depth:0:5,13 pair=[5, 13] score=-0.4597665 wins=2 losses=1 comparisons=3
- key=node:0:depth:0:5,14 pair=[5, 14] score=-2.223898925 wins=0 losses=2 comparisons=2
- key=node:0:depth:0:8,20 pair=[8, 20] score=-2.223930475 wins=0 losses=2 comparisons=2

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
