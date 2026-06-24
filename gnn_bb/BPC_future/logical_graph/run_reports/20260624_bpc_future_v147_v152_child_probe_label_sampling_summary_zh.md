# V147-V152 Child-Probe 标签采样总结

日期：2026-06-24

## 结论

V147-V152 没有证明 20 规模性能改善，也没有产出 production-ready branch-impact 训练标签。它们完成的是 branch pair / child ordering 方向的下一步基础设施：从 full replay 改成固定预算 child-probe，并开始得到 right-censored 的 child proof-cost proxy。

当前最有价值的信号是 V152：

```text
audit = BPC_future/results/journey_branch_impact_audit_v152_v151_child_probe_root_early180_20260624
branch_count = 14
child_probe_row_count = 28
forced_pair_branch_count = 6
forced_pair_matched_branch_count = 6
right_censored_branch_count = 14
usable_branch_impact_training_count = 0
total_child_negative_pricing_events = 65
total_child_exact_pricing_events = 44
total_child_completion_bound_retries = 43
total_child_fathom_events = 1
max_child_corrected_bound_gain = 3.321616
```

这些行只能作为删失 proxy 或采样导航，不能当完整反事实标签。

V153 已把 V152 的 child-probe rows 转成一份 diagnostic-only proxy score map：

```text
score_map = BPC_future/results/journey_branch_score_map_v153_v152_child_probe_proxy_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_score_map_v153_v152_child_probe_proxy_zh.md
raw_child_probe_row_count = 28
child_probe_branch_row_count = 14
branch_score_map_entry_count = 11
production_ready = false
```

由于默认公式对 right-censored 行施加强惩罚，所有候选仍是负分；`[2,9]` 只是最高的负分：

```text
node:0:depth:0:2,9   score=-8.110030433
node:0:depth:0:10,18 score=-8.895945175
node:0:depth:0:1,10  score=-8.981512717
node:0:depth:0:1,20  score=-9.375725683
node:0:depth:0:9,10  score=-9.379278283
node:0:depth:0:4,5   score=-9.818700283
```

这份 map 不能接 solver opt-in；它的用途是帮助挑下一批 longer probe / replay 候选。

V154-V155 又把同父节点 child-probe proxy 转成相对排序。新增脚本：

```text
script = BPC_future/scripts/audit_journey_branch_child_probe_proxy_ranking.py
test = BPC_future/tests/test_journey_branch_child_probe_proxy_ranking.py
```

V155 使用 `min_started_child_count=1` 过滤掉未启动 child 的空观测：

```text
proxy = BPC_future/results/journey_branch_child_probe_proxy_ranking_v155_v152_started_only_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_child_probe_proxy_ranking_v155_v152_started_only_zh.md
raw_child_probe_row_count = 28
raw_proxy_branch_row_count = 11
proxy_branch_row_count = 6
filtered_out_proxy_branch_row_count = 5
proxy_context_count = 2
proxy_ranking_pair_count = 6
right_censored_proxy_ranking_pair_count = 6
sampling_navigation_ready = true
ranking_training_ready = false
```

当前采样优先级：

```text
seed61000 node0:
  [2,9]  > [4,5]
  [2,9]  > [9,10]
  [9,10] > [4,5]

seed61103 node0:
  [10,18] > [1,20]
  [1,10]  > [1,20]
  [10,18] > [1,10]
```

这些仍是 right-censored proxy；用途是决定下一批 longer limited strong branching / replay 的优先级。

V156-V157 对 V155 的两个 top proxy pair 做了 600s full replay 验证，结果为负：

```text
seed61000 [2,9]   -> EXTERNAL_TIME_LIMIT 600.02s
seed61103 [10,18] -> EXTERNAL_TIME_LIMIT 600.02s

audit = BPC_future/results/journey_branch_impact_audit_v157_v156_longer_proxy_replay_20260624
forced_pair_matched_count = 2
right_censored_branch_count = 19
usable_branch_impact_training_count = 0
```

报告：

```text
BPC_future/logical_graph/run_reports/20260624_bpc_future_v156_v157_longer_proxy_replay_negative_zh.md
```

因此 V155 的 top proxy 不能升级为 production score map。它只能说明 `[2,9]` 有局部 child fathom / corrected gain 信号，但 full replay 仍不能解决 seed61000；`[10,18]` 对 seed61103 更弱，也未解决 timeout。

## V147/V148

V147 给 `build_journey_branch_candidate_replay_runbook.py` 增加 `probe_mode=child_probe`：

```text
default probe_max_nodes = source_depth + 1 + probe_extra_nodes_after_branch
probe_extra_nodes_after_branch = 2
optional probe_max_cg_iterations
```

child-probe 命令会打开 audit 字段，同时显式关闭 corrected-bound fathom 和 tail-action early branch 行为：

```text
journey_tail_action_audit_enabled=True
journey_corrected_node_bound_audit_enabled=True
journey_corrected_node_bound_fathom_enabled=False
journey_tail_action_early_branch_enabled=False
journey_tail_action_no_column_early_branch_enabled=False
```

第一次执行 V147 时设置了 `probe_max_cg_iterations=8`，结果 16 条都停在 root CG，审计得到：

```text
branch_count = 0
child_probe_row_count = 0
```

这说明 branch probe 不能用过紧的全局 CG cap。还没到源分支时，固定预算只会采到 root incomplete。

## V149/V150

V149 去掉 CG cap，只采 root event：

```text
runbook = BPC_future/results/journey_branch_candidate_child_probe_runbook_v149_v141_apollo_root_only_20260624
entry_count = 8
time_limit = 220
probe_max_nodes = 3
```

V150 审计：

```text
branch_count = 10
child_probe_row_count = 20
forced_pair_branch_count = 4
forced_pair_matched_branch_count = 4
right_censored_branch_count = 10
usable_branch_impact_training_count = 0
max_child_corrected_bound_gain = 0.706092833
```

结论：forced pair 能绑定，child probe 能产生 proof-cost 行，但 `220s` 对晚分支不够。seed61308 的源分支时间约 `262s`，在 220s 预算内根本到不了源分支。

## V151/V152

V151 给 runbook 生成器增加源事件时间过滤：

```text
--max-source-event-time
source_event_time
source_event_time_filter_skip_count
```

生成 root early180 runbook：

```text
runbook = BPC_future/results/journey_branch_candidate_child_probe_runbook_v151_v141_apollo_root_early180_20260624
max_source_event_time = 180.0
candidate_event_count_seen = 30
depth_filter_skip_count = 26
source_event_time_filter_skip_count = 1
excluded_entry_skip_count = 8
entry_count = 9
```

实际先跑了 seed61103 和 seed61000 的 6 条。直接 root child probe 观测：

```text
[1,10]:
  same     gain=0.150073833, neg=2, exact=2, retry=3, cpu=24.920689, fathom=0
  separate gain=0.258784333, neg=4, exact=3, retry=3, cpu=27.071661, fathom=0

[10,18]:
  same     gain=0.040789333, neg=4, exact=3, retry=3, cpu=40.815192, fathom=0
  separate gain=0.936492333, neg=2, exact=2, retry=3, cpu=17.174045, fathom=0

[1,20]:
  same     gain≈0, neg=2, exact=2, retry=3, cpu=50.158149, fathom=0
  separate gain=0.258784333, neg=8, exact=5, retry=3, cpu=49.139757, fathom=0

[9,10]:
  same     gain=0.420016667, neg=1, exact=3, retry=3, cpu=58.440962, fathom=0
  separate gain=0.054004833, neg=4, exact=4, retry=3, cpu=45.152832, fathom=0

[4,5]:
  same     gain=0, neg=18, exact=12, retry=10, cpu=90.509415, fathom=0
  separate gain=0, neg=4, exact=1, retry=0, cpu=7.734619, fathom=0

[2,9]:
  same     gain=3.321616, neg=9, exact=6, retry=8, cpu=75.739672, fathom=1
  separate gain=0, neg=7, exact=1, retry=1, cpu=29.182764, fathom=0
```

## 下一步

1. 保留 `--max-source-event-time`，后续 child-probe runbook 必须避免预算内到不了源分支的 late events。
2. 不再使用全局很小的 `probe_max_cg_iterations`；如果要限制预算，应改成 `source_event_time + post_branch_window` 或按节点数/子节点 proof window 控制。
3. V156/V157 已证明 `[2,9]`、`[10,18]` 不能直接升级为 full replay 正例；下一步不要继续围绕这两个 pair 盲加预算。
4. child-probe proxy 只能作为候选优先级提高的 proxy，不是完整强正例；若要进生产 score map 或 opt-in，必须补 timeout-resolved replay 或其他 exact-safe 正例。
5. 这条线仍服务于 branch pair / child ordering；20-scale 200s OPTIMAL 还需要 Tail Action Controller、incumbent/cuts/formulation 并行推进。
