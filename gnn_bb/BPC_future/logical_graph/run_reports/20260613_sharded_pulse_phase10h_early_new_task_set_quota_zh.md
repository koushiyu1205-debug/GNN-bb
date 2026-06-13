# Sharded Pulse Phase 10H Early-column Controlled Intervention 报告

日期：2026-06-13

## 目标

本轮只做 Phase 10H：`early-column controlled intervention / negative-result split`。

目标不是继续推进 Pulse worker、resume、parallel 或 official certificate，而是验证 Phase 10G 发现的 early inactive-to-active 轨迹是否能通过一个受控、20-only 的 early new-task-set quota profile 稳定改善 20-task hard smoke。

## 实现摘要

新增两个 calibration-only profile：

- `experimental_early_new_task_set_quota_3_20_only`
- `experimental_early_new_task_set_quota_3_return12_20_only`

新增 profile group：

- `phase10h_early_new_task_set_quota`

配置语义：

- 仅当 `task_count >= 20` 时生效；
- 要求 early-return 至少保留 3 个 new task-set；
- return8 profile 设置 pricing/heuristic max returned journeys 为 8；
- return12 profile 设置 pricing/heuristic max returned journeys 为 12；
- selection mode 使用 `diverse`；
- 显式关闭 Sharded Pulse audit、hidden-negative worker 和 dual stabilization。

本轮没有改变默认 benchmark 配置，没有启用 worker，没有启用 certificate effect。

## 测试

### Focused tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

### 语法检查

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

### 全量回归

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 483 tests in 1.453s
OK (skipped=1)
```

### Diff 检查

```bash
git diff --check
```

结果：通过。

## Smoke 矩阵

### 20-task intervention smoke

输出目录：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613`

矩阵：

- instances：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`
- profiles：
  - `baseline`
  - `experimental_early_new_task_set_quota_3_20_only`
  - `experimental_early_new_task_set_quota_3_return12_20_only`
- repeat-count：3
- rows：27

### 5/10 no-op guard

输出目录：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_5_10_guard_20260613`

矩阵：

- instances：
  - `apollo5`
  - `tranq5`
  - `apollo10`
  - `tranq10_09`
  - `tranq10_04`
- profiles：
  - `baseline`
  - `experimental_early_new_task_set_quota_3_20_only`
  - `experimental_early_new_task_set_quota_3_return12_20_only`
- repeat-count：1
- rows：15

## 5/10 Guard 结果

5/10 guard 中两个 experimental profiles 都保持：

- `official_result_changed_vs_baseline=False`
- `critical_disagreement_count=0`
- status / pricing_state 与 baseline 一致
- primal 与 baseline 完全一致

实例 primal：

| instance | baseline | quota return8 | quota return12 |
|---|---:|---:|---:|
| `apollo5` | 165.623455 | 165.623455 | 165.623455 |
| `tranq5` | 180.521929 | 180.521929 | 180.521929 |
| `apollo10` | 405.125490 | 405.125490 | 405.125490 |
| `tranq10_09` | 391.751577 | 391.751577 | 391.751577 |
| `tranq10_04` | 361.939751 | 361.939751 | 361.939751 |

这验证了 Phase 10H profile 的 20-only guard 没有污染 5/10。

## 20-task 结果

三个 profiles 都保持：

- status：9/9 `TIME_LIMIT`
- pricing：6/9 `INCOMPLETE_LIMIT`，3/9 `FOUND_NEGATIVE`
- critical disagreement：0

但 20-task incumbent 变化方向分裂。

| instance | baseline repeats | quota return8 repeats | quota return12 repeats |
|---|---:|---:|---:|
| `tranq20_01` | 781.101309, 781.101309, 781.101309 | 597.118613, 596.176491, 594.045835 | 605.126958, 593.924951, 605.126958 |
| `mt20_greedy_apollo_01` | 847.812231, 921.640296, 921.640296 | 1061.554044, 1061.554044, 770.211317 | 1061.554044, 1061.554044, 1061.554044 |
| `mt20_greedy_tranq_01` | 761.814403, 761.814403, 761.814403 | 829.395319, 829.395319, 829.395319 | 704.228463, 704.228463, 704.228463 |

`improvement_class` 计数：

| profile | improved | worsened |
|---|---:|---:|
| `experimental_early_new_task_set_quota_3_20_only` | 4 | 5 |
| `experimental_early_new_task_set_quota_3_return12_20_only` | 6 | 3 |

early-column 轨迹：

- `tranq20_01`：quota profiles 将 early additions 从 3 提高到 8，并把 active hash transition 从 2 提高到 6/7；三次 repeat 均改善。
- `mt20_greedy_apollo_01`：return8 有一次改善但两次明显变差；return12 三次都变差。
- `mt20_greedy_tranq_01`：return8 三次变差；return12 三次改善。

## 结论

Phase 10H 说明 early new-task-set quota 是一个真实的 early-column trajectory intervention，但不是稳定优化：

- 它能强烈改变 active-pool / early-column 轨迹；
- 它对 `tranq20_01` 稳定改善；
- 它对 `mt20_greedy_tranq_01` 的方向依赖 return quota；
- 它对 `mt20_greedy_apollo_01` 大多回退；
- 它没有降低 `INCOMPLETE_LIMIT` 数量；
- 它没有形成 proof-tail 或 worker ROI 证据。

因此该 profile 不能默认启用，也不能作为 official certificate gate 或 worker tuning 的依据。

## Exactness 边界

- calibration-only；
- 20-only；
- no Sharded Pulse worker；
- no audit/certificate effect；
- no dual stabilization；
- no production default change；
- no official lower-bound rule change。

## 下一步建议

当前证据更支持 negative-result split：

1. profile-DP label-cap 不稳定；
2. early-column quota 不稳定；
3. worker/probe 主线已经多轮显示没有稳定 ROI；
4. 5/10 guard 可保护小实例，但 20-task selected hard set 没有一致改善。

下一步不应继续扩大 Pulse worker 或 quota 调参。建议整理当前连续负结果，转向：

- RMP stabilization / pool compression；
- legacy final judge proof-tail optimization；
- 或写出当前 Pulse worker/proof 路线在安全约束下 ROI 不成立的 synthesis 报告。
