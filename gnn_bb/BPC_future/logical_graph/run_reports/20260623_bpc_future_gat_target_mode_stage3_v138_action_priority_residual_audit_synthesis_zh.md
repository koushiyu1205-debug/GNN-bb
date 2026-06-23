# 2026-06-23 BPC_future GAT Stage 3 v138 Action-priority Residual 审计综合报告

## 结论

v138 是一次 Stage 3 诊断性训练改动，不是 Stage 4 candidate。

本轮新增 default-off candidate/action priority residual head，并在训练中打开：

```text
candidate_action_priority_residual_scale = 0.5
delay_risk_action_priority_residual_scale = 0.5
focused_pair_action_priority_loss_multiplier = 4.0
```

结果是：

- validation local deployment gate 通过；
- accepted ROI / ROI CI-low 比 v137 略高；
- focused strict pair gate 仍失败，`74 / 78 = 0.9487179487179487`；
- checkpoint gate 仍失败；
- `stage4_candidate_ready=false`。

因此 v138 只能记录为弱正向但整体失败的 Stage 3 诊断结果。它不能进入 Stage 4 shadow / opt-in，也不能触发 kNN/OOD 后续 Stage 4 绑定审计。

## 复读边界

本轮重新对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 训练和训练硬门槛报告
- Stage 4 v53 execution synthesis
- v137 batch-priority residual 结论

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT 只能做 discovery / ordering / finite-delay admission scheduling；不能作为 pricing oracle，不能产生 official lower bound，不能生成 certificate，不能永久丢弃 true-RC negative。最终 proof 仍必须由 exact pricing 在当前 branch/cut/dual 下对完整配置宇宙做 no-negative closure。

## 本轮改动

代码层面新增的是训练/诊断用 action-priority residual：

- `BPC_future/learning/batch_impact_model.py`
  - 新增 `candidate_action_priority` head name；
  - 新增 `candidate_action_priority_residual_scale`；
  - 新增 `delay_risk_action_priority_residual_scale`；
  - 默认不开 head，默认输出零 logit，不改变旧模型行为；
  - 打开后，action-priority logit 加到 high-priority logit，并从 delay-risk logit 中扣除。

- `BPC_future/scripts/train_gat_batch_impact.py`
  - 新增 CLI / config 字段；
  - 新增 `focused_pair_action_priority_loss_multiplier`；
  - focused pair loss 可直接监督 action-priority head；
  - 如果打开 action-priority loss 但模型没有 head，会直接报错，避免静默无效。

- `BPC_future/tests/test_gat_batch_impact_model.py`
  - 覆盖 default-off 零输出；
  - 覆盖 optional trainable residual head；
  - 覆盖 head name。

- `BPC_future/tests/test_gat_batch_impact_training.py`
  - 覆盖 action-priority focused pair loss helper；
  - 覆盖 loss option 传递。

本轮没有修改 pricing、RMP、branching、final judge、certificate path 或 benchmark 默认配置。

## 训练设置

训练 artifact：

```text
metrics =
  BPC_future/results/gat_batch_impact_training_v138_action_priority_residual_seed13_20260623/metrics.json

checkpoint =
  BPC_future/results/gat_batch_impact_training_v138_action_priority_residual_seed13_20260623/model.pt

epoch_checkpoints =
  BPC_future/results/gat_batch_impact_training_v138_action_priority_residual_seed13_20260623/epoch_checkpoints/
```

数据集：

```text
BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
```

注意：这里的 `5000` 是前置 quota-selected target rows / pool 名称；训练脚本实际 materialized batch-impact samples 为：

```text
sample_count = 1117
candidate_count = 12684
train_count = 825
validation_count = 292
family_counts = {'greedy-anchor': 358, 'random-wave': 421, 'sector-wave': 338}
task_count_counts = {'5': 32, '10': 74, '20': 688, '30': 168, '50': 119, '100': 36}
```

训练仍是 offline diagnostic：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_can_certificate = false
```

## Epoch 轨迹

| epoch | local gate | accepted | ROI | false delay | high-priority precision | train loss | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | true | 35 | 4.176693 | 0.003610 | 0.999371 | 6.374202 | 6.764206 |
| 2 | true | 35 | 19.596107 | 0.003610 | 0.999077 | 5.371830 | 5.717350 |
| 3 | true | 36 | 18.825588 | 0.007220 | 0.998314 | 4.291172 | 5.243192 |
| 4 | true | 35 | 18.832292 | 0.007220 | 0.996970 | 3.889236 | 4.890735 |
| 5 | true | 35 | 18.253147 | 0.007220 | 0.996429 | 3.516943 | 5.361521 |

选择结果：

```text
best_epoch = 2
best_loss_epoch = 4
best_loss_epoch_gate_pass = true
selected_checkpoint_reason =
  local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
```

这符合 Stage 3 gate-first 选择合同：loss 不是主选择指标，先比较 ROI CI / utility / safety gate，再用 loss 做次级因素。

## v136 / v137 / v138 对比

| version | best epoch | accepted | ROI | ROI CI-low | false delay | safe CI-low | raw pass | admission pass | delay pass | strict pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v136 focused raw-all-candidate | 4 | 35 | 18.603321 | 9.467079 | 0.003610 | 0.901096 | 75/78 | 75/78 | 76/78 | 75/78 |
| v137 batch-priority residual | 2 | 35 | 19.408594 | 10.306316 | 0.003610 | 0.901096 | 74/78 | 75/78 | 75/78 | 74/78 |
| v138 action-priority residual | 2 | 35 | 19.596107 | 10.534233 | 0.003610 | 0.901096 | 75/78 | 74/78 | 74/78 | 74/78 |

解释：

- v138 比 v137 的 validation ROI / ROI CI-low 略好；
- v138 raw focused pass 从 `74/78` 回到 `75/78`；
- 但 admission / delay-risk 都从 v137 的 `75/78` 退到 `74/78`；
- strict pass 仍为 `74/78`，低于 v136 的 `75/78`。

所以 action-priority residual 没有解决 Stage 3 当前 focused gate blocker。

## Focused Pair Failure Audit

审计 artifact：

```text
summary =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/summary.json

rows =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/focused_pair_failure_rows.jsonl

report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v138_focused_pair_failure_audit_zh.md
```

审计结果：

```text
pair_count = 78
failed_pair_count = 4
pair_pass_count = 74
raw_fail_count = 3
admission_fail_count = 4
delay_risk_fail_count = 4
strict_pair_pass_rate = 0.9487179487179487
diagnosis_counts = {
  'mixed_margin_failure': 3,
  'near_margin_loss_tuning_candidate': 1,
  'pair_passes': 74
}
recommended_next_step =
  add_or_repair_context_action_consequence_features_before_more_sweeps
```

失败 pair：

| context | family | positive row | negative row | positive ROI | raw margin | admission margin | delay-risk margin | diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| b36178f6655c5f75 | greedy-anchor | 812 | 815 | 3.067643 | -0.040343 | -0.031348 | -0.019685 | mixed_margin_failure |
| b36178f6655c5f75 | greedy-anchor | 813 | 815 | 1.320944 | -0.035937 | -0.027949 | -0.017414 | mixed_margin_failure |
| ddcb5387bef3bf63 | random-wave | 779 | 398 | 12.995547 | -0.035207 | -0.021463 | -0.008262 | mixed_margin_failure |
| 7cb380a02e30e5a8 | random-wave | 810 | 808 | 0.671808 | 0.008552 | -0.000842 | -0.007609 | near_margin_loss_tuning_candidate |

Split / leakage guard：

| row | focused gate | train-focused | raw-action boost |
|---:|---|---|---|
| 812 | yes | no | no |
| 813 | yes | no | no |
| 815 | yes | no | no |
| 779 | yes | yes | yes |
| 398 | yes | yes | yes |
| 810 | yes | yes | no |
| 808 | yes | yes | no |

含义：

- `b361` 的三个 row 是 validation-focused gate row，不能直接加入 training-focused boost，否则会污染 gate。
- `ddcb` 已在 train-focused 和 raw-action boost 中，仍然失败，说明 action-priority residual 对这个 train-side hard context 也不够。
- `7cb` 的 raw margin 已转正，但 risk-adjusted admission 和 delay-risk 仍失败，说明单独提高 raw action priority 不能保证最终 admission score 排序正确。

## 判断

v138 的核心判断是：

```text
action-priority residual improves one raw ordering symptom,
but does not fix risk-adjusted admission / delay-risk focused gate.
```

继续盲目加大 residual scale 或 focused-pair multiplier 风险较高，因为：

- b361 不能被 train 直接看见，需要无泄漏 analog mining；
- ddcb 已经被 train-focused loss 看见但仍失败；
- 7cb 暴露 raw score 与 final admission / delay-risk score 不一致；
- focused failure audit 明确建议先修 action-consequence feature，而不是继续扫 multiplier。

## Stage 4 判定

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

主要 blockers：

```text
raw_pair_pass_rate_below_threshold
admission_pair_pass_rate_below_threshold
delay_risk_pair_pass_rate_below_threshold
strict_pair_pass_rate_below_threshold
knn_ood_audit_missing
knn_ood_holdout_audit_not_run
online_shadow_and_opt_in_ab_not_run
```

这里不应运行或绑定 Stage 4 kNN/OOD 审计来包装 v138，因为 focused same-context pair gate 已经失败。kNN/OOD 只能作为 checkpoint 过 focused gate 后的 safety shell 验收，不能弥补 focused ranking 失败。

## 下一步

下一步不应做盲目 multiplier sweep。更合理的 Stage 3 推进方向：

1. 对 `b361` 做 no-leak analog mining：
   - 只从 train split 找相似 action consequence；
   - 不把 row 812/813/815 直接加入训练；
   - 产出 train-only selector 和泄漏审计。

2. 对 `ddcb` 做 action-consequence feature repair：
   - 审计 positive 779 相对 negative 398 的 feature delta；
   - 找出当前 candidate/action head 看不到的 causal signal；
   - 优先补在线可用、pre-addition 的 trace / slack / risk / path-token interaction 特征。

3. 对 `7cb` 做 final-admission score 分解：
   - raw 已过但 admission/delay-risk 不过；
   - 需要检查 risk-adjusted product、delay penalty 和 action-priority residual 的相互抵消；
   - 不能用降低 delay gate 或放宽 strict gate 解决。

4. 训练下一版前继续保持：
   - Stage 3 hard gate 不放宽；
   - focused gate 要求 `raw/admission/delay/strict = 1.0`；
   - exactness boundary 不变；
   - checkpoint 未过 focused gate 时不进入 Stage 4。

## 验证状态

本报告写入后，已在当前工作树上完成验证。

语法编译：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/learning/batch_impact_model.py \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/scripts/audit_gat_batch_impact_focused_pair_failures.py \
  BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  BPC_future/tests/test_gat_batch_impact_model.py \
  BPC_future/tests/test_gat_batch_impact_training.py \
  BPC_future/tests/test_gat_batch_impact_focused_pair_failures.py \
  BPC_future/tests/test_gat_batch_impact_knn_ood.py \
  BPC_future/tests/test_gat_batch_impact_context_pair_comparator.py \
  BPC_future/tests/test_gat_batch_impact_unresolved_context_label_action.py
```

结果：

```text
pass
```

单元测试：

```bash
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
Ran 61 tests in 0.354s
OK
```

artifact sanity：

```text
v138 metrics all_checks_pass = true
v138 metrics stage4_candidate_ready = false
v138 metrics checkpoint_gate_pass = false
v138 focused audit all_checks_pass = true
v138 focused audit failed_pair_count = 4
v138 focused audit strict_pair_pass_rate = 0.9487179487179487
```

path-limited whitespace check：

```bash
git diff --check -- \
  BPC_future/learning/batch_impact_model.py \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/tests/test_gat_batch_impact_model.py \
  BPC_future/tests/test_gat_batch_impact_training.py \
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v138_action_priority_residual_seed13_zh.md \
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v138_focused_pair_failure_audit_zh.md \
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v138_action_priority_residual_audit_synthesis_zh.md
```

结果：

```text
pass
```
