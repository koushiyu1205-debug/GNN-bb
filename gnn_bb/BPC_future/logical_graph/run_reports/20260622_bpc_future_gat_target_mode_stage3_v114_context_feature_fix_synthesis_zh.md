# 2026-06-22 BPC_future GAT Target Mode Stage 3 v114 Context Feature Fix 综合报告

## 结论

v114 修复了 `recent_objective_delta_before` 在数据构建时误读当前 batch outcome `objective_delta` 的问题。这个修复是必要的，因为同一 `context_hash` 下的正负样本不应因为当前 batch 的结果而得到不同 context tensor。

但是，用修复后的 v114 数据集重新训练 GAT 后，效果没有比当前 v112 最优线更好：

- v114 selected checkpoint 通过本地 deployment threshold gate；
- v114 global/scale kNN-OOD safety shell 均通过；
- 但 v114 accepted ROI 和 ROI CI-low 均低于 v112；
- v114 focused-pair strict pass rate 从 v112 的 `0.7421875` 降到 `0.7161458333`；
- 因此 v114 不替换 v112，也不是 Stage 4 candidate。

## 输入与产物

```text
fixed_dataset = BPC_future/data/gat_batch_impact/v114_context_feature_no_outcome_delta_5000_stage4_biased_20260622
training_metrics = BPC_future/results/gat_batch_impact_training_v114_context_feature_fix_focused_nearmargin_seed13_20260622/metrics.json
checkpoint = BPC_future/results/gat_batch_impact_training_v114_context_feature_fix_focused_nearmargin_seed13_20260622/model.pt
top_context_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v114_fixed_dataset_top_context_feature_contrast_zh.md
focused_pair_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v114_context_feature_fix_pair_failure_audit_zh.md
knn_global_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v114_context_feature_fix_knn_ood_global_strict_zh.md
knn_scale_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v114_context_feature_fix_knn_ood_scale_strict_zh.md
```

## 修复点

`BPC_future/scripts/build_gat_batch_impact_dataset.py` 中的 context feature 构造原先把：

```text
recent_objective_delta_before -> objective_delta
```

作为 fallback。这会让同一 context 下的样本把当前 batch 的 outcome 写入 `*_before` 特征，造成 same-context pair 的 context tensor 漂移。v114 已移除该 alias：只有原始 row 或 event 明确提供 `recent_objective_delta_before` 时才使用，否则走默认有限值。

新增 unittest 覆盖：两个 same-context row 即使 `objective_delta` 不同，构造出的 `recent_objective_delta_before` context feature 也保持一致。

## 数据集重建结果

```text
all_checks_pass = true
sample_count = 1221
candidate_count = 13352
training_ready = true
ranking_ready = true
same_context_pair_count = 2050
same_context_comparable_pair_count = 1543
positive_negative_label_pair_count = 612
family_counts = {'greedy-anchor': 358, 'random-wave': 449, 'sector-wave': 414}
task_count_counts = {'5': 32, '10': 74, '20': 792, '30': 168, '50': 119, '100': 36}
```

## Top Context 审计

| 数据 | context drift pairs | failed drift pairs | model-input collision pairs | failed collision pairs | primary |
|---|---:|---:|---:|---:|---|
| v107 原数据 | 474 | 128 | 64 | 64 | same_context_feature_drift_blocks_pair_gate_interpretability |
| v114 fixed dataset | 0 | 0 | 64 | 64 | model_input_collision_still_exists_in_top_contexts |

解释：

- 修复后 same-context context tensor 漂移已清零；
- 当前 tensor 已包含 candidate path token、trace scalar、slack scalar；
- 剩余 blocker 不是简单的 path/timing/slack 全缺失，而是 top contexts 中仍有 64 个正负 pair 对模型输入不可区分；
- 仍缺 per-candidate branch/cut 或 active-basis interaction，当前只有 context aggregate 的 `branch_constraint_count` 和 `cut_dual_l1_norm`。

## GAT 训练对比

| run | selected epoch | accepted | ROI | ROI CI-low | safe CI-low | false-delay | checkpoint gate | Stage 4 candidate |
|---|---:|---:|---:|---:|---:|---:|---|---|
| v108 | 1 | 13 | 33.1637 | 15.0086 | 0.7719 | 0.0000 | false | false |
| v112 | 1 | 35 | 4.9211 | 2.6666 | 0.9011 | 0.0000 | false | false |
| v113 | 3 | 76 | 2.5290 | 1.3757 | 0.9519 | 0.01049 | false | false |
| v114 | 3 | 35 | 4.6059 | 2.2898 | 0.9011 | 0.0000 | false | false |

v114 selected checkpoint reason：

```text
local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
```

v114 本地 gate 通过，但整体 checkpoint gate 仍失败，原因是 focused-pair gate 和 kNN holdout / online shadow 等 Stage 4 前置项未满足。kNN/OOD 后补审计已通过，但 focused-pair blocker 仍存在。

## Focused Pair Gate

| run | pair_count | passed | failed | strict pass rate | failed all-near rate | deep failure rate |
|---|---:|---:|---:|---:|---:|---:|
| v112 | 384 | 285 | 99 | 0.7421875 | 0.7576 | 0.0000 |
| v113 | 384 | 284 | 100 | 0.7395833 | 0.6300 | 0.1900 |
| v114 | 384 | 275 | 109 | 0.7161458 | 0.8349 | 0.0000 |

v114 比 v112 更差。虽然 v114 没有 deep focused-pair failure，但 near-margin 失败更多，说明修复 outcome leakage 后，模型少了一条不该存在的“结果提示”，真实区分能力还不足。

## kNN / OOD Safety Shell

| run | grouping | accepted | ROI | ROI CI-low | safe CI-low | false-safe union | OOD | coverage | ready |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| v108 | global | 9 | 14.0045 | 8.7530 | 0.7008 | 0.0000 | 0.0000 | 1.0000 | false |
| v108 | scale | 10 | 23.2199 | 4.5569 | 0.7225 | 0.0000 | 0.0153 | 0.9847 | false |
| v112 | global | 35 | 4.9211 | 2.6666 | 0.9011 | 0.0000 | 0.0000 | 1.0000 | true |
| v112 | scale | 35 | 4.9211 | 2.6666 | 0.9011 | 0.0000 | 0.0123 | 0.9877 | true |
| v114 | global | 35 | 4.6059 | 2.2898 | 0.9011 | 0.0000 | 0.0000 | 1.0000 | true |
| v114 | scale | 35 | 4.6059 | 2.2898 | 0.9011 | 0.0000 | 0.0429 | 0.9571 | true |

v114 的 kNN/OOD 安全壳没有失败；但 scale grouping 下 OOD rate 高于 v112，且 ROI 不如 v112。

## 判断

当前主线应保持：

```text
best_stage3_checkpoint_for_safety_shell = v112
fixed_dataset_builder_required_for_future_runs = true
v114_replaces_v112 = false
stage3_completed = false
stage4_candidate_ready = false
```

下一步不应继续只扫 loss multiplier 或 threshold。主要缺口已经转为模型输入表达：

```text
recommended_next_step = add_or_repair_per_candidate_branch_cut_active_basis_interaction_features_then_retrain
```

也就是把每个候选列和当前 branch/cut/active-basis 状态的交互显式写进候选侧特征，而不是只给 context aggregate。否则同一 context 下部分正负 batch 对模型仍是 collision 或 near-margin 混淆。

## Exactness Boundary

- 本报告所有训练和审计均为 offline diagnostic；
- 不运行 BPC、pricing、RMP、worker；
- 不生成 certificate 或 official lower bound；
- GAT/kNN/OOD 只能作为调度和安全壳诊断，不能永久丢弃负 reduced-cost column；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
