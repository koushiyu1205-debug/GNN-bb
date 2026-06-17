# 2026-06-16 BPC_future GAT Stage 4 v53 Post-v51 Individual Follow-up 执行综合报告

## 读取范围

本轮复读了 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`，并对照了 Stage 3/4 的 v15、v32/v43、v45/v46、v50、v51/v52、v53 报告与本轮新生成的 reachability / A-B ROI / certificate audit。

目标边界不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## v53 执行摘要

本轮执行了 v53 guarded worker A/B runbook：

```text
execution_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/runbook_execution_summary.json

command_count = 20
executed_count = 20
failed_command_count = 0
elapsed_s = 1085.636987
all_checks_pass = true
production_ready = false
certificate_ready = false
official_bound_effect = false
```

5/10 no-regression sentinel 通过：

- 5-task sentinel：2 个实例均 `OPTIMAL`，约 `2.25s / 2.27s`；
- 10-task sentinel：2 个实例均 `OPTIMAL`，约 `5.02s / 3.57s`。

20-task individual follow-up 仍全部是 diagnostic / opt-in A/B；这些运行有 BPC / pricing 行为，但不产生 official bound，也不构成 certificate。

## v53 审计结果

### Reachability

```text
reachability_summary =
  BPC_future/results/gat_target_intervention_reachability_v53_post_v51_individual_followup_20260616/summary.json

record_count = 9
reachable_target_intervention_count = 9
reachability_class_counts = {'target_intervention_reachable': 9}
all_checks_pass = true
training_ready = false
```

9 个 target intervention 全部在 expected context 中触发，且首个执行事件均为 exact pricing `FOUND_NEGATIVE`。这说明 v53 样本可以进入 ROI label 构建候选池；但是否写成 `HIGH_PRIORITY` 仍由 trajectory ROI 判定。

### A/B ROI

```text
roi_summary =
  BPC_future/results/gat_target_priority_worker_ab_v53_post_v51_individual_followup_audit_20260616/summary.json

record_count = 9
roi_class_counts = {
  'negative_primal_roi': 4,
  'negative_retry_roi': 3,
  'positive_primal_roi': 1,
  'positive_retry_roi': 1
}
positive_primal_roi_count = 1
positive_trajectory_roi_count = 2
negative_primal_roi_count = 4
negative_trajectory_roi_count = 7
nonpositive_roi_count = 7
all_checks_pass = true
```

| context | target sequence | ROI class | primal improvement | columns delta | pricing / exact / RMP delta | label implication |
|---|---:|---|---:|---:|---:|---|
| `ac056820151e9ad7` | `20,16` | `negative_retry_roi` | `0.000000` | `-3` | `+2 / +1 / +1` | hard-negative / delay |
| `ac056820151e9ad7` | `15,5,16,7,3` | `negative_retry_roi` | `0.000000` | `+1` | `+2 / +1 / +1` | hard-negative / delay |
| `ac056820151e9ad7` | `15,20` | `negative_retry_roi` | `0.000000` | `+35` | `+3 / +1 / +2` | hard-negative / delay |
| `79fde658840fe2b8` | `1,15,17` | `negative_primal_roi` | `-26.085126` | `-1` | `0 / 0 / 0` | hard-negative |
| `79fde658840fe2b8` | `12,4,13,5` | `negative_primal_roi` | `-26.085126` | `-2` | `+1 / 0 / +1` | hard-negative |
| `79fde658840fe2b8` | `12,4,19,13` | `positive_primal_roi` | `+3.898953` | `+1` | `+3 / +1 / +2` | positive trajectory label candidate |
| `ac15bc4e7e3d6fff` | `16,17,15` | `negative_primal_roi` | `-2.609063` | `-20` | `0 / -1 / +1` | hard-negative |
| `ac15bc4e7e3d6fff` | `4,19,10,17` | `positive_retry_roi` | `0.000000` | `-28` | `0 / -1 / +1` | workload/retry positive, not primal positive |
| `ac15bc4e7e3d6fff` | `4,10,17,7` | `negative_primal_roi` | `-3.523602` | `-24` | `0 / -1 / +1` | hard-negative |

### Certificate safety

```text
certificate_summary =
  BPC_future/results/gat_target_mode_certificate_audit_v53_post_v51_individual_followup_20260616/summary.json

all_checks_pass = true
violation_count = 0
log_files = 23
events = 2686
finish_events = 22
optimal_finish_events = 4
global_certificate_pricing_events = 6
gat_events = 0
shadow_events = 0
admission_events = 0
```

本轮没有发现 GAT / admission / shadow 事件越过 exact-safe 边界。20-task A/B 仍为 `TIME_LIMIT` / `dual_bound=None` 诊断证据；最终 proof 仍未被 GAT 影响。

## 与旧版本的对比

| version | 当时结论 | v53 之后的新理解 |
|---|---|---|
| v15 | batch8 hard-negative 回流把 false-safe 压到 0，但 accepted batch 从 34 降到 13，CI 不够 | 硬负例方向正确，但单靠硬负例会让安全壳过窄；v53 提供了同 context 的更细粒度正负对照。 |
| v32/v43 | v15 missed high-ROI 不是阈值差一点：16 个 missed 全部 non-near-threshold，10/16 更靠近 negative 邻域 | 结构性 gap 仍成立；v53 说明要补的是 action consequence 监督，而不是再放宽 threshold。 |
| v44/v45/v46 | delay-safe shell 存在；false-delay contrast smoke 可把 false-delay 压到 0，但 full coverage 后复发 | loss 能局部压 false-delay，但无法让高覆盖区域同时安全。需要 context-local target 对照和更强候选表示。 |
| v50 | 5 个 false-positive context-batch 全无正 primal ROI，`79fde` / `ac15` 被视为 hard-negative context | v53 修正了这个粗标签：`79fde` 整体为负不代表所有子目标都负，`12,4,19,13` 是正 primal 子目标。 |
| v51/v52 | v50 回流只新增 4 个 non-improving batch；出现 safe epoch，但没有 epoch 同时满足 coverage 和 false-delay safe | checkpoint selection 不是主 blocker。v53 证明下一步应增加 same-context individual attribution rows，而不是继续找更好的 epoch。 |

## 新理解

### 1. Context-level hard-negative 标签过粗

v50 把 `79fde658840fe2b8` 判为 negative primal context 是对 batch 级别成立的，但 v53 拆 individual target 后发现：

```text
79fde mb1 / mb2 = negative_primal_roi
79fde mb3 12,4,19,13 = positive_primal_roi, primal improvement +3.898953
```

这说明 training label 不应只停在 context-batch 粒度。否则模型会把同 context 中真实有益的子目标一起压进 delay。

### 2. `ac056820151e9ad7` 可以从 high-priority source 降级

`ac056` 覆盖 v41 最大 false-positive cluster，但 v53 三个 individual target 全是 `negative_retry_roi`，没有 primal improvement，且 pricing / exact / RMP retry 都上升。它应该作为 context-local retry hard-negative，不应继续当 high-priority candidate source。

### 3. `ac15bc4e7e3d6fff` 暴露 workload signal 与 trajectory ROI 冲突

`ac15` 中两个 target 降低 columns，且一个是 `positive_retry_roi`，但另外两个是 negative primal。尤其 `columns_delta < 0` 仍可能伴随 primal 变差，继续支持旧结论：columns reduction、true-RC negative、exact-id hit 都不是 HIGH_PRIORITY 充分条件。

### 4. v51 失败不是 checkpoint 选择失败

v52 显示 `coverage_and_false_delay_safe_epoch_count = 0`。v53 又展示了同一 false-positive context 内部的正负 action consequence 差异。因此问题在训练分布和模型表示，不在“选错 epoch”。

### 5. Stage 5 目标仍未开始满足

本轮只证明 5/10 sentinel 无回归，以及 20-task diagnostic A/B 可安全执行。它没有证明 20-task `OPTIMAL within 200s`、official dual bound available、final exact pricing closure 或 30/50/100 加速路径。

## 当前问题

1. candidate head 仍缺少 context-local ranking 能力：同一 context 里 true-RC negative 子目标可以一个正 ROI、多个负 ROI。
2. context-batch label 会误伤 positive individual target，需要把 v53 行转成 Stage 3 individual / batch-impact rows。
3. workload 指标与 trajectory ROI 冲突仍明显，尤其 columns reduction 不能当正标签。
4. random-wave high-ROI blind spot 还没有被 v53 修复；v53 主要覆盖 sector-wave|20 false-positive context。
5. 当前所有 20-task A/B 仍无 certificate，Stage 4 mutating admission 和 Stage 5 加速目标都不能启动。

## 下一步

1. 把 v53 的 9 条 reachable rows 转成下一版 Stage 3 数据：
   - `79fde / 12,4,19,13` 标为 reachable positive primal ROI；
   - `ac15 / 4,19,10,17` 标为 reachable positive retry/workload ROI，但不能等同 primal positive；
   - 其余 7 条标为 reachable hard-negative / delay。
2. 重建 v54 dataset，保留 v51 的 v39+v50 基础，并加入 v53 individual rows。
3. 训练 v55，检查是否出现：
   - `coverage_and_false_delay_safe_epoch_count > 0`；
   - context-local ranking 中 positive individual target 排在 hard-negative 前；
   - random-wave holdout 不再 0 accepted。
4. 不放宽 precision / ROI / false-safe / coverage / CI gate；过不了 gate 的 checkpoint 仍只能 diagnostic。
5. Stage 4 只允许继续 shadow / opt-in A/B；任何默认启用前必须重新通过 5/10 no-regression、20-task ROI repeat、certificate safety audit。

## Exactness Boundary

```text
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

GAT 可以让前面的 column generation 更聪明，但最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
