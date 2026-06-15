# GAT Worker ROI v31 真实 A/B 与 Trace 修复报告

日期：2026-06-15

## 目标

本轮目标是修正 worker ROI A/B 链路，确保 GAT 的标签仍然是：

```text
candidate column -> paired baseline/worker A/B 后的 trajectory objective / retry / tail ROI
```

而不是 `rc`、GAT 分数、kNN/OOD 决策或同轮代理指标。

## 修复内容

### 1. capture context 回填

之前 `decision_records.jsonl` 中缺少 `capture_pricing_kind`，导致 runbook 无法判断目标 context 属于 heuristic 还是 exact。结果是首个 20-task worker run 虽然跑了 solver，但没有在目标 exact hook 上正确执行。

现在 `audit_gat_worker_roi_knn_ood.py` 会从 source capture JSONL 中按 `expected_context_hash` 回填：

- `capture_pricing_kind`
- `true_dual_hash`
- `cut_hash`
- `branch_hash`
- `forbidden_signature_hash`
- `active_hash_before`
- `pool_signature_hash`
- `pool_task_set_hash`

真实 v31 审计结果：

```text
validation_high_priority = 9
capture_pricing_kind = exact: 9
full_capture_context = true: 9
```

### 2. materialization trace 修复

之前 runbook 把 `[[[5,18,10],[8,13]]]` 这类 nested task list 当成 `target_materialization_traces` 传给 worker。实际 helper 需要：

```json
{
  "sequence": [5, 18, 10],
  "start_time": 0.0,
  "arc_option_sequence": [
    "0->5:low_risk:2",
    "5->18:low_time:0",
    "18->10:low_risk:1",
    "10->0:low_risk:2"
  ]
}
```

现在审计脚本从 capture 的 `returned_journeys[].trips[]` 恢复每个 sortie 的 `sequence/start_time/arc_option_sequence`。runbook 也增加检查：没有可物化 traces 的 HIGH_PRIORITY 候选不能进入 solver A/B。

## 真实 A/B 结果

本轮补跑了 9 个 validation HIGH_PRIORITY 候选的 20-task paired A/B。

汇总：

```text
record_count = 9
positive_trajectory_roi_count = 5
negative_trajectory_roi_count = 4
roi_class_counts = {
  positive_primal_roi: 5,
  negative_primal_roi: 2,
  negative_retry_roi: 2
}
```

关键正例：

```text
35a4908dfecb7ff3:
  baseline primal = 594.368004
  worker primal   = 580.681228
  improvement     = 13.686776
  worker returned/added = 1 true-RC negative journey
  true_rc = -2.729889
```

该 worker 事件确认：

```text
pulse_worker_status = FOUND_NEGATIVE
pulse_worker_reason = target_materialized_negative_true_rc
pulse_worker_target_sequence_materialized = true
pulse_worker_target_sequence_negative = true
pulse_worker_returned_journeys = 1
added_journeys = 1
new_task_set_count = 1
global_certificate_capable = false
official_bound_effect = false
```

反例也存在：

```text
67925c0d2fd4abde:
  baseline primal = 571.707652
  worker primal   = 572.837934
  improvement     = -1.130282

84ae11479ed592d4:
  baseline primal = 563.295017
  worker primal   = 565.117882
  improvement     = -1.822865
```

这说明 HIGH_PRIORITY 不是生产开关，只是候选调度；最终训练标签必须继续使用 paired A/B trajectory ROI。

## 5/10 No-Regression

本轮 runbook 的 5/10 sentinel 仍为 OPTIMAL：

```text
task005:
  status = OPTIMAL
  primal = dual = 284.084294
  solving_time = 0.425185s

task010:
  status = OPTIMAL
  primal = dual = 456.756326
  solving_time = 3.197955s
```

## 内存

20-task A/B 使用并行 4。批量运行后：

```text
MemAvailable ≈ 12GiB
Swap used ≈ 780KiB
```

本轮没有触及内存风险线。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_worker_roi_knn_ood \
BPC_future.tests.test_gat_worker_roi_solver_ab_runbook \
BPC_future.tests.test_gat_worker_roi_graph_dataset \
BPC_future.tests.test_gat_worker_roi_training
```

结果：

```text
Ran 8 tests in 0.137s
OK
```

语法与格式：

```text
py_compile: OK
git diff --check: OK
```

## 结论

本轮不是证明 GAT 已可生产，而是证明了标签链路已经从“可能 no-op / trace 错误”修正为真实 paired worker A/B。

当前状态：

- GAT 仍不是 pricing oracle；
- kNN/OOD 仍只是安全壳；
- HIGH_PRIORITY 仍只是调度优先级；
- DELAY_QUEUE 仍不能永久丢弃 true-RC negative；
- 不产生 certificate；
- 不影响 official lower bound；
- 还不能默认启用。

下一步应继续扩大真实 paired ROI 样本，而不是用 GAT 分数或 `rc` 伪造标签。
