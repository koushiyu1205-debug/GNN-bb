# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 145
failed_pair_count = 81
strict_pair_pass_rate = 0.4413793103448276
raw_fail_rate = 0.4068965517241379
admission_fail_rate = 0.4689655172413793
delay_risk_fail_rate = 0.4
all_failed_heads_near_rate_among_failed = 1.0
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.4689655172413793
path_token_jaccard_median = 0.09259259259259259
primary = pair_passes
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`145`，失败：`81`。
- near-margin 失败占失败 pair：`1.0`。
- deep 失败占失败 pair：`0.0`。
- signature overlap pair rate：`0.4689655172413793`。
- 主要诊断：`pair_passes`。

## Recommended Next Step

```json
{
  "avoid": "do_not_collect_more_data_before_testing_explicit_tranche_full_training",
  "primary": "train_combined_focused_candidate_admission_delay_loss",
  "reason": "most failed focused pairs are near-margin rather than deep structural gaps"
}
```

## Margin Stats

```json
{
  "admission_margin_stats": {
    "count": 145,
    "max": 0.03337130434806451,
    "mean": 0.007870695435809531,
    "median": 9.128862788039538e-05,
    "min": -0.0014677383074586242
  },
  "delay_risk_margin_stats": {
    "count": 145,
    "max": 0.026193439960479736,
    "mean": 0.0068858341924075426,
    "median": 0.000934302806854248,
    "min": -0.0020483732223510742
  },
  "diagnosis_counts": {
    "near_margin_loss_tuning_candidate": 55,
    "near_margin_with_shared_signature": 26,
    "pair_passes": 64
  },
  "raw_margin_stats": {
    "count": 145,
    "max": 0.07424664497375488,
    "mean": 0.01643418916340532,
    "median": 0.0004385709762573242,
    "min": -0.005148053169250488
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 25,
    "all_failed_heads_near_count": 27,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 27,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 19,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 8
    },
    "diagnostic_only": true,
    "failed_pair_count": 27,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2544662993402489,
    "mean_signature_jaccard": 0.1681547619047619,
    "min_admission_margin": -0.000620354893106495,
    "min_delay_risk_margin": -0.0008791685104370117,
    "min_raw_margin": -0.001195073127746582,
    "pair_count": 35,
    "pair_pass_count": 8,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 16,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 22,
    "all_failed_heads_near_count": 26,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 10,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 19,
      "near_margin_with_shared_signature": 7,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 26,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.22936700103770322,
    "mean_signature_jaccard": 0.15089285714285713,
    "min_admission_margin": -0.0014677383074586242,
    "min_delay_risk_margin": -0.00146406888961792,
    "min_raw_margin": -0.005148053169250488,
    "pair_count": 35,
    "pair_pass_count": 9,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 24,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 13,
    "all_failed_heads_near_count": 16,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 11,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 10,
      "near_margin_with_shared_signature": 6,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 16,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2658611111111111,
    "mean_signature_jaccard": 0.2112,
    "min_admission_margin": -0.0009793902226495899,
    "min_delay_risk_margin": -0.0020483732223510742,
    "min_raw_margin": -0.0006276369094848633,
    "pair_count": 25,
    "pair_pass_count": 9,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 10,
    "signature_overlap_pair_count": 12,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 7,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 7,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.27046783625730997,
    "mean_signature_jaccard": 0.2578125,
    "min_admission_margin": -0.0007259553149528281,
    "min_delay_risk_margin": -0.00035136938095092773,
    "min_raw_margin": -0.0024377107620239258,
    "pair_count": 12,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.2730414746543779,
    "mean_signature_jaccard": 0.15584415584415584,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": -6.967782974243164e-05,
    "min_raw_margin": 0.0,
    "pair_count": 7,
    "pair_pass_count": 4,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 2,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "45baa40751a0bf77",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.42857142857142855,
    "mean_signature_jaccard": 0.3333333333333333,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.002393960952758789,
    "pair_count": 3,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 1,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 10
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.032432432432432434,
    "mean_signature_jaccard": 0.008,
    "min_admission_margin": 0.000818169736162791,
    "min_delay_risk_margin": 0.0011504888534545898,
    "min_raw_margin": 0.0010390281677246094,
    "pair_count": 10,
    "pair_pass_count": 10,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 2,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "0df8d5cea7864e69",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.08333333333333334,
    "mean_signature_jaccard": 0.03125,
    "min_admission_margin": 0.030762914740466482,
    "min_delay_risk_margin": 0.02499416470527649,
    "min_raw_margin": 0.0670015811920166,
    "pair_count": 9,
    "pair_pass_count": 9,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 9,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.07407407407407407,
    "mean_signature_jaccard": 0.04,
    "min_admission_margin": 0.023801862664116186,
    "min_delay_risk_margin": 0.022271543741226196,
    "min_raw_margin": 0.047313809394836426,
    "pair_count": 6,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ce3508e12ad69da7",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.1875,
    "mean_signature_jaccard": 0.25,
    "min_admission_margin": 0.0017604603585706785,
    "min_delay_risk_margin": 0.0023044347763061523,
    "min_raw_margin": 0.002409040927886963,
    "pair_count": 2,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 1,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v102_20260617/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v102_20260617/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v102_20260617/focused_pair_failure_contexts.jsonl
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
