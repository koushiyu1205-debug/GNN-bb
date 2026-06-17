# GAT Target-Priority Worker A/B 首批子集报告

日期：2026-06-16

## 目的

missed high-ROI 的分数差距已经显示这不是简单阈值问题。这里从完整
 multi-batch intervention candidates 中筛出一个可控首批子集，先验证
 fixed target materialization worker 是否能在同一 RMP context 命中目标并产生
可用于下一轮数据闭环的 same-context A/B 标签。

该脚本只生成子集和 runbook 生成命令，不运行 BPC / pricing / RMP / worker，
不改变 admission，也不参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook_subset = current
status = ready
source_candidate_count = 26
eligible_context_count = 9
selected_context_count = 3
candidate_count = 8
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
    "5751b1799b606ad1": 3,
    "9fadf4f7b39742a2": 3,
    "ce3508e12ad69da7": 2
  },
  "candidate_count": 8,
  "candidate_family_counts": {
    "random-wave": 3,
    "sector-wave": 5
  },
  "candidate_task_count_counts": {
    "20": 5,
    "50": 3
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
  "exclude_context_hashes": [],
  "selected_context_count": 3,
  "skipped_counts": {
    "after_context_limit": 18
  }
}
```

## Selected Contexts

```json
[
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -11.539468769,
    "candidate_count": 3,
    "context_hash": "5751b1799b606ad1",
    "context_priority_actions": [
      "collect_same_context_positive_negative_contrast"
    ],
    "families": [
      "random-wave"
    ],
    "max_context_priority_score": 43.38562488555908,
    "max_opportunity_score": 4.385624885559082,
    "missed_high_roi": true,
    "task_counts": [
      50
    ]
  },
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -59.766543,
    "candidate_count": 3,
    "context_hash": "9fadf4f7b39742a2",
    "context_priority_actions": [
      "collect_same_context_positive_negative_contrast"
    ],
    "families": [
      "sector-wave"
    ],
    "max_context_priority_score": 40.0,
    "max_opportunity_score": 11.614195823669434,
    "missed_high_roi": true,
    "task_counts": [
      20
    ]
  },
  {
    "available_candidate_count": 2,
    "best_true_reduced_cost": -8.646581,
    "candidate_count": 2,
    "context_hash": "ce3508e12ad69da7",
    "context_priority_actions": [
      "collect_same_context_positive_negative_contrast"
    ],
    "families": [
      "sector-wave"
    ],
    "max_context_priority_score": 31.105406045913696,
    "max_opportunity_score": 2.1054060459136963,
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
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_first_tranche_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_first_tranche_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_first_tranche_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## 边界

- 子集只用于控制首批 A/B 运行规模；不是最终 Stage 4/Stage 5 结论；
- worker 跑完前不能把这些候选写成训练标签；
- true-RC negative 仍可能拖慢 RMP，失败样本进入 DELAY_QUEUE/诊断，不可永久丢弃；
- 最终 no-negative certificate 只能由当前 branch/cut/dual 下的 exact pricing closure 给出。
