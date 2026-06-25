# Journey Branch Cascade Plan

日期：2026-06-24

## 目的

从 canonical benchmark 结果中筛选 near-threshold OPTIMAL 实例，优先生成便宜的 child-probe / limited-strong-branching 计划，避免用完整 forced replay 盲扫正例。

## 机器字段

```text
context_count = 5
target_wall = 200.0
near_threshold_max_wall = 360.0
action_counts = {'BUILD_CHILD_PROBE_RUNBOOK': 4, 'COLLECT_TOP200_DIAG_LOG': 1}
time_window_family_counts = {'greedy-anchor': 3, 'sector-wave': 2}
runs_bpc_or_pricing = False
official_bound_effect = False
certificate_effect = False
production_ready = False
```

## 推荐 context

- greedy-anchor/apollo15_20km seed=61921 wall=213.97248 over=13.97248 action=COLLECT_TOP200_DIAG_LOG root_events=0
- sector-wave/apollo15_20km seed=61408 wall=220.160814 over=20.160814 action=BUILD_CHILD_PROBE_RUNBOOK root_events=1
- greedy-anchor/apollo15_20km seed=61716 wall=253.703779 over=53.703779 action=BUILD_CHILD_PROBE_RUNBOOK root_events=1
- sector-wave/tranquillitatis_balmer_like_20km seed=61308 wall=287.679798 over=87.679798 action=BUILD_CHILD_PROBE_RUNBOOK root_events=1
- greedy-anchor/tranquillitatis_balmer_like_20km seed=61001 wall=327.745824 over=127.745824 action=BUILD_CHILD_PROBE_RUNBOOK root_events=1

## 边界

该计划只生成下一步采样命令，不运行 solver，不产生 official bound/certificate，也不能作为性能达标证据。
