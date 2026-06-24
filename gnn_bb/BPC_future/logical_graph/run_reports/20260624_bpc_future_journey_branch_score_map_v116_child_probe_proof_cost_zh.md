# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 0
raw_ranking_pair_row_count = 0
include_child_probe = True
raw_child_probe_row_count = 90
child_probe_branch_row_count = 45
filtered_out_row_count = 0
branch_score_row_count = 39
branch_score_map_entry_count = 39
instance_count = 9
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
solver_priority_mode = branch_score_horizon
solver_score_path = BPC_future/results/journey_branch_score_map_v116_child_probe_proof_cost_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=node:2:depth:1:8,12 pair=[8, 12] score=6.536062081 wins=3 losses=0 comparisons=3
- key=node:6:depth:2:2,6 pair=[2, 6] score=6.224246683 wins=1 losses=0 comparisons=1
- key=node:0:depth:0:2,6 pair=[2, 6] score=5.393553672 wins=3 losses=0 comparisons=3
- key=node:2:depth:1:6,8 pair=[6, 8] score=5.290700483 wins=1 losses=0 comparisons=1
- key=node:0:depth:0:7,11 pair=[7, 11] score=3.658089175 wins=1 losses=0 comparisons=1
- key=node:8:depth:3:5,8 pair=[5, 8] score=-2.347690158 wins=0 losses=1 comparisons=1
- key=node:10:depth:4:5,8 pair=[5, 8] score=-2.968015842 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:5,18 pair=[5, 18] score=-3.243845925 wins=0 losses=1 comparisons=1
- key=node:3:depth:2:5,18 pair=[5, 18] score=-3.390100383 wins=0 losses=1 comparisons=1
- key=node:3:depth:2:3,5 pair=[3, 5] score=-4.243034433 wins=0 losses=1 comparisons=1
- key=node:6:depth:3:3,7 pair=[3, 7] score=-4.986099983 wins=0 losses=1 comparisons=1
- key=node:6:depth:2:2,5 pair=[2, 5] score=-5.571321133 wins=0 losses=1 comparisons=1

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
若使用 child-probe proof-cost 分数，更建议用 `journey_branch_candidate_priority=branch_score_horizon` 且设置正分阈值，只让正分候选打开 horizon。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
当前 score map 聚合了多个实例；在没有在线模型泛化验证前，不应直接作为 production 配置批量使用。
