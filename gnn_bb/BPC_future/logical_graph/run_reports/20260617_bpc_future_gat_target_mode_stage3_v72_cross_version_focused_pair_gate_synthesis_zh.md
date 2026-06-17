# 2026-06-17 BPC_future GAT Stage 3 v72 Cross-version Focused-pair Gate 综合报告

## 结论

本轮在 v70 的基础上继续回看 v15/v32/v36/v39/v41/v44/v45/v60/v62-v69，并把 v68 暴露的同 context positive-vs-hard-negative 排序失败固化为 v71 focused pair gate。

新理解不是“最近一次调参失败”，而是问题已经分层：

1. v15/v32/v43 证明 missed high-ROI 不是阈值差一点，而是 candidate-head score gap 和 embedding structural gap 同时存在；
2. v39/v41 证明如果 candidate threshold 退化到 0，delay gate 会成为唯一过滤器，false-delay hard negative 会集中爆发；
3. v44/v45 证明 delay-safe shell 可以存在，甚至 false-delay 可以压到 0，但 coverage 会坍缩，不能进入 Stage 4；
4. v60/v68/v71 证明即使补了 v64/v66 trace scalar，focused 同 context 正负 target 仍没有稳定排对；
5. v67/v69 证明 trace scalar 真实改善了宏观 coverage 和 random-wave capture，但 false-delay frontier 仍无可行阈值。

因此当前主 blocker 不是单纯调 threshold、delay penalty 或 ROI gate，而是 candidate action-consequence 表示不足：模型能学到一部分 family / trace aggregate 信号，但还不能在同一个 RMP context 内把真正改善 trajectory 的 target 排在 tail-delay hard-negative 前面。

## v71 新增审计

v71 对 v66 trace-feature dataset 和 v67 checkpoint 重新运行 individual context ranking，并新增 focused pair gate：

```text
output_dir = BPC_future/results/gat_batch_impact_focused_pair_gate_v71_v67_trace_features_20260617
report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v71_v67_focused_pair_gate_zh.md
focused_row_count = 9
context_count = 3
contexts_with_positive_and_negative = 2
pair_count = 4
raw_pair_pass_rate = 0.25
admission_pair_pass_rate = 0.25
delay_risk_pair_pass_rate = 0.25
strict_pair_pass_rate = 0.25
focused_pair_gate_pass = false
stage3_focused_pair_gate_ready = false
blocking_primary = candidate_head_context_ranking_failure
```

拒绝原因：

```text
raw_pair_pass_rate_below_threshold
admission_pair_pass_rate_below_threshold
delay_risk_pair_pass_rate_below_threshold
strict_pair_pass_rate_below_threshold
```

这把 v68/v70 的人工结论变成了可复跑的机器字段：后续 checkpoint 即使 global deployment gate 指标看起来改善，也必须先过 focused same-context positive-negative pair gate，才值得进入 Stage 4 shadow / mutating admission。

## 跨版本对比

| version | 当时现象 | 现在的解释 |
| --- | --- | --- |
| v15 / v32 / v43 | 16 个 missed high-ROI 没有 near-threshold miss，candidate margin 多为 deep/moderate gap；embedding 里 high-ROI 与 low-ROI/bad 混杂。 | 早期不是阈值问题，而是表示和 candidate head 同时缺口。 |
| v36 | ROI-neighbor shell 延迟了 3 个 high-ROI，建议补 same-context contrast。 | 这个方向仍正确；后续 v60/v68/v71 正是同 context pair 反例。 |
| v39 / v41 | false_high_priority_on_delay = 0.4489795918367347，candidate_threshold=0 导致 candidate head 近似失效。 | 不能让 delay gate 独自承担安全性；candidate head 必须成为真实过滤器。 |
| v44 / v45 | delay-safe shell 存在，v45 smoke 可把 false-delay 压到 0，但 accepted coverage 只有 3/123。 | 只追求 false-delay 为 0 会变成过窄安全壳层，解决不了加速目标。 |
| v60 | focused pair raw pass 1/4，primary=candidate_head_context_ranking_failure。 | hard-negative 不是全局噪声，而是同 context action-consequence 排序失败。 |
| v62 / v63 / v64 | 当前 14 维输入欠指定；trace/timing/resource payload 可取；schema 扩到 36 维。 | trace scalar 是必要修复，但只能提供 aggregate，不足以表达路径序列和资源 slack。 |
| v67 | random-wave high-ROI capture 从 0 提到 0.5，HP/safe precision CI 明显改善。 | trace scalar 有效，不应回滚。 |
| v68 / v71 | focused pair 四个 pass-rate 都只有 0.25。 | 宏观 coverage 改善掩盖了局部排序失败，必须成为模型选择硬门槛。 |
| v69 | feasible_threshold_count=0，best false_high_priority_on_delay 仍约 0.45。 | 失败不是 checkpoint selector 偶然选错，而是当前 score/risk frontier 无可行阈值。 |

## 当前问题

### 1. Macro ROI 和 focused ranking 已经分离

v67 说明模型能找到更多 high-ROI 区域，尤其 random-wave 不再完全盲；但 v71 说明它在关键 same-context target 里仍把 hard-negative 排在 positive 前面。

这意味着训练阶段不能只看 accepted ROI、high-ROI capture、precision CI。它还必须硬性报告并约束：

- focused same-context raw pair pass；
- focused same-context risk-adjusted admission pair pass；
- focused same-context delay-risk ordering pass；
- strict pair pass。

### 2. Trace scalar 是必要但不充分

v64/v66 的 22 个 trace scalar 保留价值明确，因为 v67 的 random-wave 和 precision CI 确实改善。

但 v71 说明 scalar aggregate 还不够。下一类特征应优先补：

- selected arc-option token sequence / path option embedding；
- task time-window slack、resource slack、survival-energy slack；
- active basis / dual movement overlap；
- per-candidate branch/cut coefficient interaction。

### 3. 不能推进 v67 到 Stage 4

v67 同时被三类证据挡住：

- v67 training gate：false_high_priority_on_delay 和 false_safe_rate_union 超门槛；
- v69 frontier：无可行 threshold；
- v71 focused gate：same-context positive-vs-hard-negative pair 未排对。

因此 v67 只能作为 trace-feature baseline，不是 Stage 4 candidate。

## 下一步

1. 保留 v66 36 维 trace-feature dataset 作为新 baseline，不回滚 trace scalar。
2. 将 v71 focused pair gate 纳入后续 checkpoint 选择/审计，不满足 `strict_pair_pass_rate=1.0` 的 checkpoint 不推进 Stage 4。
3. 下一轮训练不优先扫 threshold，而是补 candidate action-consequence 表示：path token sequence、slack、active basis overlap、branch/cut interaction。
4. 对 v15/v36/v60/v71 的 same-context hard-negative contexts 建一个固定 regression tranche，避免新模型只在宏观 family coverage 上变好。
5. Stage 4/Stage 5 仍保持 exact-safe 边界：GAT 只能排序和有限延迟，进入 RMP 的列必须 true-RC verified，最终 certificate 只能由当前 branch/cut/dual 下 full exact pricing no-negative closure 给出。

## Verification

```text
py_compile audit_gat_batch_impact_individual_context_ranking.py = pass
unittest BPC_future.tests.test_gat_batch_impact_individual_context_ranking = 5 tests OK
v71 focused pair gate audit = pass
runs_bpc_or_pricing = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
stage4_candidate_ready = false
```

