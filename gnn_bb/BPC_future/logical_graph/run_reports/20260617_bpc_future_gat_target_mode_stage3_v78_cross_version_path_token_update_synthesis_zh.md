# 2026-06-17 BPC_future GAT Stage 3 v78 Cross-version Path-token Update 综合报告

## 结论

这轮把最近 v72/v74 的判断和更早 v15/v23/v24/v28/v39/v45/v55/v67 对齐后，新的理解是：

1. 早期 blocker 不是阈值差一点。v15/v43 已经证明 missed high-ROI 是 candidate head 分数缺口加 embedding 结构混杂；
2. v23/v24/v28/v39/v45 证明 high-ROI coverage 和 false-delay suppression 存在稳定 Pareto 张力，单纯调 loss / threshold 会在两端摆动；
3. v67/v70 证明 trace/timing/resource scalar 有效，能修复一部分 random-wave / sector-wave coverage，但同 context positive-vs-hard-negative ranking 仍失败；
4. v75/v76/v77 的新信号是：path-token/slack schema 至少在 focused tranche 上把 raw/admission candidate ranking 从 `0.25` 提到 `1.0`，但 delay-risk head 方向仍错，`delay_risk_pair_pass_rate = 0.0`，所以还不能进 Stage 4。

因此下一步不该回到泛化 threshold sweep；应把训练目标拆硬：candidate head 继续保留 path-token/slack 表示，delay-risk head 要单独用 context-local positive/hard-negative pair 校准，并且 focused strict pair gate 继续作为进入 Stage 4 前的硬门槛。

## 本轮新增产物

### v75 path-token/slack dataset

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_batch_impact_dataset_v75_v66_path_tokens_slack_zh.md
sample_count = 392
candidate_count = 4703
batch_label_counts = {'non_improving': 116, 'roi_positive': 276}
candidate_label_counts = {'delay_queue': 407, 'high_priority': 4296}
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 120}
task_count_counts = {'5': 2, '10': 8, '20': 209, '30': 76, '50': 96, '100': 1}
candidate_feature_dim = 40
path_token_bucket_count = 4096
path_pair_bucket_count = 4096
ranking_ready = true
training_ready = true
```

v75 相比 v66 不改样本范围和标签分布，只增加 candidate action-consequence 表示：

- ordered arc-option token ids；
- arc-option pair ids；
- path type ids：`low_time` / `low_energy` / `low_risk`；
- trace occupancy bucket count；
- task-window slack：late min/mean、early min。

### v76 path-token smoke training

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v76_v75_path_token_smoke_20260617/gat_batch_impact.pt
metrics = BPC_future/results/gat_batch_impact_training_v76_v75_path_token_smoke_20260617/metrics.json
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v76_v75_path_token_training_smoke_zh.md
best_epoch = 1
checkpoint_gate_pass = false
stage4_candidate_ready = false
threshold_search.feasible_threshold_count = 0
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
```

validation selected metrics：

```text
accepted_batch_count = 18
accepted_batch_roi = 1.5125786579317517
accepted_batch_roi_ci_low = 0.11887767695280371
safe_precision = 1.0
safe_precision_ci_low = 0.8241154494176252
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9950098825524627
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
```

这只是 smoke，不是 candidate。validation false-delay 点估计为 0 不能覆盖两个硬事实：

- ROI CI-low 太低，safe precision CI-low 不过 Stage 3 hard gate；
- train 侧仍有 `false_high_priority_on_delay = 0.10150375939849623`，说明 delay-risk 安全性未稳定。

### v77 focused pair gate

```text
output = BPC_future/results/gat_batch_impact_focused_pair_gate_v77_v76_path_token_smoke_20260617
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v77_v76_path_token_focused_pair_gate_zh.md
focused_row_count = 9
context_count = 3
contexts_with_positive_and_negative = 2
pair_count = 4
raw_pair_pass_rate = 1.0
admission_pair_pass_rate = 1.0
delay_risk_pair_pass_rate = 0.0
strict_pair_pass_rate = 0.0
primary = delay_risk_head_context_ranking_failure
focused_pair_gate_pass = false
```

这是本轮最重要的新信号。对照 v71：

| audit | raw pair pass | admission pair pass | delay-risk pair pass | strict pair pass | primary |
|---|---:|---:|---:|---:|---|
| v71 / v67 trace scalar | 0.25 | 0.25 | 0.25 | 0.25 | candidate_head_context_ranking_failure |
| v77 / v76 path-token smoke | 1.0 | 1.0 | 0.0 | 0.0 | delay_risk_head_context_ranking_failure |

这说明 path-token/slack 表示很可能触碰到了 candidate head 的结构性缺口；但 delay-risk head 仍把 positive target 的 risk 预测得不低于 hard-negative。换句话说，问题从“positive 没排到 hard-negative 前面”变成“positive 虽然排前了，但 delay-risk head 不承认它更安全”。

## 跨版本对照

| version | 现象 | 现在的解释 |
|---|---|---|
| v15 / v43 | missed high-ROI = 16，near-threshold miss = 0，deep/moderate candidate score gap 明显。 | 不是调低 threshold 能修；candidate head 与 embedding 结构不足。 |
| v23 | coverage 上去，false-delay 到 0.42+。 | high-ROI boost 会把 hard-negative 一起放进来。 |
| v24 / v28 | false-delay 压到约 0.008，但 accepted 数和 CI 不够。 | delay suppression 能形成安全壳，但壳太窄。 |
| v39 / v41 | false-delay 约 0.449，集中在 `sector-wave|20`，candidate threshold 退化到 0。 | candidate head 失效后，delay gate 独自过滤会失败。 |
| v44 / v45 | delay-safe shell 存在，但 accepted 最大只有 1-2；full training coverage 回来后 false-delay 复发。 | loss/threshold 修补不能解决结构性分不开。 |
| v55 / v60 | individual followup 后 focused raw/admission/delay-risk pass 仍低。 | 同 context action-consequence ranking 必须成为硬 gate。 |
| v67 / v70 | trace scalar 大幅改善 coverage、random-wave capture、precision CI，但 false-delay frontier 无可行阈值。 | trace scalar 有效但只解决 aggregate coverage，不够表达路径动作后果。 |
| v75 / v76 / v77 | path-token/slack smoke 让 focused raw/admission pair pass 到 1.0，但 delay-risk pass 为 0.0。 | path-token 方向值得保留；下一步 blocker 是 delay-risk head 的 context-local 校准。 |

## 新问题

### 1. Delay-risk head 现在是独立 blocker

v77 的 4 个 focused pair 中，positive 的 raw/admission score 都高于 hard-negative，但 positive 的 delay-risk score 也更高：

```text
mean_raw_margin = 0.004561625421047211
mean_admission_margin = 0.004561625421047211
mean_delay_risk_margin = -0.003081671893596649
```

这说明不能只把 delay-risk 当 candidate score 的辅助 penalty。它需要自己的 context-local pairwise supervision：

- positive high-ROI safe candidate 的 delay-risk 必须低于同 context hard-negative；
- bad-mode / tail-delay negative 的 delay-risk 必须高于同 context positive；
- strict pair gate 中 raw/admission/delay-risk 三个方向都要过。

### 2. v76 只是 smoke，不能过度解读

v76 只有 1 epoch 和小 hidden dim，且训练目标不是 v67 的完整 risk-adjusted 配置。它只能证明 schema/model/training/audit 链路可运行，并给出方向性信号；不能证明 full path-token checkpoint 会过 Stage 3。

### 3. Batch head 仍不可靠

v77 pair rows 中 batch score 有 3/4 未把 positive batch 排在 negative 前面。虽然 admission scheduling 主要看 candidate/admission/delay-risk，但 batch-level ROI head 仍应作为后续辅助约束，否则 selected batch ROI CI 可能继续不稳。

## 下一步

1. 保留 v75 path-token/slack schema，不回滚到纯 trace scalar；
2. 跑正式 v79/v75 full training，但训练配置要恢复 hard risk/delay 约束，而不是只用 v76 smoke 默认；
3. 增加 delay-risk context-local pairwise loss：要求 positive target risk < hard-negative risk；
4. checkpoint selection 加硬：`raw_pair_pass_rate = 1.0`、`admission_pair_pass_rate = 1.0`、`delay_risk_pair_pass_rate = 1.0`、`strict_pair_pass_rate = 1.0`，否则不进 Stage 4；
5. 对 v77 这 4 个 pair 生成固定 regression tranche，防止后续 full training 又回到 v71 形态；
6. 等 focused gate 过后，再跑 threshold frontier、kNN/OOD、5/10 no-regression、20-task repeated ROI 和 Stage 4 shadow / opt-in A/B。

## Exactness Boundary

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
stage5_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT / CBF / kNN / OOD 仍只能做 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## Verification

```text
py_compile build_gat_batch_impact_dataset.py / batch_impact_model.py / train_gat_batch_impact.py = pass
unittest test_gat_batch_impact_model + dataset + training = 35 tests OK
v75 dataset build = pass
v76 path-token smoke training = pass
v77 focused pair gate audit = pass, gate failed as diagnostic
```
