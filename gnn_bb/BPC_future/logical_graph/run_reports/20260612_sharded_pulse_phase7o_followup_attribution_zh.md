# Sharded Pulse Phase 7O Follow-up Tail Attribution 报告

日期：2026-06-12

## 目标

本轮不继续增加 worker budget，不启用 official certificate gate，也不改变默认 benchmark 行为。

目标是补齐 Phase 7O 的后效归因字段，回答一个更具体的问题：

> Pulse worker 加入 true-RC negative column 后，后续 RMP / heuristic / exact tail 是否真的减少？

## 实现摘要

### 1. ROI calibration 增加 follow-up attribution 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中扩展 `SUMMARY_FIELDS` 和 `_worker_followup_metrics()`。

新增字段包括：

- `followup_wall_after_worker`
- `followup_pricing_calls`
- `followup_heuristic_pricing_calls`
- `followup_exact_pricing_calls`
- `followup_exact_retry_pricing_calls`
- `followup_generated_sequences`
- `followup_evaluated_timed_trips`
- `followup_legacy_final_judge_calls`
- `followup_legacy_final_judge_time`
- `followup_completion_retry_count`
- `followup_completion_retry_time`
- `followup_hidden_negative_audit_count`
- `followup_worker_negative_after_worker_count`
- `followup_last_pricing_kind/state/reason/best_rc`

同时补齐 `pulse_worker_followup_*` mirror 字段，便于 CSV 直接筛选。

### 2. 归因口径

归因从第一个 `journey_column_addition` 且 `pricing_kind=sharded_pulse_hidden_negative_worker` 的 `cg_iter` 之后开始。

统计规则：

- worker 自身的 `journey_pricing` 不计入 follow-up official pricing；
- `cg_iter > first_worker_add_iter` 的 heuristic / exact / exact retry 计入 follow-up pricing；
- `journey_exact_pricing_completion_bound_retry` 和 `completion_bound + retry` pricing 计入 completion-bound retry；
- `followup_wall_after_worker = finish.time - first_worker_addition.time`，用于解释 worker 加列后的真实剩余 wall tail。

注意：既有 `journey_pricing.time` 字段沿用历史日志口径；本轮新增 `followup_wall_after_worker`，避免只靠单个 pricing event 的 elapsed timestamp 下结论。

### 3. 单元测试

新增 focused test：

- `test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed`

覆盖：

- 没有 worker addition 时 follow-up 字段为 None/0；
- worker 自身 pricing 不计入 follow-up；
- worker 加列后的 heuristic / exact / completion-bound retry 正确计数；
- generated/evaluated、last pricing state/reason/best_rc 正确归因。

## Follow-up Smoke

输出目录：

```text
BPC_future/results/sharded_pulse_phase7o_followup_attribution_single_20260612/
```

命令要点：

- instance：`mt20_greedy_apollo_01`
- profiles：
  - `baseline`
  - `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`
- `time_limit=0.3`
- `pricing_time_limit=0.1`
- worker / current probe 仍为 opt-in profile，不改变默认配置。

## 结果

### baseline

- status：`TIME_LIMIT`
- wall time：`0.177384`
- primal：`1061.554044`
- official pricing state：`INCOMPLETE_LIMIT`
- worker：未触发

### Pulse worker candidate

- status：`TIME_LIMIT`
- wall time：`0.222371`
- primal：`1030.002361`
- worker returned / added：`1 / 1`
- new task-set：`1`
- productivity class：`changed_inactive_only`
- worker time：`0.031997`
- worker recursions：`115`
- worker pruned total：`6056`
- next RMP objective delta：`-31.551683`
- next dual L1 delta：`77.428681`

worker 加列后的 follow-up tail：

- `followup_wall_after_worker = 0.103100`
- `followup_pricing_calls = 2`
- `followup_heuristic_pricing_calls = 1`
- `followup_exact_pricing_calls = 1`
- `followup_generated_sequences = 405`
- `followup_evaluated_timed_trips = 1577`
- `followup_legacy_final_judge_calls = 1`
- `followup_completion_retry_count = 0`
- last pricing：
  - kind：`exact`
  - state：`INCOMPLETE_LIMIT`
  - reason：`profile_dp_incomplete`
  - best RC：`0.034526`

## 解释

这次归因把 Phase 7O 的无 wall-time ROI 原因说得更清楚：

1. Pulse worker 加入的列是真实有效列，且能明显移动 RMP objective / primal；
2. 但该列被分类为 `changed_inactive_only`，没有立刻形成 active-support-changing column；
3. worker 加列后仍然触发 heuristic + exact pricing；
4. follow-up exact 仍以 `INCOMPLETE_LIMIT / profile_dp_incomplete` 结束；
5. 因此当前瓶颈不是 task ordering，而是 worker 后仍没有消掉 exact tail。

## 结论

Phase 7O 仍未满足 production tuning 条件。

当前不应做：

- 默认启用 worker；
- official certificate gate；
- 增大 worker time limit；
- 20/100 A/B；
- resume / parallel。

下一步更合理的是：

- 继续做 worker productivity / impact gate；
- 或直接分析 active-support-changing return，而不是返回 `changed_inactive_only` 列；
- 同时保留 5/10 no-regression gate。

## 验证

Focused tests：

```text
Ran 4 tests in 0.001s
OK
```

语法检查：

```text
py_compile OK
```

`git diff --check`：

```text
OK
```
