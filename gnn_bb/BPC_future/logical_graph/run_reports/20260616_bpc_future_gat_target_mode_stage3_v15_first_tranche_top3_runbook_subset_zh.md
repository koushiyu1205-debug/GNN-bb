# GAT Target-Priority Worker A/B 首批子集报告

日期：2026-06-16

## 目的

v15 missed high-ROI 的分数差距已经显示这不是简单阈值问题。这里从完整
 multi-batch intervention candidates 中筛出一个可控首批子集，先验证
 fixed target materialization worker 是否能在同一 RMP context 命中目标并产生
可用于 v16 的 same-context A/B 标签。

该脚本只生成子集和 runbook 生成命令，不运行 BPC / pricing / RMP / worker，
不改变 admission，也不参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook_subset = current
status = ready
source_candidate_count = 32
eligible_context_count = 11
selected_context_count = 3
candidate_count = 9
max_contexts = 3
min_candidates_per_context = 2
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 摘要

```json
{
  "candidate_context_counts": {
    "45baa40751a0bf77": 3,
    "79fde658840fe2b8": 3,
    "ac15bc4e7e3d6fff": 3
  },
  "candidate_count": 9,
  "candidate_family_counts": {
    "sector-wave": 9
  },
  "candidate_task_count_counts": {
    "20": 9
  },
  "checks": {
    "all_candidates_have_expected_context_hash": true,
    "all_candidates_have_full_capture_context": true,
    "all_candidates_have_target_sequences": true,
    "all_candidates_true_rc_negative": true,
    "all_selected_contexts_have_min_candidates": true,
    "candidate_count_within_limit": true,
    "diagnostic_only": true,
    "has_candidate": true,
    "labels_blocked_until_worker_reachability": true,
    "no_certificate_effect": true,
    "runs_bpc_or_pricing_false": true,
    "selected_context_count_within_limit": true
  },
  "selected_context_count": 3,
  "skipped_counts": {
    "after_context_limit": 17,
    "not_missed_high_roi_context": 2
  }
}
```

## Selected Contexts

```json
[
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -31.9356514,
    "candidate_count": 3,
    "context_hash": "ac15bc4e7e3d6fff",
    "families": [
      "sector-wave"
    ],
    "max_opportunity_score": 15.120423316955566,
    "missed_high_roi": true,
    "task_counts": [
      20
    ]
  },
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -29.939646,
    "candidate_count": 3,
    "context_hash": "79fde658840fe2b8",
    "families": [
      "sector-wave"
    ],
    "max_opportunity_score": 14.969822883605957,
    "missed_high_roi": true,
    "task_counts": [
      20
    ]
  },
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -13.436328,
    "candidate_count": 3,
    "context_hash": "45baa40751a0bf77",
    "families": [
      "sector-wave"
    ],
    "max_opportunity_score": 13.436327934265137,
    "missed_high_roi": true,
    "task_counts": [
      20
    ]
  }
]
```

## 下一步命令

先生成首批 guarded worker A/B runbook；实际运行仍需显式执行生成的命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## 边界

- 子集只用于控制首批 A/B 运行规模；不是最终 Stage 4/Stage 5 结论；
- worker 跑完前不能把这些候选写成训练标签；
- true-RC negative 仍可能拖慢 RMP，失败样本进入 DELAY_QUEUE/诊断，不可永久丢弃；
- 最终 no-negative certificate 只能由当前 branch/cut/dual 下的 exact pricing closure 给出。
