# BPC Future Stage 4 方向一：20 规模 Completion-Bound Tail 修复

日期：2026-06-23

## 结论

本轮主攻方向一：不是继续提高 v154 分类指标，而是修 20-task exact solve 的
final-judge 证明尾部。

当前结论是：找到并修掉了一类真实瓶颈。20-task completion-bound retry 中的
`profile_labeling_task_set_superset_pruning` 在部分实例上会把主要时间耗在
task-filter/superset lower-bound cache 上；对 20 规模的 certificate retry
关闭这个 pruning 后，sector/apollo seed61715 从 `TIME_LIMIT 97.16s`
变成 `OPTIMAL 11.61s`，并保持相同 primal/dual `744.848595`。

但这不是全局完成。旧 Stage 4 的 5 个 20-task shadow 实例中，当前配置下
3/5 在 90s 内变成 `OPTIMAL`，2/5 仍外部超时。剩余瓶颈不是同一种：
sector/tranq 已经能做多个 completion-bound certificate，但 B&B 未收尾；
greedy/apollo 根本没进入 completion-bound retry，仍卡在普通 exact/heuristic
负列生成与过滤阶段。

## 精确性边界

本改动不是学习模型 admission，也不是 official bound。它只改变 final certificate
retry 的一个剪枝开关：在 `task_count >= 20` 时关闭
`profile_labeling_task_set_superset_pruning`。

精确性上这是保守的：关闭 lower-bound pruning 只会多探索，不会丢掉真实 negative
column，也不会凭空制造 no-negative certificate。证书仍来自原来的 true-dual
completion-bound exhaustive proof。

## 实现改动

- `BPC_future/solver/journey_driver.py`
  - 在 `_journey_pricing_config` 中写入 `task_count=len(data.tasks)`。
  - 在 `_journey_certificate_pricing_config` 中新增
    `journey_certificate_completion_bound_profile_labeling_task_set_superset_pruning_disable_min_tasks`。
  - retry mode 日志现在显式输出
    `completion_bound_profile_labeling_task_set_superset_pruning`。
- `BPC_future/configs/moon_trek_20_smoke.yaml`
  - 设置
    `journey_certificate_completion_bound_profile_labeling_task_set_superset_pruning_disable_min_tasks: 20`。
- `BPC_future/pricing/journey_pricing.py`
  - 增加 direct-label profile timing 细分字段，用于拆出 task-filter、option lookup、
    label create、priority queue、completed processing、stream callback 等耗时。
  - 保留 AMCB 与 unique-route 同时启用时跳过 AMCB 的精确安全默认行为。
- `BPC_future/scripts/audit_journey_completion_tail_profile.py`
  - 聚合新增 profile timing 字段，报告 completion-bound tail 的主要耗时项。

## 5/10 No-Regression

使用旧 Stage 4 同口径配置：

- 5-task：`BPC_future/configs/moon_trek_5_journey.yaml`
- 10-task：`BPC_future/configs/moon_trek_10_journey.yaml`

结果：

| scale | instance | status | solving_time | primal=dual | nodes | columns |
|---|---|---:|---:|---:|---:|---:|
| 5 | sector/apollo | OPTIMAL | 0.327887 | 284.084294 | 1 | 14 |
| 5 | sector/tranq | OPTIMAL | 0.331815 | 179.982081 | 1 | 18 |
| 10 | sector/apollo | OPTIMAL | 2.651162 | 456.756326 | 3 | 42 |
| 10 | sector/tranq | OPTIMAL | 1.455795 | 330.363821 | 1 | 71 |

这些日志中的 certificate retry 仍保持
`completion_bound_profile_labeling_task_set_superset_pruning=true`，说明小规模没有被
20-only 开关影响。

## 20-Task 单实例定位

同一个 sector/apollo seed61715：

| run | status | solving_time | profile_generation_time | 主要耗时 |
|---|---:|---:|---:|---|
| baseline profile v2 | TIME_LIMIT | 97.157486 | 90.008683 | task_filter_time=85.666304 |
| global no-superset probe | OPTIMAL | 11.288483 | 4.401700 | task_filter_time=0.156308 |
| 20-only certificate config | OPTIMAL | 11.605421 | 4.454371 | task_filter_time=0.160365 |

关键证据：旧路径里 `direct_label_profile_task_filter_time` 占了 85.67s；
新路径中同一项降到 0.16s，completion-bound retry 能完成
`CERTIFIED_NO_NEGATIVE`。

## 20-Task Shadow 5 实例

使用旧 Stage 4 shadow 的 5 个实例，90s 外部限时：

| instance | old Stage 4 status/time | new status/time | 说明 |
|---|---:|---:|---|
| sector/apollo seed61715 | TIME_LIMIT / 52.318019 | OPTIMAL / 11.081247 | 明确时间减少并完成证书 |
| sector/tranq seed61513 | TIME_LIMIT / 59.051556 | EXTERNAL_TIME_LIMIT / 90.014025 | 仍未收尾，但已有 5 次 certificate retry |
| greedy/apollo seed61308 | EXTERNAL_TIME_LIMIT / 85.026279 | EXTERNAL_TIME_LIMIT / 90.016681 | 未进入 completion-bound retry，瓶颈不同 |
| random/tranq seed61615 | TIME_LIMIT / 68.299230 | OPTIMAL / 34.396703 | 明确时间减少并完成证书 |
| random/apollo seed61715 | TIME_LIMIT / 67.765529 | OPTIMAL / 84.371464 | 从未证变成已证，但不算纯时间收益 |

聚合审计：

```text
completion_retry_class_counts = {'completion_bound_certified_no_negative': 4, 'no_completion_bound_retry': 1}
completion_retry_total_profile_generation_time = 59.248794
```

## 当前判断

第一方向有效，但只修掉一类 tail：

1. 对 completion-bound retry 已经触发、且卡在 superset task-filter 的实例，收益很大。
2. 对仍在普通 pricing / exact negative-column 生成阶段打转的实例，没有直接帮助。
3. 对 B&B 未收尾的实例，certificate retry 单次变快不足以保证整棵树在 90s 内结束。

所以后续真正要把 20 规模稳定降时，需要沿两个子方向继续：

1. 继续做 exact/proof tail：针对 sector/tranq 的 B&B 收尾，减少重复节点上的 certificate retry 和 exact hidden-negative patrol 反复消耗。
2. 做 admission/trajectory ROI selector：针对 greedy/apollo 这类还在找负列的实例，不能只看 v154 candidate 是否 exact-safe，还要判断当前 active basis / cut / branch context 下是否能减少 RMP/pricing 轮数。

## 产物

- 5-task no-regression：
  `BPC_future/results/journey_completion_tail_direction1_v154_20260623/superset_ge20_stage4_mouth_task005/results.csv`
- 10-task no-regression：
  `BPC_future/results/journey_completion_tail_direction1_v154_20260623/superset_ge20_stage4_mouth_task010/results.csv`
- 20-task 单实例：
  `BPC_future/results/journey_completion_tail_direction1_v154_20260623/cert_ge20_config_apollo20_sector/results.csv`
- 20-task shadow5：
  `BPC_future/results/journey_completion_tail_direction1_v154_20260623/cert_ge20_config_task020_shadow5/results.csv`
- tail audit：
  `BPC_future/results/journey_completion_tail_direction1_v154_20260623/cert_ge20_config_task020_shadow5_tail_profile/summary.json`

## 验证

```text
py_compile journey_pricing.py journey_driver.py audit_journey_completion_tail_profile.py: pass
python -m unittest BPC_future.tests.test_resource_pareto_completion: 10 tests OK
```
