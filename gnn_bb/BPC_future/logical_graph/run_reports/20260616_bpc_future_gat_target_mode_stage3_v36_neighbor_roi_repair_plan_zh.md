# 2026-06-16 BPC_future GAT Target Mode Stage 3 v36 Neighbor ROI Repair Plan 报告

## 结论

v36 是离线 repair-plan，不是 Stage 4 candidate，也不运行 BPC / pricing / RMP / worker / certificate。
它把 v35 的 ROI-neighbor blocker 拆成两个可执行队列：

- `roi_neighbor_delayed_high_roi`：被 ROI-neighbor shell 延迟、但真实 trajectory ROI 已过线的样本；
- `accepted_high_point_roi_unstable`：被接受且 point ROI 高、但需要继续做 context/outlier 分解的样本。

```text
source_record_count = 238
repair_candidate_count = 16
context_repair_count = 6
roi_neighbor_delayed_high_roi_count = 3
accepted_high_point_roi_unstable_count = 13
stage4_candidate_ready = false
```

## Top Contexts

| context | family | task | delayed high ROI | accepted high point ROI | max ROI | median ROI | action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| b6d808ebac2a6dd8 | sector-wave | 20 | 0 | 4 | 41.3185 | 2.5880 | audit_outlier_context_and_add_local_negative_contrast |
| 9fadf4f7b39742a2 | sector-wave | 20 | 1 | 4 | 27.3673 | 11.6142 | collect_same_context_contrast_and_audit_accepted_outliers |
| 79fde658840fe2b8 | sector-wave | 20 | 1 | 1 | 0.7734 | 0.7734 | collect_same_context_contrast_and_audit_accepted_outliers |
| 5751b1799b606ad1 | random-wave | 50 | 1 | 0 | 1.2014 | 1.2014 | collect_same_context_positive_negative_contrast_or_repair_embedding_neighbors |
| 9f80ae35ea87da5b | random-wave | 30 | 0 | 2 | 1.1060 | 1.1060 | audit_outlier_context_and_add_local_negative_contrast |
| ac15bc4e7e3d6fff | sector-wave | 20 | 0 | 2 | 0.8095 | 0.8095 | audit_outlier_context_and_add_local_negative_contrast |

## 判断

这批样本不支持继续全局放宽 threshold / rescue window。下一步应围绕 top contexts 做 narrow same-context contrast，
并把训练目标补成 ROI-neighborhood stability / context-local ROI ranking，而不是用 true-RC 命中率替代 trajectory ROI。

## Exact-safe Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
official_bound_effect = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT / CBF / kNN / OOD 只能做 discovery ordering 和 finite-delay admission scheduling。
最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive closure。

## 产物

```text
summary = BPC_future/results/gat_batch_impact_neighbor_roi_repair_plan_v36_20260616/summary.json
repair_candidates = BPC_future/results/gat_batch_impact_neighbor_roi_repair_plan_v36_20260616/repair_candidates.jsonl
context_repair_priority = BPC_future/results/gat_batch_impact_neighbor_roi_repair_plan_v36_20260616/context_repair_priority.jsonl
```

## 下一步

围绕 delayed high-ROI contexts 构建 narrow same-context contrast tranche，再加入 ROI-neighborhood stability 诊断后重训；在此之前不要进入 Stage 4 replay。
