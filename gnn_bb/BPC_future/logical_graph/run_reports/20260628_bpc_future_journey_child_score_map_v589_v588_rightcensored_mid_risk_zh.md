# Journey Child Score Map

日期：2026-06-28

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 196
child_probe_row_count = 82
filtered_out_child_probe_row_count = 114
right_censored_filter_skip_count = 0
skipped_row_count = 0
child_score_row_count = 82
child_score_map_entry_count = 43
duplicate_unscoped_key_count = 34
context_scoped_rows = True
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
include_right_censored = True
include_fathomed_right_censored = False
fathomed_right_censored_included_count = 0
solver_child_priority_mode = child_score
solver_score_rows_path = BPC_future/results/journey_child_score_map_v589_v588_rightcensored_mid_risk_20260628/journey_child_score_rows.json
solver_score_map_path = BPC_future/results/journey_child_score_map_v589_v588_rightcensored_mid_risk_20260628/journey_child_score_rows.json
legacy_unscoped_score_map_path = BPC_future/results/journey_child_score_map_v589_v588_rightcensored_mid_risk_20260628/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:0:depth:0:1,3:same_vehicle pair=[1, 3] kind=same_vehicle score=1.353985533 obs=1 fathom=1.0 gain=18.502833 cpu=11.589728
- key=node:0:depth:0:1,3:same_vehicle pair=[1, 3] kind=same_vehicle score=1.353695758 obs=1 fathom=1.0 gain=18.502833 cpu=11.624501
- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=-1.643682667 obs=1 fathom=1.0 gain=5.152441 cpu=20.900504
- key=node:0:depth:0:4,8:separate_vehicle pair=[4, 8] kind=separate_vehicle score=-1.644560425 obs=1 fathom=1.0 gain=5.152441 cpu=21.005835
- key=node:1:depth:1:2,18:same_vehicle pair=[2, 18] kind=same_vehicle score=-2.035475858 obs=1 fathom=1.0 gain=3.711604 cpu=33.335599
- key=node:1:depth:1:1,9:same_vehicle pair=[1, 9] kind=same_vehicle score=-2.187807508 obs=1 fathom=1.0 gain=0.066067 cpu=24.122509
- key=node:2:depth:1:3,6:same_vehicle pair=[3, 6] kind=same_vehicle score=-2.208111233 obs=1 fathom=0.0 gain=12.99941 cpu=36.959188
- key=node:2:depth:1:3,6:same_vehicle pair=[3, 6] kind=same_vehicle score=-2.210637167 obs=1 fathom=0.0 gain=12.99941 cpu=37.2623
- key=node:1:depth:1:4,7:same_vehicle pair=[4, 7] kind=same_vehicle score=-2.634078 obs=1 fathom=0.0 gain=9.8627835 cpu=12.796164
- key=node:1:depth:1:4,7:same_vehicle pair=[4, 7] kind=same_vehicle score=-2.634229833 obs=1 fathom=0.0 gain=9.8627835 cpu=12.814384
- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.7869102 obs=1 fathom=0.0 gain=9.527032 cpu=23.077992
- key=node:1:depth:1:4,11:same_vehicle pair=[4, 11] kind=same_vehicle score=-2.787680258 obs=1 fathom=0.0 gain=9.527032 cpu=23.170399

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_rows.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
默认只接收完整 child 标签；right-censored 数据必须显式 `--include-right-censored` 才会进入 map，且只能用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
`--include-fathomed-right-censored` 只允许已启动且本 child 已被 exact-safe fathom 的右删失 child 进入局部诊断 map；它仍不是完整 branch-pair 标签。
