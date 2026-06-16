# 2026-06-15 BPC_future GAT Target Mode Stage 2 数据采集报告

## 结论

Stage 2 的 batch-impact 数据结构和离线 builder 已完成，并已用当前 same-context intervention rows 生成真实图样本。

当前结果可以进入离线 diagnostic training / threshold audit，但计划级 Stage 2 覆盖 gate 尚未完全关闭：现有样本全是 task20 `sector-wave`，还没有在 manifest 中覆盖 `random-wave` 和 `greedy-anchor` family。因此本报告不是 production readiness 证明，也不是 online A/B 通过证明。

## 新增/修改文件

- `BPC_future/scripts/build_gat_batch_impact_dataset.py`
  把 same-context intervention rows 转换为 `GATBatchImpactModel` 可读取的 batch-impact 图样本。

- `BPC_future/tests/test_gat_batch_impact_dataset.py`
  覆盖 toy same-context rows -> graph samples -> `GATBatchImpactModel` forward 的完整接口链路。

- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_dataset_zh.md`
  由 builder 自动生成的数据集构建报告。

- `BPC_future/data/gat_batch_impact/v1/`
  当前真实离线 batch-impact dataset artifact。

## 数据语义

每个 sample 对应：

```text
sample = (G, x_t, U_t, y_t)
```

- `G`：logical graph / path-option graph；
- `x_t`：same-context intervention 前的 RMP/context 特征；
- `U_t`：同一上下文返回并真实加入的 candidate journey batch；
- `y_t`：加入该 batch 后的 objective / trajectory / scheduler 标签。

新增关键 tensor：

- `candidate_task_membership`
- `candidate_sequence_positions`
- `candidate_features`
- `context_features`
- `batch_features`
- `y_candidate_high_priority`
- `y_candidate_delay_risk`
- `y_candidate_true_rc_negative`
- `y_batch_roi_positive`
- `y_objective_progress`
- `y_tail_improved`
- `y_bad_mode_switch`
- `y_support_changed_good`
- `y_delta_v`
- `y_barrier_slack`
- `y_accepted_batch_roi`

`candidate_sequence_positions` 是 Stage 1 模型新增的 order-sensitive 输入，用于区分同一 task set 下不同 task order 的候选 journey。

## 真实构建结果

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_batch_impact_dataset.py --input-jsonl BPC_future/results/gat_same_run_batch_impact_dataset_20260615/same_run_batch_impact_rows.jsonl --output-dir BPC_future/data/gat_batch_impact/v1 --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_dataset_zh.md
```

结果：

```text
sample_count = 68
candidate_count = 1410
context_match_rate = 1.0
batch_label_counts = {'non_improving': 12, 'roi_positive': 56}
candidate_label_counts = {'delay_queue': 91, 'high_priority': 1319}
batch_type_counts = {'new_task_set': 65, 'replacement_heavy': 3}
instance_count = 20
region_count = 2
family_counts = {'sector-wave': 68}
task_count_counts = {'20': 68}
training_ready = true
training_blockers = []
all_checks_pass = true
```

注意：这里的 `training_ready=true` 是 builder-level 阈值，表示当前数据可以做离线训练实验；它不等于计划级 Stage 2 全部 gate 关闭。

## Exactness Boundary

数据集 manifest 和 summary 均保持：

```text
diagnostic_only=true
runs_bpc_or_pricing=false
production_ready=false
default_enabled=false
pricing_oracle=false
certificate_source=false
official_bound_effect=false
can_permanently_discard_true_rc_negative=false
delay_queue_replaces_exact_pricing=false
```

因此：

- 该数据只能训练/审计 admission scheduling；
- 不能作为 pricing oracle；
- 不能产生 official lower bound；
- 不能参与 `CERTIFIED_NO_NEGATIVE`；
- true-RC negative 的 non-improving 标签只能进入 DELAY_QUEUE 语义，不能变成永久 reject。

最终证明仍必须由当前 branch/cut/dual 下的 exact pricing 全宇宙 closure 完成。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_dataset BPC_future.tests.test_gat_batch_impact_model
```

结果：

```text
Ran 6 tests in 0.089s
OK
```

`git diff --check` 已通过。

真实样本字段抽检：

```text
sample_count = 68
candidate_count = 1410
candidate_shape = (32, 20), (32, 20), (32, 14)
context_shape = (26,)
batch_shape = (18,)
finite = True
```

## 未关闭的 Stage 2 Gate

- 缺少 `random-wave` family；
- 缺少 `greedy-anchor` family；
- 当前 manifest 只证明 task20 `sector-wave`；
- 尚未证明 5/10 capture-only official result 完全一致；
- 尚未把 family/context holdout split 固化到训练脚本；
- 尚未做 kNN/OOD holdout 审计；
- 尚未做 shadow / opt-in online A/B。

## 下一步

进入 Stage 3 前应先补齐两件事：

1. 继续采集 task20 `random-wave` 和 `greedy-anchor` same-context intervention rows，使 Stage 2 family coverage gate 可审计。
2. 写 `train_gat_batch_impact.py`，checkpoint selection 必须按 precision / accepted batch ROI / false-safe / coverage 硬门槛执行，不能只按 loss、F1 或 recall。
