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
planned_context_count = 3
selected_context_count = 2
pairwise_context_target_count = 2
candidate_count = 6
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
  "candidate_count": 6,
  "candidate_family_region_counts": {
    "random-wave|tranquillitatis_balmer_like_20km": 6
  },
  "candidate_impact_bucket_counts": {
    "new_support_changing": 4,
    "new_task_set": 2
  },
  "candidate_selection_ranking_counts": {
    "active_replacement": 2,
    "best_rc": 2,
    "impact": 2
  },
  "candidate_task_count_counts": {
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
    50
  ],
  "pairwise_context_target_count": 2,
  "require_opportunity_context": true,
  "selected_context_count": 2,
  "skipped_counts": {
    "not_enough_unique_negative_targets": 1
  }
}
```

## 下一步命令

先生成 guarded worker A/B runbook；实际运行仍是显式 opt-in：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## Worker A/B Runbook 状态

上述命令已生成 runbook：

```text
runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook.md
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook/summary.json

status = ready
worker_method = target_materialization_fixed
worker_batch_size = 1
input_candidate_count = 6
candidate_group_count = 6
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

runbook 的 policy 仍是采样/调度语义：

```text
gat_role = embedding_and_trajectory_impact_expression
knn_ood_role = safety_shell
safe_negative_action = HIGH_PRIORITY
unsafe_negative_action = DELAY_QUEUE
negative_discard_allowed = false
certificate_effect = false
fixed_worker_scope =
  same-context target materialization only;
  no Pulse search, harvest, archive, adaptive sharding, bound pruning,
  or certificate effect
```

注意：生成 runbook 不等于已经运行 worker A/B。下一步必须显式运行 runbook 中的
baseline / target worker commands，随后用
`BPC_future/scripts/build_gat_multibatch_worker_batch_impact_rows.py` 把 reachability、
target causal match、RMP trajectory 和 tail-risk 结果转成训练 rows。

## 边界

- 候选只用于补 same-context 多 batch intervention 数据；
- 候选必须是 materialized true-RC negative，但这不等于它可以跳过 exact pricing；
- worker 跑完前不能把这些候选当训练标签；必须确认 expected context reachability 与 target causal match；
- 失败或低 ROI 的 true-RC negative 只能进入 DELAY_QUEUE/诊断样本，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing closure。
