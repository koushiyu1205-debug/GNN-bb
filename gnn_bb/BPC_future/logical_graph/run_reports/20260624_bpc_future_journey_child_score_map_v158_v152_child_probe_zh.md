# Journey Child Score Map

日期：2026-06-24

## 目的

把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 28
child_probe_row_count = 12
filtered_out_child_probe_row_count = 16
skipped_row_count = 0
child_score_row_count = 12
child_score_map_entry_count = 12
key_scope = node_depth
include_log_contains = []
exclude_log_contains = []
include_unstarted = False
solver_child_priority_mode = child_score
solver_score_map_path = BPC_future/results/journey_child_score_map_v158_v152_child_probe_20260624/journey_child_score_map.json
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## Top Child Score Rows

- key=node:0:depth:0:2,9:same_vehicle pair=[2, 9] kind=same_vehicle score=-6.766840733 obs=1 fathom=1.0 gain=3.321616 cpu=75.739672
- key=node:0:depth:0:4,5:separate_vehicle pair=[4, 5] kind=separate_vehicle score=-8.064455158 obs=1 fathom=0.0 gain=0.0 cpu=7.734619
- key=node:0:depth:0:10,18:separate_vehicle pair=[10, 18] kind=separate_vehicle score=-8.255818575 obs=1 fathom=0.0 gain=0.936492333 cpu=17.174045
- key=node:0:depth:0:2,9:separate_vehicle pair=[2, 9] kind=separate_vehicle score=-8.3431897 obs=1 fathom=0.0 gain=0.0 cpu=29.182764
- key=node:0:depth:0:1,10:separate_vehicle pair=[1, 10] kind=separate_vehicle score=-8.473840308 obs=1 fathom=0.0 gain=0.258784333 cpu=27.071661
- key=node:0:depth:0:1,10:same_vehicle pair=[1, 10] kind=same_vehicle score=-8.477657642 obs=1 fathom=0.0 gain=0.150073833 cpu=24.920689
- key=node:0:depth:0:10,18:same_vehicle pair=[10, 18] kind=same_vehicle score=-8.631968733 obs=1 fathom=0.0 gain=0.040789333 cpu=40.815192
- key=node:0:depth:0:1,20:separate_vehicle pair=[1, 20] kind=separate_vehicle score=-8.657741108 obs=1 fathom=0.0 gain=0.258784333 cpu=49.139757
- key=node:0:depth:0:9,10:separate_vehicle pair=[9, 10] kind=separate_vehicle score=-8.665472633 obs=1 fathom=0.0 gain=0.054004833 cpu=45.152832
- key=node:0:depth:0:9,10:same_vehicle pair=[9, 10] kind=same_vehicle score=-8.703004683 obs=1 fathom=0.0 gain=0.420016667 cpu=58.440962
- key=node:0:depth:0:1,20:same_vehicle pair=[1, 20] kind=same_vehicle score=-8.717984575 obs=1 fathom=0.0 gain=0.0 cpu=50.158149
- key=node:0:depth:0:4,5:same_vehicle pair=[4, 5] kind=same_vehicle score=-9.754245125 obs=1 fathom=0.0 gain=0.0 cpu=90.509415

## 使用边界

使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_map.json`。
`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。
当前输出仍是 diagnostic-only；right-censored 数据可用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。
