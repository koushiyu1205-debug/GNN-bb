# BPC_future GAT 上下文加列选择器 Phase 1 报告

日期：2026-06-14

## 目标

本轮开始把已有 GAT 从 dual-anchor heuristic 扩展为上下文感知的加列选择器。

定位明确为：

```text
GAT = RMP-impact predictor / column add selector
GAT != pricing oracle
GAT != certificate source
GAT != official lower-bound source
```

所有候选列仍必须通过现有 `TimedTrip` / `JourneyColumn` 物化、`manual_journey_reduced_cost()` true-RC 校验和 exact final judge 证书语义。

## 实现内容

### 1. 复用现有 GAT 编码器

修改：

- `BPC_future/learning/gnn_model.py`

新增：

- `HierarchicalOptionGAT.encode(data)`

它返回：

- `node_h`
- `initial_node_h`
- `task_h`
- `initial_task_h`
- `pair_edge_attr`
- option attention / entropy / pooling diagnostics

原来的 dual-anchor `forward()` 仍保持兼容。

### 2. 新增上下文加列选择器

新增：

- `BPC_future/learning/column_selector.py`

核心类：

- `ContextAwareColumnSelector`

输入：

- 逻辑图 GAT encoding；
- candidate task-membership mask；
- candidate-local features；
- RMP / pool / active-basis / dual trajectory context features。

输出：

```text
skip / add / abstain logits
```

这为后续 conservative selector 提供接口：不确定时可 `abstain`，保护 5/10 no-regression。

### 3. 离线数据集构建脚本

新增：

- `BPC_future/scripts/build_gnn_column_selector_dataset.py`

默认读取：

- `BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv`

输出：

- `BPC_future/data/column_selector/v1/manifest.json`
- `BPC_future/data/column_selector/v1/summary.json`
- `BPC_future/data/column_selector/v1/samples/*.pt`

本轮生成结果：

```json
{
  "sample_count": 253,
  "label_counts": {
    "add": 183,
    "skip": 70
  },
  "instance_count": 2,
  "skipped_counts": {
    "missing_logical_graph": 27
  },
  "runs_bpc_or_pricing": false,
  "all_checks_pass": true
}
```

### 4. 离线训练脚本

新增：

- `BPC_future/scripts/train_gnn_column_selector.py`

本轮训练命令使用 10 epoch、CPU、小模型配置，输出：

- `BPC_future/data/column_selector/v1/context_aware_column_selector.pt`
- `BPC_future/results/gnn_column_selector_training_20260614/summary.json`

训练摘要：

```json
{
  "sample_count": 253,
  "train_count": 90,
  "validation_count": 163,
  "best_validation_loss": 0.40007823934504316,
  "validation_metrics": {
    "accuracy": 0.8404907975460123,
    "add_precision": 0.8309859154929577,
    "add_recall": 0.9833333333333333,
    "confusion": [
      [19, 24, 0],
      [2, 118, 0],
      [0, 0, 0]
    ]
  },
  "selector_is_pricing_oracle": false,
  "selector_can_certificate": false
}
```

## 当前解释

这一步已经把 GAT 改造成“可训练的上下文加列选择器”雏形。

但当前模型还不能作为 production gate：

- 数据只有 2 个 20-task instance；
- validation 仍有 `24` 个 skip 被预测为 add；
- 还没有 5/10 no-regression A/B；
- 还没有 20/30/50/100 speedup A/B；
- 还没有接 solver online trigger；
- 还没有 full context / instance / dataset holdout。

因此当前 checkpoint 只是离线实验产物，不允许默认启用。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_learning_components.ContextAwareColumnSelectorTests \
BPC_future.tests.test_learning_components.LearningModelTests \
BPC_future.tests.test_learning_components.LearningDatasetBuilderTests.test_gnn_column_selector_dataset_builder_writes_exactness_metadata \
BPC_future.tests.test_learning_components.LearningDatasetBuilderTests.test_gnn_column_selector_label_and_task_set_helpers
```

结果：

```text
Ran 6 tests in 0.061s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/tests/test_learning_components.py \
BPC_future/scripts/build_gnn_column_selector_dataset.py \
BPC_future/scripts/train_gnn_column_selector.py \
BPC_future/learning/column_selector.py \
BPC_future/learning/gnn_model.py
```

结果：通过。

## 下一步

1. 扩展训练数据到更多 no-certificate-effect full-snapshot / component-payload contexts；
2. 加 context / instance / dataset holdout 评估脚本；
3. 加 conservative threshold：高置信 add、低置信 abstain；
4. 只在 opt-in worker path 中做 audit-only online scoring；
5. 先证明 5/10 不触发或无退化，再测 selected 20 hard cases；
6. 目标仍未完成，不能标记为 production optimization。
