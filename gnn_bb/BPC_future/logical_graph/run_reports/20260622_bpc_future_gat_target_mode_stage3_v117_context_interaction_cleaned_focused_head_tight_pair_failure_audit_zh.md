# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 217
failed_pair_count = 28
strict_pair_pass_rate = 0.8709677419354839
raw_fail_rate = 0.07834101382488479
admission_fail_rate = 0.07834101382488479
delay_risk_fail_rate = 0.12903225806451613
all_failed_heads_near_rate_among_failed = 0.32142857142857145
any_failed_head_deep_rate_among_failed = 0.39285714285714285
signature_overlap_pair_rate = 0.5023041474654378
path_token_jaccard_median = 0.0
primary = pair_passes
recommended_next_step = add_or_repair_context_action_consequence_features_before_more_sweeps
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`217`，失败：`28`。
- near-margin 失败占失败 pair：`0.32142857142857145`。
- deep 失败占失败 pair：`0.39285714285714285`。
- signature overlap pair rate：`0.5023041474654378`。
- 主要诊断：`pair_passes`。

## Recommended Next Step

```json
{
  "avoid": "do_not_continue_blind_multiplier_sweeps",
  "primary": "add_or_repair_context_action_consequence_features_before_more_sweeps",
  "reason": "focused pair failures include non-near mixed/deep margins"
}
```

## Margin Stats

```json
{
  "admission_margin_stats": {
    "count": 217,
    "max": 0.2411818231414814,
    "mean": 0.10351288704034078,
    "median": 0.123396476834366,
    "min": -0.16646382092270995
  },
  "delay_risk_margin_stats": {
    "count": 217,
    "max": 0.36641019582748413,
    "mean": 0.08842761890130109,
    "median": 0.09985697269439697,
    "min": -0.17482593655586243
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 11,
    "mixed_margin_failure": 4,
    "near_margin_loss_tuning_candidate": 1,
    "near_margin_with_shared_signature": 8,
    "pair_passes": 189,
    "shared_signature_confounder": 4
  },
  "raw_margin_stats": {
    "count": 217,
    "max": 0.4801119714975357,
    "mean": 0.1769639635072326,
    "median": 0.20067444443702698,
    "min": -0.30449599027633667
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 8,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 8,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "deep_structural_score_gap": 8,
      "shared_signature_confounder": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 12,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.013333333333333334,
    "min_admission_margin": -0.16646382092270995,
    "min_delay_risk_margin": -0.17482593655586243,
    "min_raw_margin": -0.2617255449295044,
    "pair_count": 12,
    "pair_pass_count": 0,
    "primary": "deep_structural_score_gap",
    "raw_fail_count": 8,
    "signature_overlap_pair_count": 4,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 6,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 6,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.056,
    "min_admission_margin": 0.006040448798433545,
    "min_delay_risk_margin": -0.007346630096435547,
    "min_raw_margin": 0.010534584522247314,
    "pair_count": 15,
    "pair_pass_count": 9,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 1,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "deep_structural_score_gap": 1,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.23636363636363636,
    "min_admission_margin": -0.10136378564346309,
    "min_delay_risk_margin": -0.1019667387008667,
    "min_raw_margin": -0.21205513179302216,
    "pair_count": 5,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.018000694286693764,
    "min_delay_risk_margin": -0.015866756439208984,
    "min_raw_margin": -0.030196577310562134,
    "pair_count": 4,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 2,
    "context_hash": "62c86745ed2b3aaa",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "deep_structural_score_gap": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.15420413478685852,
    "min_delay_risk_margin": -0.15493807196617126,
    "min_raw_margin": -0.30449599027633667,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "deep_structural_score_gap",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "45baa40751a0bf77",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.25,
    "min_admission_margin": 0.015090854743714743,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": 0.034600257873535156,
    "pair_count": 3,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "84ae11479ed592d4",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.012611640350205844,
    "min_delay_risk_margin": -0.011685401201248169,
    "min_raw_margin": -0.01543399691581726,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "9f80ae35ea87da5b",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.015625,
    "min_admission_margin": -0.0031140033758590424,
    "min_delay_risk_margin": -0.0013431906700134277,
    "min_raw_margin": -0.007980972528457642,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 1,
    "task_count": 30
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "be33b2560df0147a",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306|be33b2560df0147a",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0072036107102157465,
    "min_delay_risk_margin": -5.3048133850097656e-05,
    "min_raw_margin": -0.017120182514190674,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 30
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 35
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.037797619047619045,
    "min_admission_margin": 0.07374290866693825,
    "min_delay_risk_margin": 0.0960417091846466,
    "min_raw_margin": 0.106930673122406,
    "pair_count": 35,
    "pair_pass_count": 35,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 17,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v117_context_interaction_cleaned_focused_head_tight_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v117_context_interaction_cleaned_focused_head_tight_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v117_context_interaction_cleaned_focused_head_tight_5000_20260622/focused_pair_failure_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `runs_rmp=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
