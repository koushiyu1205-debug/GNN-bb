# 2026-06-16 BPC_future GAT Target Mode Stage 4 Opt-in Full No-Regression 报告

## 结论

本轮在 balanced60 的 5-task / 10-task 全量 40 个实例上运行了
`journey_gat_admission_scheduler_enabled=true` 的 opt-in admission scheduling。

结论分开看：

- exactness / official result no-regression：通过。
  - tasks5：20/20 `OPTIMAL`，official mismatch = 0；
  - tasks10：20/20 `OPTIMAL`，official mismatch = 0；
  - full certificate audit：0 violation。

- wall-time no-regression：没有干净通过。
  - tasks5 总时间比 baseline 更快，和 shadow 基本持平；
  - tasks10 总时间比 baseline / shadow 慢约 3.9%，主要来自一个 45-node tail 实例增加约 9.2s。

因此 Stage 4 目前只能声明：opt-in admission scheduler 的 exactness boundary 和 5/10 official no-regression 通过；但 wall-time no-regression / overhead gate 仍是 blocker。不能进入 20-task opt-in A/B，也不能进入 Stage 5。

## 本轮修复

全量 tasks5 第一次运行时暴露了一个集成 bug：

```text
UnboundLocalError: cannot access local variable 'final_pricing_kind'
```

触发位置是 duplicate/retry pricing exhausted 后的 certificate promotion 分支。该分支本地变量是
`retry_pricing_kind`，不是 `final_pricing_kind`。

修复：

```text
release_gat_admission_before_certificate(pricing, retry_pricing_kind)
```

修复后复跑触发实例：

```text
tranquillitatis_balmer_like_20km_balanced_tasks05_09_seed136818
status = OPTIMAL
primal_bound = 178.253745
dual_bound = 178.253745
gap = 0.0
solving_time = 1.351609
```

随后重新跑完整 tasks5，完成 20/20。

## 运行配置

共同 opt-in flags：

```text
journey_gat_target_mode_shadow_enabled = true
journey_gat_admission_scheduler_enabled = true
journey_gat_admission_max_delay_rounds = 1
journey_gat_admission_log_shadow_decisions = true
```

数据集：

```text
BPC_future/data/generated/moon_trek_balanced_60_20260609
```

baseline / shadow 参考：

```text
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks5_baseline.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks10_baseline.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks5_shadow.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks10_shadow.csv
```

opt-in 输出：

```text
BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/tasks5_optin_admission.csv
BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/tasks10_optin_admission.csv
BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/logs_tasks5
BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/logs_tasks10
```

## tasks5 结果

```text
instances = 20
baseline OPTIMAL = 20/20
opt-in OPTIMAL = 20/20
official_mismatch_count = 0

baseline_total_time = 8.241215
shadow_total_time = 7.337385
optin_total_time = 7.380078

delta_vs_baseline = -0.861137
ratio_vs_baseline = 0.895508
delta_vs_shadow = +0.042693
ratio_vs_shadow = 1.005819

max_delta_vs_baseline = +0.007275
avg_delta_vs_baseline = -0.043057
```

tasks5 full opt-in 没有发现官方结果退化，也没有明显 wall-time 退化。

## tasks10 结果

```text
instances = 20
baseline OPTIMAL = 20/20
opt-in OPTIMAL = 20/20
official_mismatch_count = 0

baseline_total_time = 269.417666
shadow_total_time = 269.368748
optin_total_time = 279.989033

delta_vs_baseline = +10.571367
ratio_vs_baseline = 1.039238
delta_vs_shadow = +10.620285
ratio_vs_shadow = 1.039427

max_delta_vs_baseline = +9.196849
avg_delta_vs_baseline = +0.528568
```

最差 tail：

```text
instance = tranquillitatis_balmer_like_20km_balanced_tasks10_10_seed141920
baseline_time = 88.424027
shadow_time = 88.437083
optin_time = 97.620876
delta_vs_baseline = +9.196849
nodes = 45 / 45 / 45
```

该实例 opt-in admission 日志：

```text
admission_events = 20
scheduled_events = 1
candidate_journeys = 62
admitted_journeys = 62
delay_queue_journeys = 1
released_journeys = 1
true_negative_journeys = 1
```

因此当前 wall-time regression 不伴随 node_count 或 official bound 变化，但仍不能忽略。Stage 4 的 wall-time overhead gate 未关闭。

## Admission Event Summary

tasks5：

```text
log_files = 20
admission_events = 24
candidate_journeys = 82
admitted_journeys = 82
released_journeys = 0
delay_queue_journeys = 0
true_negative_journeys = 0
certificate_candidate_events = 24
```

tasks5 的 admission 基本都是 certificate-candidate pass-through，没有实际 delay。

tasks10：

```text
log_files = 20
admission_events = 93
scheduled_events = 3
candidate_journeys = 495
admitted_journeys = 495
released_journeys = 3
delay_queue_journeys = 3
true_negative_journeys = 3
certificate_candidate_events = 39
```

tasks10 有 3 个 true-RC negative 被 heuristic opt-in scheduler delay，随后 release。没有 negative 被 reject。

## Certificate Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/logs_tasks5 \
  --log-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/logs_tasks10 \
  --output-dir BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/certificate_audit \
  --report BPC_future/results/gat_target_mode_stage4_optin_admission_full_20260616/certificate_audit/report.md
```

结果：

```text
all_checks_pass = true
violation_count = 0
log_files = 40
finish_events = 40
optimal_finish_events = 40
global_certificate_pricing_events = 152
gat_events = 237
shadow_events = 120
admission_events = 117
candidate_journeys = 1158
true_negative_journeys = 584
delay_queue_journeys = 584
reject_nonnegative_only_journeys = 0
pricing_kinds = exact:226, exact_completion_bound_retry:2, exact_hidden_negative_patrol:1, heuristic:8
```

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m py_compile \
  BPC_future/solver/journey_driver.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_target_mode_scheduler \
  BPC_future.tests.test_gat_target_mode_certificate_safety \
  BPC_future.tests.test_gat_target_mode_certificate_audit
```

```text
Ran 14 tests in 0.011s
OK
```

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
Ran 29 tests in 1.300s
OK
```

```bash
git diff --check -- \
  BPC_future/solver/journey_driver.py \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  BPC_future/tests/test_gat_target_mode_scheduler.py \
  BPC_future/tests/test_gat_target_mode_certificate_audit.py \
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_optin_admission_probe_zh.md
```

通过。

## Stage 4 Gate 状态

通过：

- 5/10 official result no-regression；
- delayed true-RC negative 不会被 reject；
- exact path preserved；
- certificate audit 无 violation；
- default-off 仍成立。

未通过 / 未关闭：

- tasks10 wall-time no-regression 未干净通过；
- opt-in admission 目前只有 3 个实际 scheduled true-negative，覆盖太低；
- high-priority safe candidate 在线来源仍是人工 safe id / shadow shell，不是生产 checkpoint；
- 20-task opt-in ROI 未跑；
- 20-task 200s exact OPTIMAL 未证明。

下一步不应直接进入 20-task A/B。应先降低 opt-in admission overhead：

1. 对比 worst tail 在 `shadow-only`、`admission-enabled-without-shadow`、`admission-enabled-with-shadow` 三种模式下的重复运行；
2. 确认 wall-time 差异来自日志/调度开销、运行噪声，还是 release 改变了 RMP trajectory；
3. 若 admission 覆盖仍只有极少 true negatives，应先回到 Stage 3/4 threshold 和 safe-id 来源，而不是扩大到 20-task。

