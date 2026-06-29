# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 16
child_probe_row_count = 6
filtered_out_child_probe_row_count = 10
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 6
child_score_map_entry_count = 3
duplicate_unscoped_key_count = 3
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v584_v583_rightcensored_mid_risk_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v584_v583_rightcensored_mid_risk_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v584_v583_rightcensored_mid_risk_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.7869102 obs=1 fathom=0.0 gain=9.527032 cpu=23.077992
- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.787680258 obs=1 fathom=0.0 gain=9.527032 cpu=23.170399
- key=node:0:depth:0:2,3:separate_vehicle pair=[2, 3] kind=separate_vehicle score=-4.765703717 obs=1 fathom=0.0 gain=0.747548667 cpu=19.825614
- key=node:0:depth:0:2,3:separate_vehicle pair=[2, 3] kind=separate_vehicle score=-4.766330975 obs=1 fathom=0.0 gain=0.747548667 cpu=19.900885
- key=node:0:depth:0:2,3:same_vehicle pair=[2, 3] kind=same_vehicle score=-5.6615303 obs=1 fathom=0.0 gain=0.363567 cpu=28.109244
- key=node:0:depth:0:2,3:same_vehicle pair=[2, 3] kind=same_vehicle score=-5.664420458 obs=1 fathom=0.0 gain=0.363567 cpu=28.456063

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
