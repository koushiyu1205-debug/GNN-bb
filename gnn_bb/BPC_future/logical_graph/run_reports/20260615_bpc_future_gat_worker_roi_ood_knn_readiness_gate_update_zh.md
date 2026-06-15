# GAT Worker ROI OOD/kNN Readiness Gate 更新报告

日期：2026-06-15

## 目标

本轮只收紧 GAT worker-ROI 的离线安全壳审计，不运行 BPC、pricing、RMP、worker，也不产生 certificate 或 official lower bound。

核心目标是把 OOD/kNN 从普通分类指标中拆出来，单独检查：

- `safe_precision`
- `false_safe_rate_ood`
- `false_safe_rate_knn_unsafe`
- `false_safe_rate_label_unsafe`
- `false_safe_rate_union`
- `coverage`
- `delay_rate`
- `accepted_batch_count`
- `accepted_batch_roi`
- `harmful_batch_recall`
- `false_positive_context_count`

## 实现摘要

### 1. Worker-ROI OOD/kNN 生产化门槛收紧

`BPC_future/scripts/audit_gat_worker_roi_knn_ood.py` 现在显式检查：

- `precision >= 0.95`
- `recall >= 0.65`
- `F0.5 >= 0.90`
- `max false-safe rate <= 0.02`
- `false_positive_context_count <= 0`
- OOD / kNN unsafe / label unsafe / union 四类 false-safe 分开统计

其中 `validation_candidate_ready` 不再只看普通分类召回或 F1。

### 2. 分组 safety shell

worker-ROI OOD/kNN 新增：

- `--threshold-grouping global|scale|family|scale_family`
- `--threshold-selection calibrated|zero_fp`

默认仍使用训练得到的 calibrated threshold，避免 zero-FP threshold 过度保守。

分组壳只影响安全半径和邻域；稀疏或单标签 group 会回退 global guard。

### 3. Same-run batch-impact 对齐

`BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py` 同步增加：

- high-priority `F0.5`
- false-positive context 统计
- OOD / kNN / label / union false-safe 分开统计
- 更严格的 validation safety checks

## v35 focal-hard 复审结果

| safety shell | validation HP | validation false-safe max | validation harmful recall | validation coverage | all-scope HP | all-scope precision | all-scope recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| global | 0 | 0.0 | 1.0 | 1.000 | 7 | 1.0 | 0.1167 |
| scale | 0 | 0.0 | 1.0 | 1.000 | 7 | 1.0 | 0.1167 |
| family | 0 | 0.0 | 1.0 | 0.955 | 8 | 1.0 | 0.1333 |
| scale_family | 0 | 0.0 | 1.0 | 0.955 | 8 | 1.0 | 0.1333 |

## 结论

当前 v35 的问题不是 OOD/kNN false-safe 太高，而是 safety shell 对 validation 正 ROI 全部 delay：

- validation `false-safe = 0`
- validation `harmful_batch_recall = 1`
- validation `accepted_batch_count = 0`
- validation `recall = 0`

分 family / scale 校准后，all-scope recall 略有改善，但 validation 仍然没有 HIGH_PRIORITY。

这说明当前 GAT embedding / 数据分布还不能把 holdout 正 ROI 放进安全邻域。下一步不应该继续放松 OOD/kNN 阈值，而应该采集或构造真正能进入 active support、降低后续 retry / objective tail 的 trajectory-positive 样本。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_worker_roi_knn_ood \
BPC_future.tests.test_gat_same_run_batch_impact_knn_ood
```

结果：

```text
Ran 5 tests in 0.149s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/audit_gat_worker_roi_knn_ood.py \
BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py \
BPC_future/tests/test_gat_worker_roi_knn_ood.py \
BPC_future/tests/test_gat_same_run_batch_impact_knn_ood.py
```

结果：通过。
