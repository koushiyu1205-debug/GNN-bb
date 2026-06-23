# 2026-06-23 BPC_future Stage 4 Direction 1 Completion-tail Probe 报告

## 对齐计划

本轮已复读 `gat_bpc_future_target_mode_optimization_plan_zh.md` 与当前五阶段主线报告：

- Stage 1：batch-impact / trajectory-oriented 模型结构已是 offline / audit-only，不进入 certificate path。
- Stage 2：same-context intervention 数据是训练前置，不是 production readiness。
- Stage 3：v154 比 v152 更接近，但 `stage3_completed=false`、`stage4_candidate_ready=false`；不能用 F1/recall 或 77/78 pair 修复替代 ROI gate。
- Stage 4：v154 5/10 sentinel 没有 no-regression 问题，但 20-task shadow / opt-in 没有 wall-time ROI。
- Stage 5：最终目标仍是 exact-safe 20/30/50/100 加速，20-task 必须 200s 内 `OPTIMAL` 且 certificate 只来自 exact pricing closure；Stage 4 完整通过前不进入 Stage 5。

本轮主攻用户指定的第一个方向：真正减少 20 规模精确求解时间的 exact-pricing / completion-bound proof tail。

## Exactness 边界

本轮所有新增运行和代码改动均保持：

```text
selector_can_certificate = false
official_bound_effect = false for diagnostic scripts
certificate source = exact pricing / final judge only
default config behavior unchanged
```

没有把 GAT/kNN/OOD 当 pricing oracle，也没有让 delay queue、safe-source 或 helper bound 产生 official lower bound。

## 新增诊断工具

新增只读脚本：

```text
BPC_future/scripts/audit_journey_completion_tail_profile.py
```

用途：读取 solver JSONL，聚合 `exact_completion_bound_retry` / final judge tail 状态。脚本不运行 BPC、pricing 或 RMP，不产生 certificate。

已生成报告：

```text
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_completion_tail_profile_v154_stage4_probe_zh.md
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_completion_tail_profile_finalcap90_apollo20_sector_zh.md
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_completion_tail_profile_finalcap90_rpce_apollo20_sector_zh.md
BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_completion_tail_profile_finalcap90_amcb_combined_apollo20_sector_zh.md
```

## Stage 4 v154 tail 画像

对 v154 Stage 4 实测日志做聚合：

```text
log_count = 12
completion_retry_class_counts = {'completion_bound_time_limit_no_column_uncertified': 9, 'no_completion_bound_retry': 3}
incomplete_tail_count = 9
completion_retry_total_profile_generation_time = 405.684712
completion_retry_total_generated_sequences = 147280
completion_retry_total_evaluated_timed_trips = 159266
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
```

解释：v154 的 Stage 4 blocker 不是候选没有触发，也不是 GAT exact-safe-id overlap 不够；主要时间耗在 no-negative completion-bound final judge tail，但它既没有找到负列，也没有证明 no-negative。

## 单实例 90s final judge 预算探针

实例：

```text
BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json
```

只把 completion-bound final judge cap 从默认 45s 提到 90s，总 time-limit 给 240s 以避免 120s reserve 截断 final judge。结果：

```text
status = TIME_LIMIT
solving_time = 97.926189
dual_bound = None
completion_retry_total_profile_generation_time = 90.007762
completion_retry_total_generated_sequences = 38345
completion_retry_total_evaluated_timed_trips = 14284
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
```

结论：不是 45s 刚好差一点。把 final judge 预算翻倍到 90s 仍不能闭合 certificate，也不产负列。单纯加预算不能实现 20-task 200s 内 exact optimal。

## RPCE opt-in 探针

运行参数：

```text
journey_certificate_completion_bound_final_judge_time_limit=90.0
journey_resource_pareto_completion_enabled=True
```

结果：

```text
status = TIME_LIMIT
solving_time = 97.244379
dual_bound = None
completion_retry_total_profile_generation_time = 90.052318
completion_retry_total_generated_sequences = 1
completion_retry_total_evaluated_timed_trips = 0
completion_retry_total_negative_journeys = 0
```

日志显示 RPCE 最终 `rpce_disable_reason=deadline`。它压低了 completion retry 的 sequence/evaluation 数，但把 90s 花在 resource-Pareto front 构造上，没有 certificate。当前形式不能作为加速方案。

## AMCB 与 unique-route 并用探针

新增一个默认不改变行为的 opt-in 开关：

```text
journey_available_mask_completion_bound_skip_with_unique_route
```

默认 `true`，保持旧行为；显式设为 `false` 时，AMCB 可以与 unique-route helper 并用，取更强 optimistic lower bound。两个 bound 都是 lower bound，因此取 max 仍 exact-safe。

运行参数：

```text
journey_certificate_completion_bound_final_judge_time_limit=90.0
journey_available_mask_completion_bound_enabled=True
journey_available_mask_completion_bound_skip_with_unique_route=False
```

结果：

```text
status = TIME_LIMIT
solving_time = 97.216593
dual_bound = None
completion_retry_total_profile_generation_time = 90.005209
completion_retry_total_generated_sequences = 34438
completion_retry_total_evaluated_timed_trips = 14180
completion_retry_total_negative_journeys = 0
```

日志显示：

```text
amcb_enabled = true
amcb_query_count = 1
amcb_state_count = 200000
amcb_disable_reason = state_budget
amcb_pruned_labels = 0
```

AMCB 并用后 sequence 有小幅下降，但仍无 wall-time ROI、无 certificate。当前 AMCB 不是这条 20-tail 的直接解。

## 代码改动

新增：

```text
BPC_future/scripts/audit_journey_completion_tail_profile.py
```

修改：

```text
BPC_future/pricing/journey_pricing.py
BPC_future/solver/journey_driver.py
BPC_future/tests/test_resource_pareto_completion.py
```

改动内容：

- 增加 AMCB 与 unique-route 并用的 opt-in flag；
- 默认行为不变；
- retry-mode 日志输出该 flag；
- 单测覆盖默认 quarantine 和显式并用配置。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/audit_journey_completion_tail_profile.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_resource_pareto_completion
```

结果：编译通过；`test_resource_pareto_completion` 10 个用例通过。

## 当前结论

v154 的 77/78 修到 78/78 仍不太可能带来真正的 20-task exact wall-time 改善，因为当前主要瓶颈已经在 final no-negative proof tail，而不是 high-priority 候选覆盖。

本轮证伪了三个容易误判的方向：

1. 只把 final judge cap 从 45s 提到 90s不能闭合。
2. 直接启用 RPCE 不能闭合，且会把预算耗在 front 构造。
3. AMCB 与 unique-route 并用不能闭合，AMCB 很快打满 state budget 且未实际剪枝。

## 下一步

继续主攻第一个方向，但不再盲目加 proof budget 或直接打开现有 helper。下一步应做：

1. 开启 direct-label profile timing 的单实例 probe，定位 90s `profile_generation_time` 内部真正热点。
2. 给 RPCE/AMCB 增加更严格的 fail-fast / build-budget 诊断，确保 helper 不会吃完整个 final judge budget 后才退化。
3. 在定位热点后再做 exact-safe loop-level 剪枝或缓存，而不是继续扩大 GAT Stage 4 worker。
4. 第二方向保留为 trajectory ROI selector / context admission selector，但当前不是主攻点。

Stage 4 当前仍未通过；不得进入 Stage 5。
