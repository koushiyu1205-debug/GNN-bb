# V745-V749 RouteOpt/BKF Preset Repro 与 Cut Snapshot 诊断复盘

日期：2026-06-29

## 背景

V744 修复了一个实验正确性问题：`phase1_cut_snapshot_enabled=True` 时，cut snapshot 的诊断耗时不应进入 BKF `phase_wall` penalty。修复后需要验证两件事：

1. diagnostic-only cut snapshot 是否仍会改变 branch ordering；
2. 当前 RouteOpt/BKF staged controller 是否还能复现 V736 的 seed61311 110s OPTIMAL 路径。

## 关键发现

V745/V746 一开始都 timeout，但不是 V744 修复导致，也不是 cut snapshot 耗时导致。

真正原因是实验命令没有显式复原 V736 的 RouteOpt/BKF 参数，导致当前默认退回到：

```text
phased_testing_base_priority = branch_score_horizon
phased_testing_dynamic_k_min_candidates = 1
phased_testing_dynamic_k_diverse_pool_enabled = False
phased_testing_phase2_time_limit = 0.0
```

结果：

- `[2,16]` 被 dynamic-K 排除；
- `[2,8]` 以 `probed_incomplete / missing_time_budget` 被选中；
- seed61311 从历史 V736 的 110s OPTIMAL 路径退化为 240s timeout。

这说明 `routeopt_bkf_staged` 不能靠隐式默认参数运行。RouteOpt 风格 controller 必须带完整 staged testing preset。

## 对照结果

| version | config difference | root pair | status | wall | note |
|---|---|---:|---:|---:|---|
| V736 | 手写 V736 staged 参数，no snapshot | `[2,16]` | OPTIMAL | `110.914s` | 历史强正例 |
| V745 | 缺 V736 staged 参数，snapshot on | `[2,8]` | EXTERNAL_TIME_LIMIT | `240.026s` | 坏路径 |
| V746 | 缺 V736 staged 参数，snapshot off | `[2,8]` | EXTERNAL_TIME_LIMIT | `240.034s` | 证明不是 snapshot 问题 |
| V747 | 手写 V736 staged 参数，snapshot off | `[2,16]` | OPTIMAL | `125.361s` outer / `110.901s` solver | 复现 V736 |
| V748 | 手写 V736 staged 参数，snapshot on，snapshot weight=0 | `[2,16]` | OPTIMAL | `113.180s` outer / `111.036s` solver | V744 修复有效 |
| V749 | `preset=routeopt_bkf_v736`，snapshot on，snapshot weight=0 | `[2,16]` | OPTIMAL | `112.770s` outer | preset 可用 |

## V736-like staged 参数

V736 能复现的关键参数是：

```text
journey_branch_candidate_phased_testing_base_priority=fractionality
journey_branch_candidate_phased_testing_phase0_min_fractionality=0.45
journey_branch_candidate_phased_testing_phase1_max_candidates=12
journey_branch_candidate_phased_testing_phase2_max_candidates=3
journey_branch_candidate_phased_testing_phase2_time_limit=0.08
journey_branch_candidate_phased_testing_dynamic_k_min_candidates=9
journey_branch_candidate_phased_testing_dynamic_k_phase1_max_candidates=12
journey_branch_candidate_phased_testing_dynamic_k_phase2_max_candidates=3
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_extra_candidates=2
```

本轮已新增 opt-in preset：

```text
journey_branch_candidate_phased_testing_preset=routeopt_bkf_v736
```

该 preset 只在显式设置时生效；显式传入的单项参数仍会覆盖 preset 默认值。

日志中新增：

```text
phased_testing_preset
```

用于复盘时确认是否使用了稳定 preset。

## Cut Snapshot 结论

V748 证明，在 V736 staged 参数正确时：

- `phase1_cut_snapshot_enabled=True`
- snapshot BKF weights = `0`

不会破坏 seed61311 的 `[2,16]` 好路径，也不会阻止 240s 内 OPTIMAL。

因此 V744 的诊断耗时拆分是有效的：

```text
phase1_wall_time
phase1_cut_snapshot_wall_time
phase1_diagnostic_wall_time
```

后续可以把 snapshot 作为诊断/训练特征保留，但不能像 V743 那样直接给正权重上线。

## 代码与测试

代码改动：

- `journey_driver.py`
  - 新增 `journey_branch_candidate_phased_testing_preset=routeopt_bkf_v736`；
  - preset 填入 V736 staged 参数；
  - 日志输出 `phased_testing_preset`。
- `test_bpc_future.py`
  - 新增 `test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters`。

已通过：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

已通过：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_v736_preset_fills_stable_parameters \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_uses_sqrt_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_phase1_cut_snapshot_is_diagnostic \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_ignores_cut_snapshot_diagnostic_wall_time
```

结果：

```text
Ran 5 tests in 0.012s
OK
```

## Exact-Safe

本轮所有改动只影响 branch candidate ordering / diagnostic logging / training features。

不改变：

- official lower bound；
- pricing certificate；
- fathom/prune 条件；
- child lower bound exactness；
- cut validity。

V747/V748/V749 的 OPTIMAL 均来自 solver finish event，`primal=dual=570.891015`。

## 下一步

1. 不再裸开 `routeopt_bkf_staged` 做性能实验。

后续 RouteOpt/BKF staged 性能实验必须显式使用：

```text
journey_branch_candidate_phased_testing_preset=routeopt_bkf_v736
```

或者在报告中列出完整等价参数。

2. 用 preset 跑 greedy-anchor hard2。

先跑：

- seed61311：no-regression；
- seed61635：确认仍 timeout 且 dual/gap 是否不动。

3. 若 seed61635 仍不动，进入 stronger cuts/formulation。

V736/V747/V748 只证明 staged branch + gated SRC 能解决 seed61311 这一类 hard case；seed61635 的 best dual 不动，仍需要 pricing-compatible stronger cuts / route-aware cuts / master formulation。

4. Cut snapshot 下一步只作为诊断/训练特征。

默认保持 snapshot weight = `0`。只有当 full replay 证明某类 cut snapshot signal 能稳定改善 whole-run wall/gap/fathom，才允许进入 live BKF ordering。
