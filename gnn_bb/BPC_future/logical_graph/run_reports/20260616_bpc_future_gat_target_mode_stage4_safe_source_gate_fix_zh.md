# 2026-06-16 BPC_future GAT Target Mode Stage 4 Safe-source Gate 修复报告

## 结论

上一轮 full opt-in admission A/B 中，5/10 official result no-regression 已通过，但
tasks10 wall-time 比 baseline / shadow 慢约 3.9%。本轮对最差 tail 做隔离后确认：

- regression 不是 shadow logging；
- regression 来自 admission scheduler 在没有 safe/ROI source 时延迟了一个 root heuristic true-RC negative；
- 该单列 delay 改变了 RMP trajectory，使 root 后续多出 2 次 RMP / pricing，并增加约 55k generated sequences。

修复后新增 safe-source gate：

- 没有 safe source 时，opt-in admission scheduler 只能 pass-through / audit；
- 只有存在 safe candidate ids、或显式 `journey_gat_admission_safe_source_ready=true`、或测试专用 `journey_gat_admission_allow_unsourced_delay=true` 时，才允许 mutating delay；
- certificate boundary 不变：GAT 仍不能生成 official bound 或 certificate。

修复后 balanced60 5/10 full opt-in rerun：

- tasks5：20/20 `OPTIMAL`，official mismatch = 0，总时间 `7.310029s`；
- tasks10：20/20 `OPTIMAL`，official mismatch = 0，总时间 `269.041006s`；
- full certificate audit：0 violation。

因此 Stage 4 的 5/10 official no-regression 和当前 no-safe-source opt-in wall-time no-regression 已通过。仍未证明 20-task ROI，也没有真正启用 high-priority safe model。

## 隔离实验

固定实例：

```text
BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_balanced_tasks10_10_seed141920_logical_graph.json
```

四模式顺序运行：

```text
clean              admission=false, shadow=false
shadow_only        admission=false, shadow=true
admission_only     admission=true, shadow=false
admission_shadow   admission=true, shadow=true
```

结果：

| mode | status | time | nodes | rmp | pricing | generated | evaluated | columns |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | OPTIMAL | 88.033006 | 45 | 64 | 224 | 283402 | 115182 | 110 |
| shadow_only | OPTIMAL | 88.172332 | 45 | 64 | 224 | 283160 | 115177 | 110 |
| admission_only | OPTIMAL | 97.401006 | 45 | 66 | 226 | 338803 | 148202 | 109 |
| admission_shadow | OPTIMAL | 97.568038 | 45 | 66 | 226 | 339078 | 148294 | 109 |

定位：

```text
cg_iter = 2
pricing_kind = heuristic
certificate_candidate = false
status = scheduled
delay_queue_journeys = 1
delayed_negative_journeys = 1

cg_iter = 3
pricing_kind = exact
released_journeys = 1
```

结论：没有 safe source 时延迟 heuristic true-RC negative 会改变 trajectory，不能作为 Stage 4 no-regression 默认行为。

## 修复

修改文件：

- `BPC_future/solver/journey_driver.py`
  - 新增 `_journey_gat_admission_safe_source_available()`；
  - mutating admission 前检查 safe source；
  - no safe source 时记录 `reason=missing_safe_source` 并 pass-through；
  - 不产生 delay，不改变 exact path，不改变 certificate source。

- `BPC_future/tests/test_gat_target_mode_scheduler.py`
  - 新增 no-safe-source pass-through 测试；
  - 原 delay/release 测试显式设置 `journey_gat_admission_allow_unsourced_delay=true`。

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
  - 增加 `journey_gat_admission_safe_source_ready`；
  - 增加 `journey_gat_admission_allow_unsourced_delay`；
  - 明确 no safe source 时不得 delay true-RC negative。

## 修复后 Tail Recheck

同一 worst-tail 实例，`admission_only_safe_source_gate`：

```text
status = OPTIMAL
primal_bound = 335.726923
dual_bound = 335.726923
gap = 0.0
time = 87.6534
nodes = 45
rmp_solves = 64
pricing_calls = 224
generated_sequences = 283604
evaluated_timed_trips = 115517
columns = 110
```

admission event：

```text
pricing_kind = heuristic
status = bypassed
reason = missing_safe_source
candidate_journeys = 1
admitted_journeys = 1
delay_queue_journeys = 0
released_journeys = 0
delay_queue_size = 0
```

certificate audit：

```text
all_checks_pass = true
violation_count = 0
admission_events = 15
shadow_events = 0
reject_nonnegative_only_journeys = 0
```

## 5/10 Full Rerun

输出目录：

```text
BPC_future/results/gat_target_mode_stage4_optin_admission_full_safe_source_gate_20260616
```

### tasks5

```text
instances = 20
status = 20/20 OPTIMAL
official_mismatch_count = 0

baseline_total_time = 8.241215
shadow_total_time = 7.337385
optin_safe_source_gate_total_time = 7.310029

delta_vs_baseline = -0.931186
ratio_vs_baseline = 0.887009
delta_vs_shadow = -0.027356
ratio_vs_shadow = 0.996272
max_delta_vs_baseline = +0.008241
```

### tasks10

```text
instances = 20
status = 20/20 OPTIMAL
official_mismatch_count = 0

baseline_total_time = 269.417666
shadow_total_time = 269.368748
optin_safe_source_gate_total_time = 269.041006

delta_vs_baseline = -0.376660
ratio_vs_baseline = 0.998602
delta_vs_shadow = -0.327742
ratio_vs_shadow = 0.998783
max_delta_vs_baseline = +0.086282
```

之前 regression 的 worst tail：

```text
tranquillitatis_balmer_like_20km_balanced_tasks10_10_seed141920
baseline_time = 88.424027
shadow_time = 88.437083
unsafe_admission_time = 97.620876
safe_source_gate_time = 88.317150
nodes = 45
columns = 110
```

## Admission Summary

修复后 no safe source 的 admission 事件：

```text
tasks5:
  admission_events = 24
  delay_queue_journeys = 0
  released_journeys = 0
  reasons = certificate_candidate_release:24

tasks10:
  admission_events = 84
  delay_queue_journeys = 0
  released_journeys = 0
  reasons = certificate_candidate_release:35, pricing_kind_not_mutated:46, missing_safe_source:3
```

说明：本轮 no-regression 通过的原因是无 safe source 时保持 pass-through。它不是 GAT 加速 ROI 证明。

## Certificate Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_safe_source_gate_20260616/logs_tasks5 \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_safe_source_gate_20260616/logs_tasks10 \
  --output-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_safe_source_gate_20260616/certificate_audit \
  --report BPC_future/results/gat_target_mode_stage4_optin_admission_full_safe_source_gate_20260616/certificate_audit/report.md
```

结果：

```text
all_checks_pass = true
violation_count = 0
log_files = 40
finish_events = 40
optimal_finish_events = 40
global_certificate_pricing_events = 152
gat_events = 221
shadow_events = 113
admission_events = 108
candidate_journeys = 1144
true_negative_journeys = 576
delay_queue_journeys = 576
reject_nonnegative_only_journeys = 0
```

注意：audit 中的 `delay_queue_journeys = 576` 来自 shadow view；修复后的 admission events 自身没有实际 delay。

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_target_mode_certificate_audit \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_dataset \
  BPC_future.tests.test_gat_batch_impact_model
```

```text
Ran 30 tests in 0.204s
OK
```

```bash
git diff --check -- \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py
```

通过。

## Stage 4 状态

已关闭：

- 5/10 official no-regression；
- no safe source 下 opt-in admission wall-time no-regression；
- certificate safety audit；
- default-off / exact-safe boundary。

仍未关闭：

- 真正使用 Stage 3 safe/ROI checkpoint 的 mutating admission A/B；
- HIGH_PRIORITY 在线来源；
- 20-task repeatable wall-time / tail retry ROI；
- 20-task 200 秒 exact OPTIMAL；
- Stage 5 scale。

下一步应回到 Stage 3/4 的 safe source 接入：只有当 checkpoint / CBF / kNN / OOD 能提供可审计 safe ids 或 safe-source-ready signal 时，才允许重新打开 mutating delay，并重新跑 5/10 no-regression。

