# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 Safe-source Guarded Probe 报告

## 结论

本轮继续推进 Stage 4，但发现 v10 safe-source 不能直接作为 5/10 mutating
admission source 使用：

- v10 safe-source 有 `408` 个 safe candidate id；
- 在 tasks10 worst-tail online candidate batch 中，safe id 命中数为 `0`；
- shadow 视角下 `62` 个 true-RC negative 全部会进入 `DELAY_QUEUE`；
- admission 视角如果不加覆盖保护，会延迟一个 heuristic true-RC negative，但这不是
  `HIGH_PRIORITY` 命中，也不是 GAT 找到高 ROI 列。

因此本轮新增 coverage-aware safe-source guard：

```text
journey_gat_admission_require_online_safe_hit_for_delay = true
```

含义是：即使存在 offline safe candidate ids，也必须在当前 online candidate batch
中至少命中一个 safe id，才允许 mutating delay；否则记录
`reason=no_online_safe_hit` 并 pass-through。

这个 guard 不改变 exact pricing / certificate 语义，只防止覆盖不到当前
benchmark / family / task-size 的 safe-source 改变 5/10 trajectory。

## 背景

Stage 3 v10 已经通过 offline hard gate：

```text
safe_source_ready = true
safe_candidate_id_count = 408
validation_candidate_ready = true
validation_safety_ready = true
safe_precision_ci_low = 0.9010957324106112
accepted_batch_roi_ci_low = 5.073187796362916
```

但 v10 的训练 / safe-source 覆盖主要来自 task20/30/50/100 same-context rows。
Stage 4 的第一道门是 5/10 no-regression；如果 safe-source 对 tasks10 online
candidate signature 没有覆盖，却让 scheduler 延迟未知 true-RC negative，就会把
5/10 no-regression 风险重新引入。

## Unguarded v10 Probe

实例：

```text
BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_balanced_tasks10_10_seed141920_logical_graph.json
```

输出目录：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_probe_20260616
```

CSV：

```text
status = OPTIMAL
primal_bound = 335.726923
dual_bound = 335.726923
gap = 0.0
time = 77.822047
nodes = 45
rmp_solves = 66
pricing_calls = 225
exact_pricing_calls = 159
generated_sequences = 343868
evaluated_timed_trips = 148361
columns = 108
```

admission 事件：

```text
admission_events = 20
scheduled_events = 1
high_priority_journeys = 0
delay_queue_journeys = 1
true_negative_journeys = 1
reasons = pricing_kind_not_mutated:15, opt_in_admission_scheduler:1, certificate_candidate_release:4
```

shadow 事件：

```text
shadow_events = 22
shadow_true_negative_journeys = 64
shadow_high_priority_journeys = 0
shadow_delay_queue_journeys = 64
```

解释：v10 safe ids 在该 online tasks10 tail 上没有产生任何 `HIGH_PRIORITY`。
唯一实际轨迹改变来自把一个未命中的 heuristic true-RC negative 放入 delay queue。
这不能作为 GAT ROI 证明。

certificate audit：

```text
all_checks_pass = true
violation_count = 0
```

## Guarded Code Change

修改文件：

- `BPC_future/solver/journey_driver.py`
  - 新增 `_journey_gat_admission_require_online_safe_hit_for_delay()`；
  - safe-source 存在但当前 candidate batch 没有 safe-id 命中时 pass-through；
  - admission event 增加 `safe_source_candidate_count` 和
    `online_safe_hit_journeys`；
  - 保留显式 opt-out：
    `journey_gat_admission_require_online_safe_hit_for_delay=false`。

- `BPC_future/tests/test_gat_target_mode_scheduler.py`
  - 覆盖 safe-source 存在但 online 无命中时 pass-through；
  - 覆盖显式 opt-out 时仍可 delay；
  - 覆盖 safe candidate 命中时 `online_safe_hit_journeys=1`。

- `BPC_future/scripts/audit_gat_target_mode_certificate_closure.py`
  - 保留原总计字段；
  - 新增 `shadow_*` 和 `admission_*` 分项统计；
  - 新增 `admission_online_safe_hit_journeys`，避免把 shadow delay 误读成实际
    admission delay。

- `BPC_future/tests/test_gat_target_mode_certificate_audit.py`
  - 覆盖 shadow / admission 分项统计。

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
  - 写入 coverage-aware safe-source gate。

## Guarded v10 Probe

输出目录：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_probe_20260616
```

配置差异：

```text
journey_gat_admission_require_online_safe_hit_for_delay = true
journey_gat_safe_candidate_ids = v10 safe-source 408 ids
journey_gat_shadow_safe_candidate_ids = v10 safe-source 408 ids
```

CSV：

```text
status = OPTIMAL
primal_bound = 335.726923
dual_bound = 335.726923
gap = 0.0
time = 70.577946
nodes = 45
rmp_solves = 64
pricing_calls = 224
exact_pricing_calls = 160
generated_sequences = 290288
evaluated_timed_trips = 116232
columns = 110
```

admission 事件：

```text
admission_events = 15
admission_candidate_journeys = 55
admission_high_priority_journeys = 0
admission_delay_queue_journeys = 0
admission_true_negative_journeys = 0
admission_online_safe_hit_journeys = 0
reasons = pricing_kind_not_mutated:10, no_online_safe_hit:1, certificate_candidate_release:4
```

shadow 事件：

```text
shadow_events = 19
shadow_candidate_journeys = 62
shadow_true_negative_journeys = 62
shadow_high_priority_journeys = 0
shadow_delay_queue_journeys = 62
```

解释：

- v10 safe ids 仍然没有命中 tasks10 online candidates；
- 新 guard 阻止了实际 mutating delay；
- 本轮 guarded probe 只是证明覆盖缺失时不改 admission trajectory；
- 它不是 GAT HIGH_PRIORITY ROI 证明。

certificate audit：

```text
all_checks_pass = true
violation_count = 0
global_certificate_pricing_events = 45
admission_delay_queue_journeys = 0
admission_online_safe_hit_journeys = 0
selector_can_certificate = false
official_bound_effect = false
hard_filter_enabled = false
```

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_target_mode_certificate_audit
```

```text
Ran 17 tests in 0.090s
OK
```

```bash
git diff --check -- \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py \
  BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md
```

通过。

## Stage 4 状态

已确认：

- v10 safe-source offline gate 仍是当前唯一 Stage 4 候选；
- v11 仍是 diagnostic，不能替代 v10；
- v10 safe ids 在该 tasks10 online tail 上无命中；
- coverage-aware guard 可以防止无命中 safe-source 造成实际 delay；
- exact certificate audit 通过，GAT 仍不产生 official bound / certificate。

仍未关闭：

- 5/10 full guarded safe-source no-regression；
- v10 safe-source 在 20-task hard-tail online candidates 上的 `HIGH_PRIORITY` 命中；
- 20-task repeatable wall-time / tail retry ROI；
- 20-task `OPTIMAL <= 200s`；
- Stage 5 scale acceleration。

## 下一步

1. 用 guarded v10 safe-source 重跑 balanced60 5/10 full opt-in A/B。
   预期如果 safe ids 不覆盖 5/10，应表现为 pass-through no-regression。
2. 在 20-task hard-tail 上先跑 shadow hit-rate probe：
   必须看到 `online_safe_hit_journeys > 0` 和 `high_priority_journeys > 0`，才值得开启
   mutating delay / priority A/B。
3. 如果 20-task 也无命中，不能继续调 admission；应回 Stage 3 补 online-signature
   aligned safe-source，或把 safe-source export 从 exact signature id 升级为
   family/context/candidate-feature rule。
4. 不降低 precision / ROI / false-safe 门槛，不让 GAT 参与 certificate。
