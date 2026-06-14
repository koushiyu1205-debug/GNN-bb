# Branch-price Worker Observability 与 GAT ROI Guard 报告

日期：2026-06-14

## 目标

本轮不是放开 GAT、worker 或 certificate，而是修正一个关键观测盲点：

```text
5/10/20 主线配置均启用 journey_branching_enabled=True，
实际运行路径是 journey_branch_price。
此前 hidden-negative worker hook 只接在 root-only journey loop，
因此 worker profile 在主线 branch-price 路径上不会触发。
```

这意味着之前某些 worker ROI probe 如果没有 worker event，不能解释为
“worker 没有 ROI”；它只能说明该 run 没有真正进入 worker。

## 实现调整

在 `BPC_future/solver/journey_driver.py` 的 branch-node pricing loop 中增加
严格 opt-in hook：

```text
journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True
```

该 hook：

- 只在显式 opt-in 时启用；
- 默认配置不变；
- 复用既有 `_run_journey_sharded_pulse_hidden_negative_worker()`；
- 传入当前 node 的 branch constraints / cuts / true SCIP dual；
- worker 返回列仍经过 true-RC sanitize 和 impact filter；
- worker no-column / incomplete / skip 不产生 certificate；
- worker pricing 记录为 `pricing_kind=sharded_pulse_hidden_negative_worker`；
- worker 返回列只走正常 `_add_priced_journeys()` 加列路径；
- 不改变 official lower bound 或 no-negative certificate 语义。

新增 focused regression：

```text
test_branch_price_before_heuristic_worker_is_observable_when_opted_in
```

该测试在 branch-price very_small 上打开 opt-in skip logging，确认能观测到
`journey_sharded_pulse_hidden_negative_worker` 事件，且事件不具备 certificate
能力。

## 验证

Focused tests：

```text
Ran 12 tests in 0.085s
OK
```

覆盖：

- branch-price opt-in worker observability；
- current-probe negative / incomplete / small-fast skip；
- GAT selector `HIGH_PRIORITY / DELAY_QUEUE / REJECT_NONNEGATIVE_ONLY` 语义；
- GAT embedding audit runbook / analysis guard。

语法检查：

```text
py_compile: OK
git diff --check: OK
```

## 5/10 默认 no-regression

输出目录：

```text
BPC_future/results/gat_knn_ood_worker_roi_probe_20260614/default_no_regression_after_branch_hook
```

结果：

| 规模 | 实例 | status | primal | dual | wall time |
|---:|---|---|---:|---:|---:|
| 5 | Apollo sector-wave #1 | OPTIMAL | 284.084294 | 284.084294 | 0.588673s |
| 5 | Tranq sector-wave #1 | OPTIMAL | 179.982081 | 179.982081 | 0.576712s |
| 10 | Apollo sector-wave #1 | OPTIMAL | 456.756326 | 456.756326 | 3.188304s |
| 10 | Tranq sector-wave #1 | OPTIMAL | 330.363821 | 330.363821 | 1.949248s |

结论：

```text
5/10 默认路径仍然全部 OPTIMAL，秒级，无回归。
```

## 20 branch-path worker observability smoke

输出目录：

```text
BPC_future/results/gat_knn_ood_worker_roi_probe_20260614/task020_branch_worker_observable_probe
```

实例：

```text
BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/
apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
```

结果：

```text
status = TIME_LIMIT
primal_bound = 740.122399
dual_bound = None
wall_time = 80.587978s
pricing_calls = 16
exact_pricing_calls = 6
columns = 257
```

worker observability：

```text
worker_events = 12
pricing_worker_events = 0
addition_events = 0
skip_counts = {"not_certificate_candidate": 12}
```

解释：

- branch-price hook 已经生效；
- worker event 现在可观测；
- 但当前 `audit_signal_or_current_probe` 触发仍要求 `certificate_candidate=True`；
- 该 Apollo20 run 的 12 个 root CG rounds 都不是 certificate candidate；
- 因此 worker 只记录 skip，没有进入 pricing，也没有加列；
- official result 与 baseline/capture-only 一致。

## 对 GAT 主线的含义

GAT 没有被放弃，但当前证据链必须分清三层：

1. GAT embedding + kNN/OOD 已在 20 capture-only validation 中产生第一个
   `HIGH_PRIORITY` 信号；
2. branch-price worker hook 现在已经可观测；
3. 但 GAT `HIGH_PRIORITY` 尚未变成合法在线触发条件。

所以目前仍不能声称：

```text
GAT improves 20 wall time
```

只能声称：

```text
GAT+kNN/OOD offline signal exists；
branch-price online worker path is now observable；
current certificate-candidate gate prevents worker from running on this 20 smoke。
```

## 下一步

下一步不应默认启用 GAT/worker，也不应进入 official certificate gate。

应做一个更窄的 Phase：

```text
GAT HIGH_PRIORITY -> branch-price audit-only online trigger
```

要求：

- 只读 GAT/kNN/OOD 通过的 context/family signal；
- 只作为 opt-in worker trigger 或 target-priority scheduler；
- worker 返回列必须 true-RC negative；
- 不通过的 true-RC negative 仍进 `DELAY_QUEUE`，不能 discard；
- worker no-column / incomplete 不产生 certificate；
- 先跑 5/10 no-regression；
- 再跑 20 Apollo/Tranq ROI A/B；
- 只有看到 wall-time、retry、gap 或 tail 指标改善，才讨论 production tuning。

当前仍保持：

```text
production_ready = false
default_enable_allowed = false
certificate_effect_allowed = false
```

