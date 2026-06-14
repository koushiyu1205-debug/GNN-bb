# CBF Branch-price Capture Hook 修复报告

日期：2026-06-14

## 目标

修复 `journey_branch_price` 路径没有写出
`journey_counterfactual_replay_capture` 的问题。

该 capture 是 CBF / RMP-impact 数据采集的只读诊断事件，用于离线重建：

```text
state_t, action_t, state_{t+1}
```

它不加列、不改 certificate、不产生 official lower bound。

## 修改

在 `BPC_future/solver/journey_driver.py` 的 branch-price main exact pricing
路径中，`_log_journey_pricing()` 后补充调用：

```text
_log_journey_counterfactual_replay_capture(...)
```

传入当前真实上下文：

- `solution.duals`
- `cuts`
- `node.branch_constraints`
- `journey_pool`
- `active_task_sets`
- `solution.variable_values`
- `solution.reduced_costs`
- `exact_config`
- `exact_dual_source`

该 hook 仍由 `journey_counterfactual_replay_capture_enabled` 控制，默认关闭。

## 新增测试

新增 focused regression：

```text
test_counterfactual_replay_capture_branch_driver_smoke_records_returned_batch
```

它验证：

- `journey_branching_enabled=True` 时也能写出 capture；
- capture 事件保持 `replay_no_certificate_effect=True`；
- capture 事件保持 `official_bound_effect=False`；
- returned journey payload 包含 task set 和 context hash。

同时补齐老 root smoke fake RMP 的 `variable_values/reduced_costs` 字段。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_counterfactual_replay_capture_driver_smoke_records_returned_batch \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_counterfactual_replay_capture_branch_driver_smoke_records_returned_batch
```

结果：

```text
Ran 2 tests in 0.025s
OK
```

## 真实 smoke

### Apollo05 branch capture

命令使用 `moon_trek_5_journey.yaml`，单实例 Apollo05，capture opt-in。

结果：

```text
status=OPTIMAL
primal=102.041475
dual=102.041475
time=2.397033s
nodes=1
cols=31
```

结构化日志统计：

```text
journey_counterfactual_replay_capture = 1
journey_pricing = 4
```

CBF audit：

```text
capture_event_count = 1
transition_count = 0
has_transition_evidence = false
all_checks_pass = true
```

解释：Apollo05 一轮闭合，只有一个 capture，因此没有相邻 transition。

### Tranquillitatis10 branch capture

命令使用 `moon_trek_10_journey.yaml`，单实例 Tranq10，capture opt-in。

结果：

```text
status=TIME_LIMIT
primal=203.590288
dual=None
time=41.995902s
nodes=1
cols=405
```

结构化日志统计：

```text
journey_counterfactual_replay_capture = 5
journey_pricing = 12
```

CBF audit：

```text
capture_event_count = 5
transition_count = 4
mode_switch_count = 4
bad_mode_transition_count = 3
cbf_feasible_observed_count = 1
cbf_infeasible_observed_count = 3
has_transition_evidence = true
all_checks_pass = true
```

## 结论

branch-price 路径现在可以采集 CBF mode-transition 证据。

这一步不证明加速，也不证明模型可上线；它只修复了数据闭环缺口：
5/10/20 的真实 `journey_branch_price` run 现在可以进入
`state_t, action_t, state_{t+1}` 离线审计。

当前 Tranq10 smoke 已经观察到 4 个相邻 transition，其中 3 个在当前
Lyapunov surrogate 下违反 CBF slack。这支持当前判断：

```text
问题不是单纯找负列，而是 returned batch 对 RMP dual / residual-family mode
切换的影响不可控。
```

下一步应扩大 capture 矩阵，采集足够多的 no-certificate-effect transition，
再训练或评估 conservative RMP-impact / CBF gate。不能据此开启 production
worker 或 official certificate。
