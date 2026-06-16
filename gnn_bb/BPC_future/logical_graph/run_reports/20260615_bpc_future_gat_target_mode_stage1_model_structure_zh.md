# 2026-06-15 BPC_future GAT Target Mode Stage 1 模型结构报告

## 结论

Stage 1 已完成 offline / audit-only 的 batch-impact 模型结构原型。新增模型把目标从“候选列分类”推进到“true-RC 验证后的候选列批次是否改善 RMP trajectory”，但没有接入 solver、pricing dispatch、benchmark config 或 certificate path。

本阶段不声明 `production_ready`，不声明 wall-time ROI，不声明 20-task exact proof 改善。

## 新增/修改文件

- `BPC_future/learning/batch_impact_model.py`
  新增 `JourneyCandidateEncoder`、`BatchImpactEncoder`、`RMPContextEncoder`、`GATBatchImpactModel`。

- `BPC_future/tests/test_gat_batch_impact_model.py`
  覆盖 multi-head 输出、finite check、backward、sequence order sensitivity 和 exact-safe contract。

- `BPC_future/learning/__init__.py`
  仅登记 `batch_impact_model` 模块名，不引入 torch import side effect。

## 模型结构

`GATBatchImpactModel` 复用现有 `HierarchicalOptionGAT.encode()`：

- logical graph / path-option graph 仍由 `FutureGraphBuilder` 和 `OptionEncoder` 表示；
- task embedding 来自现有 GATv2Conv message passing；
- 新增 ordered journey candidate 表示；
- 新增 candidate batch pooling；
- 新增 RMP context embedding；
- 新增 candidate-level 和 batch-level heads。

新增输出包括：

- `high_priority_probability`
- `delay_risk_probability`
- `batch_roi_positive_probability`
- `objective_progress_probability`
- `tail_improved_probability`
- `bad_mode_switch_probability`
- `support_changed_good_probability`
- `predicted_delta_v`
- `predicted_barrier_slack`
- `predicted_accepted_batch_roi`

这组 head 是后续训练脚本和 offline audit 的目标接口。训练阶段必须用 precision / ROI / false-safe / coverage 门槛选择 checkpoint，不能只按 validation loss、F1 或 recall。

## Stage 3 训练目标加硬后的约束

计划文档已把训练验收目标改成 deployment-facing metrics：

- HIGH_PRIORITY 必须高精准、高回报；
- accepted batch count 必须大于 0；
- accepted batch ROI 必须高于 random / best-RC / old-GAT baseline；
- false HIGH_PRIORITY 和 false-safe 必须强惩罚；
- high recall 不能抵消 low precision；
- high F1 不能抵消 low accepted ROI；
- zero-FP 但 accepted batch count = 0 不能进入 online A/B。

这次 Stage 1 模型结构已经为这些硬目标预留了对应 head，特别是 `batch_roi_positive_probability`、`predicted_accepted_batch_roi`、`high_priority_probability` 和 `bad_mode_switch_probability`。

## Exactness Boundary

新增模块的 contract 为：

```text
production_ready=false
pricing_oracle=false
certificate_source=false
official_bound_effect=false
can_permanently_discard_true_rc_negative=false
delay_queue_replaces_exact_pricing=false
```

因此：

- 模型不能证明无负 reduced-cost journey；
- 模型不能产生 official lower bound；
- 模型不能永久丢弃 true-RC negative candidate；
- DELAY_QUEUE 只能延迟调度，不能替代 final exact pricing closure；
- 最终 certificate 仍必须由当前 branch/cut/dual 下的 exact pricing 重新确认整个配置宇宙没有负 reduced-cost journey。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_model
```

结果：

```text
Ran 4 tests in 2.340s
OK
```

测试覆盖：

- model forward 输出维度；
- sigmoid probability 范围；
- regression heads finite；
- backward gradient 非零；
- 同一 task set、不同 task order 的 candidate 表示不同；
- exact-safe contract 明确 audit-only。

## 尚未完成

- 未实现 `build_gat_batch_impact_dataset.py`。
- 未实现 `train_gat_batch_impact.py`。
- 未训练 checkpoint。
- 未做 kNN/OOD holdout。
- 未做 shadow / opt-in online A/B。
- 未证明 5/10 no-regression 或 20-task wall-time ROI。

## 下一步

进入 Stage 2 前，需要先定 batch-impact dataset schema：

- same-context intervention sample；
- pre-addition RMP context，避免 post-addition leakage；
- candidate batch payload；
- H-step objective / dual / basis / tail retry trajectory labels；
- family/context holdout 字段；
- checkpoint manifest 中继续写死 `production_ready=false`。
