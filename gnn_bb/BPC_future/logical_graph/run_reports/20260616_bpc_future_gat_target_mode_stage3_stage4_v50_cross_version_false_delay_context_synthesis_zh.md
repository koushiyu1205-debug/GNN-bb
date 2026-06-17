# 2026-06-16 BPC_future GAT Stage 3/4 v50 Cross-version False-delay Context 综合报告

## 读取范围

本轮复读并对比：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 3 v15 / v36 / v41 / v43 / v44 / v45 / v46
- Stage 4 v14 / v15 / v38 / v40
- 最新 Stage 3/4 v49 runbook 与 v50 context-batch pilot / ROI audit

边界保持不变：GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列仍必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 full exact pricing no-negative closure。

## Cross-version 证据链

| version | 主要结论 | 对当前判断的意义 |
|---|---|---|
| v15 | A/B ROI 回流后 false-safe 降到 0，但 accepted batch 从 34 降到 13，CI 不够 | 说明硬负例有效，但安全覆盖会塌缩 |
| v23 | positive boost 提高 high-ROI 覆盖，但 false_high_priority_on_delay 到 0.425532 | 说明单纯追 ROI 会放大 delay false positive |
| v24/v28 | delay suppression / risk-adjusted scoring 把 false-delay 压到 0.008475，但 coverage 仍不够 | 说明安全和覆盖存在 Pareto 张力 |
| v36 | repair plan 将问题收敛到少数 context，尤其 `b6d808`、`79fde`、`ac15` | 说明不应继续全局扫阈值，应做 context-local contrast |
| v38/v40 | `b6d808` first tranche 4 个 target 都没有正 trajectory ROI，4/4 即时 objective improvement 仍非正最终 ROI | 说明即时 RMP objective movement 会系统性误导标签 |
| v39 | hard-negative 回流后 accepted=46、ROI CI-low=3.321518，但 false-delay=0.448980 | 说明 hard-negative rows 还没让当前结构学会 delay trajectory consequence |
| v41 | 44 个 false high-priority 全集中在 `sector-wave|20` 的 5 个 context | blocker 已经不是全局噪声，而是 context-local ranking 失败 |
| v44 | delay-safe shell 存在，但最多只接受 2 个 batch | 不是没有安全阈值，是安全壳太窄 |
| v45/v46 | false-delay contrast smoke 可压 false-delay，但 full coverage 后 false-delay 复发 | loss 局部修补没有解决结构性分不开 |
| v50 | 5 个 false-positive context-batch A/B 全部无正 primal ROI，其中 2 个 negative primal ROI | 最新真实 A/B 证实这些 context 应作为 hard-negative / delay supervision，而不是 HIGH_PRIORITY 候选 |

## v50 Pilot 结果

本轮实际执行 context-batch pilot：

```text
execution_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v50_v39_context_batch_pilot_20260616/execution_summary.json

executed_count = 10
failed_command_count = 0
elapsed_s = 588.414780
runs_bpc_or_pricing = true
all_checks_pass = true
production_ready = false
certificate_ready = false
official_bound_effect = false
```

ROI audit：

```text
audit_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v50_v39_context_batch_pilot_20260616/roi_audit/summary.json

record_count = 5
positive_primal_roi_count = 0
positive_trajectory_roi_count = 0
nonpositive_roi_count = 5
negative_primal_roi_count = 2
negative_trajectory_roi_count = 3
roi_class_counts = {
  'negative_primal_roi': 2,
  'negative_retry_roi': 1,
  'no_observed_roi': 2
}
all_checks_pass = false
```

`all_checks_pass=false` 是 ROI gate 失败，不是执行失败。5 个 context 的 worker / baseline 都是 `TIME_LIMIT`，均无 official dual bound。

| context | v41 false-positive count | v50 ROI class | primal improvement | columns delta | 判断 |
|---|---:|---|---:|---:|---|
| `ac056820151e9ad7` | 33 | `negative_retry_roi` | 0.000000 | +2 | 最大 false-positive context；不应作为 positive source |
| `b6d808ebac2a6dd8` | 4 | `no_observed_roi` | 0.000000 | -17 | 只有 workload 弱信号，无 primal / proof ROI |
| `79fde658840fe2b8` | 4 | `negative_primal_roi` | -26.085126 | -1 | 明确 hard-negative |
| `ac15bc4e7e3d6fff` | 2 | `negative_primal_roi` | -1.081723 | -35 | 明确 hard-negative，虽然 columns 降低 |
| `7b430465c7ae76b3` | 1 | `no_observed_roi` | 0.000000 | 0 | 中性/无可观测 ROI |

## 新理解

### 1. false-delay blocker 已经从“模型全局不稳”缩小到“少数 context 内排序错误”

v41 的 44 个 false high-priority 全部来自 `sector-wave|20` 的 5 个 context。v50 直接跑这 5 个 context-batch 后没有发现正 primal ROI，反而发现 2 个明确 negative primal ROI。这说明当前应优先把这些 context 当成 context-local hard-negative training/evaluation set，而不是继续做全局 threshold sweep。

### 2. `true-RC negative`、`exact-id hit`、`columns reduction` 都不是 HIGH_PRIORITY 充分条件

v14 证明 exact safe-id hit batch8 仍可能导致 negative retry ROI；v38/v40 证明即时 RMP objective improvement 仍可能最终非正 ROI；v50 进一步证明 columns 降低也可能伴随 primal 变差，例如 `ac15` columns -35 但 primal improvement -1.081723。

因此 admission label 必须继续绑定 A/B trajectory ROI、tail retry、pricing workload、RMP solves 和 final proof tail，而不是绑定 reduced cost 命中或短视 objective movement。

### 3. 现在的问题不是“阈值差一点”

v43 已经显示 v15 missed high-ROI 的 `near_threshold_miss_count=0`，v44/v45 显示 delay-safe shell 存在但 coverage 极窄。v50 的真实 A/B 又确认高 false-positive context 不是可直接抢救的正源。因此下一步如果继续只调 candidate threshold / delay threshold，大概率只会在“覆盖低但安全”和“覆盖高但 false-delay 爆”之间摆动。

### 4. `b6d808` 需要降级为 workload-only / ambiguous，而不是 high-ROI anchor

v36 把 `b6d808` 标为最高 opportunity context；v38/v40 的 4 个 individual target 没有正 trajectory ROI；v50 context-batch 也只有 columns -17，无 primal improvement，并且 pricing/RMP 没有明显下降。因此它最多是 workload-only / ambiguous evidence，不应再作为 Stage 4 HIGH_PRIORITY anchor。

### 5. `79fde` 与 `ac15` 是优先 hard-negative supervision

这两个 context 在 v50 中出现 negative primal ROI，且它们之前已经出现在 v36/v41 的 repair / false-positive context 中。它们适合用于训练 candidate head / delay-risk head 的 same-context hard-negative contrast，目标是在同一 context 内把这些 target 排到真正 high-ROI safe candidate 之后。

## 当前问题

1. candidate head 缺少 context-local ranking 能力，尤其是 `sector-wave|20`。
2. delay-risk head 能形成安全壳，但覆盖太窄，无法支撑 Stage 4 candidate。
3. 当前模型仍不能表达“true-RC negative 但加入后拖累 RMP trajectory / final proof tail”的动作后果。
4. 现有 audit summary 对 runbook candidate metadata 的保留还不够，后续应让 ROI audit 直接携带 context priority / false-delay fields，减少人工对齐。
5. 所有 20-task worker A/B 仍是 `TIME_LIMIT` 且 `dual_bound=None`，没有任何 certificate 或 official bound 证据。

## 下一步

1. 把 v50 中 `79fde658840fe2b8`、`ac15bc4e7e3d6fff` 标成 high-confidence context-local hard-negative supervision；`ac056820151e9ad7` 标成 retry hard-negative；`b6d808ebac2a6dd8` 标成 workload-only / ambiguous；`7b430465c7ae76b3` 标成 neutral。
2. 先做 reachability / causal match 审计，确认 worker target materialization 与 expected context 真正命中，再把 v50 写入 Stage 3 dataset。
3. 不跑全量 individual attribution；如果要拆，只优先拆 `b6d808` 和 `ac056`，因为前者有 workload 弱信号，后者覆盖 33/44 个 false-positive。
4. 训练目标继续保持 `precision-constrained ROI maximization`，并新增/强化 context-local false-delay contrast：同一 context 内 high-ROI safe candidate 必须排在 hard-negative target 前。
5. 下一版 Stage 3 gate 不放宽 precision / ROI / false-safe / coverage / CI；过不了 gate 的 checkpoint 只能 diagnostic，不能进入 Stage 4 mutating admission。

## Exactness Boundary

```text
runs_bpc_or_pricing = true for v50 pilot only
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 可以让前面的 column generation 更聪明，但最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中不存在任何负 reduced-cost journey。
