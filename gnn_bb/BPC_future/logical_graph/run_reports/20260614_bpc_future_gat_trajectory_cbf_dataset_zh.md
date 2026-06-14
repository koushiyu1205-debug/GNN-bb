# GAT Trajectory CBF Dataset 构造报告

日期：2026-06-14

## 目的

把现有 H=2 CBF trajectory rows 与 `journey_counterfactual_replay_capture`
事件对齐，生成离线 GAT 样本。该数据集用于后续训练 trajectory / residual-family
embedding 或 impact/barrier head，不运行 BPC / pricing / RMP，不生成列，不产生
certificate 或 official lower bound。

## 实现

新增脚本：

```text
BPC_future/scripts/build_gat_trajectory_cbf_dataset.py
```

输入：

```text
BPC_future/results/cbf_trajectory_gate_dataset_global_all_h2_20260614/cbf_trajectory_gate_transitions.jsonl
```

输出：

```text
BPC_future/data/gat_trajectory_cbf/v1/summary.json
BPC_future/data/gat_trajectory_cbf/v1/manifest.json
BPC_future/data/gat_trajectory_cbf/v1/samples/*.pt
```

## 结果

```text
schema_version = gat_trajectory_cbf_dataset_summary_v1
all_checks_pass = true
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
sample_count = 136
candidate_count = 1599
instance_count = 23
label_counts = {add: 34, skip: 102}
has_mixed_horizon_labels = true
skipped_counts = {invalid_logical_graph: 3}
```

`add` / `skip` 这里不是旧 column-level immediate impact 标签，而是
`label_horizon_cbf_feasible` 的 batch-level H=2 轨迹标签，广播到该 capture
事件中的 returned candidate journeys。该语义只用于训练 trajectory-aware
embedding / barrier head，不能解释为单列可直接加入 RMP。

## 当前边界

- 已有 trajectory-labeled GAT 数据集；
- 还没有用该数据集训练新的 horizon CBF checkpoint；
- 旧 `context_aware_column_selector.pt` 仍是 add/skip/abstain column selector；
- GAT readiness audit 因此仍为 `embedding_candidate_ready=false`；
- 后续必须训练 horizon checkpoint 并通过 kNN/OOD 独立验证后，才可进入
  audit-only online smoke。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_trajectory_cbf_dataset \
BPC_future.tests.test_gat_cbf_knn_ood_readiness
```

结果：

```text
Ran 3 tests in 0.013s
OK
```
