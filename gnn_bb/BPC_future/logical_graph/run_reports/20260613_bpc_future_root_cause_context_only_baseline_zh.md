# BPC_future 根因审计补充：context-only baseline

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是检查：

> 仅用 dataset / instance / profile 上下文身份和训练集 base rate，能解释多少 improved / worsened？

这用于判断 batch feature 的信号是否大量来自上下文混杂。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_context_only_baseline.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_context_only_baseline.py \
--output-dir BPC_future/results/root_cause_context_only_baseline_20260613
```

输出：

```text
BPC_future/results/root_cause_context_only_baseline_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

## 最佳 context-only baseline

每个 hold-out 维度下，选训练集上可用的最佳 context set。

| hold-out | best context set | accuracy | precision | recall | tp | fp | tn | fn |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dataset | `profile_then_instance` | `0.5659722222222222` | `0.5679012345679012` | `0.3382352941176471` | `46` | `35` | `117` | `90` |
| instance | `profile` | `0.6388888888888888` | `0.635593220338983` | `0.5514705882352942` | `75` | `43` | `109` | `61` |
| profile | `instance` | `0.65625` | `0.6796116504854369` | `0.5147058823529411` | `70` | `33` | `119` | `66` |

## 解释

Context-only baseline 明显不是随机：

- hold-out instance / profile 时 precision 可到 `0.63` 到 `0.68`；
- 说明 profile / instance context 本身携带大量 trajectory outcome 信息；
- 这也解释了为什么 aggregate feature gate 会在不同 result-set 中失效。

但 context-only baseline 也不是 production selector：

- hold-out dataset precision 只有 `0.5679`，recall `0.3382`；
- 所有 hold-out 组合都没达到 precision `0.75` 且 recall `0.5` 的稳定 gate；
- 它只能说明“必须建模上下文”，不能直接作为优化策略。

## 对根因判断的影响

本轮进一步说明：

> 当前 returned-batch outcome 的可预测性很大一部分来自 dataset / instance / profile context base rate，而不是单纯来自具体 returned batch feature。

因此：

- 不建模 context 的全局阈值会失效；
- 只用 context identity 又不够；
- 下一步如果继续找优化方向，需要 context-aware + batch feature + counterfactual/replay 共同证明。

## 当前不能得出的结论

不能说：

- context-only baseline 可以上线；
- profile 固定策略就能解决；
- instance-specific rule 足够；
- 当前问题只是 profile 选择问题。

只能说：

- context 是必要变量；
- 但不是充分变量；
- production selector 还缺少更强的因果或 replay 证据。

## 结论

根因进一步收紧为：

> 20-task hard-tail 的 returned-batch trajectory selector 必须同时处理上下文基准率和具体 batch composition。单独的 batch feature 或单独的 context identity 都不能形成 production-safe gate。
