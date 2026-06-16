# 2026-06-16 BPC_future GAT Stage 3 Training Objective Hardening 报告

## 结论

本次只收紧计划文档，不改 solver / pricing / trainer 代码。

Stage 3 训练目标必须从普通分类训练改成硬约束 admission policy 训练：

```text
primary_objective = precision_constrained_roi_maximization
```

也就是说，训练阶段必须同时考虑回报率和精准率，而且二者不能互相抵消。validation loss、F1、AUC、recall 只能作为 surrogate / diagnostic / tie-breaker；不能决定 checkpoint 是否合格。

更硬地说，训练阶段不是“先学一个分数，再用 evaluator 看看 ROI”。合格 checkpoint
必须在同一组 frozen threshold / OOD / fallback rule 下同时通过：

```text
precision / safe_precision / precision_CI
accepted_batch_ROI / ROI_CI / ROI_over_baseline
false_high_priority_on_delay / accepted_bad_mode / false_safe_union
nonzero useful coverage
family_context_holdout_precision_and_ROI
```

任一项失败都必须直接输出：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
training_objective_not_satisfied = true
```

不能用更高 recall、更低 loss、更好 F1/AUC 或更宽 coverage 抵消 precision / ROI /
safety gate 失败。

## 本次文档变更

更新：

```text
BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md
```

新增 `Stage 3: Training` 入口硬合同：

- 默认 `stage4_candidate_ready=false`；
- 只有同一组 frozen threshold / OOD / fallback rule 同时证明 precision、safe precision、accepted ROI、ROI-CI、baseline margin、coverage、family/context holdout 全部过线，checkpoint 才能成为 Stage 4 candidate；
- `best_epoch` 不能来自 `min(validation_loss)`；
- 合法 checkpoint selection 必须先筛掉未通过 precision / safety / ROI / ROI-CI / baseline / coverage / holdout gate 的 epoch，再在 feasible checkpoint 内比较 ROI-CI、baseline margin 和 trajectory utility；
- artifact 缺少 ROI / precision / CI / baseline / reject reason 任一硬字段时，必须输出 `training_contract_incomplete=true`。

## 新硬边界

训练阶段不能再出现以下结论包装：

- high recall + low precision；
- high precision + low accepted ROI；
- positive ROI point estimate 但 ROI lower bound 不过 baseline；
- zero false positive 但 accepted batch count = 0；
- validation loss 最低但 ROI / precision gate 失败；
- 只报告分类指标，不报告 deployment-facing ROI / precision / coverage。

这些情况都必须标记为：

```text
stage4_candidate_ready = false
training_objective_not_satisfied = true
```

## Exactness Boundary

本次只是文档目标收紧：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
```

GAT 仍只能做 pricing priority / true-RC negative admission scheduling；最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 no-negative closure。
