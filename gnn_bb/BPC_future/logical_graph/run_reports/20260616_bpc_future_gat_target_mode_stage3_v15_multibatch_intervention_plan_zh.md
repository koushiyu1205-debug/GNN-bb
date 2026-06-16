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
candidate_count = 32
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
  "candidate_count": 32,
  "candidate_family_region_counts": {
    "random-wave|tranquillitatis_balmer_like_20km": 6,
    "sector-wave|apollo15_20km": 8,
    "sector-wave|tranquillitatis_balmer_like_20km": 18
  },
  "candidate_impact_bucket_counts": {
    "new_support_changing": 24,
    "new_task_set": 5,
    "replacement_like": 2,
    "support_changing": 1
  },
  "candidate_selection_ranking_counts": {
    "active_replacement": 10,
    "best_rc": 11,
    "impact": 11
  },
  "candidate_task_count_counts": {
    "20": 26,
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
  "require_opportunity_context": true,
  "selected_context_count": 11,
  "skipped_counts": {
    "not_enough_unique_negative_targets": 1
  }
}
```

## 下一步命令

先生成 guarded worker A/B runbook；实际运行仍是显式 opt-in：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## Worker A/B Runbook 状态

上述命令已生成 runbook，但尚未执行 runbook 中的 baseline / target-worker
commands：

```text
worker_ab_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook.md
worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook/summary.json

status = ready
input_candidate_count = 32
candidate_group_count = 32
worker_method = target_materialization_fixed
worker_batch_size = 1
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

runbook 的语义仍是采样 / 诊断：

```text
safe_negative_action = HIGH_PRIORITY
unsafe_negative_action = DELAY_QUEUE
negative_discard_allowed = false
fixed_worker_scope =
  same-context target materialization only;
  no Pulse search, harvest, archive, adaptive sharding, bound pruning,
  or certificate effect
```

下一步如果要把这些 candidate 变成训练 rows，必须先显式运行 runbook 中的
baseline / target-worker commands，再用 A/B audit summary 检查 expected context
reachability、target causal match、trajectory ROI 和 tail-risk。worker 跑完前，
这些 candidate 只能是采样目标，不能作为 `HIGH_PRIORITY` 正例。

## First-Tranche Top-3 Runbook 状态

完整 runbook 有 32 个 candidate A/B group，串行直接跑成本偏高。为避免盲目重跑，
已从 missed high-ROI contexts 中筛出首批 top-3 子集，先验证 worker reachability
和 causal target match：

```text
subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_first_tranche_top3_runbook_subset_zh.md
subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/summary.json
subset_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/summary.json

source_candidate_count = 32
eligible_context_count = 11
selected_context_count = 3
candidate_count = 9
candidate_task_count_counts = {'20': 9}
candidate_family_counts = {'sector-wave': 9}
candidate_context_counts =
  {'45baa40751a0bf77': 3,
   '79fde658840fe2b8': 3,
   'ac15bc4e7e3d6fff': 3}

worker_ab_status = ready
worker_ab_command_count = 20
worker_ab_command_type_counts =
  {'kept_sentinel': 2, 'mainline_baseline': 9, 'target_priority_worker': 9}
worker_method = target_materialization_fixed
worker_batch_size = 1
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

这一步仍然没有运行 BPC。后续先执行这 20 条显式 commands；如果 context reachability
和日志完整性可用，再扩到完整 32 个 candidate runbook。

## 边界

- 候选只用于补 same-context 多 batch intervention 数据；
- 候选必须是 materialized true-RC negative，但这不等于它可以跳过 exact pricing；
- worker 跑完前不能把这些候选当训练标签；必须确认 expected context reachability 与 target causal match；
- 失败或低 ROI 的 true-RC negative 只能进入 DELAY_QUEUE/诊断样本，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing closure。
