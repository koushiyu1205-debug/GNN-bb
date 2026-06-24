# Journey Child Score Map

日期：2026-06-24

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 20
child_probe_row_count = 18
filtered_out_child_probe_row_count = 2
skipped_row_count = 0
child_score_row_count = 10
child_score_map_entry_count = 10
key_scope = node_depth
include_log_contains = ['greedy-anchor']
exclude_log_contains = []
include_unstarted = False
solver_child_priority_mode = child_score
solver_score_map_path = BPC_future/results/journey_child_score_map_v159_v114_positive_chain_20260624/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:2:depth:1:8,12:separate_vehicle pair=[8, 12] kind=separate_vehicle score=6.915182806 obs=3 fathom=3.0 gain=5.109067 cpu=69.151798
- key=node:0:depth:0:2,6:same_vehicle pair=[2, 6] kind=same_vehicle score=6.734998341 obs=3 fathom=3.0 gain=2.0602652 cpu=60.846962
- key=node:2:depth:1:8,12:same_vehicle pair=[8, 12] kind=same_vehicle score=6.733446875 obs=3 fathom=3.0 gain=1.688514 cpu=52.483461
- key=node:6:depth:2:2,6:separate_vehicle pair=[2, 6] kind=separate_vehicle score=6.658329133 obs=1 fathom=1.0 gain=0.0 cpu=17.000504
- key=node:2:depth:1:6,8:same_vehicle pair=[6, 8] kind=same_vehicle score=6.623259875 obs=1 fathom=1.0 gain=0.0 cpu=21.208815
- key=node:6:depth:2:2,6:same_vehicle pair=[2, 6] kind=same_vehicle score=6.56591755 obs=1 fathom=1.0 gain=0.0 cpu=28.089894
- key=node:2:depth:1:6,8:separate_vehicle pair=[6, 8] kind=separate_vehicle score=4.667440608 obs=1 fathom=0.0 gain=0.0 cpu=15.907127
- key=node:0:depth:0:2,6:separate_vehicle pair=[2, 6] kind=separate_vehicle score=4.658555331 obs=3 fathom=0.0 gain=0.0 cpu=38.920081
- key=node:0:depth:0:7,11:separate_vehicle pair=[7, 11] kind=separate_vehicle score=4.629433225 obs=1 fathom=0.0 gain=0.0 cpu=20.468013
- key=node:0:depth:0:7,11:same_vehicle pair=[7, 11] kind=same_vehicle score=4.02865595 obs=1 fathom=0.0 gain=0.0 cpu=44.561286

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_map.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
当前输出仍是 diagnostic-only；right-censored 数据可用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
