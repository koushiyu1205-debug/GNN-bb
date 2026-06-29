# 20260627 V554：Completion-Bound Retry / Harvest Tail 诊断

## 结论

本轮没有改 solver 行为，只增强了只读日志审计：

- 脚本：`BPC_future/scripts/audit_journey_completion_tail_profile.py`
- 输入：`BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs`
- 输出：`BPC_future/results/journey_completion_tail_profile_v554_v545_harvest_tail_20260627/summary.json`
- 自动报告：`BPC_future/logical_graph/run_reports/20260627_bpc_future_journey_completion_tail_profile_v554_v545_harvest_tail_zh.md`

V554 的核心结论是：

不能简单关闭 retry。V545 的 completion-bound retry 同时承担了两个 exact-safe 职责：

1. 找出 ordinary/profile worker 漏掉的 true-RC 负列；
2. 在没有负列时给出 `CERTIFIED_NO_NEGATIVE` 证书。

但 retry 里确实存在大量 proof-cost 压力。下一步优化应分两类推进：

- 对 `expensive_no_harvest_candidate`：优化 direct-label proof loop / completion-bound 剪枝成本；
- 对 `harvest_returned_new_task_set`：检查这些新 task-set 是否真能改善后续闭环，必要时让 branch score / tail controller 避免无效反复。

## V554 机器字段

```text
completion_retry_class_counts = {
  'completion_bound_certified_no_negative': 55,
  'completion_bound_found_negative': 2,
  'completion_bound_time_limit_no_column_uncertified': 3
}

completion_retry_harvest_tail_class_counts = {
  'expensive_no_harvest_candidate': 15,
  'harvest_replacement_only_selected': 3,
  'harvest_returned_new_task_set': 28,
  'no_harvest_candidate': 14
}

completion_retry_harvest_count_totals = {
  'harvest_candidate_negative_count': 17816,
  'harvest_candidate_new_task_set_count': 236,
  'harvest_selected_count': 287,
  'harvest_selected_new_task_set_count': 229,
  'harvest_selected_replacement_task_set_count': 58,
  'harvest_selected_support_changing_count': 229,
  'harvest_fallback_fill_count': 67
}

completion_retry_total_profile_generation_time = 8289.953808
completion_retry_total_negative_journeys = 287
completion_retry_total_selected_trips = 141
completion_retry_total_generated_sequences = 283642308
completion_retry_total_evaluated_timed_trips = 60709126
completion_retry_tail_min_fill_candidate_count = 74
completion_retry_tail_min_fill_applied_count = 0
```

## 解释

`retry` 不是普通意义上的重复尝试，而是 true-dual completion-bound final judge。关闭它以后，worker 的 `LOCAL_NO_COLUMN_UNCERTIFIED` 不能变成合法证书；如果还有 hidden negative，也不会被补出来。

V554 说明 retry 并非全部无效：

- `55` 个日志最后一次 retry 给出 certified no-negative；
- `2` 个日志最后一次 retry 找到负列；
- 全部 retry 累计发现 `287` 条 negative journey，选出 `141` 条；
- 其中 selected new task-set 为 `229`，说明它确实在扩张 RMP 方向。

但它也暴露了真正的性能压力：

- `15` 个实例属于 `expensive_no_harvest_candidate`，即花了大量 profile-generation 时间但没有可返回的 true-RC 负列；
- `28` 个实例属于 `harvest_returned_new_task_set`，说明 retry 仍在频繁充当昂贵 worker；
- `3` 个实例是 replacement-only，更多是改善已有物理代表，不一定推进 LP 方向；
- V553 的 low-min-fill smoke 已证明“更早吐少量列”会退化，因此不能把降低 min-fill 当主线。

## 对当前主线的影响

当前不应做：

- 不关 retry；
- 不把 worker no-column 当 official certificate；
- 不继续扩大 low-min-fill；
- 不把 retry 全部提前当 worker 用。

当前应做：

1. 对 `expensive_no_harvest_candidate` 样本开启小规模 profile timing，定位 direct-label proof loop 的真实热点。
2. 对 `harvest_returned_new_task_set` 样本做后续闭环贡献分析：这些 new task-set 是否降低后续 branch/CB retry 时间。
3. 在 tail action / branch score 标签中加入 retry 负担字段：`retry_profile_time`、`retry_harvest_tail_class`、`retry_selected_new_task_set_count`。
4. 后续任何 retry 触发收缩都必须 fail-closed：少触发可以，但不能把未证 worker 结果升级为证书。

## Exact-Safe 边界

V554 是 diagnostic-only：

- 不运行 BPC；
- 不运行 pricing；
- 不改 RMP；
- 不产生 official bound；
- 不产生 certificate；
- 不改变任何分支或列生成行为。

因此它只是把“retry 到底为什么贵、贵在哪里”分型清楚，为下一步 exact-safe 优化选方向。
