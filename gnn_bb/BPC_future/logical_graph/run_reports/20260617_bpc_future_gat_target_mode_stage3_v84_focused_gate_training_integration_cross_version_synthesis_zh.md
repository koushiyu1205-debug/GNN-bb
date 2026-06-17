# 2026-06-17 BPC_future GAT Stage 3 v84 Focused Gate 训练集成与跨版本综合报告

## 读取范围

本轮复读并横向对照了目标模式计划、Stage 3 v15/v39/v43-v46/v51/v55/v61-v64/v67/v71-v72/v75-v83，以及 Stage 4 v53 execution / A-B ROI / certificate audit。

边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 本轮代码集成

v83 的下一步要求是把 focused same-context positive-vs-hard-negative pair gate 固化进训练后 artifact，而不是继续人工跑一次外部审计。

本轮在 `BPC_future/scripts/train_gat_batch_impact.py` 中新增训练后 focused gate：

- `--focused-pair-gate-row-index-min`：指定固定 regression tranche 起始 row，例如当前 v77/v80/v82 focused rows 使用 `383`；
- `--min-focused-pair-count`；
- `--min-focused-raw-pair-pass-rate`；
- `--min-focused-admission-pair-pass-rate`；
- `--min-focused-delay-risk-pair-pass-rate`；
- `--min-focused-strict-pair-pass-rate`。

训练完成后，trainer 会从 manifest rows 和全数据预测记录生成：

```text
focused_pair_gate.active
focused_pair_gate.summary
focused_pair_gate.context_rows
focused_pair_gate.pair_rows
focused_pair_gate.gate.reject_reasons
focused_pair_gate_reject_reasons
```

这些 reject reasons 已并入：

```text
checkpoint_gate_pass
rejected_checkpoint_reasons
rejected_checkpoint_reason_categories
stage4_blockers
training_contract.focused_pair_gate
training.focused_pair_gate
report machine fields
```

默认未启用 focused gate 时会写入 `focused_pair_gate_not_run`，并阻止 checkpoint 被视为 Stage 4 candidate。这是有意的：v83 之后，没有固定 focused regression tranche 的 checkpoint 不应进入 mutating admission。

## 跨版本新理解

| 版本线 | 旧现象 | 新理解 |
|---|---|---|
| v15 / v32 / v43 | 16 个 missed high-ROI 全部不是 near-threshold miss。 | 早期不是调 threshold 问题，而是 candidate head 分数缺口和 embedding structural gap。 |
| v39 / v41 | coverage 上去，但 false-delay 约 `0.449`，且集中在 `sector-wave|20` 少数 context。 | blocker 是 context-local action ranking 失败，不是全局噪声。 |
| v44 / v45 | delay-safe shell 存在，v45 smoke 可把 false-delay 压到 `0.0`，但 accepted 只有 `3 / 123`。 | 只追求 false-delay 为 0 会变成过窄安全壳层，不能满足加速目标。 |
| v50 / v53 | context-batch hard-negative 能发现坏区域，但 v53 发现 `79fde` 内有 positive individual target。 | context-level label 太粗，会误伤同 context 正目标；必须保留 target sequence / trace 粒度。 |
| v55 / v60 | individual follow-up 后仍不过 gate，focused raw pass 低。 | 不是 checkpoint selector 失败，而是同 context positive-vs-hard-negative 排序没学稳。 |
| v64 / v67 / v71 | trace scalar 改善 macro coverage 和 random-wave capture，但 focused pair pass 仍只有 `0.25`。 | trace scalar 有效但不够；宏观 ROI 会掩盖局部排序失败。 |
| v75 / v76 / v77 | path-token/slack 后 focused raw/admission pair pass 到 `1.0`，delay-risk pass 为 `0.0`。 | path-token/slack 应保留；candidate head 部分修复，delay-risk head 成为独立 blocker。 |
| v79 / v80 | delay-risk pairwise weight `1.0` 把 delay-risk pair pass 提到 `0.5`，accepted `37`，false-delay `0.0071`。 | 方向有效，但 strict focused gate 未过，不能进 Stage 4。 |
| v81 / v82 | weight `3.0` false-delay 回到 `0.0`，但 accepted 降到 `14`，raw/admission 回退到 `0.75`。 | 继续盲加 delay-risk 权重会破坏 candidate ranking 并重回窄壳。 |

## 当前判断

1. v75 path-token/slack 表示不应回滚。它是目前唯一把 focused raw/admission ranking 拉到 `1.0` 的结构性改动。
2. v79 是当前 delay-risk pairwise smoke baseline。weight `1.0` 有增益；weight `3.0` 是负结果。
3. Stage 3 的目标必须同时硬约束：
   - macro ROI / precision / CI；
   - family holdout 和 random-wave capture；
   - false-delay / false-safe；
   - focused raw/admission/delay-risk/strict pair pass；
   - kNN/OOD；
   - 5/10 no-regression 和 20-task repeat A/B 前置条件。
4. 当前没有任何 checkpoint Stage 4 ready。v53 Stage 4 只证明了 5/10 sentinel 无回归、20-task diagnostic A/B 可安全执行、certificate audit 无 violation；20-task 仍是 `TIME_LIMIT` / `dual_bound=None`。

## 仍然暴露的问题

1. Focused gate 样本很少：当前固定 tranche 是 9 rows / 4 pairs，只适合作为 regression sentinel，不能替代 full validation。
2. Delay-risk head 仍分不开剩余 hard-negative pair。需要更明确的 risk-head supervised signal，而不是只调 admission penalty。
3. Batch ROI head 仍不稳。v77 已显示 candidate/admission 可过但 batch score 仍有未排对情况，ROI CI-low 也经常不过。
4. random-wave / sector-wave 的 coverage 和 false-delay 仍存在 Pareto 张力。
5. Stage 5 目标尚未接近：20-task 还没有稳定 `OPTIMAL < 200s`、official dual bound、final exact pricing closure。

## 下一步

1. 用 v79 配置作为 baseline，启用训练内 focused gate：

```text
--focused-pair-gate-row-index-min 383
--min-focused-pair-count 1
--min-focused-raw-pair-pass-rate 1.0
--min-focused-admission-pair-pass-rate 1.0
--min-focused-delay-risk-pair-pass-rate 1.0
--min-focused-strict-pair-pass-rate 1.0
```

2. 保持 path-token/slack 和 candidate pair loss，delay-risk pairwise weight 在 `0.5 - 1.5` 内探索，不继续盲目增大。
3. 增加样本内 risk-head 校准，例如 hard negative delay loss 与 hard ROI safe delay loss，但必须监控 raw/admission pair 不回退。
4. 只有 focused strict gate、threshold frontier、family holdout、kNN/OOD 都过后，才重新考虑 Stage 4 shadow / opt-in A/B。

## Verification

```text
python3 -m py_compile BPC_future/scripts/train_gat_batch_impact.py = pass
python3 -m py_compile BPC_future/tests/test_gat_batch_impact_training.py = pass
python3 -m unittest BPC_future.tests.test_gat_batch_impact_training = 26 skipped
```

当前系统 Python 缺少 `torch`，所以学习栈单测被 skip；本轮没有运行新的 training smoke 或 BPC / pricing / RMP。

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

Focused gate 只是训练后 model-selection / deployment-readiness hard gate，不能产生 official lower bound、不能替代 true-RC verification、不能参与 no-negative certificate。
