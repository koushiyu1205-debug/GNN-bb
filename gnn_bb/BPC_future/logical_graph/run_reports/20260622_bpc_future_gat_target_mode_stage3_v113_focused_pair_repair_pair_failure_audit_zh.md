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
failed_pair_count = 100
strict_pair_pass_rate = 0.7395833333333334
raw_fail_rate = 0.22916666666666666
admission_fail_rate = 0.21614583333333334
delay_risk_fail_rate = 0.2265625
all_failed_heads_near_rate_among_failed = 0.63
any_failed_head_deep_rate_among_failed = 0.19
signature_overlap_pair_rate = 0.46875
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

- focused pair 总数：`384`，失败：`100`。
- near-margin 失败占失败 pair：`0.63`。
- deep 失败占失败 pair：`0.19`。
- signature overlap pair rate：`0.46875`。
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
    "count": 384,
    "max": 0.39003009993974347,
    "mean": 0.08895225534784561,
    "median": 0.03192406812235582,
    "min": -0.16905644085175525
  },
  "delay_risk_margin_stats": {
    "count": 384,
    "max": 0.3382304757833481,
    "mean": 0.07402249553706497,
    "median": 0.027490556240081787,
    "min": -0.132705956697464
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 19,
    "mixed_margin_failure": 17,
    "near_margin_loss_tuning_candidate": 27,
    "near_margin_with_shared_signature": 36,
    "pair_passes": 284,
    "shared_signature_confounder": 1
  },
  "raw_margin_stats": {
    "count": 384,
    "max": 0.423101544380188,
    "mean": 0.08716034481767565,
    "median": 0.03884147107601166,
    "min": -0.150951087474823
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 28,
    "all_failed_heads_near_count": 18,
    "any_failed_head_deep_count": 8,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 28,
    "diagnosis_counts": {
      "deep_structural_score_gap": 8,
      "mixed_margin_failure": 6,
      "near_margin_loss_tuning_candidate": 10,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 23
    },
    "diagnostic_only": true,
    "failed_pair_count": 32,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.1970909090909091,
    "min_admission_margin": -0.16905644085175525,
    "min_delay_risk_margin": -0.132705956697464,
    "min_raw_margin": -0.150951087474823,
    "pair_count": 55,
    "pair_pass_count": 23,
    "primary": "pair_passes",
    "raw_fail_count": 28,
    "signature_overlap_pair_count": 29,
    "task_count": 20
  },
  {
    "admission_fail_count": 12,
    "all_failed_heads_near_count": 14,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 14,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 10,
      "pair_passes": 54
    },
    "diagnostic_only": true,
    "failed_pair_count": 18,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.13917824074074073,
    "min_admission_margin": -0.0036646304875119218,
    "min_delay_risk_margin": -0.010137557983398438,
    "min_raw_margin": -0.00432857871055603,
    "pair_count": 72,
    "pair_pass_count": 54,
    "primary": "pair_passes",
    "raw_fail_count": 12,
    "signature_overlap_pair_count": 30,
    "task_count": 20
  },
  {
    "admission_fail_count": 12,
    "all_failed_heads_near_count": 16,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 12,
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
    "min_admission_margin": -0.004711453386999909,
    "min_delay_risk_margin": -0.001886814832687378,
    "min_raw_margin": -0.00795358419418335,
    "pair_count": 65,
    "pair_pass_count": 49,
    "primary": "pair_passes",
    "raw_fail_count": 16,
    "signature_overlap_pair_count": 31,
    "task_count": 20
  },
  {
    "admission_fail_count": 10,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 6,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 10,
    "diagnosis_counts": {
      "deep_structural_score_gap": 6,
      "mixed_margin_failure": 2,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 8
    },
    "diagnostic_only": true,
    "failed_pair_count": 10,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.12,
    "min_admission_margin": -0.033167861750859784,
    "min_delay_risk_margin": -0.022557199001312256,
    "min_raw_margin": -0.05084088444709778,
    "pair_count": 18,
    "pair_pass_count": 8,
    "primary": "pair_passes",
    "raw_fail_count": 10,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 5,
    "all_failed_heads_near_count": 5,
    "any_failed_head_deep_count": 2,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 7,
    "diagnosis_counts": {
      "deep_structural_score_gap": 2,
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 23
    },
    "diagnostic_only": true,
    "failed_pair_count": 7,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.116,
    "min_admission_margin": -0.09472921493428257,
    "min_delay_risk_margin": -0.07838112115859985,
    "min_raw_margin": -0.12235444784164429,
    "pair_count": 30,
    "pair_pass_count": 23,
    "primary": "pair_passes",
    "raw_fail_count": 5,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 2,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "deep_structural_score_gap": 2,
      "mixed_margin_failure": 1,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 15
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.19196428571428573,
    "min_admission_margin": -0.07437866439702187,
    "min_delay_risk_margin": -0.0647861659526825,
    "min_raw_margin": -0.0889626145362854,
    "pair_count": 21,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 4,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 4,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "near_margin_loss_tuning_candidate": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.007460794410998492,
    "min_delay_risk_margin": -0.01020050048828125,
    "min_raw_margin": -0.016240805387496948,
    "pair_count": 4,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 4,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac056820151e9ad7",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "pair_passes": 15,
      "shared_signature_confounder": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.18556397306397307,
    "min_admission_margin": -0.03745613711737655,
    "min_delay_risk_margin": -0.025395363569259644,
    "min_raw_margin": -0.04701268672943115,
    "pair_count": 18,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 10,
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
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.2916666666666667,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.0006132721900939941,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v113_focused_pair_repair_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v113_focused_pair_repair_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v113_focused_pair_repair_5000_20260622/focused_pair_failure_contexts.jsonl
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
