# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 27
raw_ranking_pair_row_count = 27
filtered_out_row_count = 0
branch_score_row_count = 8
branch_score_map_entry_count = 8
instance_count = 1
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
solver_priority_mode = branch_score
solver_score_path = BPC_future/results/journey_branch_score_map_v85_v84_positive_context_combined_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=node:0:depth:0:2,6 pair=[2, 6] score=3.692166045 wins=7 losses=0 comparisons=7
- key=node:0:depth:0:2,15 pair=[2, 15] score=-2.083726507 wins=2 losses=5 comparisons=7
- key=node:0:depth:0:7,15 pair=[7, 15] score=-1.927497083 wins=0 losses=6 comparisons=6
- key=node:0:depth:0:9,15 pair=[9, 15] score=-1.9273143 wins=0 losses=6 comparisons=6
- key=node:0:depth:0:6,7 pair=[6, 7] score=1.514384312 wins=6 losses=1 comparisons=7
- key=node:0:depth:0:7,11 pair=[7, 11] score=0.709450217 wins=5 losses=2 comparisons=7
- key=node:0:depth:0:7,18 pair=[7, 18] score=-0.708853364 wins=3 losses=4 comparisons=7
- key=node:0:depth:0:6,8 pair=[6, 8] score=0.18070334 wins=4 losses=3 comparisons=7

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
