# 2026-06-17 BPC_future GAT Target Mode Stage 3 v105 Coverage-constrained Frontier 报告

## 结论

本报告只做离线 Stage 3 frontier 审计，不运行 BPC、pricing、RMP、worker 或 certificate。
目标是回答：现有 v99/v102/v103 logits 中是否存在同时满足 safety 和 high-ROI family coverage 的阈值面。

```text
run_count = 3
coverage_constraint_pass_run_count = 0
coverage_constrained_gate_pass_run_count = 0
coverage_constraint_pass_runs = []
coverage_constrained_gate_pass_runs = []
recommended_next_step = collect_or_train_sector_wave_context_local_high_roi_repair_before_more_global_sweeps
stage3_completed = false
stage4_candidate_ready = false
selector_can_certificate = false
```

## Constraints

```json
{
  "max_accepted_bad_mode_count": 0,
  "max_false_high_priority_on_delay": 0.01,
  "max_false_safe_rate_union": 0.01,
  "min_accepted_batch_count": 1,
  "min_family_accepted_high_roi_count": 1,
  "min_family_high_roi_capture_rate": 0.0,
  "min_safe_precision_ci_low": 0.85,
  "required_high_roi_families": [
    "sector-wave"
  ]
}
```

## Run Comparison

| run | threshold local pass | coverage pass | coverage+gate pass | best accepted | best safe CI | best ROI CI | best false-safe | sector accepted high-ROI | best coverage reject |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| v99 | 0 | 0 | 0 | 54 | 0.9336 | 1.6050 | 1.0000 | 18 | ['false_high_priority_on_delay_above_coverage_limit', 'false_safe_rate_union_above_coverage_limit'] |
| v102 | 0 | 0 | 0 | 18 | 0.8241 | 0.2997 | 0.0000 | 3 | ['safe_precision_ci_low_below_coverage_limit'] |
| v103 | 0 | 0 | 0 | 19 | 0.8318 | 0.2780 | 0.0000 | 3 | ['safe_precision_ci_low_below_coverage_limit'] |

## Best Candidate Snapshots

### v99

```json
{
  "best_coverage_candidate": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 54,
    "accepted_batch_rate": 0.7397260273972602,
    "accepted_batch_roi": 3.6421064379890056,
    "accepted_batch_roi_ci_low": 1.604991839953049,
    "accepted_high_roi_family_count": 2,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "high_priority",
    "candidate_delay_gate_enabled": false,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 0.0,
    "candidate_threshold": 0.0,
    "coverage_constrained_gate_pass": false,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "false_high_priority_on_delay_above_coverage_limit",
      "false_safe_rate_union_above_coverage_limit"
    ],
    "false_high_priority_on_delay": 1.0,
    "false_safe_rate_union": 1.0,
    "family_holdout_min_accepted_high_roi_count": 2,
    "family_holdout_min_accepted_roi": 0.15810342626225196,
    "family_holdout_min_high_roi_capture_rate": 1.0,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_snapshot": {
      "greedy-anchor": {
        "accepted_batch_count": 14,
        "accepted_batch_roi": 0.15810342626225196,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.3729059570892291,
        "accepted_high_roi_count": 2,
        "high_roi_capture_rate": 1.0,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0
      },
      "sector-wave": {
        "accepted_batch_count": 29,
        "accepted_batch_roi": 6.564080488129423,
        "accepted_high_roi_count": 18,
        "high_roi_capture_rate": 1.0,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0
      }
    },
    "high_priority_precision": 0.9046052631578947,
    "high_priority_precision_ci_low": 0.883806985243981,
    "oracle_high_roi_family_count": 2,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9335841332189981,
    "sector_wave_accepted_high_roi_count": 18,
    "sector_wave_high_roi_capture_rate": 1.0,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "candidate_threshold_zero_disables_candidate_head_filter",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "best_coverage_constrained_gate_candidate": {},
  "coverage_constrained_gate_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v99_coverage_constrained_gate_candidates.jsonl",
  "coverage_reject_reason_counts": {
    "accepted_batch_count_below_coverage_limit": 1797,
    "false_high_priority_on_delay_above_coverage_limit": 10720,
    "false_safe_rate_union_above_coverage_limit": 10720,
    "family_high_roi_capture_count_below_limit:random-wave": 4617,
    "family_high_roi_capture_count_below_limit:sector-wave": 2452,
    "required_high_roi_family_zero_capture:sector-wave": 2452,
    "safe_precision_ci_low_below_coverage_limit": 9177
  },
  "top_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v99_coverage_top_candidates.jsonl"
}
```

### v102

```json
{
  "best_coverage_candidate": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 18,
    "accepted_batch_rate": 0.2465753424657534,
    "accepted_batch_roi": 0.5027831030181713,
    "accepted_batch_roi_ci_low": 0.2997363556908496,
    "accepted_high_roi_family_count": 2,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 2.0,
    "candidate_threshold": 0.15007750573798778,
    "coverage_constrained_gate_pass": false,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "safe_precision_ci_low_below_coverage_limit"
    ],
    "false_high_priority_on_delay": 0.0,
    "false_safe_rate_union": 0.0,
    "family_holdout_min_accepted_high_roi_count": 2,
    "family_holdout_min_accepted_roi": 0.0680497953047355,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_snapshot": {
      "greedy-anchor": {
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.0680497953047355,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0
      },
      "random-wave": {
        "accepted_batch_count": 6,
        "accepted_batch_roi": 0.6179059656957785,
        "accepted_high_roi_count": 2,
        "high_roi_capture_rate": 1.0,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0
      },
      "sector-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 0.5709456304709116,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.16666666666666666,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0
      }
    },
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9933054696627083,
    "oracle_high_roi_family_count": 2,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8241154494176252,
    "sector_wave_accepted_high_roi_count": 3,
    "sector_wave_high_roi_capture_rate": 0.16666666666666666,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "best_coverage_constrained_gate_candidate": {},
  "coverage_constrained_gate_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v102_coverage_constrained_gate_candidates.jsonl",
  "coverage_reject_reason_counts": {
    "accepted_batch_count_below_coverage_limit": 3566,
    "false_high_priority_on_delay_above_coverage_limit": 8774,
    "false_safe_rate_union_above_coverage_limit": 8774,
    "family_high_roi_capture_count_below_limit:random-wave": 5189,
    "family_high_roi_capture_count_below_limit:sector-wave": 10668,
    "required_high_roi_family_zero_capture:sector-wave": 10668,
    "safe_precision_ci_low_below_coverage_limit": 24941
  },
  "top_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v102_coverage_top_candidates.jsonl"
}
```

### v103

```json
{
  "best_coverage_candidate": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 19,
    "accepted_batch_rate": 0.2602739726027397,
    "accepted_batch_roi": 0.47668465815092387,
    "accepted_batch_roi_ci_low": 0.277958020798426,
    "accepted_high_roi_family_count": 2,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.6,
    "candidate_delay_score_penalty": 1.0,
    "candidate_threshold": 0.24574109176330694,
    "coverage_constrained_gate_pass": false,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "safe_precision_ci_low_below_coverage_limit"
    ],
    "false_high_priority_on_delay": 0.0,
    "false_safe_rate_union": 0.0,
    "family_holdout_min_accepted_high_roi_count": 2,
    "family_holdout_min_accepted_roi": 0.06713869329541922,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_snapshot": {
      "greedy-anchor": {
        "accepted_batch_count": 2,
        "accepted_batch_roi": 0.06713869329541922,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0
      },
      "random-wave": {
        "accepted_batch_count": 7,
        "accepted_batch_roi": 0.5380898836467948,
        "accepted_high_roi_count": 2,
        "high_roi_capture_rate": 1.0,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0
      },
      "sector-wave": {
        "accepted_batch_count": 10,
        "accepted_batch_roi": 0.5156101932749152,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.16666666666666666,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0
      }
    },
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9936695177126947,
    "oracle_high_roi_family_count": 2,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8318156346315495,
    "sector_wave_accepted_high_roi_count": 3,
    "sector_wave_high_roi_capture_rate": 0.16666666666666666,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "best_coverage_constrained_gate_candidate": {},
  "coverage_constrained_gate_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v103_coverage_constrained_gate_candidates.jsonl",
  "coverage_reject_reason_counts": {
    "accepted_batch_count_below_coverage_limit": 7919,
    "false_high_priority_on_delay_above_coverage_limit": 6336,
    "false_safe_rate_union_above_coverage_limit": 6336,
    "family_high_roi_capture_count_below_limit:random-wave": 12007,
    "family_high_roi_capture_count_below_limit:sector-wave": 9790,
    "required_high_roi_family_zero_capture:sector-wave": 9790,
    "safe_precision_ci_low_below_coverage_limit": 15712
  },
  "top_candidates_path": "BPC_future/results/gat_batch_impact_coverage_constrained_frontier_v105_v99_v102_v103_20260617/v103_coverage_top_candidates.jsonl"
}
```

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

`DELAY_QUEUE` 只能有限延迟 true-RC negative，不能永久丢弃。即使本审计找到可行 frontier，最终 certificate 仍只能由当前 branch/cut/dual 下的 exact pricing full no-negative closure 给出。
