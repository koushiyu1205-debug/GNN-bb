# BPC_future 根因审计补充：5/10 small-scale overhead guard audit

日期：2026-06-13

## 目标

前几轮主要解释了 20-task 为什么不能稳定优化：

- 不是缺负列；
- 不是单纯 Pulse 不够强；
- 而是缺少跨 context 泛化的 returned-batch trajectory selector。

本轮补齐另一个问题：

> 为什么 5/10 规模不能不退化？

本轮只读已有 small / guard summary，不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

扫描已有 5/10 guard / small-matrix / gate 结果集，选取：

- `tasks in {5, 10}`；
- 非 baseline rows；
- 同 summary 内有对应 baseline 可比较 wall time；
- 读取 worker / audit / official result / wall-time delta。

纳入：

```text
datasets = 21
nonbaseline small rows = 545
task5 rows = 380
task10 rows = 165
```

整体标签：

```text
improvement_class:
  no_regression = 313
  worsened      = 208
  improved      = 24

official_result_changed_vs_baseline:
  False = 528
  True  = 17

worker/audit triggered:
  False = 325
  True  = 220
```

注意：

- 这里的 `improvement_class=improved` 多数是 wall-time 轻微下降，不代表 official primal / bound 改变；
- 关键指标是 official result 是否改变、worker/audit 是否触发、wall-time delta 是否稳定。

## 触发 vs 不触发

### 真实触发 worker/audit 的小规模 rows

```text
rows = 220
class:
  worsened = 208
  no_regression = 12
  improved = 0

official_changed = 17
delta wall time:
  min    = +0.049295
  median = +0.3165025
  max    = +1.082235

relative delta:
  median = +12.1315695952616

worse_count = 220
better_count = 0
```

结论非常直接：

> 5/10 上只要 worker/audit/probe 真实触发，就没有任何 wall-time 正收益样本；220/220 都变慢。

### 没有触发 worker/audit 的小规模 rows

```text
rows = 325
class:
  no_regression = 301
  improved = 24
  worsened = 0

official_changed = 0
delta wall time:
  min    = -0.172665
  median = -0.000043
  max    = +0.049725

relative delta:
  median = -0.0003062338
```

解释：

- official result 全部不变；
- wall-time 中位数接近 0；
- `improved` 基本是运行噪声或 gate/no-op 后的微小时间波动；
- 这不是优化机制成功，而是没有真正做额外工作。

## Task 5 / Task 10 拆分

### Task 5

未触发：

```text
rows = 220
class:
  no_regression = 196
  improved = 24
official_changed = 0
median_delta = -0.000124
max_delta = +0.049725
```

触发：

```text
rows = 160
class:
  worsened = 152
  no_regression = 8
official_changed = 0
median_delta = +0.316148
max_delta = +0.370055
```

Task 5 上，触发机制不会改变 official result，只会增加时间。

### Task 10

未触发：

```text
rows = 105
class:
  no_regression = 105
official_changed = 0
median_delta = +0.000149
max_delta = +0.009166
```

触发：

```text
rows = 60
class:
  worsened = 56
  no_regression = 4
official_changed = 17
median_delta = +0.3205295
max_delta = +1.082235
```

Task 10 上更危险：

- 触发后时间明显增加；
- 有 17 行 official result 变化；
- 这说明小规模 active worker/probe 不只是开销，还可能改变求解路径。

## 结果集对照

### 20-only / strict gate 类结果

典型结果集：

- `sharded_pulse_phase10h_early_new_task_set_quota_5_10_guard_20260613`
- `sharded_pulse_phase11a_profile_pricing_time_sensitivity_5_10_guard_20260613`
- `sharded_pulse_phase11b_profile_selection_mode_sensitivity_5_10_guard_20260613`
- `sharded_pulse_phase7o_20_only_cooldown_gate_20260612`
- `sharded_pulse_phase7p_*_small_matrix_20260613`

共同特征：

```text
triggered = 0
official_changed = 0
median_delta ~= 0
```

这些结果保住 5/10 的原因不是机制优化了小规模，而是 gate 让机制没有真正触发。

### full profile gate 结果

`sharded_pulse_phase7o_full_profile_gate_20260612`：

```text
rows = 243
class:
  worsened = 208
  no_regression = 33
  improved = 2
official_changed = 15
triggered = 216
delta wall time:
  median = +0.315262
  max = +1.082235
relative delta median = +11.948898678414098
```

这是一组关键反例：

- 只要不做 20-only/min-task/hard-tail gate，小规模就大量退化；
- 很多 worker 虽然因为 `instance_too_small` / `current_probe_instance_too_small` / `not_certificate_candidate` / `no_previous_audit_negative_signal` 跳过真正加列，但 audit / trigger plumbing 本身已经产生固定成本；
- 这证明“小规模 no-regression”不能靠事后跳过，必须在更早、更便宜的位置 no-op。

## Top regressions

最大的 10-task 回退来自 `full_profile_gate`：

```text
apollo10_04 / strict_worker_current_probe_support_aware_mid_budget:
  delta = +1.082235
  relative = +10.623791
  official_changed = True
  triggered = True

tranq10_09 / strict_worker_current_probe_support_aware_mid_budget:
  delta = +1.007324
  relative = +9.597675
  official_changed = True
  triggered = True

apollo10 / strict_worker_current_probe_support_aware_mid_budget:
  delta = +1.006920
  relative = +10.112786
  official_changed = True
  triggered = True
```

最大的 5-task 回退也来自 `full_profile_gate`：

```text
tranquillitatis_balmer_like_tasks05_07 / strict_worker_current_probe_support_aware:
  delta = +0.370055
  relative = +15.228601
  official_changed = False
  triggered = True

apollo15_tasks05_08 / strict_worker_current_probe_support_aware_low_budget:
  delta = +0.361430
  relative = +13.328539
  official_changed = False
  triggered = True
```

这说明：

- 5-task 即使 official result 不变，固定开销也会造成大比例退化；
- 10-task 还可能出现 official path 改变；
- 小规模不能用“触发后再判断有没有用”的策略。

## 根因结论：5/10 为什么不能不退化

5/10 的根因不是某个 Pulse bug，也不是单独某个参数。

证据支持的结论是：

> 5/10 基准本身求解时间太短，worker / audit / current-probe / support-aware harvesting / extra returned path 的固定开销已经大于潜在收益；如果没有足够早、足够便宜、几乎 no-op 的 gate，任何真实触发都会退化。

这和 20-task 的根因互相咬合：

- 20 需要更多/更好的 candidate trajectory 选择；
- 5/10 不能承担这种探索成本；
- 因此一个 production 方向必须同时满足：
  - 小规模触发成本近似 0；
  - 20 规模只在高置信 hard-tail context 下触发；
  - 触发后必须有跨 context 泛化的 trajectory selector；
  - 否则小规模会被固定开销拖慢，20 也可能走坏 trajectory。

## 已证伪的方向

不能把下面方向作为 5/10-safe 主线：

- 默认 audit-only；
- 默认 current-context probe；
- 默认 active worker；
- worker 触发后再用 `instance_too_small` 等 late skip；
- support-aware harvesting 默认启用；
- full-profile gate；
- 单纯降低 worker budget。

原因：

- 即使 worker 不加列，audit/trigger plumbing 也能造成明显固定成本；
- 5/10 的安全路径必须是 early no-op，而不是 late skip。

## 当前仍能保留的边界

以下机制仍可作为 guard，不代表优化：

- `20_only`；
- min-task gate；
- hard-tail gate；
- no-op default；
- explicit experimental config；
- 只读 calibration。

它们的作用是防止退化，不是提供收益。

## 目标状态

目标仍未完成。

本轮新增证据：

- 5/10 不退化主要来自不触发；
- 真触发的小规模 rows `220/220` wall-time 变差；
- 未触发 rows official result 全部不变，wall-time 接近噪声；
- 因此 5/10 no-regression 与 20 exploration 存在结构性冲突。

这补齐了根因解释的另一半，但还没有证明任何可上线优化方向。

