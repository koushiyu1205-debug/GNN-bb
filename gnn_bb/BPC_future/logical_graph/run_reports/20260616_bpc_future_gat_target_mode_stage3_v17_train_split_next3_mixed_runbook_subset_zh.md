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
source_candidate_count = 33
eligible_context_count = 8
selected_context_count = 3
candidate_count = 9
max_contexts = 3
min_candidates_per_context = 3
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
    "0df8d5cea7864e69": 3,
    "39e3a497e73941e5": 3,
    "9a2ca522ff49991c": 3
  },
  "candidate_count": 9,
  "candidate_family_counts": {
    "random-wave": 6,
    "sector-wave": 3
  },
  "candidate_task_count_counts": {
    "20": 3,
    "50": 6
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
  "exclude_context_hashes": [
    "67c11b5ec80925ec",
    "d519291840dd7000",
    "ddcb5387bef3bf63"
  ],
  "selected_context_count": 3,
  "skipped_counts": {
    "after_context_limit": 15,
    "excluded_context": 9
  }
}
```

## Selected Contexts

```json
[
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -117.548412,
    "candidate_count": 3,
    "context_hash": "9a2ca522ff49991c",
    "families": [
      "random-wave"
    ],
    "max_opportunity_score": 2.3691615510204067,
    "missed_high_roi": false,
    "task_counts": [
      50
    ]
  },
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -88.177463321,
    "candidate_count": 3,
    "context_hash": "39e3a497e73941e5",
    "families": [
      "random-wave"
    ],
    "max_opportunity_score": 1.6387622040816328,
    "missed_high_roi": false,
    "task_counts": [
      50
    ]
  },
  {
    "available_candidate_count": 3,
    "best_true_reduced_cost": -67.696691,
    "candidate_count": 3,
    "context_hash": "0df8d5cea7864e69",
    "families": [
      "sector-wave"
    ],
    "max_opportunity_score": 1.5335839583333335,
    "missed_high_roi": false,
    "task_counts": [
      20
    ]
  }
]
```

## 下一步命令

先生成首批 guarded worker A/B runbook；实际运行仍需显式执行生成的命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_target_priority_worker_ab_runbook.py --candidates-file BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/candidates.json --output-dir BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook --report BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook.md --worker-method target_materialization_fixed --worker-batch-size 1
```

## 边界

- 子集只用于控制首批 A/B 运行规模；不是最终 Stage 4/Stage 5 结论；
- worker 跑完前不能把这些候选写成训练标签；
- true-RC negative 仍可能拖慢 RMP，失败样本进入 DELAY_QUEUE/诊断，不可永久丢弃；
- 最终 no-negative certificate 只能由当前 branch/cut/dual 下的 exact pricing closure 给出。
