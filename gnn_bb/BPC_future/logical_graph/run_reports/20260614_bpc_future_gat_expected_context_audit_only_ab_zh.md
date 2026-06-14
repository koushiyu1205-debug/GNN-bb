# GAT Expected-context Audit-only A/B 报告

日期：2026-06-14

## 目标

本轮只验证一件事：

把离线 GAT embedding + kNN/OOD 通过的 `HIGH_PRIORITY` context，作为严格白名单接到
branch-price 的 sharded Pulse hidden-negative worker。

边界保持不变：

- GAT 负责 embedding / trajectory impact 表达；
- kNN/OOD 负责安全壳；
- 通过的 true-RC negative 可进入 `HIGH_PRIORITY`；
- 未通过的 true-RC negative 只能进入 `DELAY_QUEUE`，不能永久丢弃；
- GAT / kNN / OOD / worker 不产生 certificate，也不改变 official lower bound；
- 默认配置仍不启用该 worker。

## 实现摘要

在 `_run_journey_sharded_pulse_hidden_negative_worker()` 中增加一个窄口径开关：

```text
journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate
```

只有同时满足以下条件时，才允许 current-probe 在非 certificate-candidate 轮次运行：

1. `trigger == audit_signal_or_current_probe`；
2. `journey_sharded_pulse_hidden_negative_worker_expected_context_hash` 已配置；
3. 当前 true dual / cuts / branch / forbidden-signature context hash 完全匹配；
4. 上面的 allow flag 显式为 `True`；
5. current-probe 自身的 min-task / remaining-time / hard-tail fingerprint 等 guard 继续通过。

运行后日志标记：

```text
pulse_worker_signal_source = expected_context_current_probe
```

没有显式 allow flag 时，即使 context 匹配，也仍然被：

```text
pulse_worker_skip_reason = not_certificate_candidate
```

拦住。

## Focused 回归

新增/覆盖测试：

- `test_sharded_pulse_expected_context_current_probe_runs_without_certificate_candidate`
- `test_sharded_pulse_expected_context_current_probe_requires_explicit_allow_flag`
- 既有 current-probe / expected-context / GAT audit runbook tests

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_negative_runs_without_previous_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_expected_context_current_probe_runs_without_certificate_candidate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_expected_context_current_probe_requires_explicit_allow_flag \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_incomplete_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_small_fast_gate_skips \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_worker_expected_context_guard \
BPC_future.tests.test_learning_components.ContextAwareColumnSelectorTests \
BPC_future.tests.test_gat_embedding_audit_ab_results \
BPC_future.tests.test_gat_embedding_audit_ab_runbook
```

结果：

```text
Ran 14 tests in 0.075s
OK
```

语法与 whitespace：

```text
py_compile: passed
git diff --check: passed
```

## 5/10 No-regression

使用 `logical_graph/tasks_005/010` 的主线 journey config：

- `moon_trek_5_journey.yaml`
- `moon_trek_10_journey.yaml`

结果：

| scale | instance | status | primal | dual | wall |
|---:|---|---|---:|---:|---:|
| 5 | Apollo sector-wave #1 | OPTIMAL | 284.084294 | 284.084294 | 2.17s |
| 5 | Tranq sector-wave #1 | OPTIMAL | 179.982081 | 179.982081 | 2.16s |
| 10 | Apollo sector-wave #1 | OPTIMAL | 456.756326 | 456.756326 | 5.05s |
| 10 | Tranq sector-wave #1 | OPTIMAL | 330.363821 | 330.363821 | 3.57s |

日志检查：

```text
new sharded_pulse / GAT-kNN-OOD worker events = 0
journey_learning events present
```

解释：

- 旧主线 GAT dual anchor 没有被移除；
- 新的 GAT/kNN/OOD trajectory gate 没有默认启用；
- 5/10 主线结果没有被本轮 expected-context worker 改动污染。

## 20-task Audit-only A/B

### Baseline

配置：

```text
moon_trek_20_smoke.yaml
Apollo20 sector-wave #1
default current mainline
```

结果：

| status | primal | dual | wall | rmp solves | pricing calls | exact pricing |
|---|---:|---:|---:|---:|---:|---:|
| TIME_LIMIT | 740.299496 | None | 75.05s | 20 | 26 | 6 |

该 run 使用当前默认学习/主线口径，轨迹与离线 GAT capture 的
`context_hash=c488c428ee5822de` 不一致，因此不能用于触发那个离线候选。

### Expected-context probe

配置与之前 GAT capture/branch-worker observability 对齐：

```text
journey_learning_enabled = false
journey_sharded_pulse_hidden_negative_worker_enabled = true
journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled = true
journey_sharded_pulse_hidden_negative_worker_trigger = audit_signal_or_current_probe
journey_sharded_pulse_hidden_negative_worker_expected_context_hash = c488c428ee5822de
journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate = true
journey_sharded_pulse_worker_current_probe_time_limit = 0.5
```

结果：

| status | primal | dual | wall | rmp solves | pricing calls | exact pricing | columns |
|---|---:|---:|---:|---:|---:|---:|---:|
| TIME_LIMIT | 740.122399 | None | 80.60s | 12 | 17 | 7 | 257 |

worker 事件：

```text
worker_events = 12
residual_target_context_mismatch = 11
RUN = 1
```

唯一运行点：

```text
cg_iter = 7
context_hash = c488c428ee5822de
pulse_worker_signal_source = expected_context_current_probe
pulse_worker_status = INCOMPLETE_LIMIT
pulse_worker_reason = sharded_pulse_incomplete
pulse_worker_returned_journeys = 0
pulse_worker_global_certificate_capable = false
```

## 为什么第一个 GAT 候选没有继续加列

它已经继续到了在线 worker：

```text
offline GAT/kNN/OOD HIGH_PRIORITY
    -> expected context hash match
    -> branch-price current-probe worker runs at cg_iter=7
```

但当前 worker 只给了 0.5s / 20000 recursions 的 audit-only 预算，结果是：

```text
INCOMPLETE_LIMIT
returned_journeys = 0
```

所以它没有可加入 RMP 的 true-RC negative JourneyColumn。

这不是 certificate 问题，也不是 GAT 被放弃；它说明：

1. GAT/kNN/OOD 的 context guard 已经能把离线候选接到在线 probe；
2. 该 probe 在当前小预算下没有产出列；
3. 因而还没有 20-task ROI 证据；
4. 不能默认启用，也不能放开 certificate gate。

## 当前结论

当前状态是：

```text
GAT embedding signal exists
kNN/OOD safety shell exists
expected-context online trigger works
5/10 mainline no-regression passes
20 expected-context worker has no returned column yet
certificate effect remains false
default enable remains false
```

下一步应该继续做窄口径 audit-only ROI：

1. 用同一 context 白名单提高或扫描 current-probe 小预算；
2. 记录 `worker_returned_journeys / added_journeys / next RMP objective_delta / dual_l1_delta`；
3. 若仍然 0 列或无 objective/dual 改善，不能推 worker；
4. 若出现稳定 support-changing true-RC negative 并改善 20-task tail，再考虑更严格的 production tuning。

