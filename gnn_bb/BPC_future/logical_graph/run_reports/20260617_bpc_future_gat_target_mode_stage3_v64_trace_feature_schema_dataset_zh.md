# 2026-06-17 BPC_future GAT Stage 3 v64 Trace-feature Schema Dataset 报告

## 读取范围

本轮复读了：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 v62 feature/structure gap 审计
- Stage 3 v63 trace payload availability 审计
- Stage 4 v53 individual follow-up 执行综合报告
- Stage 5 20/30/50/100 exact-safe acceleration 目标

目标边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能用于 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列仍必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 背景

v62 证明 focused v53/v60 pairs 不是完全 input collision：正负 target 在粗 task set / sequence / scalar feature 上有差异，但 3/4 pair 的 raw candidate ranking 仍失败。

v63 进一步证明 source capture 中 9/9 focused target 都能取到：

```text
arc-option sequence = 9 / 9
timing payload = 9 / 9
resource payload = 9 / 9
trace_numeric_feature_count = 22
```

因此下一步不是继续扫 threshold / delay penalty，而是把已经可取的 trace/timing/resource scalar 先接入 batch-impact candidate schema。

## 代码改动

修改 `BPC_future/scripts/build_gat_batch_impact_dataset.py`：

- `BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA` 从 14 维扩展到 36 维；
- 新增 22 个 trace scalar features：

```text
trace_trip_count
trace_arc_option_count
trace_unique_arc_option_count
trace_low_time_arc_count
trace_low_energy_arc_count
trace_low_risk_arc_count
trace_journey_start_time
trace_journey_end_time
trace_journey_duration
trace_total_distance
trace_total_energy
trace_total_risk
trace_total_travel_time
trace_total_recharge_time
trace_max_load
trace_min_survival_energy
trace_service_start_min
trace_service_start_max
trace_service_start_span
trace_inter_sortie_gap_sum
trace_inter_sortie_gap_max
trace_idle_time_proxy
```

这些字段只从 capture 中已有的 `journey.trips[*]` / `journey.start_time` / `journey.end_time` 提取，不运行 pricing，不重新求 reduced cost，不影响 RMP 或 certificate。

修改 `BPC_future/tests/test_gat_batch_impact_dataset.py`：

- toy journey 增加 arc-option / timing / resource payload；
- 验证新 trace fields 写入 `candidate_features`；
- 验证扩维后的 sample 仍可喂给 `GATBatchImpactModel` forward。

## v64 Dataset Smoke

使用 v53 focused 9 条 individual rows 构建 trace-feature dataset：

```text
input =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

dataset =
  BPC_future/data/gat_batch_impact/v64_v53_trace_features_20260617

dataset_report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_batch_impact_dataset_v64_v53_trace_features_zh.md
```

结果：

```text
sample_count = 9
candidate_count = 9
candidate_feature_dim = 36
trace_feature_count = 22
batch_label_counts = {'non_improving': 7, 'roi_positive': 2}
candidate_label_counts = {'delay_queue': 7, 'high_priority': 2}
context_match_rate = 1.0
candidate_signature_source_coverage = 1.0
ranking_ready = true
ranking_blockers = []
training_ready = false
training_blockers = ['need_more_regions_for_holdout']
all_checks_pass = true
```

`training_ready=false` 是预期结果：v64 只是 focused schema smoke，只有 `sector-wave` / task20 / 单 region，不是可上线训练集。

真实 sample 抽检：

```text
candidate_feature_dim = 36
sample0 trace_arc_option_count = 3.0
sample0 trace_low_time_arc_count = 3.0
sample0 trace_total_energy = 30.900316
sample0 trace_total_risk = 1.960701
sample0 trace_service_start_span = 90.910919
sample0 trace_idle_time_proxy = 53.229156
```

## 当前仍缺的字段

v64 只接入了 v63 中“capture 已经 9/9 可取”的 scalar trace features。

仍未接入：

- `task_time_window_slack`：需要从 logical graph task windows / service times 另行计算；
- per-candidate branch/cut coefficients：需要走 cut evaluator / branch compatibility 口径，不能只用 context aggregate；
- active basis coefficient overlap：需要从 active basis rows 中提取 per-candidate overlap。

这些字段应作为下一轮 v65 的审计/实现对象，不应混在本轮 scalar trace schema smoke 里。

## 对 Stage 3/4 的影响

v64 只关闭了 v62/v63 暴露的一部分输入缺口：trace/timing/resource scalar 已经可以进入模型输入。

它还没有证明：

- v55 / v57 的 false-delay blocker 被修复；
- focused context ranking 通过；
- random-wave high-ROI blind spot 被覆盖；
- kNN/OOD holdout 通过；
- Stage 4 mutating admission 可启用；
- Stage 5 20-task `OPTIMAL < 200s`。

下一步需要用 v64 schema 重建包含 v54/v51 历史数据的完整 dataset，再训练新 checkpoint，并重新跑 v57-v60 类审计。

## Exactness Boundary

```text
v64_builder_runs_bpc_or_pricing = false
v64_changes_solver_behavior = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
stage5_ready = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

最终证明仍必须由当前 branch/cut/dual 下 exact pricing exhaustive no-negative closure 产生；本轮改动只影响离线 batch-impact dataset candidate features。
