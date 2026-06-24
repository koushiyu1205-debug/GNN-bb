# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 15
raw_ranking_pair_row_count = 15
filtered_out_row_count = 0
branch_score_row_count = 6
branch_score_map_entry_count = 6
instance_count = 1
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
solver_priority_mode = branch_score
solver_score_path = BPC_future/results/journey_branch_score_map_seed61001_root_only_replay6_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=node:0:depth:0:2,15 pair=[2, 15] score=-4.080474857 wins=0 losses=5 comparisons=5
- key=node:0:depth:0:2,6 pair=[2, 6] score=3.787759323 wins=5 losses=0 comparisons=5
- key=node:0:depth:0:6,7 pair=[6, 7] score=1.263525443 wins=4 losses=1 comparisons=5
- key=node:0:depth:0:6,8 pair=[6, 8] score=-0.709548017 wins=2 losses=3 comparisons=5
- key=node:0:depth:0:7,15 pair=[7, 15] score=-0.620471237 wins=1 losses=4 comparisons=5
- key=node:0:depth:0:7,11 pair=[7, 11] score=0.359209343 wins=3 losses=2 comparisons=5

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
