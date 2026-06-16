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
planned_context_count = 12
selected_context_count = 11
pairwise_context_target_count = 11
candidate_count = 33
targets_per_context = 3
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
  "candidate_count": 33,
  "candidate_family_region_counts": {
    "random-wave|apollo15_20km": 12,
    "random-wave|tranquillitatis_balmer_like_20km": 12,
    "sector-wave|apollo15_20km": 6,
    "sector-wave|tranquillitatis_balmer_like_20km": 3
  },
  "candidate_impact_bucket_counts": {
    "new_support_changing": 22,
    "new_task_set": 3,
    "replacement_like": 8
  },
  "candidate_selection_ranking_counts": {
    "active_replacement": 11,
    "best_rc": 11,
    "impact": 11
  },
  "candidate_task_count_counts": {
    "20": 27,
    "50": 6
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
  "include_task_counts": [
    20,
    50
  ],
  "pairwise_context_target_count": 11,
  "require_opportunity_context": false,
  "selected_context_count": 11,
  "skipped_counts": {
    "not_enough_unique_negative_targets": 1
  },
  "split_instance_count": 40,
  "split_mode": "train"
}
```

## 下一步命令

先生成 guarded worker A/B runbook；实际运行仍是显式 opt-in：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## Runbook 状态

完整 train-split runbook 已生成，但尚未执行正式 BPC commands：

```text
worker_ab_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/worker_ab_runbook.md
worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/worker_ab_runbook/summary.json

status = ready
candidate_group_count = 33
command_count = 68
candidate_task_counts = [20, 50]
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

为避免第一轮 train-side 补样混入 task50 运行成本，已额外筛出 top3 task20
子集并生成 runbook：

```text
subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v16_train_split_top3_task20_runbook_subset_zh.md
subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/summary.json
subset_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/summary.json
subset_dry_run_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/runbook_execution_dry_run_summary.json

selected_context_count = 3
candidate_count = 9
candidate_task_count_counts = {'20': 9}
candidate_family_counts = {'random-wave': 9}
candidate_context_counts =
  {'67c11b5ec80925ec': 3,
   'd519291840dd7000': 3,
   'ddcb5387bef3bf63': 3}
worker_ab_command_count = 20
dry_run_count = 20
all_checks_pass = true
```

这批 top3 task20 是下一轮推荐执行入口。它的目的不是 Stage 4 结论，而是补
train split 的 same-context positive/delay pair；正式运行后仍必须先做 A/B
ROI、reachability、target causal match 和 certificate closure audit。

## 边界

- 候选只用于补 same-context 多 batch intervention 数据；
- 候选必须是 materialized true-RC negative，但这不等于它可以跳过 exact pricing；
- worker 跑完前不能把这些候选当训练标签；必须确认 expected context reachability 与 target causal match；
- 失败或低 ROI 的 true-RC negative 只能进入 DELAY_QUEUE/诊断样本，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing closure。
