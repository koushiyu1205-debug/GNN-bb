# V143-V146: apollo 前缀 branch replay 负结果

## 目的

V141 说明 no-column D 类 early branch 不能全局打开。为了继续沿 branch pair / child ordering 主线推进，本轮从 V141 前 4 个 `greedy-anchor/apollo15_20km` 失败日志中抽取 high-risk branch candidates，尝试用 forced-pair replay 找新的 timeout-resolved 正例。

## V141 Branch-Impact 审计

```text
audit = BPC_future/results/journey_branch_impact_audit_v141_prefix4_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_v141_prefix4_zh.md
branch_count = 30
candidate_log_branch_count = 30
right_censored_branch_count = 30
usable_branch_impact_training_count = 0
```

聚合信号：

```text
tail_class_counts:
  completion_bound_tail = 16
  unprocessed_children = 11
  negative_chain_continues = 2
  early_branch_continues = 1

total_child_completion_bound_retries = 75
total_child_exact_pricing_events = 123
total_child_negative_pricing_events = 114
total_child_fathom_events = 1
max_child_corrected_bound_gain = 19.255997
```

解释：这些日志包含大量 child proof-cost 信号，但全部 right-censored，不能直接作为完整训练标签。

## V143 Runbook

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v143_v141_prefix4_depth01_20260624
entry_count = 12
candidate_event_count_seen = 30
candidate_event_count_with_replay_entries = 6
depth_filter_skip_count = 19
alt_pairs_per_event = 2
time_limit = 220
```

前 4 条执行项：

| idx | instance | source | forced pair | result |
| --- | --- | --- | --- | --- |
| 001 | `seed61103` | depth1 node2 | `[12,13]` | `EXTERNAL_TIME_LIMIT / 220.020s` |
| 002 | `seed61103` | depth1 node2 | `[4,12]` | `EXTERNAL_TIME_LIMIT / 220.021s` |
| 003 | `seed61205` | root node0 | `[3,13]` | `EXTERNAL_TIME_LIMIT / 220.022s` |
| 004 | `seed61205` | root node0 | `[3,14]` | `EXTERNAL_TIME_LIMIT / 220.023s` |

## V144-V146 审计

Branch-impact:

```text
branch_impact = BPC_future/results/journey_branch_impact_audit_v144_v143_first4_20260624
branch_count = 12
forced_pair_branch_count = 2
forced_pair_matched_branch_count = 2
right_censored_branch_count = 12
usable_branch_impact_training_count = 0
tail_class_counts = {completion_bound_tail: 6, unprocessed_children: 6}
total_child_completion_bound_retries = 31
total_child_exact_pricing_events = 45
total_child_negative_pricing_events = 58
```

Counterfactual delta:

```text
delta = BPC_future/results/journey_branch_counterfactual_delta_v145_v143_first4_20260624
matched_counterfactual_count = 2
forced_pair_matched_count = 2
status_pair_counts = {EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT: 2}
timeout_resolved_count = 0
usable_counterfactual_training_count = 0
right_censored_counterfactual_count = 2
proof_cost_proxy_improved = 2
```

Ranking:

```text
ranking = BPC_future/results/journey_branch_counterfactual_ranking_v146_v145_first4_20260624
context_count = 1
ranking_pair_count = 0
ranking_training_ready = false
```

## 结论

这批 replay 没有找到新的正例。apollo 前缀的 high-risk branch-impact priority 能指出证明尾部重的位置，但不能直接当作正例发现器。继续用 220s full replay 盲扫，会产生大量 right-censored hard negatives，性价比低。

下一步应调整为：

- 用 limited strong branching / fixed-expansion child probe 代替完整 220s replay；
- 给每个候选 pair 固定预算，直接记录 child corrected LB gain、child proof CPU、CB retry、time-to-certificate；
- 把 right-censored 行作为删失样本，不作为失败或正例；
- 同时推进 incumbent / cuts / formulation，因为这些 apollo 节点大量处于 `z_RMP < UB`，pricing proof 本身不能 fathom。
