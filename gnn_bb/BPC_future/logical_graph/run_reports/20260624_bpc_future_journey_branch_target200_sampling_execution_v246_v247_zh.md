# V246 Target-200 采样执行与 V247 child-probe runbook 汇总

日期：2026-06-24

## 目的

执行 V246 选出的 canonical random-TW `tasks_020` top200 诊断命令，并把实际 branch-candidate 日志转成下一步 root child-probe runbook。该过程不启用 score-map opt-in，不启用 early-branch，不产生 official bound 或 certificate。

## V246 执行结果

```text
diag_root = BPC_future/results/journey_branch_target200_sampling_plan_v246_full600_v244_20260624/diag_runs
selected_context_count = 12
parallelism = 4

status_counts = {
  'EXTERNAL_TIME_LIMIT': 10,
  'TIME_LIMIT': 2
}

new_target_200_positive = 0
new_full_run_hard_negative = 0
```

逐 context 状态：

```text
greedy-anchor/apollo seed61205: EXTERNAL_TIME_LIMIT, wall=260.029556
greedy-anchor/apollo seed61921: TIME_LIMIT, wall=154.261481, nodes=1
random-wave/apollo seed61000: EXTERNAL_TIME_LIMIT, wall=600.016871
random-wave/apollo seed61102: EXTERNAL_TIME_LIMIT, wall=260.038144
random-wave/apollo seed61408: EXTERNAL_TIME_LIMIT, wall=600.015806
random-wave/apollo seed61919: EXTERNAL_TIME_LIMIT, wall=600.018526
random-wave/tranquillitatis seed61001: EXTERNAL_TIME_LIMIT, wall=600.015066
random-wave/tranquillitatis seed61103: EXTERNAL_TIME_LIMIT, wall=600.015974
random-wave/tranquillitatis seed61309: EXTERNAL_TIME_LIMIT, wall=600.020156
random-wave/tranquillitatis seed61411: EXTERNAL_TIME_LIMIT, wall=600.017162
random-wave/tranquillitatis seed61717: EXTERNAL_TIME_LIMIT, wall=600.015609
sector-wave/tranquillitatis seed61308: TIME_LIMIT, wall=151.211911, nodes=3
```

## 候选日志

V246 没有直接产生新的训练标签，但补到了 branch-candidate 覆盖：

```text
total_journey_branch_candidate_events = 160
root_candidate_context_count = 9
```

candidate event 分布：

```text
greedy-anchor/apollo seed61205: 0
greedy-anchor/apollo seed61921: 0
sector-wave/tranquillitatis seed61308: 1
random-wave/apollo seed61000: 18
random-wave/apollo seed61408: 18
random-wave/apollo seed61919: 11
random-wave/tranquillitatis seed61001: 26
random-wave/tranquillitatis seed61103: 17
random-wave/tranquillitatis seed61309: 26
random-wave/tranquillitatis seed61411: 34
random-wave/tranquillitatis seed61717: 9
```

解释：V246 的价值是把 random-wave family 从“缺 target-200 正例且缺候选日志”推进到“已有大量候选事件可采样”。它没有证明新的加速，也没有新增 strong positive。

## V247 Runbook

```text
output = BPC_future/results/journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_candidate_replay_runbook_v247_v246_root_child_probe_zh.md

candidate_event_count_seen = 160
depth_filter_skip_count = 151
candidate_event_count_with_replay_entries = 9
entry_count = 50
candidate_selection = layered
candidate_source = priority_top
probe_mode = child_probe
probe_max_nodes = 3
probe_max_cg_iterations = 20
time_limit = 120
official_bound_effect = false
certificate_effect = false
```

V247 只生成命令清单，不运行 BPC / pricing / RMP。下一步应先跑这 50 条 120s child-probe，做 branch-impact audit / proxy ranking，再挑少量高潜力 pair 做 full replay。不要直接把 160 个 candidate event 全量 full replay，否则大概率再次制造大量右删失样本。
