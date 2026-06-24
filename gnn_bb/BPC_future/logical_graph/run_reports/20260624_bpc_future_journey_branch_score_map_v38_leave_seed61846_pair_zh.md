# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 3
raw_ranking_pair_row_count = 6
filtered_out_row_count = 3
branch_score_row_count = 5
branch_score_map_entry_count = 5
instance_count = 2
key_scope = pair
include_instance_contains = []
exclude_instance_contains = ['seed61846']
solver_priority_mode = branch_score
solver_score_path = BPC_future/results/journey_branch_score_map_v38_leave_seed61846_pair_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=1,18 pair=[1, 18] score=1.860969667 wins=1 losses=0 comparisons=1
- key=1,4 pair=[1, 4] score=-1.860969667 wins=0 losses=1 comparisons=1
- key=7,11 pair=[7, 11] score=-1.2185835 wins=0 losses=1 comparisons=1
- key=6,7 pair=[6, 7] score=1.12530895 wins=2 losses=0 comparisons=2
- key=7,10 pair=[7, 10] score=-1.0320344 wins=0 losses=1 comparisons=1

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
当前 score map 聚合了多个实例；在没有在线模型泛化验证前，不应直接作为 production 配置批量使用。
