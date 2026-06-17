# GAT Target Mode Stage 3 v48 v39 False-delay Context Plan 报告

日期：2026-06-16

## 结论

本报告把 v41 false-positive catalog 转成同一 RMP context 的 hard-negative
采样计划。它只生成 context-priority 行和 guarded worker runbook 输入，不运行
BPC、pricing、RMP、worker 或 certificate。

跨版本结论和 v46 一致：v23 证明 coverage 能上去但 false-delay 爆，v24/v28
证明 false-delay 能压住但 coverage / CI 不够，v39/v45 证明两者合并后误放行
复发，v47 又排除了简单 checkpoint selection。下一步应补
`sector-wave|20` context-local false-delay hard negative，而不是继续普通阈值 sweep。

## 机器字段

```text
status = ready
context_priority_row_count = 5
intervention_selected_context_count = 5
intervention_pairwise_context_target_count = 5
intervention_candidate_count = 15
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## v41 输入诊断

```json
{
  "candidate_threshold_zero": true,
  "context_false_positive_count": 5,
  "false_high_priority_on_delay": 0.4489795918367347,
  "false_high_priority_on_delay_count": 44,
  "family_task_counts": {
    "sector-wave|20": 44
  },
  "primary_diagnosis": "raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate"
}
```

## Top Context Priority

| context | family | task | false-delay FP | signatures | batch records | priority | action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| ac056820151e9ad7 | sector-wave | 20 | 33 | 32 | 6 | 33327.0 | collect_same_context_false_delay_hard_negative_contrast |
| b6d808ebac2a6dd8 | sector-wave | 20 | 4 | 4 | 9 | 4054.0 | collect_same_context_false_delay_hard_negative_contrast |
| 79fde658840fe2b8 | sector-wave | 20 | 4 | 3 | 8 | 4042.0 | collect_same_context_false_delay_hard_negative_contrast |
| ac15bc4e7e3d6fff | sector-wave | 20 | 2 | 2 | 8 | 2034.0 | collect_same_context_false_delay_hard_negative_contrast |
| 7b430465c7ae76b3 | sector-wave | 20 | 1 | 1 | 1 | 1011.0 | collect_same_context_false_delay_hard_negative_contrast |

## Intervention Plan 摘要

```json
{
  "candidate_count": 15,
  "checks": {
    "diagnostic_only": true,
    "intervention_checks_pass": true,
    "intervention_does_not_run_bpc_or_pricing": true,
    "intervention_has_candidates": true,
    "no_certificate_effect": true,
    "priority_rows_have_false_delay_contexts": true,
    "source_catalog_diagnostic_only": true,
    "source_catalog_does_not_run_bpc_or_pricing": true
  },
  "pairwise_context_target_count": 5,
  "selected_context_count": 5,
  "skipped_counts": {},
  "status": "ready"
}
```

## 下一步命令

该命令只生成 worker A/B runbook；实际 worker 运行仍需显式 opt-in：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_false_delay_context_plan_v48_v39_20260616/multibatch_intervention_plan/candidates.json --output-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v48_v39_20260616/multibatch_intervention_plan/worker_ab_runbook --report BPC_future/results/gat_batch_impact_false_delay_context_plan_v48_v39_20260616/multibatch_intervention_plan/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## 边界

- 本计划只服务 Stage 3 采样和训练诊断，不是 Stage 4 production gate；
- 选出的候选必须是 materialized true-RC negative，但不能直接成为训练标签；
- worker 跑完前必须验证 expected context reachability 与 target causal match；
- 低 ROI 或拖尾 true-RC negative 只能作为 DELAY_QUEUE / hard-negative 证据，不能永久丢弃；
- 最终 OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下 exact pricing exhaustive closure。
