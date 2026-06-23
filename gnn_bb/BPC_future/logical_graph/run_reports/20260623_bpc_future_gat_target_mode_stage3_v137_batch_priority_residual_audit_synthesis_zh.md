# BPC_future GAT target-mode Stage 3 v137 审计综合报告

日期：2026-06-23

## 结论

v137 是负结果。它在 v136 的 raw-all-candidate focused loss 基础上，新增默认关闭的
batch/context priority residual 机制：

```text
candidate_batch_priority_logit -> 加到 candidate high-priority raw logit
candidate_batch_priority_logit -> 从 candidate delay-risk logit 中扣除
```

目标是让同 context pairwise 监督不再只训练一个 auxiliary comparator，而是直接影响
focused gate 实际比较的 raw / admission / delay-risk 三个量。

结果上，v137 的 selected checkpoint local deployment gate 通过，ROI-CI 还略高于
v136；但 focused pair gate 从 v136 的 strict `75/78` 退化到 `74/78`。因此 v137
不能进入 kNN/OOD，也不能作为 Stage 4 candidate。

本轮不运行 BPC / pricing / RMP，不生成 certificate 或 official lower bound。GAT 仍只
是 admission scheduling 的 offline diagnostic 组件。

## 运行对象

- dataset:
  `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint:
  `BPC_future/results/gat_batch_impact_training_v137_batch_priority_residual_seed13_20260623/model.pt`
- metrics:
  `BPC_future/results/gat_batch_impact_training_v137_batch_priority_residual_seed13_20260623/metrics.json`
- training report:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v137_batch_priority_residual_seed13_zh.md`
- focused failure audit:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v137_focused_pair_failure_audit_zh.md`

## 本轮代码改动

新增模型参数，默认均为 `0.0`：

```text
candidate_batch_priority_residual_scale
delay_risk_batch_priority_residual_scale
```

当任一 scale 非零时，模型新增 `candidate_batch_priority_head`，输出
`candidate_batch_priority_logit`。该 logit 会：

- 按 `candidate_batch_priority_residual_scale` 加到每个 candidate 的
  `high_priority_logit`；
- 按 `delay_risk_batch_priority_residual_scale` 从每个 candidate 的
  `delay_risk_logit` 中扣除。

训练脚本新增：

```text
--candidate-batch-priority-residual-scale
--delay-risk-batch-priority-residual-scale
--focused-pair-batch-priority-loss-multiplier
```

`focused_pair_batch_priority_loss_multiplier` 只训练这个 residual head 的同 context
正负排序。如果 residual scale 为 0，却试图单独训练 priority loss，训练会报错，避免再次
落入“只训练不参与 admission 的 auxiliary score”路径。

## v137 配置

相对 v136，只新增：

```text
candidate_batch_priority_residual_scale = 0.5
delay_risk_batch_priority_residual_scale = 0.5
focused_pair_batch_priority_loss_multiplier = 4.0
```

其他数据集、seed、split、ROI/precision gate、focused gate、raw-all-candidate loss
均保持同口径。

## 关键指标

selected epoch = `2`；best validation-loss epoch = `4`。epoch 4 local gate 未通过，
所以不能按 validation loss 选。

epoch 2 validation deployment metrics：

- `threshold_local_gate_pass = true`
- `accepted_batch_count = 35`
- `accepted_batch_roi = 19.40859424812453`
- `accepted_batch_roi_ci_low = 10.306315927021846`
- `high_priority_precision = 0.9992260061919505`
- `high_priority_precision_ci_low = 0.9956286800857106`
- `safe_precision = 1.0`
- `safe_precision_ci_low = 0.9010957324106112`
- `false_high_priority_on_delay = 0.0036101083032490976`
- `false_safe_rate_union = 0.0036101083032490976`
- `nonfinite_skipped_update_rate = 0.0`

focused pair gate：

- `pair_count = 78`
- raw = `74/78`
- admission = `75/78`
- delay-risk = `75/78`
- strict = `74/78`
- blocking primary = `candidate_head_context_ranking_failure`

Stage 4 blockers：

- `raw_pair_pass_rate_below_threshold`
- `admission_pair_pass_rate_below_threshold`
- `delay_risk_pair_pass_rate_below_threshold`
- `strict_pair_pass_rate_below_threshold`
- `knn_ood_audit_missing`
- `knn_ood_holdout_audit_not_run`
- `online_shadow_and_opt_in_ab_not_run`

## Epoch 轨迹

| epoch | local gate | accepted | ROI | ROI CI low | false-delay | safe CI low | raw | admission | delay-risk | strict |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | true | 35 | 11.682 | 3.401 | 0.0036 | 0.901 | 73/78 | 73/78 | 71/78 | 71/78 |
| 2 | true | 35 | 19.409 | 10.306 | 0.0036 | 0.901 | 74/78 | 75/78 | 75/78 | 74/78 |
| 3 | false | 93 | 7.766 | 3.897 | 0.0144 | 0.960 | 74/78 | 75/78 | 74/78 | 73/78 |
| 4 | false | 16 | 25.158 | 11.162 | 0.0000 | 0.806 | 74/78 | 74/78 | 75/78 | 74/78 |
| 5 | false | 9 | 14.004 | 8.753 | 0.0000 | 0.701 | 74/78 | 75/78 | 75/78 | 74/78 |

没有任何 epoch 达到 focused strict `78/78`。

## 与 v136 对比

| run | selected epoch | local gate | accepted | ROI | ROI CI low | false-delay | focused raw | focused admission | focused delay-risk | focused strict |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v136 | 4 | true | 35 | 18.603 | 9.467 | 0.0036 | 75/78 | 75/78 | 76/78 | 75/78 |
| v137 | 2 | true | 35 | 19.409 | 10.306 | 0.0036 | 74/78 | 75/78 | 75/78 | 74/78 |

v137 的 ROI / ROI-CI 比 v136 略好，但 focused strict 退化，不能替代 v136。

## Failure Anatomy

v137 focused failure audit：

```text
pair_count = 78
failed_pair_count = 4
pair_pass_count = 74
raw_fail_count = 4
admission_fail_count = 3
delay_risk_fail_count = 3
all_failed_heads_near_rate_among_failed = 0.25
any_failed_head_deep_rate_among_failed = 0.0
diagnosis_counts = {
  mixed_margin_failure: 3,
  near_margin_loss_tuning_candidate: 1,
  pair_passes: 74
}
```

失败 pair：

| context | family | positive row | negative row | positive ROI | raw margin | admission margin | delay-risk margin | diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 812 | 815 | 3.068 | -0.0275 | -0.0197 | -0.0139 | mixed margin |
| `b36178f6655c5f75` | greedy-anchor | 813 | 815 | 1.321 | -0.0375 | -0.0269 | -0.0196 | mixed margin |
| `ddcb5387bef3bf63` | random-wave | 779 | 398 | 12.996 | -0.0127 | -0.0170 | -0.0197 | mixed margin |
| `7cb380a02e30e5a8` | random-wave | 810 | 808 | 0.672 | -0.0065 | 0.0020 | 0.0081 | near margin |

和 v136 对比：

- 修复了 v136 的 `84ae11479ed592d4`；
- 修复了 v136 的 `9f80ae35ea87da5b`；
- `b36178f6655c5f75` 从 1 个失败扩大为 2 个失败；
- 新增 `ddcb5387bef3bf63` 和 `7cb380a02e30e5a8` 失败。

这说明 batch-level residual 有信号，但作为同一个 scalar 加到所有 candidate 上太粗：
它能修复某些 context-level ordering，却会压扁或反转另一些 candidate/action-level差异。

## 为什么不跑 kNN/OOD

kNN/OOD 是 Stage 4 前安全壳，不是 focused ranking 修复工具。v137 selected checkpoint
已经被 focused gate 拦住：

```text
raw/strict = 74/78
admission/delay-risk = 75/78
required = 78/78
```

即使 kNN/OOD 通过，也不能覆盖 focused gate 失败。因此本轮跳过 kNN/OOD。

## 判断

v137 证明“把 batch/context priority scalar 直接残差加到所有 candidate head”不是当前
主 blocker 的可靠修复。它相比纯 auxiliary comparator 更接近正确方向，因为确实能影响
admission score 并修掉一部分 v136 失败；但它粒度过粗，会牺牲 candidate/action-local
差异，导致 focused gate 总体退化。

下一步不应继续盲目放大或缩小这个 scalar residual。更合理的方向是：

1. 做 candidate/action-level delta head，而不是 batch-level scalar residual；
2. 让 pairwise 监督作用到“positive labeled candidate vs negative row max candidate”的
   可解释差异特征，而不是对整批 candidate 加同一个偏置；
3. 对 `b361`、`ddcb`、`7cb` 这类被 residual 新破坏的 context 做无泄漏 analog mining；
4. 保留 residual 作为默认关闭实验开关，但下一轮主线回到更细粒度的 context-local
   candidate/action ranking。

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

GAT 只能排序、调度和有限延迟 true-RC negative；最终 no-negative certificate 仍必须来自
当前 branch/cut/dual 下 exact pricing full closure。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/learning/batch_impact_model.py \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/tests/test_gat_batch_impact_model.py \
  BPC_future/tests/test_gat_batch_impact_training.py \
  BPC_future/scripts/audit_gat_batch_impact_focused_pair_failures.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_model \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_focused_pair_failures \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_context_pair_comparator \
  BPC_future.tests.test_gat_batch_impact_unresolved_context_label_action
```

结果：

```text
py_compile: pass
Ran 59 tests in 0.697s
OK
```

JSON 校验：

```text
v137 metrics.json: pass
v137 focused failure summary.json: pass
```

`git diff --check` 对本轮触达文件通过。
