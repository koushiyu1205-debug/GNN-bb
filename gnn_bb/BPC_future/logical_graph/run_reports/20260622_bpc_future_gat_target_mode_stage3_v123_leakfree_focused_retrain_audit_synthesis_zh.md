# BPC_future GAT target-mode Stage 3 v123 leak-free focused retrain 综合审计

日期：2026-06-22

## 结论

v123 不是 Stage 4 candidate。

本轮修正的是训练/审计边界：focused gate 仍用完整 102 行 hard set，但 focused training loss 只用 seed13 train split 内的 81 行；v121 focused boost 也只保留 7 行 train rows，避免把 validation focused rows 放进 loss replay。

这个边界修正是正确的，但效果没有超过 v121：

- validation local gate 通过，accepted=35，safe precision CI low=0.9011，false high-priority on delay=0.00361；
- accepted ROI=19.349，低于 v121 的 19.616，高于 v122 的 19.036；
- focused same-context strict pair pass=74/78=0.9487，低于 v121 的 75/78=0.9615；
- kNN/OOD global strict 和 scale strict 都只有 accepted=33，safe precision CI low=0.8957，低于 0.9。

因此 v123 只能作为 diagnostic checkpoint，不能进入 Stage 4 shadow / opt-in，也不能作为默认 selector。

## 本轮输入

- dataset: `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- selector summary: `BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/summary.json`
- training metrics: `BPC_future/results/gat_batch_impact_training_v123_leakfree_focused_seed13_20260622/metrics.json`
- training report: `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v123_leakfree_focused_retrain_seed13_zh.md`
- focused audit: `BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v123_leakfree_focused_20260622/summary.json`
- kNN global strict: `BPC_future/results/gat_batch_impact_knn_ood_audit_v123_leakfree_focused_global_strict_20260622/summary.json`
- kNN scale strict: `BPC_future/results/gat_batch_impact_knn_ood_audit_v123_leakfree_focused_scale_strict_20260622/summary.json`

## leak-free focused 配置

使用训练脚本 seed13 / validation_fraction=0.25 复算 split：

- full focused gate rows: 102
- focused training rows: 81
- focused validation rows: 21
- v121 focused boost train rows: 7
- v121 targeted safe-positive train rows: 24
- v122 35 行 targeted positive replay 未使用

训练脚本现在区分两个输入：

- `--focused-pair-row-indices-file`: gate/audit 使用的完整 focused hard set；
- `--focused-pair-training-row-indices-file`: loss replay 使用的 train-only focused set。

本轮没有运行 BPC/pricing，也没有改变 pricing universe、RMP、bound 或 certificate。

## 训练结果

| run | best epoch | best loss epoch | local gate | accepted | ROI | ROI CI low | safe CI low | false-delay | focused strict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| v120 | 6 | 3 | true | 35 | 19.337 | 10.355 | 0.9011 | 0.0072 | 0.9231 |
| v121 | 4 | 3 | true | 35 | 19.616 | 10.558 | 0.9011 | 0.0072 | 0.9615 |
| v122 | 2 | 4 | true | 35 | 19.036 | 9.872 | 0.9011 | 0.0036 | 0.7564 |
| v123 | 2 | 4 | true | 35 | 19.349 | 10.235 | 0.9011 | 0.0036 | 0.9487 |

v123 的 selected checkpoint 是 `epoch 2`。不是选择 validation loss 最低的 `epoch 4`，因为 checkpoint selection 仍是 `deployment_gate_first_then_roi_ci_baseline_utility_loss`，优先满足部署 gate / ROI / CI / safety 约束，而不是按 validation loss 最小选择。

按 epoch 粗看：

- epoch 4 虽然 validation loss 最低，但 accepted=9，不满足覆盖；
- epoch 6 accepted=101、epoch 7 accepted=63、epoch 8 accepted=44，但 precision 分别只有 0.9975、0.9945、0.9887，安全约束不如 selected epoch；
- epoch 2 在本轮里是 local gate 可行解，accepted=35、safe CI low=0.9011、false-delay=0.00361。

## focused pair 审计

v123 focused pair audit:

- pair_count=78
- pair_pass_count=74
- failed_pair_count=4
- strict_pair_pass_rate=0.9487179487
- raw_fail_count=3
- admission_fail_count=4
- delay_risk_fail_count=3
- contexts_with_failure_count=4
- diagnosis_counts: mixed_margin_failure=3, near_margin_loss_tuning_candidate=1

这比 v122 的 59/78 明显恢复，但仍低于 v121 的 75/78，而且离 Stage 3 focused gate 要求的 1.0 仍有 4 对失败。

重要的是，失败不是纯 near-margin loss tuning：

- 只有 1 个 failed pair 属于 near-margin；
- 3 个 failed pair 是 mixed-margin failure；
- audit 建议为 `add_or_repair_context_action_consequence_features_before_more_sweeps`，并明确避免 `do_not_continue_blind_multiplier_sweeps`。

因此，继续只调 focused multiplier 或 replay 行，很可能只是在 v121/v123 附近来回摆动，不能稳定过 gate。

## kNN/OOD strict audit

global strict:

- accepted=33
- accepted ROI=16.054
- ROI CI low=8.107
- safe precision=1.0
- safe precision CI low=0.895727
- false high-priority on delay=0
- false safe union=0
- OOD count=0
- validation_candidate_ready=false
- blockers: `validation_safe_precision_ci_low_below_min`, `validation_candidate_not_ready`

scale strict:

- accepted=33
- accepted ROI=18.371
- ROI CI low=8.813
- safe precision=1.0
- safe precision CI low=0.895727
- false high-priority on delay=0
- false safe union=0
- OOD count=9
- coverage=0.9692
- validation_candidate_ready=false
- blockers: `validation_safe_precision_ci_low_below_min`, `validation_candidate_not_ready`

kNN/OOD 没有发现 false-safe，但把训练 summary 的 35 accepted 压到 33。33 个全安全 accepted 的 Wilson 下界只有 0.8957，低于 0.9；至少还需要约 2 个全安全 accepted 才能回到 35 accepted / 0.9011 的边界。

## Stage 状态

- `stage3_completed=false`
- `stage4_candidate_ready=false`
- `production_ready=false`
- `default_enabled=false`
- `diagnostic_only=true`

不能进入 Stage 4，原因：

- focused same-context pair gate 未通过；
- kNN/OOD global strict 未通过；
- kNN/OOD scale strict 未通过；
- online shadow / opt-in A/B 未运行；
- 5/10 no-regression 和 20-task wall-time ROI 未运行；
- GAT/kNN/OOD 不能提供 official bound 或 exact certificate。

## 下一步

v123 说明“去掉 validation focused loss 泄漏”是必要的工程修正，但不是性能修复本身。下一步不应该继续盲目增减 replay 权重，而应转向特征和选择边界：

1. 回到 v121 checkpoint 附近，把 v121 作为当前最强 diagnostic baseline。
2. 做 kNN-aware threshold/frontier search，目标是在保持 focused strict 不低于 0.9615 的前提下，把 strict-shell accepted 从 34/33 提到至少 35。
3. 针对 v123 audit 里的 4 个失败 pair 做 action-consequence feature audit，优先检查模型是否能看到“同 context 下选择该 batch 后的后续队列/trajectory 变化”。
4. 若继续训练，必须只用 train split 失败对；每轮训练后立即审计完整 102 focused gate 和 kNN global/scale strict。

## exactness boundary

本轮只运行离线训练、focused pair audit、kNN/OOD safety-shell audit 和报告生成：

- 不运行 BPC/pricing。
- 不修改 pricing oracle、RMP、bound、certificate 或 exact closure。
- GAT/kNN/OOD 仍是 diagnostic-only。
- `selector_is_pricing_oracle=false`
- `selector_can_certificate=false`
- `gate_can_permanently_discard_negative_columns=false`
- true-RC negative columns 必须保持 eventually reachable。
