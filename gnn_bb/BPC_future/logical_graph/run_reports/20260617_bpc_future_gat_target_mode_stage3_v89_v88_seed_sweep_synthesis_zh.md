# 2026-06-17 BPC_future GAT Stage 3 v89 v88 受控 Seed Sweep 综合报告

## 读取范围

本轮按目标模式计划复读了 Stage 1、Stage 2、Stage 3 v87、Stage 4 v53，以及 Stage 5 20/30/50/100 目标。边界保持：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 目的

v87 暴露一个关键问题：旧 v79 checkpoint 经外部 v80 focused audit 有较好局部排序表现，但新训练内 focused gate 复跑 v85 没有重现。为排除单次 seed 偶然，本轮固定：

```text
dataset = BPC_future/data/gat_batch_impact/v75_v66_path_tokens_slack_20260617
epochs = 1
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_gate_row_index_min = 383
min focused raw/admission/delay-risk/strict pass rate = 1.0
```

只改变 seed，串行跑：

```text
seed = 13
seed = 41
seed = 73
```

本轮不运行 BPC / pricing / RMP / worker / certificate。

## 结果表

| run | seed | accepted | accepted ROI | ROI CI-low | HP precision | HP CI-low | safe CI-low | false-delay | focused raw/admission | focused delay-risk | focused strict | primary |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| v80 old external audit on v79 | unknown | n/a | n/a | n/a | n/a | n/a | n/a | n/a | `1.0 / 1.0` | `0.5` | `0.5` | delay_risk_head_context_ranking_failure |
| v85 old seed41-like rerun | unknown | 15 | 0.7002 | 0.4004 | 1.0000 | 0.9957 | 0.7961 | 0.0000 | `0.0 / 0.0` | `0.25` | `0.0` | candidate_head_context_ranking_failure |
| v88 seed13 | 13 | 4 | 1.0204 | 0.7272 | 1.0000 | 0.9789 | 0.5101 | 0.0000 | `0.75 / 0.75` | `0.5` | `0.25` | candidate_head_context_ranking_failure |
| v88 seed41 | 41 | 16 | 2.3638 | -0.9154 | 1.0000 | 0.9953 | 0.8064 | 0.0000 | `0.0 / 0.0` | `0.5` | `0.0` | candidate_head_context_ranking_failure |
| v88 seed73 | 73 | 12 | 8.9378 | 0.6656 | 0.9427 | 0.9290 | 0.7575 | 1.0000 | `0.25 / 0.25` | `0.25` | `0.25` | candidate_head_context_ranking_failure |

All v88 checkpoints:

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

## 关键观察

### 1. 旧 v79/v80 的 focused candidate ranking 没被三次复跑重现

旧 v80 外部审计：

```text
raw_pair_pass_rate = 1.0
admission_pair_pass_rate = 1.0
delay_risk_pair_pass_rate = 0.5
strict_pair_pass_rate = 0.5
primary = delay_risk_head_context_ranking_failure
```

v88 三个带完整 `training_run_config` 的复跑：

```text
raw/admission max = 0.75 / 0.75
strict max = 0.25
primary = candidate_head_context_ranking_failure
```

因此不能再把旧 v79 当作可复现实验基线。它可以作为“曾经出现过的有利 checkpoint 行为”，但不能作为稳定训练策略的证明。

### 2. Seed 对 macro ROI 和 focused ranking 的影响非常大

seed73 的 accepted ROI point estimate 高达 `8.9378`，ROI CI-low 也略过 `0.65`，但：

```text
false_high_priority_on_delay = 1.0
false_safe_rate_union = 1.0
focused strict = 0.25
```

这再次证明 Stage 3 不能用 ROI point estimate 抵消 safety / focused gate 失败。

seed13 false-delay 为 `0.0`，ROI CI-low 为 `0.7272`，但 accepted 只有 `4`，safe precision CI-low 只有 `0.5101`，focused strict 只有 `0.25`。这属于安全但过窄、统计不稳的壳层。

seed41 accepted 较多且 false-delay 为 `0.0`，但 ROI CI-low 为负，focused raw/admission 为 `0.0/0.0`。

### 3. 当前 blocker 回到 candidate head 稳定性

v78/v80 之后曾把 blocker 描述为 delay-risk head。v88 说明更精确的说法应改为：

```text
path-token/slack 能让 candidate ranking 偶尔变好，
delay-risk pairwise 能局部改善 risk ordering，
但 candidate head 的同 context 排序稳定性没有被训练目标锁住。
```

下一步如果只调 risk-head loss，很可能继续出现 seed73 这种高 ROI / 高 false-delay，或 seed41 这种安全但 focused candidate ranking 完全失败。

## 当前结论

1. v75 path-token/slack 仍应保留，但它不是充分条件。
2. v79/v80 不应作为可复现实验基线，只能作为参考 checkpoint。
3. v88 三 seed 均未过 focused strict gate，也均未过 Stage 3 deployment gate。
4. 当前优先修复目标应从 “调 delay-risk 权重” 转为 “candidate head focused pair 稳定过 gate，再校准 risk head”。
5. 后续训练必须把 focused pair gate 从训练后 hard gate 前移为训练/selection 的强约束，否则 seed 漂移会继续掩盖失败。

## 下一步

1. 在训练 loss 中增加 focused tranche oversampling 或 focused pair loss weight，而不是只依赖全局 same-context pairwise loss。
2. focused pair loss 应分别约束：
   - positive raw candidate score > hard-negative raw candidate score；
   - positive admission score > hard-negative admission score；
   - positive delay-risk < hard-negative delay-risk；
   - strict pair pass。
3. 保留 v75 path-token/slack 和 pairwise delay-risk weight `1.0`，但不要继续增加到 `3.0`。
4. risk-head calibration 的小权重消融应推迟到 candidate head focused raw/admission 稳定后；否则会混淆 candidate ranking 和 safety failure。
5. 扩展 focused regression tranche，加入 random-wave same-context positive / hard-negative 和 v53 `79fde/ac15/ac056` individual rows；当前 9 rows / 4 pairs 太小。

## Verification

```text
v88 seed13 training smoke = pass, gate failed as diagnostic
v88 seed41 training smoke = pass, gate failed as diagnostic
v88 seed73 training smoke = pass, gate failed as diagnostic
runs_bpc_or_pricing = false
production_ready = false
stage4_candidate_ready = false
stage5_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

并行 seed sweep 曾启动但未产生产物，已中断；本报告只使用后续串行三次成功运行的 metrics。

## Exactness Boundary

本轮只做离线训练和报告综合，不改变 solver、pricing、RMP、branch/cut、final judge 或 benchmark 默认配置。

GAT 可以帮助 pricing 更早搜索可能改善 RMP trajectory 的列族、路径序列和候选 batch；GAT+CBF/kNN/OOD 可以对 true-RC verified negative candidates 做有限延迟 admission scheduling。最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
