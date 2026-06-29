# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 92
child_probe_row_count = 38
filtered_out_child_probe_row_count = 54
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 38
child_score_map_entry_count = 22
duplicate_unscoped_key_count = 15
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v586_v585_rightcensored_mid_risk_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v586_v585_rightcensored_mid_risk_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v586_v585_rightcensored_mid_risk_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=-1.643682667 obs=1 fathom=1.0 gain=5.152441 cpu=20.900504
- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=-1.644560425 obs=1 fathom=1.0 gain=5.152441 cpu=21.005835
- key=node:1:depth:1:1,9:same_vehicle pair=[1, 9] kind=same_vehicle score=-2.187807508 obs=1 fathom=1.0 gain=0.066067 cpu=24.122509
- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.7869102 obs=1 fathom=0.0 gain=9.527032 cpu=23.077992
- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.787680258 obs=1 fathom=0.0 gain=9.527032 cpu=23.170399
- key=node:0:depth:0:6,15:same_vehicle pair=[6, 15] kind=same_vehicle score=-3.5746258 obs=1 fathom=0.0 gain=7.336421667 cpu=35.029216
- key=node:0:depth:0:6,15:same_vehicle pair=[6, 15] kind=same_vehicle score=-3.575058717 obs=1 fathom=0.0 gain=7.336421667 cpu=35.081166
- key=node:2:depth:1:2,10:same_vehicle pair=[2, 10] kind=same_vehicle score=-3.786821942 obs=1 fathom=0.0 gain=1.584195667 cpu=12.439329
- key=node:2:depth:1:2,10:same_vehicle pair=[2, 10] kind=same_vehicle score=-3.787095742 obs=1 fathom=0.0 gain=1.584195667 cpu=12.472185
- key=node:0:depth:0:1,5:separate_vehicle pair=[1, 5] kind=separate_vehicle score=-3.787312625 obs=1 fathom=0.0 gain=0.551288833 cpu=17.708447
- key=node:0:depth:0:1,5:separate_vehicle pair=[1, 5] kind=separate_vehicle score=-3.787516383 obs=1 fathom=0.0 gain=0.551288833 cpu=17.732898
- key=node:2:depth:1:2,10:same_vehicle pair=[2, 10] kind=same_vehicle score=-3.796817408 obs=1 fathom=0.0 gain=3.40460175 cpu=27.328531

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
