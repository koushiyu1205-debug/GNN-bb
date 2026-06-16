# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 20-task Shadow Hit-rate Probe 报告

## 结论

本轮按 Stage 4 guarded full no-regression 报告的下一步，只做 20-task
shadow-only hit-rate probe，不开启 mutating admission。

结论：

- certificate safety audit：通过；
- solver 状态：`TIME_LIMIT`，且没有 official dual bound；
- admission scheduler：关闭，实际 admission event = 0；
- v10 safe-source shadow 没有产生 `HIGH_PRIORITY` 命中；
- `75` 个 true-RC negative online candidate 在 shadow 视角全部进入
  `DELAY_QUEUE`。

因此本轮只能证明：

```text
v10 safe-source shadow 在该 20-task sector-wave 实例上没有破坏 exact-safe 边界。
```

不能证明：

```text
v10 safe-source 已经能命中 20-task online HIGH_PRIORITY；
v10 safe-source 能改善 20-task wall-time / tail retry；
可以开启 20-task mutating opt-in A/B；
可以进入 Stage 5。
```

## 运行配置

实例：

```text
BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json
```

输出目录：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616
```

safe-source：

```text
BPC_future/results/gat_batch_impact_safe_source_v10_random_wave_task50_5751_20260616/safe_source.json
safe_candidate_id_count = 408
```

关键 flags：

```text
--config BPC_future/configs/moon_trek_20_smoke.yaml
--time-limit 200

journey_gat_target_mode_shadow_enabled = true
journey_gat_admission_log_shadow_decisions = true
journey_gat_admission_scheduler_enabled = false
journey_gat_certificate_hard_filter_enabled = false
journey_gat_shadow_safe_candidate_ids = v10 safe-source 408 ids
```

注意：本轮明确关闭 `journey_gat_admission_scheduler_enabled`，所以所有 GAT
decision 都只进入 shadow 日志，不改变 column admission trajectory。

## Solver 结果

CSV：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616/sector_tranq20_01_shadow_hit.csv
```

结果：

```text
status = TIME_LIMIT
solving_time = 52.152317
primal_bound = 632.987632
dual_bound = None
gap = None
node_count = 1
rmp_solves = 9
pricing_calls = 14
exact_pricing_calls = 5
generated_sequences = 32642
evaluated_timed_trips = 48798
columns = 236
computed_R_bar = 13
fleet_bound_heuristic_R = 11
fleet_bound_UB = 935.049539
cuts_added = 1
fleet_lb_cut_added = 1
```

解释：

- 该 probe 的目的不是证明 optimality，也不是做 wall-time A/B；
- `TIME_LIMIT` 下没有 official dual bound，符合当前 exact-safe 边界；
- 因为 admission scheduler 关闭，GAT 不可能影响本轮 solver trajectory。

## Shadow Hit-rate

日志：

```text
BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616/logs_sector_tranq20_01_shadow_hit/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl
```

shadow 统计：

```text
shadow_events = 8
shadow_candidate_journeys = 75
shadow_true_negative_journeys = 75
shadow_high_priority_journeys = 0
shadow_delay_queue_journeys = 75
shadow_reject_nonnegative_only_journeys = 0
pricing_kinds = heuristic:6, exact:2
```

hit-rate：

```text
online HIGH_PRIORITY hit-rate = 0 / 75 = 0.0
online safe-source useful hit = 0
```

代表性 shadow decision：

```text
decision = DELAY_QUEUE
reason = true_rc_negative_delayed_not_rejected
true_reduced_cost examples = -119.727184, -116.213903, -73.900558, -25.4432665
```

解释：

- 这些 candidate 都已经通过 true-RC negative 验证；
- v10 safe-source 的 exact candidate id 没有命中当前 online candidates；
- shadow 中的 `DELAY_QUEUE` 只是诊断视角，不是实际 admission；
- 如果直接开启 mutating admission，当前 v10 safe-source 不能提供
  `HIGH_PRIORITY` 加速信号。

## Certificate Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python \
  BPC_future/scripts/audit_gat_target_mode_certificate_closure.py \
  --log-dir BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616/logs_sector_tranq20_01_shadow_hit \
  --output-dir BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616/certificate_audit \
  --report BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_20260616/certificate_audit/report.md
```

结果：

```text
all_checks_pass = true
violation_count = 0
log_files = 1
finish_events = 1
optimal_finish_events = 0
global_certificate_pricing_events = 0

gat_events = 8
shadow_events = 8
admission_events = 0

candidate_journeys = 75
true_negative_journeys = 75
high_priority_journeys = 0
delay_queue_journeys = 75

admission_candidate_journeys = 0
admission_high_priority_journeys = 0
admission_delay_queue_journeys = 0
admission_true_negative_journeys = 0
admission_online_safe_hit_journeys = 0

selector_can_certificate = false
selector_is_pricing_oracle = false
official_bound_effect = false
hard_filter_enabled = false
```

注意：本轮 `delay_queue_journeys=75` 全部来自 shadow 分项；实际 admission 分项全部
为 `0`。因此不能把该数字解释成 solver 实际延迟了负列。

## Stage 4 判定

本轮新增证据：

- v10 safe-source guarded 5/10 full no-regression 之后，20-task shadow
  hit-rate 仍为 `0`；
- exact-safe / certificate audit 仍通过；
- v10 exact-signature safe-source 的 online coverage 仍不足，至少在该
  20-task sector-wave 实例上没有 `HIGH_PRIORITY` 命中。

Stage 4 当前结论：

```text
stage4_20_shadow_hit_gate = failed
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

下一步不应该降低 precision / ROI / false-safe 门槛，也不应该打开 mutating delay。
应回到 Stage 3 / Stage 4 边界，改进 safe-source 表达和 20-task online coverage：

1. 继续补 20-task online shadow / worker rows，尤其是同 context 下的 high-ROI
   vs low-ROI candidate 对；
2. 不只导出 exact candidate id，可增加 family/context/route-signature 层级的
   safe-source 表达，但必须保留 true-RC verified admission 前提；
3. 重新训练 / threshold search 后，先要求 20-task shadow 中
   `shadow_high_priority_journeys > 0` 且 certificate audit 0 violation；
4. 只有 shadow hit gate 通过，才允许进入 mutating opt-in A/B。

## Exactness Boundary

本轮保持：

```text
selector_can_certificate = false
selector_is_pricing_oracle = false
official_bound_effect = false
hard_filter_enabled = false
admission_scheduler_enabled = false
```

GAT 仍只能做 ordering / priority / finite-delay scheduling 的候选证据。
最终 certificate 必须由当前 branch/cut/dual 下的 exact pricing 重新确认：
完整配置宇宙里没有任何 negative reduced-cost journey。
