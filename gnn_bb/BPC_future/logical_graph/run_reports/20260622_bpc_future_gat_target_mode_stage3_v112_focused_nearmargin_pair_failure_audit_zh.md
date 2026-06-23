# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 384
failed_pair_count = 99
strict_pair_pass_rate = 0.7421875
raw_fail_rate = 0.21614583333333334
admission_fail_rate = 0.21614583333333334
delay_risk_fail_rate = 0.234375
all_failed_heads_near_rate_among_failed = 0.7575757575757576
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.46875
path_token_jaccard_median = 0.0
primary = pair_passes
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`384`，失败：`99`。
- near-margin 失败占失败 pair：`0.7575757575757576`。
- deep 失败占失败 pair：`0.0`。
- signature overlap pair rate：`0.46875`。
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
    "count": 384,
    "max": 0.1669536321581247,
    "mean": 0.03987590126399069,
    "median": 0.011498494649985494,
    "min": -0.03903736382072523
  },
  "delay_risk_margin_stats": {
    "count": 384,
    "max": 0.14647594094276428,
    "mean": 0.034541713539510965,
    "median": 0.01246275007724762,
    "min": -0.037512391805648804
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 15,
    "near_margin_loss_tuning_candidate": 41,
    "near_margin_with_shared_signature": 34,
    "pair_passes": 285,
    "shared_signature_confounder": 9
  },
  "raw_margin_stats": {
    "count": 384,
    "max": 0.18317896127700806,
    "mean": 0.041364007629454136,
    "median": 0.01268334686756134,
    "min": -0.0366939902305603
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 28,
    "all_failed_heads_near_count": 28,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 28,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "near_margin_loss_tuning_candidate": 20,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 19,
      "shared_signature_confounder": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 36,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.1970909090909091,
    "min_admission_margin": -0.03903736382072523,
    "min_delay_risk_margin": -0.037512391805648804,
    "min_raw_margin": -0.0366939902305603,
    "pair_count": 55,
    "pair_pass_count": 19,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 28,
    "signature_overlap_pair_count": 29,
    "task_count": 20
  },
  {
    "admission_fail_count": 16,
    "all_failed_heads_near_count": 16,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 16,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 8,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 49
    },
    "diagnostic_only": true,
    "failed_pair_count": 16,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.17419871794871794,
    "min_admission_margin": -0.0033234371142499552,
    "min_delay_risk_margin": -0.0025954842567443848,
    "min_raw_margin": -0.004572451114654541,
    "pair_count": 65,
    "pair_pass_count": 49,
    "primary": "pair_passes",
    "raw_fail_count": 16,
    "signature_overlap_pair_count": 31,
    "task_count": 20
  },
  {
    "admission_fail_count": 14,
    "all_failed_heads_near_count": 8,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 14,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 58,
      "shared_signature_confounder": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 14,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.13917824074074073,
    "min_admission_margin": -0.019218618798111625,
    "min_delay_risk_margin": -0.018755823373794556,
    "min_raw_margin": -0.024658381938934326,
    "pair_count": 72,
    "pair_pass_count": 58,
    "primary": "pair_passes",
    "raw_fail_count": 14,
    "signature_overlap_pair_count": 30,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 10,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 10,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 8,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 8
    },
    "diagnostic_only": true,
    "failed_pair_count": 10,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.12,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": -0.001958876848220825,
    "min_raw_margin": 0.0,
    "pair_count": 18,
    "pair_pass_count": 8,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 7,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 7,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 23
    },
    "diagnostic_only": true,
    "failed_pair_count": 7,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.116,
    "min_admission_margin": -0.024056579106911974,
    "min_delay_risk_margin": -0.024715542793273926,
    "min_raw_margin": -0.0245245099067688,
    "pair_count": 30,
    "pair_pass_count": 23,
    "primary": "pair_passes",
    "raw_fail_count": 7,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "mixed_margin_failure": 3,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 15
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.19196428571428573,
    "min_admission_margin": -0.02680993237960594,
    "min_delay_risk_margin": -0.025720179080963135,
    "min_raw_margin": -0.0323428213596344,
    "pair_count": 21,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 4,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 4,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.00531025523844289,
    "min_delay_risk_margin": -0.007834970951080322,
    "min_raw_margin": -0.006536394357681274,
    "pair_count": 4,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 4,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac056820151e9ad7",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 15,
      "shared_signature_confounder": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.18556397306397307,
    "min_admission_margin": -0.013941523799578776,
    "min_delay_risk_margin": -0.010658115148544312,
    "min_raw_margin": -0.019653379917144775,
    "pair_count": 18,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 10,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "45baa40751a0bf77",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.2916666666666667,
    "min_admission_margin": -0.007920033050655945,
    "min_delay_risk_margin": -0.003862738609313965,
    "min_raw_margin": -0.01529461145401001,
    "pair_count": 6,
    "pair_pass_count": 4,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 4,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 1,
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.16883116883116883,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": 0.0,
    "pair_count": 7,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v112_focused_nearmargin_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v112_focused_nearmargin_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v112_focused_nearmargin_5000_20260622/focused_pair_failure_contexts.jsonl
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
