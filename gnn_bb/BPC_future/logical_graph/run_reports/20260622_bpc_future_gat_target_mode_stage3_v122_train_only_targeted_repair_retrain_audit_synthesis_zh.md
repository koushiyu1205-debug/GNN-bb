# BPC_future GAT target-mode Stage 3 v122 train-only targeted repair 综合审计

日期：2026-06-22

## 结论

v122 不是 Stage 4 candidate。

这轮 train-only targeted repair 解决了一部分 v108/v121 的验证集本地安全覆盖问题：训练 summary 中 selected checkpoint 为 `epoch 2`，validation local gate 已通过，accepted=35，safe precision CI low=0.9011，false high-priority on delay=0.00361。

但它没有让整体 Stage 3 通过，原因有两个：

1. focused same-context pair gate 明显退化：strict pair pass 从 v121 的 75/78=0.9615 降到 v122 的 59/78=0.7564。
2. kNN/OOD strict shell 后 accepted 从 35 降到 32，safe precision CI low=0.8928，低于 0.9，下界还差 3 个全安全 accepted 验证样本左右。

因此 v122 只能保留为 diagnostic checkpoint，不能进入 Stage 4 shadow/opt-in，也不能启用为默认 selector。

## 本轮输入

- dataset: `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- training metrics: `BPC_future/results/gat_batch_impact_training_v122_train_only_targeted_repair_seed13_20260622/metrics.json`
- training report: `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v122_train_only_targeted_repair_retrain_seed13_zh.md`
- focused audit: `BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v122_train_only_targeted_repair_20260622/summary.json`
- kNN global strict: `BPC_future/results/gat_batch_impact_knn_ood_audit_v122_train_only_targeted_repair_global_strict_20260622/summary.json`
- kNN scale strict: `BPC_future/results/gat_batch_impact_knn_ood_audit_v122_train_only_targeted_repair_scale_strict_20260622/summary.json`

## 为什么 v108 没选 epoch 7/8

v108 的 checkpoint selection 不是按 validation loss 选，而是 `deployment_gate_first_then_roi_ci_baseline_utility_loss`。

- v108 `best_epoch=1`
- v108 `best_loss_epoch=7`
- v108 `epoch 7`: validation loss 最低，但 false high-priority on delay=0.0350，超过 0.01 硬线。
- v108 `epoch 8`: accepted=182，但 false high-priority on delay=0.1469，更不能选。
- v108 `epoch 1`: false high-priority on delay=0，但 accepted=13，safe CI low=0.7719，不足以通过 Stage 3，只能作为最安全的诊断 checkpoint。

所以没有选 epoch 7/8 是正确的：它们覆盖更高、loss 更低，但违反 safety veto。

## v122 训练结果

| run | best epoch | best loss epoch | local gate | accepted | ROI | ROI CI low | high-priority precision | safe CI low | false-delay | focused strict |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| v108 | 1 | 7 | false | 13 | 33.164 | 15.009 | 1.0000 | 0.7719 | 0.0000 | 未运行 |
| v121 | 4 | 3 | true | 35 | 19.616 | 10.558 | 0.9967 | 0.9011 | 0.0072 | 0.9615 |
| v122 | 2 | 4 | true | 35 | 19.036 | 9.872 | 0.9990 | 0.9011 | 0.0036 | 0.7564 |

v122 相比 v121：

- false-delay 从 0.0072 降到 0.0036，安全率变好。
- high-priority precision 从 0.9967 升到 0.9990。
- ROI 从 19.616 小幅降到 19.036。
- focused pair strict pass 从 0.9615 大幅降到 0.7564，这是主退化。

训练层面的 local gate 已经不是主要问题；问题转移到 focused pair 排序一致性和 kNN/OOD shell 后的 accepted 覆盖。

## focused pair 审计

v122 focused pair audit:

- pair_count=78
- pair_pass_count=59
- failed_pair_count=19
- strict_pair_pass_rate=0.7564102564
- raw_fail_count=17
- admission_fail_count=15
- delay_risk_fail_count=17
- contexts_with_failure_count=13
- any_failed_head_deep_rate_among_failed=0.0
- all_failed_heads_near_rate_among_failed=0.7368

这说明 v122 失败大多不是深结构不可分，而是 near-margin / loss balancing 问题。但退化幅度太大，不能接受。

特别要注意：v121 剩余的 validation context `9f80ae35ea87da5b` 在 v122 focused gate 里已经 pass；但 v122 新增了大量 20-task focused pair 失败，说明 train-only boost 的选择把局部排序从原来的少数硬点修复，变成了多处近边界扰动。

## kNN/OOD strict audit

global strict:

- accepted=32
- accepted ROI=15.284
- ROI CI low=7.084
- false high-priority on delay=0
- false safe union=0
- safe precision=1.0
- safe precision CI low=0.892817
- validation_candidate_ready=false
- blocker: `validation_safe_precision_ci_low_below_min`

scale strict:

- accepted=32
- accepted ROI=16.782
- ROI CI low=7.201
- false high-priority on delay=0
- false safe union=0
- OOD rate=0.03425
- safe precision=1.0
- safe precision CI low=0.892817
- validation_candidate_ready=false
- blocker: `validation_safe_precision_ci_low_below_min`

kNN/OOD 没有发现 false-safe，但它把训练 summary 的 35 accepted 压到 32 accepted。32 个全安全 accepted 的 Wilson 下界只有 0.8928，低于 0.9；需要至少约 35 个全安全 accepted 才能回到 0.9011。

## Stage 状态

- `stage3_completed=false`
- `stage4_candidate_ready=false`
- `production_ready=false`
- `default_enabled=false`
- `diagnostic_only=true`

不能进入 Stage 4，原因：

- focused pair gate 失败；
- kNN/OOD strict validation candidate 未 ready；
- online shadow / opt-in A/B 未运行；
- 5/10 no-regression 和 20-task wall-time ROI 未运行；
- GAT/kNN/OOD 不能提供 official bound 或 exact certificate。

## 下一步

不要继续沿 v122 的 train-only targeted safe-positive replay 直接加权。它虽然让本地 safety metrics 更好，但破坏了 focused same-context ranking。

下一步应回到 v121 方向，做两个更窄的修复：

1. 保留 v121 的 focused pair 结构，不再引入会扰乱 20-task context 的大范围 targeted positive replay。
2. 专门提升 kNN strict 后的 accepted 覆盖，从 32 提到至少 35，同时硬约束 focused pair strict pass 不能低于 v121。

可执行方向：

- 对 v121 checkpoint 做 threshold/frontier 层面的 kNN-aware selection，优先找能通过 global strict 的 35 accepted 阈值组合。
- 若继续训练，只允许 train split 内 near-margin failed pair 微调，且每轮必须即时审计 focused strict pass。
- 不要用 validation row 做训练 boost；validation 只能用于审计和选择，不进入 loss replay。

## exactness boundary

本轮只运行离线训练、focused pair audit、kNN/OOD safety-shell audit 和报告生成：

- 不运行 BPC/pricing。
- 不修改 pricing oracle、RMP、bound、certificate 或 exact closure。
- GAT/kNN/OOD 仍是 diagnostic-only。
- `selector_is_pricing_oracle=false`
- `selector_can_certificate=false`
- `gate_can_permanently_discard_negative_columns=false`
- true-RC negative columns 必须保持 eventually reachable。
