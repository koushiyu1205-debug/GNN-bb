# 2026-06-17 BPC_future GAT Stage 3 v70 Trace-feature Full-training 综合报告

## 目的

承接 v64/v65 的结论，本轮把 trace/timing/resource scalar schema 从 focused smoke 扩展到 v54/v51 历史完整 batch-impact dataset，并训练新 checkpoint，回答两个问题：

1. trace features 是否缓解 v55 的 random-wave high-ROI 盲区；
2. trace features 是否修复 v60 暴露的 `79fde/ac15` 同 context positive-vs-hard-negative 排序失败。

本轮仍是离线 Stage 3 diagnostic，不运行 BPC、pricing、RMP、worker 或 certificate。

## Exact-safe Boundary

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能用于 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列仍必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 本轮产物

### v66 完整 trace-feature dataset

```text
dataset =
  BPC_future/data/gat_batch_impact/v66_v54_trace_features_20260617

dataset_report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_batch_impact_dataset_v66_v54_trace_features_zh.md
```

v66 使用 v54 manifest 的 15 个 `source_jsonl_paths` 重建，和 v54 完全对齐：

```text
sample_count = 392
candidate_count = 4703
batch_label_counts = {'non_improving': 116, 'roi_positive': 276}
candidate_label_counts = {'delay_queue': 407, 'high_priority': 4296}
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 120}
task_count_counts = {'5': 2, '10': 8, '20': 209, '30': 76, '50': 96, '100': 1}
training_ready = true
ranking_ready = true
skipped_counts = {}
candidate_feature_dim = 36
trace_feature_count = 22
```

对比 v54，样本、候选、标签、family/task 分布不变；主要变化是 candidate feature schema 从 14 维扩到 36 维。

focused row 抽检：

```text
row_index = 383
context_hash = ac056820151e9ad7
feature_shape = [1, 36]
trace_arc_option_count = 3.0
trace_total_energy = 30.900316
```

### v67 trace-feature training

```text
checkpoint =
  BPC_future/results/gat_batch_impact_training_v67_v66_trace_features_20260617/gat_batch_impact.pt

metrics =
  BPC_future/results/gat_batch_impact_training_v67_v66_trace_features_20260617/metrics.json

training_report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v67_v66_trace_feature_training_zh.md
```

训练配置复用 v55 的 hard ROI / delay-risk / pairwise false-delay contrast 配置：

```text
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = true
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
false_high_priority_loss_multiplier = 12.0
candidate_delay_loss_multiplier = 2.0
hard_roi_negative_delay_loss_multiplier = 2.0
hard_roi_safe_delay_loss_multiplier = 1.0
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
```

v67 selected checkpoint：

```text
best_epoch = 8
best_loss_epoch = 3
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons =
  ['false_high_priority_on_delay_too_high',
   'false_safe_rate_union_too_high',
   'knn_ood_audit_missing']
```

### v68 focused individual context ranking

```text
summary =
  BPC_future/results/gat_batch_impact_individual_context_ranking_v68_v67_trace_features_20260617/summary.json

report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v68_v67_trace_feature_individual_context_ranking_zh.md
```

同 v60 一样，固定 `focus_row_index_min = 383`，审计 v53 individual rows。

### v69 threshold frontier

```text
summary =
  BPC_future/results/gat_batch_impact_threshold_frontier_v69_v67_trace_features_20260617/summary.json

report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v69_v67_trace_feature_threshold_frontier_zh.md
```

## 与 v55 的对比

| metric | v55 old schema | v67 trace schema | 判断 |
|---|---:|---:|---|
| selected accepted batch | 3 | 44 | coverage 大幅提升 |
| accepted batch ROI | 32.523210 | 6.743340 | v67 ROI 仍高，但不再只接受极少数高 ROI 点 |
| accepted batch ROI CI-low | 23.902833 | 3.516113 | v67 coverage 更高但 ROI 均值下降 |
| HP precision | 0.333333 | 0.930233 | candidate precision 明显改善 |
| HP precision CI-low | 0.120582 | 0.908710 | v67 过 0.9 CI 门槛 |
| safe precision | 1.000000 | 1.000000 | 两者点估计都安全 |
| safe precision CI-low | 0.438494 | 0.919702 | v67 safe CI 明显改善 |
| false_high_priority_on_delay | 0.042553 | 0.410256 | v67 高覆盖后 false-delay 爆发 |
| false_high_priority_on_delay_count | 6 | 48 | 仍是 hard blocker |
| random-wave accepted | 0 | 11 | random-wave 盲区被缓解 |
| random-wave high-ROI capture | 0.0 | 0.5 | v67 捕获 3/6 random-wave high ROI |
| sector-wave high-ROI capture | 0.115385 | 0.846154 | sector-wave 覆盖也提高 |
| missing accepted opportunity families | `['random-wave']` | `[]` | family opportunity coverage 有进步 |

结论：trace/timing/resource scalar features 确实改变了模型行为。它不只是噪声输入：v67 显著提高了 random-wave 和 sector-wave high-ROI coverage，也把 HP precision / safe precision CI 从 v55 的不可用状态推到较高水平。

但这个进步是以 false-delay 复发为代价。selected checkpoint 的 `false_high_priority_on_delay = 0.410256`，远高于 Stage 3 gate 的 `0.01`。

## Focused Ranking 对比

| metric | v60 / v55 | v68 / v67 | 判断 |
|---|---:|---:|---|
| focused rows | 9 | 9 | 同一 row range |
| positive/negative pair count | 4 | 4 | 同一 focused gate |
| raw pair pass | 1/4 | 1/4 | 未改善 |
| admission pair pass | 2/4 | 1/4 | 变差 |
| delay-risk pair pass | 2/4 | 1/4 | 变差 |
| strict pair pass | 1/4 | 1/4 | 未改善 |
| mean raw margin | -0.007311 | -0.051244 | positive 相对 hard-negative 更弱 |
| mean admission margin | -0.003809 | -0.033501 | risk-adjusted 排序更弱 |
| primary | candidate_head_context_ranking_failure | candidate_head_context_ranking_failure | blocker 未变 |

结论：v67 修复了宏观 family coverage 的一部分，但没有修复 `79fde/ac15` 同 context individual attribution 的核心反例。positive target 仍没有稳定排在 hard-negative 前面。

这点很关键：如果只看 v67 training metrics，会误以为 trace features 已经接近 Stage 4；但 v68 说明 candidate head 的 action-consequence ranking 仍不可靠。

## Threshold Frontier

v69 独立 frontier 审计确认：

```text
global_frontier_count = 17125
family_delay_fallback_frontier_count = 18244
family_local_frontier_count = 0
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = model_ranking_false_delay_blocker
best_accepted_batch_count = 45
best_accepted_batch_roi_ci_low = 3.434025
best_safe_precision_ci_low = 0.921346
best_false_high_priority_on_delay = 0.452991
best_false_safe_rate_union = 0.452991
best_local_reject_reasons =
  ['false_high_priority_on_delay_too_high',
   'false_safe_rate_union_too_high']
```

这说明 v67 的 Stage 3 失败不是训练脚本 checkpoint selector 的偶然结果。完整 frontier 没有找到满足 gate 的阈值。

## 新理解

### 1. v64/v66 trace scalar 有效，但只解决了 coverage 侧

之前 v65 判断 random-wave 盲区仍未被 v53/v64 路线覆盖。v67 更新这个判断：trace scalar 接入完整 dataset 后，random-wave 不是 0 accepted 了，high-ROI capture 到 0.5。

因此，trace/timing/resource scalar 应保留，不应回滚。

### 2. false-delay tradeoff 仍存在

v67 回到 v39/v45/v46 的旧形态：coverage 和 ROI 回来后，false-delay 大幅复发。v69 的 best frontier `false_high_priority_on_delay = 0.452991`，与旧版本 0.44 左右的失败形态一致。

所以当前不是“没有更多信息”，而是当前 22 个 trace scalar 还不足以表达：

- 同 context 下哪个 path-option / timing pattern 会真正改善 trajectory；
- 哪个 true-RC negative 会引发 retry / proof-tail / primal regression；
- candidate 与 active basis / cuts / branch rows 的相互作用。

### 3. focused individual ranking 仍是硬 gate

v68 证明，哪怕宏观 coverage 改善，`79fde/ac15` focused positive-vs-hard-negative 排序仍失败。下一版训练不能只追求 family coverage 或 accepted ROI，需要把 focused context pair gate 纳入模型选择：

```text
79fde positive > 79fde hard-negative
ac15 positive > ac15 hard-negative
```

至少在 diagnostic 里，raw candidate score、admission score、delay-risk score 都应分别过关。

### 4. 下一步应从 scalar trace 转向 candidate interaction / token sequence

v64 只接入了可直接从 capture 中恢复的 scalar trace。v70 的结果说明 scalar aggregate 有帮助，但无法充分区分同 context hard-negative。

下一步更像模型/特征结构问题，而不是继续调阈值：

- tokenized arc-option sequence / path-type sequence；
- task time-window slack；
- per-candidate branch/cut coefficients；
- active basis / active pool coefficient overlap；
- candidate signature embedding；
- candidate-level proof-tail / retry proxy。

## 当前结论

```text
stage3_completed = false
stage4_candidate_ready = false
stage5_ready = false
production_ready = false
default_enabled = false
```

v67/v68/v69 的综合判断：

1. v66 trace-feature dataset 构建正确，和 v54 数据范围一致；
2. v67 trace-feature checkpoint 相比 v55 有真实进步：coverage、random-wave capture、HP precision CI、safe precision CI 都明显改善；
3. v67 仍不能进入 Stage 4，因为 false_high_priority_on_delay / false_safe_rate_union 严重超 gate；
4. v68 focused ranking 没有改善，甚至 admission / delay-risk pair pass 下降；
5. v69 full frontier 仍 `feasible_threshold_count = 0`，primary blocker 仍是 `model_ranking_false_delay_blocker`；
6. final certificate / 20-task `OPTIMAL < 200s` 没有任何新增证明。

## 下一步

1. 不推进 v67 到 Stage 4 shadow / mutating admission。
2. 保留 v66 36 维 trace-feature dataset 作为后续基线。
3. 加一个 focused pair model-selection audit/gate：如果 `79fde/ac15` raw/admission ranking 不过，不允许用全局 metrics 推进。
4. 补特征而不是继续扫 threshold：
   - arc-option token sequence；
   - task-window / energy / load slack；
   - active basis overlap；
   - per-candidate branch/cut interaction。
5. 数据侧继续补：
   - `ac056` 同 context positive counterpart；
   - random-wave same-context hard-negative contrast，以防 v67 的 random-wave gain 只是阈值副作用。
6. 进入任何 Stage 4 前，仍需重新通过 kNN/OOD holdout、5/10 no-regression、20-task repeat ROI、certificate safety audit。

## Exactness Boundary

```text
v66_builder_runs_bpc_or_pricing = false
v67_training_runs_bpc_or_pricing = false
v68_ranking_audit_runs_bpc_or_pricing = false
v69_frontier_runs_bpc_or_pricing = false
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

最终 proof 仍必须由当前 branch/cut/dual 下 exact pricing exhaustive no-negative closure 产生；本轮只产生离线 Stage 3 训练和审计证据。
