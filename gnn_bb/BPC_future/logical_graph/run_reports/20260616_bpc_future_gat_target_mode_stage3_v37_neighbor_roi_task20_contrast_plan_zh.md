# GAT Batch-Impact Multi-Batch Intervention Plan 报告

日期：2026-06-16

## 目的

Stage 3 现在按 precision-constrained ROI maximization 验收，不能只靠单例
context 样本训练普通分类器。本报告生成同一 RMP context 下多个 target
 materialization 候选，用于下一轮 opt-in worker A/B 后形成 same-context
 high-ROI / low-ROI pairwise 监督。

该脚本只读 manifest / opportunity / capture JSONL，不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_multibatch_intervention_plan = current
status = ready
planned_context_count = 4
selected_context_count = 4
pairwise_context_target_count = 4
candidate_count = 16
targets_per_context = 4
min_negative_targets_per_context = 2
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 摘要

```json
{
  "candidate_count": 16,
  "candidate_family_region_counts": {
    "sector-wave|apollo15_20km": 4,
    "sector-wave|tranquillitatis_balmer_like_20km": 12
  },
  "candidate_impact_bucket_counts": {
    "new_support_changing": 13,
    "new_task_set": 2,
    "replacement_like": 1
  },
  "candidate_selection_ranking_counts": {
    "active_replacement": 4,
    "best_rc": 4,
    "diverse": 4,
    "impact": 4
  },
  "candidate_task_count_counts": {
    "20": 16
  },
  "checks": {
    "all_candidate_instances_exist": true,
    "all_candidates_have_arc_targets": true,
    "all_candidates_have_full_capture_context": true,
    "all_candidates_have_full_sortie_traces": true,
    "all_candidates_true_rc_negative": true,
    "diagnostic_only": true,
    "has_candidate": true,
    "has_pairwise_context_targets": true,
    "labels_blocked_until_worker_reachability": true,
    "no_certificate_effect": true,
    "runs_bpc_or_pricing_false": true
  },
  "context_priority_jsonl_paths": [
    "BPC_future/results/gat_batch_impact_neighbor_roi_repair_plan_v36_20260616/context_repair_priority.jsonl"
  ],
  "context_priority_row_count": 6,
  "include_families": [],
  "include_task_counts": [
    20
  ],
  "pairwise_context_target_count": 4,
  "require_opportunity_context": true,
  "selected_context_count": 4,
  "skipped_counts": {},
  "split_instance_count": 0,
  "split_mode": "all"
}
```

## Selected Contexts

| context | task | opportunity | delayed high ROI | accepted high point ROI | targets | unique negatives | action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| b6d808ebac2a6dd8 | 20 | 41.3185 | 0 | 4 | 4 | 25 | audit_outlier_context_and_add_local_negative_contrast |
| 9fadf4f7b39742a2 | 20 | 27.3673 | 1 | 4 | 4 | 32 | collect_same_context_contrast_and_audit_accepted_outliers |
| 79fde658840fe2b8 | 20 | 0.7734 | 1 | 1 | 4 | 32 | collect_same_context_contrast_and_audit_accepted_outliers |
| ac15bc4e7e3d6fff | 20 | 0.8095 | 0 | 2 | 4 | 32 | audit_outlier_context_and_add_local_negative_contrast |

## 下一步命令

先生成 guarded worker A/B runbook；实际运行仍是显式 opt-in：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## 边界

- 候选只用于补 same-context 多 batch intervention 数据；
- 候选必须是 materialized true-RC negative，但这不等于它可以跳过 exact pricing；
- worker 跑完前不能把这些候选当训练标签；必须确认 expected context reachability 与 target causal match；
- 失败或低 ROI 的 true-RC negative 只能进入 DELAY_QUEUE/诊断样本，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing closure。
