# 2026-06-17 BPC_future GAT Stage 3 v94 Focused Head Loss 综合报告

## 读取范围

本轮复读了：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 / Stage 2 基础报告
- Stage 3 v36 / v41 / v44 / v45 / v87 / v89 / v91
- Stage 4 v53
- Stage 5 20/30/50/100 目标

目标边界仍是：

```text
Learning-guided discovery, exact-certified closure
```

本轮只改离线训练脚本和训练单测，不改 solver、pricing、RMP、branch/cut、final judge 或 benchmark 默认配置。GAT 仍不能产生 official bound 或 certificate。

## 代码改动

`BPC_future/scripts/train_gat_batch_impact.py` 在 v91 的 focused pair plumbing 基础上新增分头 focused loss，全部默认关闭：

```text
--focused-pair-candidate-loss-multiplier
--focused-pair-admission-loss-multiplier
--focused-pair-delay-risk-loss-multiplier
--focused-pair-batch-loss-multiplier
```

新增 helper：

```text
_focused_pair_head_loss_enabled()
_focused_pair_head_loss()
```

语义：

- candidate loss：只训练 focused positive 的 labeled HIGH_PRIORITY logit 高于 focused hard-negative 的 labeled delay logit；
- admission loss：用实际 `candidate_admission_score_mode` 训练 focused positive admission score 高于 hard-negative；
- delay-risk loss：只训练 hard-negative delay-risk logit 高于 positive delay-risk logit；
- batch loss：只训练 positive batch ROI logit 高于 hard-negative batch ROI logit。

旧的 `--focused-pair-loss-multiplier` 保留，语义仍是“对 focused tranche 额外复用完整 `_pairwise_ranking_loss`”。后续不建议继续放大旧整体 multiplier。

`BPC_future/tests/test_gat_batch_impact_training.py` 新增/更新：

- `loss_options` 写出四个新分头 multiplier；
- fake-model 单测覆盖 candidate-only focused head loss；
- fake-model 单测覆盖 delay-risk-only focused head loss；
- checkpoint / summary contract 断言新字段存在。

## Smoke 对比

统一配置：

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
seed = 13
epochs = 1
device = cpu
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_gate_row_index_min = 383
```

| run | focused setting | accepted | accepted ROI | ROI CI-low | safe CI-low | focused raw/admission | focused delay-risk | focused strict | gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| v88 | none | 4 | 1.0204 | 0.7272 | 0.5101 | 0.75 / 0.75 | 0.50 | 0.25 | failed |
| v90 | old full focused pair = 1.0 | 8 | 0.8994 | 0.6643 | 0.6756 | 0.50 / 0.50 | 0.25 | 0.00 | failed |
| v92 | candidate-only = 1.0 | 8 | 0.8994 | 0.6643 | 0.6756 | 0.50 / 0.50 | 0.25 | 0.00 | failed |
| v93 | delay-risk-only = 1.0 | 8 | 0.8994 | 0.6643 | 0.6756 | 0.75 / 0.75 | 0.25 | 0.25 | failed |

产物：

```text
v92 metrics =
  BPC_future/results/gat_batch_impact_training_v92_seed13_focused_candidate_loss_v75_delay_risk_pairwise_20260617/metrics.json
v92 report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v92_seed13_focused_candidate_loss_training_smoke_zh.md

v93 metrics =
  BPC_future/results/gat_batch_impact_training_v93_seed13_focused_delay_risk_loss_v75_delay_risk_pairwise_20260617/metrics.json
v93 report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v93_seed13_focused_delay_risk_loss_training_smoke_zh.md
```

## 新理解

1. v90 的退化主要来自 candidate-head focused pressure。
   v92 candidate-only 基本复现 v90：accepted 从 v88 的 4 增到 8，但 accepted ROI 降到 0.8994，focused raw/admission 从 0.75/0.75 降到 0.50/0.50，strict 变 0。

2. delay-risk-only 不是当前 blocker 的单点修复。
   v93 保住了 raw/admission 0.75/0.75，但 delay-risk 仍只有 0.25，strict 仍只有 0.25，没有通过 focused gate。

3. 继续扫 focused multiplier 大概率不是主方向。
   v36、v41、v44、v45 已经说明：问题不是 threshold 差一点，而是 candidate head 可用性、delay-safe 壳层 coverage、context-local action consequence 表示不足。v92/v93 进一步把这个结论从 gate 审计推进到训练 loss 层。

4. context-level 标签仍过粗。
   v53 证明 `79fde658840fe2b8` 这类 context 内部存在正 ROI individual target 和多个负 ROI target。训练不能只把整个 context-batch 标成 positive 或 hard-negative。

5. exact-safe hit / true-RC negative 仍不是 admission 正例。
   v14/v15/v53 共同说明：true-RC verified negative、exact safe-id hit、columns reduction 都可能增加 RMP/pricing/exact workload 或恶化 primal trajectory。Stage 3 标签必须继续用 trajectory ROI / tail-risk consequence。

## 当前问题

- focused candidate loss 会压坏 focused raw/admission ranking，不能作为默认训练项。
- focused delay-risk loss 单独不能修复 strict gate。
- same-context positive/negative pair 太少，且 margin 很小，当前 1 epoch 下 pair margin 只在 `1e-4 ~ 1e-3` 级别摆动。
- random-wave / greedy-anchor 的 coverage 问题仍未被本轮修复。
- Stage 4/5 仍未满足：没有 Stage 4 candidate、没有 20-task `OPTIMAL < 200s`、没有 official dual bound/certificate 改善。

## 下一步

1. 保留分头 focused loss 代码，但默认关闭；不要把 v92/v93 当 Stage 4 candidate。
2. 不继续放大 `focused_pair_candidate_loss_multiplier`；它已经复现旧退化。
3. 若继续训练 loss 方向，应优先试更窄的 admission-only 小权重或 margin schedule，但必须先加 same-context individual attribution rows。
4. 更优先的方向是 Stage 2/3 数据闭环：
   - 把 v53 individual follow-up rows 系统回流；
   - 区分 positive primal ROI、positive retry/workload ROI、hard-negative；
   - 对 `79fde` / `ac15` 这类 context 做 action-level contrast。
5. 不放宽 precision / ROI / safety / coverage / CI gate；final certificate 仍只来自 exact pricing full closure。

## Verification

```text
py_compile train_gat_batch_impact.py + test_gat_batch_impact_training.py = pass
unittest BPC_future.tests.test_gat_batch_impact_training = 29 tests OK
v92 focused candidate-only smoke = pass, gate failed as diagnostic
v93 focused delay-risk-only smoke = pass, gate failed as diagnostic
runs_bpc_or_pricing = false
production_ready = false
stage4_candidate_ready = false
stage5_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Exactness Boundary

本轮不改变 exact proof path。GAT 可以让前面的 column generation 更聪明，但最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
