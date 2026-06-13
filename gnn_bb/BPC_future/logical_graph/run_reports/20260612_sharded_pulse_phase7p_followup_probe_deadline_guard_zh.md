# Sharded Pulse Phase 7P Follow-up Probe / Deadline Guard 报告

日期：2026-06-12

## 目标

上一轮 Phase 7O follow-up attribution 说明：

- Pulse worker 能加入 true-RC negative new task-set；
- RMP objective / primal 会改善；
- 但 worker 成功后下一轮仍进入 heuristic + exact tail，最终 exact 仍 `INCOMPLETE_LIMIT`。

本轮只做两个窄目标：

1. 修正 hidden-negative worker 的 per-call deadline guard，避免 opt-in worker 超出 solver remaining time；
2. 增加一个独立 opt-in follow-up probe profile，对比“worker 成功后继续 probe”是否比 success cooldown 更有价值。

不做：

- 默认启用 worker；
- official certificate gate；
- 增加 worker budget；
- 20/100 A/B；
- resume / parallel。

## 实现摘要

### 1. Worker call time limit 裁剪 remaining time

在 `BPC_future/solver/journey_driver.py` 中，hidden-negative worker 的 call time limit 现在会被当前 solver `remaining_time` 裁剪：

```text
worker_time_limit = min(requested_worker_time_limit, remaining_time)
```

该规则同时作用于：

- ordinary hidden-negative worker；
- current-context probe worker。

这避免了 late CG iteration 中 worker 仍拿完整 probe cap，导致 run 超出总 time limit。

新增 focused test：

- `test_sharded_pulse_hidden_negative_worker_caps_call_time_by_remaining_time`

测试通过 mock `price_journeys()` 确认：

- `worker_config.time_limit == remaining_time`
- 传入 `price_journeys()` 的 config 也被裁剪；
- `absolute_deadline` 非空。

### 2. 新增 follow-up probe profile

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增 profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup
```

它与当前较干净的 candidate profile 保持相同边界：

- 20-task only；
- pre-heuristic worker；
- current-context probe；
- impact filter；
- low-budget probe；
- stop-after-first-negative；
- default / 5 / 10 不注入 worker。

唯一差异：

- 不设置 `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds=2`。

因此 worker 成功后，下一轮仍可继续 pre-heuristic probe。

## 单实例对照

输出：

```text
BPC_future/results/sharded_pulse_phase7p_followup_probe_deadline_single_20260612/
```

Instance：

- `mt20_greedy_apollo_01`

Profiles：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup`

### 结果摘要

| profile | wall | primal | worker events | added | follow-up official pricing |
|---|---:|---:|---:|---:|---:|
| baseline | 0.179647 | 1061.554044 | 0 | 0 | 0 |
| cooldown candidate | 0.218650 | 1030.002361 | 1 | 1 | 2 |
| follow-up probe | 0.301395 | 1022.575388 | 3 | 3 | 0 |

Follow-up probe 细节：

- worker returned / added：`3 / 3`
- worker time：`0.183396`
- worker recursions：`610`
- addition classes：
  - `changed_inactive_only`
  - `changed_inactive_only`
  - `active_replacement_task_set`
- follow-up worker negative after first addition：`2`
- follow-up official pricing calls：`0`

解释：

- no-cooldown follow-up probe 能持续找到负列；
- 第三轮找到了 active replacement task-set；
- 但它用 worker 填满了预算，wall time 仍高于 baseline；
- 它改善的是 under-budget primal，不是 wall-time speedup。

## Phase 7O Gate 对照

输出：

```text
BPC_future/results/sharded_pulse_phase7p_followup_probe_gate_20260612/
```

矩阵：

- balanced 5-task 全量 20 个；
- 10-task 指定 7 个；
- 20-task smoke 3 个；
- profiles：baseline + follow-up probe。

### Gate 聚合

5-task：

- worker events：`0`
- avg wall：`0.024986 -> 0.024653`
- classes：`1 improved / 19 no_regression`

10-task：

- worker events：`0`
- avg wall：`0.117617 -> 0.117258`
- classes：`7 no_regression`

20-task：

- worker events：`3`
- added journeys：`2`
- avg wall：`0.211294 -> 0.254920`
- `mt20_greedy_apollo_01`：
  - primal：`1061.554044 -> 1022.575388`
  - worker additions：`2`
  - productivity classes：`changed_inactive_only|changed_inactive_only`

Safety：

- critical disagreement：`0`
- objective mismatch：`0`
- no official certificate side effect。

## 结论

这轮结论分两层。

### 工程修正成立

Hidden-negative worker 现在受 `remaining_time` 裁剪，避免 opt-in worker 在 late iteration 拿完整 probe cap。这个修正应保留。

### Follow-up probe 不是 production candidate

Follow-up probe 能把 `mt20_greedy_apollo_01` 的 under-budget primal 推得更低，但代价是用 worker 填满预算：

- 5/10 no-regression 成立；
- 20-task primal 有改善；
- 20-task wall time 没有 ROI；
- 这不是可以进入 production tuning 的证据。

下一步不应扩大 worker budget，也不应默认启用 worker。

更合理的下一步是：

1. 保留 deadline guard；
2. 把 follow-up probe 作为实验 profile；
3. 继续做 productivity gate，重点判断何时继续 worker 能换来 active-support-changing / strong objective movement；
4. 对 20-task 目标，只把它记录为 under-budget primal improvement signal，而不是 wall-time speedup。

## 验证

Focused tests：

```text
Ran 3 tests in 0.002s
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
