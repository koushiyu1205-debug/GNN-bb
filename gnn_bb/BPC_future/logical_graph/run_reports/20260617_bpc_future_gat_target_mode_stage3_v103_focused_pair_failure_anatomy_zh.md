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
failed_pair_count = 61
strict_pair_pass_rate = 0.5793103448275863
raw_fail_rate = 0.3310344827586207
admission_fail_rate = 0.3103448275862069
delay_risk_fail_rate = 0.36551724137931035
all_failed_heads_near_rate_among_failed = 0.9344262295081968
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

- focused pair 总数：`145`，失败：`61`。
- near-margin 失败占失败 pair：`0.9344262295081968`。
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
    "max": 0.061980605595641336,
    "mean": 0.013564690183271503,
    "median": 0.001179434080434305,
    "min": -0.020441027742942097
  },
  "delay_risk_margin_stats": {
    "count": 145,
    "max": 0.101569265127182,
    "mean": 0.023356436449905923,
    "median": 0.0005213022232055664,
    "min": -0.01980578899383545
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 4,
    "near_margin_loss_tuning_candidate": 34,
    "near_margin_with_shared_signature": 23,
    "pair_passes": 84
  },
  "raw_margin_stats": {
    "count": 145,
    "max": 0.033589959144592285,
    "mean": 0.004842090401156195,
    "median": 0.0016301274299621582,
    "min": -0.023668497800827026
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 16,
    "all_failed_heads_near_count": 18,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 16,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 13,
      "near_margin_with_shared_signature": 5,
      "pair_passes": 17
    },
    "diagnostic_only": true,
    "failed_pair_count": 18,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2544662993402489,
    "mean_signature_jaccard": 0.1681547619047619,
    "min_admission_margin": -0.0012647094177680174,
    "min_delay_risk_margin": -0.0006319880485534668,
    "min_raw_margin": -0.0023016035556793213,
    "pair_count": 35,
    "pair_pass_count": 17,
    "primary": "pair_passes",
    "raw_fail_count": 16,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 10,
    "all_failed_heads_near_count": 15,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 13,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 9,
      "near_margin_with_shared_signature": 6,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 16,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2658611111111111,
    "mean_signature_jaccard": 0.2112,
    "min_admission_margin": -0.004677160110531986,
    "min_delay_risk_margin": -0.010305643081665039,
    "min_raw_margin": -0.0005051195621490479,
    "pair_count": 25,
    "pair_pass_count": 9,
    "primary": "pair_passes",
    "raw_fail_count": 10,
    "signature_overlap_pair_count": 12,
    "task_count": 20
  },
  {
    "admission_fail_count": 10,
    "all_failed_heads_near_count": 10,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 10,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 6,
      "pair_passes": 25
    },
    "diagnostic_only": true,
    "failed_pair_count": 10,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.22936700103770322,
    "mean_signature_jaccard": 0.15089285714285713,
    "min_admission_margin": -0.0016134016942448426,
    "min_delay_risk_margin": -0.0008220672607421875,
    "min_raw_margin": -0.002670377492904663,
    "pair_count": 35,
    "pair_pass_count": 25,
    "primary": "pair_passes",
    "raw_fail_count": 10,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.27046783625730997,
    "mean_signature_jaccard": 0.2578125,
    "min_admission_margin": -0.009096545764856856,
    "min_delay_risk_margin": -0.013368606567382812,
    "min_raw_margin": -0.005994230508804321,
    "pair_count": 12,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 4,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.032432432432432434,
    "mean_signature_jaccard": 0.008,
    "min_admission_margin": 0.005009224850816452,
    "min_delay_risk_margin": -0.0007483959197998047,
    "min_raw_margin": 0.011597037315368652,
    "pair_count": 10,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 2,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.2730414746543779,
    "mean_signature_jaccard": 0.15584415584415584,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.0011452436447143555,
    "pair_count": 7,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 4,
    "signature_overlap_pair_count": 2,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "45baa40751a0bf77",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.42857142857142855,
    "mean_signature_jaccard": 0.3333333333333333,
    "min_admission_margin": -0.020441027742942097,
    "min_delay_risk_margin": -0.01980578899383545,
    "min_raw_margin": -0.023668497800827026,
    "pair_count": 3,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 1,
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
    "min_admission_margin": 0.056350447497873546,
    "min_delay_risk_margin": 0.10034525394439697,
    "min_raw_margin": 0.016473978757858276,
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
    "min_admission_margin": 0.024617233453103182,
    "min_delay_risk_margin": 0.051072537899017334,
    "min_raw_margin": 0.0001628100872039795,
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
    "min_admission_margin": 0.0030360899479688896,
    "min_delay_risk_margin": 0.003683924674987793,
    "min_raw_margin": 0.002919793128967285,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v103_20260617/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v103_20260617/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v103_20260617/focused_pair_failure_contexts.jsonl
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
