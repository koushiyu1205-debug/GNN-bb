# CBF Gate Family-aware Policy 审计报告

日期：2026-06-14

## 目的

审计 `(task_count, family)` 分层的 CBF/RMP-impact gate。小规模仍强制
abstain；20 规模内每个 family 必须通过 within-family leave-one-instance
安全审计，才能作为后续 production A/B 候选。本脚本只读离线数据。

## 机器字段

```text
cbf_gate_family_policy_audit = current
status = cbf_gate_family_policy_audited
diagnostic_only = true
runs_bpc_or_pricing = false
family_policy_ready = false
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "family_policy_ready": false,
  "family_results": [
    {
      "family": "very_small",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 5,
      "status": "guarded_abstain_below_min_task_count",
      "task_count": 4
    },
    {
      "family": "moon_trek_tasks10",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 4,
      "status": "guarded_abstain_below_min_task_count",
      "task_count": 10
    },
    {
      "family": "greedy-anchor",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 4,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 3,
        "fold_count": 7,
        "productive_fold_count": 4,
        "skipped_count": 3,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 3
        }
      },
      "must_abstain": true,
      "row_count": 154,
      "status": "family_gate_not_ready",
      "task_count": 20
    },
    {
      "family": "moon_trek_tasks20",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 3,
      "status": "insufficient_family_rows",
      "task_count": 20
    },
    {
      "family": "random-wave",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 13,
      "status": "insufficient_family_rows",
      "task_count": 20
    },
    {
      "family": "sector-wave",
      "family_gate_candidate_ready": false,
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 6,
      "status": "insufficient_family_rows",
      "task_count": 20
    }
  ],
  "label_counts": {
    "0": 152,
    "1": 33
  },
  "ready_families": [],
  "row_count": 185,
  "task_family_histogram": {
    "10|moon_trek_tasks10": 4,
    "20|greedy-anchor": 154,
    "20|moon_trek_tasks20": 3,
    "20|random-wave": 13,
    "20|sector-wave": 6,
    "4|very_small": 5
  }
}
```

## 解释

- family-aware gate 是比 scale-aware 更细的离线审计，不是 production 接入；
- `family_policy_ready=false` 表示当前没有 family 可进入 production A/B；
- 小规模 family 强制 abstain 是为了保护 5/10 不退化；
- 该策略不影响 certificate，也不能证明 no-negative。
