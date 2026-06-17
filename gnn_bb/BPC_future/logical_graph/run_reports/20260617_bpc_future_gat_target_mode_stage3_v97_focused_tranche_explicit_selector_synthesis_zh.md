# 2026-06-17 BPC_future GAT Target Mode Stage 3 v97 Focused Tranche Explicit Selector 综合报告

## 结论

v97 是 Stage 3 离线训练/审计 plumbing 与对比综合，不是 Stage 4 candidate。

本轮把最近 v95/v96 与早期 v36/v41/v44/v45 的结论对齐后，新的判断是：

1. 早期问题不是“阈值差一点”，而是同一 RMP/context 内 positive high-ROI 候选与 delay/hard-negative 候选的局部排序仍然不稳。
2. v95 证明 v75 数据里已经有足够多的 focused same-context 对比样本，可以作为硬训练 tranche。
3. v96 证明显式 row-index selector 能正确接入训练和 focused gate，但 1 epoch smoke 的 raw/admission/delay-risk/strict pair pass rate 仍未过关。
4. 继续用 `row_index_min` 选择 focused rows 不安全，因为 v75 的 focused rows 是非连续的，会混入大量非 focused 样本。

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
recommended_next_step = train_with_explicit_focused_row_indices_and_audit_pair_failures_by_context
```

## 与早期版本对比

### v36

v36 把 ROI-neighbor blocker 拆成 repair 队列，已经指出需要围绕 top contexts 做 narrow same-context contrast，而不是继续全局放宽 threshold。

关键问题：

```text
repair_candidate_count = 16
context_repair_count = 6
roi_neighbor_delayed_high_roi_count = 3
accepted_high_point_roi_unstable_count = 13
```

这些 top contexts 后续持续出现：`b6d808`、`79fde`、`ac15` 等。

### v41

v41 审计 v39 的 false high priority on delay，核心诊断是 candidate threshold 为 0 时 candidate head 实际失效，delay gate 独自承担过滤。

```text
false_high_priority_on_delay_count = 44
false_high_priority_on_delay = 0.4489795918367347
family_counts = {"sector-wave": 44}
primary_diagnosis = raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate
```

这说明问题集中在 sector-wave 20-task 的若干 context，不是全局分布随机噪声。

### v44

v44 说明 delay-safe shell 是存在的，但覆盖太小。

```text
delay_safe_threshold_count = 1309
delay_safe_with_accepted_batch_count = 335
delay_safe_accepted_batch_count_max = 2
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
```

因此只加严 delay gate 会牺牲 coverage，不能直接进入 Stage 4。

### v45

v45 加 false-delay contrast 后，false-delay suppression 方向有效，但 coverage 仍不足。

```text
false_high_priority_on_delay = 0.0
accepted_batch_count = 3
safe_precision_ci_low = 0.4384939195509822
stage4_candidate_ready = false
```

这与 v44 一致：模型能形成安全壳，但壳太窄。

### v54 到 v94

后续版本逐步加入 individual context rows、path-token/slack、trace scalar、risk head 与 focused loss。它们改进了可审计性和部分覆盖，但没有解决 strict same-context pair gate。

v94 的 focused-head loss 结果尤其重要：只在旧 focused tranche 上加 candidate-only 或 delay-risk-only loss，仍会复现候选排序不稳的问题。因此下一步不能再盲扫单一 multiplier，必须使用更干净、更大的 explicit focused tranche，并按 context/pair failure 分类。

## v95 Focused Tranche Mining

v95 是 checkpoint-independent manifest mining，不运行 BPC、pricing、RMP、worker 或 certificate。

输入：

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
```

核心结果：

```text
sample_count = 392
focused_row_count = 82
focused_positive_row_count = 39
focused_hard_negative_row_count = 43
focused_pair_count = 145
trainable_context_count = 11
negative_only_context_count = 66
positive_only_context_count = 17
focused_family_counts = {"random-wave": 24, "sector-wave": 58}
focused_task_count_counts = {"20": 80, "50": 2}
```

最关键的 selector 发现：

```text
row_index_min = 10
selected_count = 382
focused_count = 82
extra_nonfocused_count = 300
extra_nonfocused_rate = 0.7853403141361257
recommended_selector = explicit_row_indices
```

这说明原先 `focused_pair_gate_row_index_min` 只适合旧的 contiguous focused rows。v75 focused rows 是非连续 tranche，必须用显式 row index 文件，否则训练会被 300 条非 focused rows 稀释。

产物：

```text
summary = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/summary.json
focused_row_indices = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json
focused_pairs = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_pairs.jsonl
```

## v97 代码/审计改动

新增：

```text
BPC_future/scripts/audit_gat_batch_impact_focused_tranche_mining.py
BPC_future/tests/test_gat_batch_impact_focused_tranche_mining.py
```

训练脚本新增显式 focused row index 支持：

```text
--focused-pair-row-indices-file
```

支持输入：

```text
JSON list: [10, 11, ...]
JSON object: {"focused_row_indices": [...]}
JSONL rows: {"row_index": 10}
```

并写入：

```text
loss_options.focused_pair_row_indices_file
loss_options.focused_pair_row_indices
training_run_config.focused_pair_gate_config.focused_pair_selector
training_contract.focused_pair_row_indices_count
focused_pair_gate.focus_selector
```

## v96 Explicit Selector Smoke

v96 是 1 epoch CPU smoke，用 v95 的 explicit focused row file 验证真实训练路径。

命令要点：

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_delay_risk_loss_multiplier = 0.5
```

结果：

```text
checkpoint_gate_pass = false
focused_pair_gate_active = true
focus_selector = explicit_row_indices
focus_row_indices_count = 82
focused_pair_count = 145
raw_pair_pass_rate = 0.4689655172413793
admission_pair_pass_rate = 0.4689655172413793
delay_risk_pair_pass_rate = 0.6482758620689655
strict_pair_pass_rate = 0.296551724137931
accepted_batch_count = 8
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9916458189080761
safe_precision_ci_low = 0.6755843804891231
accepted_batch_roi = 0.8994215540587902
accepted_batch_roi_ci_low = 0.6642962464132351
```

Stage 4 blockers：

```text
raw_pair_pass_rate_below_threshold
admission_pair_pass_rate_below_threshold
delay_risk_pair_pass_rate_below_threshold
strict_pair_pass_rate_below_threshold
safe_precision_ci_low_below_threshold_or_not_measurable
knn_ood_audit_missing
knn_ood_holdout_audit_not_run
online_shadow_and_opt_in_ab_not_run
```

解释：

1. explicit selector 的 plumbing 是通的。
2. 当前模型在 v95 focused tranche 上仍然没有学会同一 context 内的 strict positive-vs-delay 排序。
3. delay-risk head 比 raw/admission head 好一些，但 strict pass rate 只有 0.2966，说明只训练 delay-risk 不够。
4. validation precision 点估计高，但 safe precision CI low 仍不足，不能进入 Stage 4。

## 新理解和问题

### 新理解

早期 v44/v45 的“安全壳太窄”现在可以更具体地解释为：

```text
same-context positive-vs-delay local ranking is not stable enough
```

模型不是完全找不到安全列，而是在同一个 RMP context 下无法稳定区分：

- 真正能改善 trajectory 的 high-ROI positive batch；
- true-RC 已验证但可能引发拖尾的 delay/hard-negative batch。

这正好对应目标模式：GAT 不应该替代 exact pricing，而应该学习 admission scheduling，把更可能改善 RMP trajectory 的列设为 HIGH_PRIORITY，把可能拖尾的负列放入 DELAY_QUEUE。

### 当前问题

1. `row_index_min` focused selector 对 v75 不成立，会引入 78.5% 非 focused rows。
2. v95 focused tranche 主要仍集中在 20-task，50-task 只有 2 行，不能证明 30/50/100 泛化。
3. 66 个 negative-only context 没有同 context positive 对照，说明还需要补数据或构造邻域对比。
4. v96 只跑 1 epoch，不能评价 full training 上限，但已经足以证明 current head/loss 仍未过 strict pair gate。
5. 不能用 validation precision 点估计替代 CI gate、kNN/OOD shell、Stage 4 online shadow 或 final exact certificate。

## Exact-safe Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
runs_worker = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
official_bound_effect = false
```

GAT / CBF / kNN / OOD 只能做 discovery ordering 与 finite-delay admission scheduling。
进入 RMP 的列仍必须 true-RC verified。
最终 OPTIMAL / no-negative certificate 仍只能由当前 branch/cut/dual 下 exact pricing 对完整配置宇宙 exhaustive closure 产生。

## 下一步

不建议继续做盲目 threshold 或单一 multiplier sweep。下一步应围绕 v95 explicit focused tranche 做两件事：

1. 正式训练时使用 `--focused-pair-row-indices-file`，不要再用 `row_index_min`。
2. 对 v96 的 145 个 pair failure 按 context、family、candidate signature、path-token/slack、delay-risk margin 分类，判断 raw/admission 失败是分数差一点还是结构性分不开。

之后再选择训练方向：

```text
if many margins are near zero:
  try combined focused candidate/admission/delay-risk loss with explicit tranche
else:
  add or repair context/action-consequence features before more training
```

在 focused strict pair gate、precision/ROI CI、kNN/OOD shell 都过之前，不进入 Stage 4 replay。
