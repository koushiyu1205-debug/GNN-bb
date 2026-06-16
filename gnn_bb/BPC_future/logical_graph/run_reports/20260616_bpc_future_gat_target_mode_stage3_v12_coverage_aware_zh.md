# 2026-06-16 BPC_future GAT Target Mode Stage 3 v12 Coverage-aware Selection 报告

## 结论

本轮把 v11 暴露的 “ROI-CI 越高但 safe shell 越窄” 问题写成训练阶段的硬约束：

```text
min_family_accepted_high_roi_count = 2
min_family_high_roi_capture_rate = 0.20
```

含义是：只要某个 family 在 validation 中存在 oracle high-ROI opportunity，checkpoint
就不能只靠 sector-wave 的高 ROI 通过；它必须在这些 family 中捕获足够的 high-ROI
batch。该 gate 默认关闭，不改变旧训练命令；显式启用时参与 threshold / checkpoint
selection 和 reject reason。

v12 训练 local gate 已通过，并修复了 v11 的 random-wave 覆盖过窄问题。第一轮
global kNN/OOD 后 safe precision CI 略低于 0.85；随后改用已有的 scale-level
kNN/OOD safety shell，validation gate 全部通过，并成功导出 Stage 4 safe-source。

```text
stage3_scale_safe_source_ready = true
production_ready = false
default_enabled = false
```

## 修改文件

- `BPC_future/scripts/train_gat_batch_impact.py`
  - 新增 `--min-family-accepted-high-roi-count`；
  - 新增 `--min-family-high-roi-capture-rate`；
  - `family_holdout_metrics` 输出 `accepted_high_roi_count` 和 `high_roi_capture_rate`；
  - threshold / checkpoint feasible key 在 ROI-CI 与 baseline margin 之后加入 family high-ROI capture；
  - 新增 hard reject reasons：
    - `family_accepted_high_roi_count_below_threshold`
    - `family_high_roi_capture_rate_below_threshold`

- `BPC_future/tests/test_gat_batch_impact_training.py`
  - 增加 coverage shortfall 单测：random-wave 有 5 个 high-ROI opportunity 但只捕获 1 个时，checkpoint 必须被拒绝。

## 训练结果

训练 artifact：

```text
BPC_future/results/gat_batch_impact_training_v12_coverage_aware_20260616/
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v12_coverage_aware_training_zh.md
```

命令使用 v10 dataset：

```text
BPC_future/data/gat_batch_impact/v10_mixed_v8_plus_random_wave_task50_5751_20260616
```

核心 validation local gate：

```text
accepted_batch_count = 22
accepted_batch_roi = 13.906624
accepted_batch_roi_ci_low = 8.755177
safe_precision = 1.0
safe_precision_ci_low = 0.851340
false_safe_rate_union = 0.0
family_holdout_min_accepted_high_roi_count = 3
family_holdout_min_high_roi_capture_rate = 0.6
threshold_local_gate_pass = true
```

family 覆盖：

```text
greedy-anchor:
  oracle_high_roi_count = 0
  accepted_batch_count = 0

random-wave:
  oracle_high_roi_count = 5
  accepted_batch_count = 5
  accepted_high_roi_count = 3
  high_roi_capture_rate = 0.60
  accepted_batch_roi = 1.422634

sector-wave:
  oracle_high_roi_count = 22
  accepted_batch_count = 17
  accepted_high_roi_count = 17
  high_roi_capture_rate = 0.772727
  accepted_batch_roi = 17.578386
```

对比 v11：

```text
v11 random-wave accepted_batch_count = 1
v12 random-wave accepted_batch_count = 5
v12 random-wave accepted_high_roi_count = 3
```

这说明 coverage-aware constraint 按预期避免了 ROI-CI selection 退化成过窄
sector-wave shell。

## kNN/OOD 结果

global kNN/OOD artifact：

```text
BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_knn34_20260616/
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v12_coverage_aware_knn_ood_zh.md
```

配置：

```text
knn_k = 3
max_neighbor_delay_fraction = 0.34
min_safe_precision = 0.90
min_safe_precision_ci_low = 0.85
```

结果：

```text
accepted_batch_count = 21
accepted_batch_roi = 13.943609
accepted_batch_roi_ci_low = 8.541261
safe_precision = 1.0
safe_precision_ci_low = 0.845356
false_safe_rate_union = 0.0
validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']
```

0.35 的邻居 delay fraction 探测未改变 accepted count 或 safe CI，因此当前 blocker
不是单纯的 `0.34 -> 0.35` 阈值边界问题。

进一步比较已有 grouping：

```text
global:
  accepted_batch_count = 21
  safe_precision_ci_low = 0.845356
  validation_candidate_ready = false

family:
  accepted_batch_count = 6
  accepted_batch_roi_ci_low = 0.094193
  safe_precision_ci_low = 0.609657
  validation_candidate_ready = false

scale_family:
  accepted_batch_count = 6
  accepted_batch_roi_ci_low = 0.094193
  safe_precision_ci_low = 0.609657
  validation_candidate_ready = false

scale:
  accepted_batch_count = 22
  accepted_batch_roi = 13.906624
  accepted_batch_roi_ci_low = 8.755177
  safe_precision = 1.0
  safe_precision_ci_low = 0.851340
  false_safe_rate_union = 0.0
  validation_candidate_ready = true
  production_block_reasons = []
```

scale grouping 有效的原因是 task-scale 内的 safe shell 能覆盖该 20-task
sector-wave high-ROI 正例，而不会像 family / scale_family 那样因为 sector-wave
训练组过窄而过度 delay。

safe-source export：

```text
BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v12_coverage_aware_safe_source_export_zh.md

safe_source_ready = true
safe_candidate_id_count = 142
high_priority_decision_record_count = 22
blockers = []
```

## 判定

v12 的正确结论：

- coverage-aware gate 已经有效；
- random-wave high-ROI opportunity capture 明显好于 v11；
- precision / ROI / false-safe local gate 仍保持硬；
- global kNN/OOD 后 safe precision CI 差 `0.004644`，不能作为 safe-source；
- scale-level kNN/OOD 通过所有 validation gate，可以作为 Stage 4 shadow /
  guarded no-regression 的 safe-source candidate；
- 仍不能宣称 production-ready，后续必须先跑 5/10 guarded no-regression 和
  certificate audit，再做 20-task shadow hit-rate / ROI A/B。

## 2026-06-16 Accepted Bad-mode 硬门槛补充

基于后续 Stage 4 sequential target-materialization 反例，训练 gate 继续收紧：
accepted bad-mode batch 不能被 false-safe 比例平均掉。默认：

```text
max_accepted_bad_mode_count = 0
accepted_bad_mode_count_above_limit => threshold_local_gate_pass = false
hard_reject_category = accepted_bad_mode
```

该补充针对的是 `[15,20] -> [1,9]` 这类样本：候选均为 true-RC negative，
也能触发 active replacement，但 longer-horizon workload 变重。因此它们必须是
bad-mode / DELAY_QUEUE 训练信号，不能被任何 high ROI point estimate、safe
precision 或较低 false-safe rate 抵消。

新增反例单测构造 100 个 bad-mode batch，其中 threshold 只接受 1 个；旧的
`false_safe_rate_union=0.01` 可以低于 `0.02`，但新 gate 会因为
`accepted_bad_mode_count=1` 直接拒绝。

已对当前 v12 scale kNN/OOD decision records 追加 audit-only 复核：

```text
audit_artifact = BPC_future/results/gat_accepted_bad_mode_gate_v12_scale_20260616/summary.json
audit_report = BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v12_accepted_bad_mode_gate_audit_zh.md
decision_record_count = 102
high_priority_decision_count = 22
bad_mode_record_count = 8
accepted_bad_mode_count = 0
max_accepted_bad_mode_count = 0
accepted_bad_mode_gate_pass = true
```

含义：v12 scale safe-source 在离线 decision-record 层没有接受 bad-mode batch，
因此通过新增 accepted bad-mode hard gate。但这仍不改变 production-ready 结论：
该 safe-source 只能继续作为 Stage 4 shadow / guarded A/B 候选，不能直接启用
mutating admission。

## Exactness Boundary

本轮只改 offline trainer 和测试，训练 / audit 均不运行 BPC、pricing、RMP 或 worker。

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
no-negative closure。

## Verification

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_safe_source_export
```

结果：

```text
Ran 17 tests in 0.246s
OK
```

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m py_compile \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  BPC_future/tests/test_gat_batch_impact_training.py
```

结果：通过。
