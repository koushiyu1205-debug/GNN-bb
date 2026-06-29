# V644-V646 RouteOpt-BKF Branch Candidate Probe Status

## 本轮做了什么

基于 RouteOpt 调研结论，本轮没有直接改 solver 剪枝逻辑，而是在离线 forced replay / child-probe 采样线上增加了一个 `candidate_selection=routeopt_bkf` 模式。

这个模式只影响“下一批要测试哪些 Ryan-Foster alternative pair”，不运行 BPC / pricing / RMP，不产生 official bound，不产生 certificate。

新增字段：

- `source_alt_routeopt_bkf_score`
- `source_alt_routeopt_bkf_reason`
- `source_alt_selection_reason=routeopt_bkf_test_priority`

评分综合：

- branch score；
- fractionality；
- required tie tolerance；
- child width / total width / balance gap；
- incumbent disagreement；
- candidate rank。

目标是把 child-probe / full replay 预算优先花在“接近当前选择、结构不过宽、可能改善 proof-tail”的候选上。

## 代码与测试

修改：

- `BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py`
- `BPC_future/tests/test_journey_branch_candidate_replay_runbook.py`

验证：

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest BPC_future.tests.test_journey_branch_candidate_replay_runbook
Ran 16 tests in 0.127s
OK
```

## V644 Runbook

输出：

- `BPC_future/results/journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_20260628/`
- `BPC_future/logical_graph/run_reports/20260628_bpc_future_journey_branch_candidate_replay_runbook_v644_v545_routeopt_bkf_child_probe_zh.md`

输入：

- V545 full60 logs
- V573 retry-tax branch-impact rows

设置：

- `candidate_selection=routeopt_bkf`
- `candidate_source=both`
- `paired_probe=True`
- `probe_mode=child_probe`
- `probe_max_cg_iterations=36`
- `probe_extra_nodes_after_branch=5`
- `max_source_depth=2`
- `max_source_event_time=180`
- `max_events_per_instance=1`

结果：

```text
candidate_event_count_seen = 566
branch_impact_priority_context_count = 566
candidate_event_count_with_replay_entries = 24
paired_group_count = 24
paired_baseline_entry_count = 24
paired_alternative_entry_count = 48
entry_count = 72
diagnostic_only = true
official_bound_effect = false
certificate_effect = false
```

## V645/V646 Smoke

只执行 V644 前 6 条命令，即 2 个 paired groups：

- 2 baseline
- 4 alternatives

全部命令返回码为 0，求解状态均为 `TIME_LIMIT`。

V645 branch-impact audit：

```text
branch_count = 44
right_censored_branch_count = 44
complete_label_branch_count = 0
forced_pair_branch_count = 15
forced_pair_matched_branch_count = 15
tail_class_counts = {'completion_bound_tail': 21, 'unprocessed_children': 23}
total_child_completion_bound_retries = 137
total_child_negative_pricing_events = 236
total_child_fathom_events = 1
max_child_corrected_bound_gain = 29.124763
usable_branch_impact_training_count = 0
```

V646 paired summary：

```text
result_available_entry_count = 6
observed_alternative_entry_count = 4
label_counts = {'neutral_proxy': 4, 'missing_result': 44}
production_ready = false
official_bound_effect = false
```

已观测的两个 groups：

| group | baseline pair | best alt | wall gain | child CB retry gain | label |
|---|---:|---:|---:|---:|---|
| sector/apollo seed61000 depth1 node2 | `[5,8]` | `[8,15]` | `+21.773378s` | `+5` | neutral_proxy |
| greedy/tranquillitatis seed61635 depth2 node5 | `[2,5]` | `[2,12]` | `+29.792059s` | `0` | neutral_proxy |

## 解释

这次结果说明 `routeopt_bkf` 不是随机乱采。它选到的两个 observed groups 都有 wall-time 改善，其中一个还减少了 5 次 child completion-bound retry。

但它也没有找到强正例：

- 没有 full solve positive；
- 没有 complete child-probe label；
- 全部 branch rows 仍是 right-censored；
- paired summary 只有 `neutral_proxy`。

因此这批数据不能直接训练 production branch score，只能作为：

- 采样策略 smoke；
- hard/neutral auxiliary；
- 下一批 full replay 或更深 paired probe 的候选来源。

## 当前判断

RouteOpt-BKF 方向是有用的，但第一版 scoring 还偏保守，采到的是“中性改善候选”，不是能把 hard case 推到 OPTIMAL 的关键 pair。

下一步不应该马上把 V644 结果上线为 score map，而应该：

1. 跑完 V644 中剩余高优先级 groups，先扩大 observed paired groups；
2. 对 `wall gain > 20s` 或 `CB retry gain > 0` 的 groups 做 full replay；
3. 将 full replay 的 gap / incumbent / fathom / wall-time 改善转成 weak 或 strict labels；
4. 调整 `routeopt_bkf` 权重，让它更重视：
   - gap/fathom 改善；
   - child CB retry 下降；
   - incumbent 改善；
   - 避免只追求短预算 wall gain。

## Exact-Safe 边界

本轮改动和实验都不改变求解器正确性：

- 不提供 lower bound；
- 不提供 certificate；
- 不剪枝；
- 不修改 pricing oracle；
- forced replay 若 pair 不合法，仍由现有 exact-safe fallback 处理；
- child-probe 只产生右删失诊断标签。
