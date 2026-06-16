# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 Guarded Full No-regression 报告

## 结论

本轮用 v10 safe-source 的 `408` 个 safe candidate id，在 coverage-aware guard
开启的条件下，重跑 balanced60 的 5-task / 10-task 全量 opt-in A/B。

结论：

- 5/10 official no-regression：通过；
- 5/10 wall-time no-regression：通过；
- certificate safety audit：通过；
- 实际 admission 没有 `HIGH_PRIORITY`，没有 mutating delay；
- v10 safe-source 在 5/10 online candidate 上仍没有 safe-id 命中。

因此本轮只能声明：

```text
guarded v10 safe-source 在 5/10 覆盖缺失时可以安全 pass-through，
不会引入上一轮 unsourced delay regression。
```

不能声明：

```text
GAT 已经在 5/10 产生 HIGH_PRIORITY ROI；
GAT 已经改善 20-task wall-time；
可以进入 Stage 5。
```

## 运行配置

输出目录：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616
```

共同 flags：

```text
journey_gat_target_mode_shadow_enabled = true
journey_gat_admission_scheduler_enabled = true
journey_gat_admission_max_delay_rounds = 1
journey_gat_admission_log_shadow_decisions = true
journey_gat_admission_safe_source_ready = true
journey_gat_admission_allow_unsourced_delay = false
journey_gat_admission_require_online_safe_hit_for_delay = true
journey_gat_certificate_hard_filter_enabled = false
journey_gat_safe_candidate_ids = v10 safe-source 408 ids
journey_gat_shadow_safe_candidate_ids = v10 safe-source 408 ids
```

实例集：

```text
BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/*/tasks_05/*.json
BPC_future/data/generated/moon_trek_balanced_60_20260609/logical_graphs/*/tasks_10/*.json
```

baseline / shadow 对比：

```text
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks5_baseline.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615/tasks10_baseline.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks5_shadow.csv
BPC_future/results/gat_target_mode_shadow_smoke_20260615_rerun/tasks10_shadow.csv
```

## tasks5 结果

```text
instances = 20
guarded OPTIMAL = 20/20
official_mismatch_count = 0

baseline_total_time = 8.241215
shadow_total_time = 7.337385
guarded_total_time = 5.504828

delta_vs_baseline = -2.736387
ratio_vs_baseline = 0.667963
delta_vs_shadow = -1.832557
ratio_vs_shadow = 0.750244
max_delta_vs_baseline = -0.045049
max_delta_vs_shadow = -0.042236
```

Admission summary：

```text
admission_events = 24
statuses = bypassed:24
reasons = certificate_candidate_release:24
admission_candidate_journeys = 82
admission_high_priority_journeys = 0
admission_delay_queue_journeys = 0
admission_true_negative_journeys = 0
admission_online_safe_hit_journeys = 0
```

解释：tasks5 没有实际 mutating admission，只有 certificate candidate release /
pass-through 事件。因此 wall-time 变化不能解释为 GAT ROI，只能作为 no-regression
证据。

## tasks10 结果

```text
instances = 20
guarded OPTIMAL = 20/20
official_mismatch_count = 0

baseline_total_time = 269.417666
shadow_total_time = 269.368748
guarded_total_time = 218.806241

delta_vs_baseline = -50.611425
ratio_vs_baseline = 0.812145
delta_vs_shadow = -50.562507
ratio_vs_shadow = 0.812293
max_delta_vs_baseline = -0.188779
max_delta_vs_shadow = -0.200048
```

Admission summary：

```text
admission_events = 84
statuses = bypassed:84
reasons = certificate_candidate_release:35, pricing_kind_not_mutated:46, no_online_safe_hit:3
admission_candidate_journeys = 486
admission_high_priority_journeys = 0
admission_delay_queue_journeys = 0
admission_true_negative_journeys = 0
admission_online_safe_hit_journeys = 0
```

解释：tasks10 中 safe-source 覆盖缺失被 guard 捕获了 3 次
`no_online_safe_hit`。实际 admission 没有 delay，因此本轮没有重现之前
unsourced delay regression。

两个 hard-tail：

```text
tranq09:
  status = OPTIMAL
  time = 87.025468
  nodes = 45
  rmp_solves = 60
  pricing_calls = 210
  exact_pricing_calls = 150
  generated_sequences = 477842
  evaluated_timed_trips = 221065
  columns = 95

tranq10:
  status = OPTIMAL
  time = 71.227723
  nodes = 45
  rmp_solves = 64
  pricing_calls = 224
  exact_pricing_calls = 160
  generated_sequences = 291557
  evaluated_timed_trips = 116771
  columns = 110
```

## Certificate Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks5 \
  --log-dir BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks10 \
  --output-dir BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/certificate_audit \
  --report BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/certificate_audit/report.md
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

shadow_true_negative_journeys = 576
shadow_delay_queue_journeys = 576
shadow_high_priority_journeys = 0

admission_candidate_journeys = 568
admission_high_priority_journeys = 0
admission_delay_queue_journeys = 0
admission_true_negative_journeys = 0
admission_online_safe_hit_journeys = 0

selector_can_certificate = false
selector_is_pricing_oracle = false
official_bound_effect = false
hard_filter_enabled = false
```

注意：总计 `delay_queue_journeys=576` 来自 shadow 视角；实际 admission 分项中
`admission_delay_queue_journeys=0`。后续报告必须使用分项统计，不能把 shadow delay
当成 solver 实际 delay。

## Stage 4 判定

本轮关闭：

- guarded v10 safe-source 的 5/10 full official no-regression；
- guarded v10 safe-source 的 5/10 wall-time no-regression；
- guarded safe-source coverage-miss pass-through；
- certificate audit 分项统计；
- exact-safe boundary。

仍未关闭：

- v10 safe-source 在 20-task hard-tail online candidates 上的 `HIGH_PRIORITY`
  命中；
- mutating admission 对 20-task wall-time / tail retry 的 repeatable ROI；
- online pricing priority hook；
- 20-task `OPTIMAL <= 200s`；
- 30/50/100 scale acceleration。

## 下一步

1. 进入 20-task 前先做 shadow hit-rate probe，不直接开 mutating delay。
2. 20-task shadow 必须看到：
   `online_safe_hit_journeys > 0`、`high_priority_journeys > 0`、certificate audit 0 violation。
3. 如果 20-task shadow 也没有 safe-id 命中，则 v10 exact-signature safe-source
   不是可用 online safe-source；应回 Stage 3/4 改 safe-source 表达，优先考虑
   family/context/candidate-feature safe rule 或 online signature-aligned export。
4. 继续保持：GAT 不参与 official bound，不参与 certificate，不永久丢弃 true-RC
   negative。
