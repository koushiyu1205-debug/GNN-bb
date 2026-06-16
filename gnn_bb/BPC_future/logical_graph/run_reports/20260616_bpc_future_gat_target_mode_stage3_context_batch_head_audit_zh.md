# 2026-06-16 BPC_future GAT Target Mode Stage 3 Context/Batch Head Audit 报告

## 结论

本轮针对 v13 `missed_high_roi_opportunities` 做模型结构复核。结论是：

```text
candidate_priority_head_context_batch_aware = true
v13_primary_blocker = high_roi_candidate_score_capture_shortfall
stage4_candidate_ready = false
production_ready = false
```

`GATBatchImpactModel` 的 candidate-level `HIGH_PRIORITY` / `DELAY_QUEUE` head
已经同时接收 candidate embedding、batch embedding 和 RMP context embedding。
因此 v13 random-wave high-ROI capture 不足，不能解释成“candidate head 完全看不到
RMP / batch context”。继续只做简单 loss 加权或重复接入 context，不是当前最高优先级。

## 代码证据

当前模型结构：

```text
BPC_future/learning/batch_impact_model.py

candidate_decision_dim =
  candidate_hidden_dim + batch_hidden_dim + context_hidden_dim

candidate_decision_input =
  concat(candidate_embedding, batch_embedding, context_embedding)

high_priority_logit = high_priority_head(candidate_decision_input)
delay_risk_logit = delay_risk_head(candidate_decision_input)
```

新增回归测试：

```text
BPC_future/tests/test_gat_batch_impact_model.py
test_candidate_priority_head_depends_on_context_and_batch
```

该测试固定 graph、candidate membership、sequence positions 和 candidate features，
分别只改变 `context_features` 或 `batch_features`，要求
`high_priority_logit` 随之变化；同时检查 `high_priority_head` 的输入维度包含
candidate、batch、context 三段。

## 对 v13 blocker 的解释

v13 opportunity mining 显示：

```text
validation_high_roi_opportunities = 27
accepted_high_roi_opportunities = 18
missed_high_roi_opportunities = 9
random_wave_missed_high_roi = 4 / 5
primary_missed_reason = no_candidate_above_threshold
```

结合本轮模型结构审计，当前失败更可能来自：

- random-wave / task50 同 context positive-negative pair 不足；
- high-ROI batch 内 safe candidate score margin 不够；
- threshold frontier 在 precision / false-safe / ROI-CI gate 下没有 feasible point；
- candidate boost 只增大 hard-ROI / pairwise loss 权重，不能创造缺失的同 context 监督信号。

## 下一步

下一步不应把“让 candidate head 接入 context/batch”作为主线，因为这已经存在。
更直接的推进是：

1. 对 v13 missed high-ROI rows 做 candidate score margin audit，输出每个 family/context
   的 top safe candidate score、threshold gap 和是否有同 context negative 对照。
2. 补 random-wave same-context high-ROI positive / negative rows，优先覆盖
   task50 `5751b1799b606ad1` 附近的 missed contexts。
3. 训练 gate 继续保持 `precision_constrained_roi_maximization`，
   `accepted_bad_mode_count=0` 和 family high-ROI capture hard gate。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
delay_queue_replaces_exact_pricing = false
stage4_candidate_ready = false
```

本轮只增加离线模型结构回归测试，不接入 solver、pricing dispatch、admission
scheduler 或 certificate path。最终 certificate 仍只能由当前 branch/cut/dual 下的
exact pricing full closure 产生。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_batch_impact_model

Ran 6 tests in 0.146s
OK
```

```text
git diff --check -- \
  BPC_future/tests/test_gat_batch_impact_model.py \
  BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md \
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_context_batch_head_audit_zh.md

OK
```
