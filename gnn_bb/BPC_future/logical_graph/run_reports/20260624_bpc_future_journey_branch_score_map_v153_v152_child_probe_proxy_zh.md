# Journey Branch Score Map

日期：2026-06-24

## 目的

把 V33 这类同 parent counterfactual ranking rows 转成 solver 的 `branch_score` opt-in 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
ranking_pair_row_count = 0
raw_ranking_pair_row_count = 0
include_child_probe = True
raw_child_probe_row_count = 28
child_probe_row_count = 28
child_probe_branch_row_count = 14
filtered_out_child_probe_row_count = 0
filtered_out_row_count = 0
branch_score_row_count = 11
branch_score_map_entry_count = 11
instance_count = 6
key_scope = node_depth
include_instance_contains = []
exclude_instance_contains = []
include_child_probe_log_contains = []
exclude_child_probe_log_contains = []
solver_priority_mode = branch_score_horizon
solver_score_path = BPC_future/results/journey_branch_score_map_v153_v152_child_probe_proxy_20260624/journey_branch_score_rows.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Score Rows

- key=node:0:depth:0:2,9 pair=[2, 9] score=-8.110030433 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:10,18 pair=[10, 18] score=-8.895945175 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:1,10 pair=[1, 10] score=-8.981512717 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:1,20 pair=[1, 20] score=-9.375725683 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:9,10 pair=[9, 10] score=-9.379278283 wins=0 losses=1 comparisons=1
- key=node:0:depth:0:4,5 pair=[4, 5] score=-9.818700283 wins=0 losses=1 comparisons=1
- key=node:1:depth:1:1,2 pair=[1, 2] score=-10.0 wins=0 losses=3 comparisons=3
- key=node:2:depth:1:12,16 pair=[12, 16] score=-10.0 wins=0 losses=1 comparisons=1
- key=node:2:depth:1:4,13 pair=[4, 13] score=-10.0 wins=0 losses=2 comparisons=2
- key=node:1:depth:1:3,7 pair=[3, 7] score=-10.0 wins=0 losses=1 comparisons=1
- key=node:2:depth:1:2,9 pair=[2, 9] score=-10.0 wins=0 losses=1 comparisons=1

## 使用边界

使用方式：`journey_branch_candidate_priority=branch_score`，并把 `journey_branch_candidate_score_path` 指向 `journey_branch_score_rows.json`。
若使用 child-probe proof-cost 分数，更建议用 `journey_branch_candidate_priority=branch_score_horizon` 且设置正分阈值，只让正分候选打开 horizon。
`branch_score` 只改变 opt-in 的 Ryan-Foster pair 排序；排序范围仍由 `journey_branch_fractionality_tie_tolerance` 决定。
它不能提供 official bound、no-negative certificate 或 fathom 依据；所有 child 最终仍必须靠 exact pricing closure。
当前 score map 聚合了多个实例；在没有在线模型泛化验证前，不应直接作为 production 配置批量使用。
