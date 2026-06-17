# 2026-06-17 BPC_future GAT Stage 3 v91 Focused Pair Loss 实现与 Smoke 报告

## 读取范围

本轮复读了目标模式计划、Stage 1、Stage 2、Stage 3 v87/v89、Stage 4 v53 和 Stage 5 目标。

边界保持：

```text
Learning-guided discovery, exact-certified closure
```

本轮只改离线训练脚本和训练测试，不改 solver、pricing、RMP、branch/cut、final judge 或 benchmark 默认配置。GAT 仍不能产生 official bound 或 certificate。

## 背景

v89 的三 seed sweep 说明：旧 v79/v80 的 focused raw/admission `1.0/1.0` 没有被带完整 `training_run_config` 的 v88 复跑稳定重现。当前 blocker 重新聚焦为：

```text
candidate head focused same-context ranking 不稳定
```

因此本轮把 focused tranche 从“训练后 gate”推进到“可选训练 loss”：默认关闭，只有显式设置时才对 fixed focused rows 增加 positive-vs-hard-negative pairwise 训练压力。

## 代码改动

`BPC_future/scripts/train_gat_batch_impact.py` 新增：

- CLI / dataclass 参数：

```text
--focused-pair-loss-multiplier
```

- `loss_options` 新字段：

```text
focused_pair_loss_multiplier
focused_pair_row_index_min
```

- focused training pair helper：

```text
_focused_training_pairs(samples, focus_row_index_min=...)
```

语义：

```text
只选 batch_impact_source_row_index >= focused_pair_gate_row_index_min 的样本；
同 context 内 positive_high_priority 对 delay_or_hard_negative 形成训练 pair；
额外用 focused_pair_loss_multiplier * _pairwise_ranking_loss(...) 训练。
```

该 loss 默认 `0.0`，所以旧训练命令不改变行为。

`BPC_future/tests/test_gat_batch_impact_training.py` 新增：

- `_loss_options()` 写出 focused loss multiplier 和 row_index；
- `_focused_training_pairs()` 只从 fixed focused tranche 生成同 context positive-vs-hard-negative pair。

## v90 Smoke

在 v88 seed13 基础上只打开：

```text
--focused-pair-loss-multiplier 1.0
--focused-pair-gate-row-index-min 383
```

其他保持：

```text
dataset = v75_v66_path_tokens_slack_20260617
seed = 13
epochs = 1
pairwise_delay_risk_contrast_loss_multiplier = 1.0
```

结果：

| run | focused loss | accepted | accepted ROI | ROI CI-low | HP precision | HP CI-low | safe CI-low | false-delay | focused raw/admission | focused delay-risk | focused strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v88 seed13 | 0.0 | 4 | 1.0204 | 0.7272 | 1.0000 | 0.9789 | 0.5101 | 0.0000 | `0.75 / 0.75` | `0.5` | `0.25` |
| v90 seed13 | 1.0 | 8 | 0.8994 | 0.6643 | 1.0000 | 0.9921 | 0.6756 | 0.0000 | `0.5 / 0.5` | `0.25` | `0.0` |

v90：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
primary = candidate_head_context_ranking_failure
```

## 结论

实现链路是可用的，artifact 也能记录 focused loss 配置；但 `focused_pair_loss_multiplier=1.0` 的第一版策略是负结果：

1. accepted coverage 从 `4` 增到 `8`，但这不是 Stage 3 目标的核心改进。
2. focused raw/admission 从 `0.75/0.75` 降到 `0.5/0.5`。
3. focused delay-risk 从 `0.5` 降到 `0.25`。
4. focused strict 从 `0.25` 降到 `0.0`。
5. safe precision CI-low 仍只有 `0.6756`，不过 gate。

这说明简单地把完整 pairwise loss 复制到 focused tranche 并乘以 `1.0`，不能稳定修复 focused strict gate。它可能把 batch/candidate/risk 三个头的梯度混在一起，导致 risk ordering 被压坏。

## 新理解

focused pair 训练不应只是全局 `_pairwise_ranking_loss` 的额外权重。下一步需要拆成分头约束：

- focused candidate raw loss：只修 `positive raw > hard-negative raw`；
- focused admission loss：只修实际 admission score；
- focused delay-risk loss：单独修 `positive risk < hard-negative risk`；
- 分别扫小权重，避免一个整体 multiplier 同时扰动 candidate head 和 risk head。

## 下一步

1. 保留当前默认关闭实现，因为它提供了可复用的 focused tranche plumbing。
2. 不继续放大 `focused_pair_loss_multiplier`。
3. 下一版应实现分头 focused loss，默认仍关闭：
   - `focused_pair_candidate_loss_multiplier`
   - `focused_pair_delay_risk_loss_multiplier`
   - 可选 `focused_pair_batch_loss_multiplier`
4. 先在 seed13/41/73 上用小权重验证 focused raw/admission 是否稳定提升，再考虑 risk-head calibration。
5. focused strict、family holdout、kNN/OOD 都过之前，仍不得进入 Stage 4 mutating admission。

## Verification

```text
py_compile train_gat_batch_impact.py + test_gat_batch_impact_training.py = pass
unittest BPC_future.tests.test_gat_batch_impact_training = 27 tests OK
v90 focused pair loss smoke = pass, gate failed as diagnostic
runs_bpc_or_pricing = false
production_ready = false
stage4_candidate_ready = false
stage5_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Exactness Boundary

本轮不改变 exact proof path。最终 optimality proof 仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
