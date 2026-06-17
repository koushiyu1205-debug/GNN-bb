# 2026-06-17 BPC_future GAT Stage 3 v101 Focused Failure + Combined Training 综合报告

## 结论

v101 综合 v98 / v99 / v100。它仍是 Stage 3 离线训练与审计结论，不是 Stage 4 candidate。

核心新理解：

1. v96 focused pair 失败主要是 near-margin，不是 deep structural gap。
2. explicit focused tranche + combined candidate/admission/delay head loss 能改善 focused pair gate，也能恢复 validation coverage / ROI。
3. 但 v99 同时打开了太多 delay / low-ROI admission，导致 false-safe 和 family ROI gate 失败。
4. 下一步不应继续加 coverage 或降低 threshold；应在保持 explicit focused tranche 的同时，先修复 delay-risk / family ROI safety，再谈 Stage 4。

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
recommended_next_step = safety_constrained_combined_focused_training_with_delay_gate_or_family_roi_guard
```

## v98: v96 Focused Pair Failure Anatomy

输入：

```text
metrics = BPC_future/results/gat_batch_impact_training_v96_seed13_explicit_focused_tranche_v75_delay_risk_pairwise_20260617/metrics.json
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
```

v98 结果：

```text
pair_count = 145
failed_pair_count = 102
strict_pair_pass_rate = 0.296551724137931
raw_fail_rate = 0.5310344827586206
admission_fail_rate = 0.5310344827586206
delay_risk_fail_rate = 0.35172413793103446
all_failed_heads_near_rate_among_failed = 1.0
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.4689655172413793
primary = near_margin_loss_tuning_candidate
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
```

解释：

- 102 个失败 pair 的失败 head 全部落在 `abs(margin) <= 0.01`。
- 没有 `<= -0.05` 的 deep gap。
- 因此 v96 不是“结构彻底分不开”，而是 score margin 太薄，适合先做 explicit focused combined head loss。

## v99: Explicit Focused Combined Head Training

训练设置：

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
seed = 13
epochs = 8
focused_pair_selector = explicit_row_indices
focused_pair_row_indices_count = 82
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_candidate_loss_multiplier = 1.0
focused_pair_admission_loss_multiplier = 1.0
focused_pair_delay_risk_loss_multiplier = 1.0
```

产物：

```text
metrics = BPC_future/results/gat_batch_impact_training_v99_seed13_explicit_focused_combined_head_v75_20260617/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v99_seed13_explicit_focused_combined_head_training_zh.md
```

对比 v96：

| 指标 | v96 | v99 | 判断 |
|---|---:|---:|---|
| focused strict pair pass rate | 0.2966 | 0.4483 | 改善但远未过 1.0 gate |
| focused raw/admission pass rate | 0.4690 | 0.4759 | 几乎不变 |
| focused delay-risk pass rate | 0.6483 | 0.6345 | 略退 |
| validation accepted batch count | 8 | 49 | coverage 大幅恢复 |
| validation accepted batch ROI | 0.8994 | 3.9984 | ROI point/CI 改善 |
| validation accepted batch ROI CI low | 0.6643 | 1.7758 | 过 ROI lower-bound |
| validation safe precision CI low | 0.6756 | 0.9273 | 过 safe CI |
| false high-priority on delay | 0.0 | 0.2069 | 严重失败 |
| false safe rate union | 0.0 | 0.2069 | 严重失败 |
| family holdout min accepted ROI | 0.7914 | 0.1618 | 严重失败 |
| checkpoint gate pass | false | false | 仍不可进 Stage 4 |

v99 的好消息：

- explicit focused combined loss 确实增加了 coverage；
- validation accepted ROI 从 `0.8994` 到 `3.9984`；
- safe precision CI low 从 `0.6756` 到 `0.9273`；
- focused strict pair pass 从 `43 / 145` 到 `65 / 145`。

v99 的坏消息：

- false high-priority on delay 从 `0.0` 变成 `0.2069`；
- false-safe union 从 `0.0` 变成 `0.2069`；
- greedy-anchor validation accepted ROI 只有 `0.1618`；
- random-wave validation accepted ROI 只有 `0.4043`；
- focused gate 仍被 raw/admission/delay-risk/strict pair rate 拦下。

因此 v99 不能叫 Stage 4 candidate。

## v100: v99 Remaining Failure Anatomy

输入：

```text
metrics = BPC_future/results/gat_batch_impact_training_v99_seed13_explicit_focused_combined_head_v75_20260617/metrics.json
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
```

结果：

```text
pair_count = 145
failed_pair_count = 80
pair_pass_count = 65
strict_pair_pass_rate = 0.4482758620689655
raw_fail_rate = 0.5241379310344828
admission_fail_rate = 0.5241379310344828
delay_risk_fail_rate = 0.36551724137931035
all_failed_heads_near_rate_among_failed = 0.9625
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.4689655172413793
diagnosis_counts = {
  "mixed_margin_failure": 3,
  "near_margin_loss_tuning_candidate": 34,
  "near_margin_with_shared_signature": 43,
  "pair_passes": 65
}
```

剩余主要失败 context：

```text
79fde658840fe2b8: failed 20 / 35
b6d808ebac2a6dd8: failed 20 / 25
ac15bc4e7e3d6fff: failed 19 / 35
4e481a6307fca228: failed 7 / 12
ddcb5387bef3bf63: failed 6 / 6
```

解释：

- v99 没有产生 deep score gap，剩余失败仍可训练；
- 但单纯继续加 focused ordering pressure 会继续冒 false-delay / false-safe 风险；
- `near_margin_with_shared_signature` 增加，说明同一或相近 candidate signature 下，模型需要更强的 context/action consequence 条件化，而不是只看 journey 本体。

## 新判断

v98 证明：v96 不是结构性不可分，所以可以训练。

v99 证明：focused combined loss 的方向有效，但如果没有 safety / family ROI guard，会把很多 low-ROI 或 delay 行也打开。

v100 证明：剩余 focused ranking 失败仍是 near-margin，但当前 blocker 已经从“能否拉动排序”转成：

```text
can_improve_focused_ranking_without_reopening_false_delay_and_family_low_roi_admission
```

也就是说，下一步不是继续盲目加大 focused loss，而是把 combined focused loss 放进 safety-constrained admission 目标里：

- delay-risk head 必须真正压住 delay/hard-negative；
- family holdout ROI 不能靠 sector-wave 高 ROI 掩盖 greedy/random 低 ROI；
- threshold / delay gate / fallback rule 必须冻结并参与 checkpoint selection；
- focused pair gate 仍必须继续作为 hard diagnostic gate。

## Exact-safe Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

所有 v98/v99/v100 产物都只用于离线训练和审计。GAT / CBF / kNN / OOD 只能做 discovery ordering 与 finite-delay admission scheduling；进入 RMP 的列仍必须 true-RC verified；最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## 下一步

建议下一轮不是继续单一 multiplier sweep，而是做一个 safety-constrained v102：

1. 保留 `--focused-pair-row-indices-file` 和 combined focused head loss；
2. 启用或审计 delay-risk admission gate，目标是把 `false_high_priority_on_delay <= 0.01`；
3. 增强 low-ROI / hard-negative delay loss，避免 v99 的 `false_safe_rate_union = 0.2069`；
4. 增加 family ROI guard 或 family fallback，避免 greedy-anchor / random-wave low ROI 被 sector-wave 高 ROI 掩盖；
5. 若 focused strict pair pass 继续提升但 false-safe 仍失败，优先修 delay-risk / family guard，不进入 Stage 4。

进入 Stage 4 前仍必须同时满足：

```text
focused_pair_gate_pass = true
precision / safe precision CI pass
accepted ROI / ROI CI pass
false-safe gate pass
family/context holdout pass
kNN/OOD shell pass
5/10 no-regression and online shadow gates later pass
```
