# 2026-06-22 BPC_future GAT Target Mode Stage 3 v111 诊断 checkpoint 选择修复与复训报告

## 结论

本轮完成了一个窄范围工程修复：当没有任何 epoch 通过 Stage 3 local deployment
gate 时，训练脚本不再用可行 checkpoint 的 ROI-CI 排序逻辑去保存失败模型，而是改用
diagnostic key，优先选择 reject reason 更少、precision CI / safe CI / coverage
更接近 Stage 3 缺口的 checkpoint。

该修复没有放宽任何 Stage 3 gate，也没有改变 exactness boundary。v111 复训后：

```text
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
```

v111 的主要收益是诊断 checkpoint 更合理：从 v110 的低覆盖 `epoch8`
恢复到 v111 的 `epoch1`，其 validation accepted 从 `11` 提高到 `22`，
`safe_precision_ci_low` 从 `0.7412` 提高到 `0.8513`，shortfall 从
`24` 个全成功 accepted 降回 `13` 个。  
但 v111 没有超过 v108 的最佳 frontier，也没有通过 Stage 3。

## 代码变更

修改文件：

```text
BPC_future/scripts/train_gat_batch_impact.py
```

变更点：

- 通过 local deployment gate 的 checkpoint：仍按原来的
  `accepted_batch_roi_ci_low / ROI-over-baseline / utility / loss` 排序；
- 没有 checkpoint 通过 local gate 时：改用 `_threshold_diagnostic_selection_key`
  选择诊断 checkpoint；
- `selected_checkpoint_reason` 更新为：

```text
no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_ci_safe_ci_coverage
```

这只影响失败 checkpoint 的保存与后续审计可读性，不会把失败模型升级为 Stage 4
candidate。

## v111 训练结果

训练输入仍为 v107 optimized 5000 selected dataset：

```text
BPC_future/data/gat_batch_impact/v107_optimized_5000_stage4_biased_first362_scale30first16_greedy30cap4_worker16_sector30cap4_worker16_scale50sgcap12_scale100open34_batch24_sectorcapfix_20context180new120batch4_followup40_20260619
```

输出：

```text
BPC_future/results/gat_batch_impact_training_v111_5000_stage4_biased_diagnostic_selector_fix_seed13_20260622/model.pt
BPC_future/results/gat_batch_impact_training_v111_5000_stage4_biased_diagnostic_selector_fix_seed13_20260622/metrics.json
```

关键字段：

```text
best_epoch = 1
best_loss_epoch = 7
checkpoint_gate_pass = false
stage4_candidate_ready = false

validation accepted_batch_count = 22
validation accepted_batch_roi = 12.614279
validation accepted_batch_roi_ci_low = 5.023888
validation false_high_priority_on_delay = 0.0
validation false_safe_rate_union = 0.0
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.851340
```

`epoch7` 是最低 validation loss，但不是可用 checkpoint：

```text
epoch7 accepted_batch_count = 37
epoch7 false_high_priority_on_delay = 0.0104895
```

它超过 `1%` false-delay hard gate，因此仍必须 veto。v111 继续证明：
loss 更低不等于 admission 更安全。

## Threshold Frontier 与 Shortfall

frontier 输出：

```text
BPC_future/results/gat_batch_impact_threshold_frontier_v111_diagnostic_selector_fix_5000_20260622/summary.json
BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v111_diagnostic_selector_fix_threshold_frontier_zh.md
```

结果：

```text
feasible_threshold_count = 0
best accepted_batch_count = 22
best accepted_batch_roi = 12.614279
best accepted_batch_roi_ci_low = 5.023888
best safe_precision_ci_low = 0.851340
best false_high_priority_on_delay = 0.0
best false_safe_rate_union = 0.0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
```

shortfall 输出：

```text
BPC_future/results/gat_batch_impact_gate_shortfall_v111_diagnostic_selector_fix_5000_20260622/summary.json
BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v111_diagnostic_selector_fix_gate_shortfall_zh.md
```

结果：

```text
safe_precision_additional_all_success_needed = 13
recommended_next_step = collect_more_safe_validation_accepts
```

也就是说，v111 的安全 frontier 是一个接近但未过线的 near-miss。不能靠降低
`safe_precision_ci_low >= 0.90` 解决，只能补出更多同规则下仍全成功的 accepted
验证证据，或者让模型在不增加 false-delay 的前提下多接受安全样本。

## Focused Pair Gate

focused pair audit 输出：

```text
BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v111_diagnostic_selector_fix_5000_20260622/summary.json
BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v111_diagnostic_selector_fix_pair_failure_audit_zh.md
```

结果：

```text
pair_count = 384
strict_pair_pass_rate = 0.692708
failed_pair_count = 118
all_failed_heads_near_rate_among_failed = 0.728814
any_failed_head_deep_rate_among_failed = 0.0
```

和 v110 相比，focused pair strict pass 从 `0.778646` 降到 `0.692708`。
但失败性质发生变化：v111 的失败几乎都是 near-margin，没有 deep structural gap。
因此下一步不应继续 blind multiplier sweep，也不应直接收集更多大而散的数据；
更合理的是先做 explicit focused tranche 的 combined focused candidate/admission/delay
loss 复训，专门压这些 near-margin pair。

失败最集中的 context 仍包括：

```text
b6d808ebac2a6dd8  sector-wave  pair_count=55  failed=31
ac15bc4e7e3d6fff  sector-wave  pair_count=65  failed=30
79fde658840fe2b8  sector-wave  pair_count=72  failed=14
```

其中 `b6d808ebac2a6dd8` 仍是最大 blocker，但 v111 下它的最小 margin 只有
`-0.03` 量级，不再是 v110 报告中的 deep score gap 类型。

## 与 v108/v110 对比

```text
v108 frontier:
  accepted = 22
  safe_precision_ci_low = 0.851340
  false_delay = 0.003497
  shortfall = 13

v110 focused-safety selected checkpoint:
  accepted = 11
  safe_precision_ci_low = 0.741160
  false_delay = 0.0
  shortfall = 24

v111 selector-fix checkpoint:
  accepted = 22
  safe_precision_ci_low = 0.851340
  false_delay = 0.0
  shortfall = 13
```

解释：

- v111 修复了 v110 “保存低覆盖诊断点”的工程问题；
- v111 没有产生新的 Stage 3 candidate；
- v111 的 frontier 只是回到 v108 级别，并没有解决核心模型/数据问题；
- focused pair gate 仍失败，且成为显式 blocker。

## 当前判断

Stage 3 还没有完成，不能进入 Stage 4。当前最准确的 blocker 是两个：

1. safe accepted validation evidence 不足：最佳安全 frontier 只有 22 个全成功 accepted，
   Wilson lower bound 为 `0.8513`，离 `0.90` 还差 13 个全成功 accepted；
2. focused same-context pair 排序不稳：strict pass 只有 `0.6927`，主要是 near-margin
   admission/delay 排序失败。

下一步建议：

```text
1. 保留 v111 selector 修复；
2. 不降低 Stage 3 gate；
3. 不把 epoch7/8 或 coverage-ready-but-unsafe checkpoint 送入 Stage 4；
4. 先做 explicit focused tranche full training：
   - 针对 near-margin focused pairs；
   - 适度提高 focused candidate/admission/delay loss；
   - 不扩大到盲目新数据；
   - 目标是 strict_pair_pass_rate 提高，同时保持 false_delay <= 1%；
5. 如果 focused loss 不能把 accepted safe count 从 22 推到至少 35，再收集
   context-local safe accepted validation tranche。
```

## 验证

已运行：

```bash
/home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/train_gat_batch_impact.py
/home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training
/home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_knn_ood
```

结果：

```text
test_gat_batch_impact_training: Ran 32 tests, OK
test_gat_batch_impact_knn_ood: Ran 5 tests, OK
```

本轮所有训练/审计仍为 offline diagnostic-only；没有运行 BPC / pricing / RMP，
没有改变 certificate semantics。
