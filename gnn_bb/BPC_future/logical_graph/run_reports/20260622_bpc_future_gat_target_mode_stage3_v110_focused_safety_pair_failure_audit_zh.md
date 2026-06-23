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
failed_pair_count = 85
strict_pair_pass_rate = 0.7786458333333334
raw_fail_rate = 0.20833333333333334
admission_fail_rate = 0.2109375
delay_risk_fail_rate = 0.2109375
all_failed_heads_near_rate_among_failed = 0.5882352941176471
any_failed_head_deep_rate_among_failed = 0.18823529411764706
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

- focused pair 总数：`384`，失败：`85`。
- near-margin 失败占失败 pair：`0.5882352941176471`。
- deep 失败占失败 pair：`0.18823529411764706`。
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
    "max": 0.3112687023025524,
    "mean": 0.07003865759981472,
    "median": 0.06406799277977665,
    "min": -0.14302069063782402
  },
  "delay_risk_margin_stats": {
    "count": 384,
    "max": 0.5625186264514923,
    "mean": 0.061574212120225034,
    "median": 0.046611487865448,
    "min": -0.14568908512592316
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 16,
    "mixed_margin_failure": 14,
    "near_margin_loss_tuning_candidate": 16,
    "near_margin_with_shared_signature": 34,
    "pair_passes": 299,
    "shared_signature_confounder": 5
  },
  "raw_margin_stats": {
    "count": 384,
    "max": 0.6234987173229456,
    "mean": 0.06644633261627557,
    "median": 0.02844792604446411,
    "min": -0.04190129041671753
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 31,
    "all_failed_heads_near_count": 10,
    "any_failed_head_deep_count": 16,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 31,
    "diagnosis_counts": {
      "deep_structural_score_gap": 16,
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 24,
      "shared_signature_confounder": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 31,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.1970909090909091,
    "min_admission_margin": -0.14302069063782402,
    "min_delay_risk_margin": -0.14568908512592316,
    "min_raw_margin": -0.04190129041671753,
    "pair_count": 55,
    "pair_pass_count": 24,
    "primary": "pair_passes",
    "raw_fail_count": 31,
    "signature_overlap_pair_count": 29,
    "task_count": 20
  },
  {
    "admission_fail_count": 12,
    "all_failed_heads_near_count": 16,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 8,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 56
    },
    "diagnostic_only": true,
    "failed_pair_count": 16,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.13917824074074073,
    "min_admission_margin": -0.0013915846476889038,
    "min_delay_risk_margin": -0.004754573106765747,
    "min_raw_margin": -0.004241764545440674,
    "pair_count": 72,
    "pair_pass_count": 56,
    "primary": "pair_passes",
    "raw_fail_count": 12,
    "signature_overlap_pair_count": 30,
    "task_count": 20
  },
  {
    "admission_fail_count": 12,
    "all_failed_heads_near_count": 12,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 53
    },
    "diagnostic_only": true,
    "failed_pair_count": 12,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.17419871794871794,
    "min_admission_margin": -0.0022505010033838646,
    "min_delay_risk_margin": -0.0022774338722229004,
    "min_raw_margin": -0.0012111067771911621,
    "pair_count": 65,
    "pair_pass_count": 53,
    "primary": "pair_passes",
    "raw_fail_count": 12,
    "signature_overlap_pair_count": 31,
    "task_count": 20
  },
  {
    "admission_fail_count": 12,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "mixed_margin_failure": 10,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 12,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.12,
    "min_admission_margin": -0.039180610759179724,
    "min_delay_risk_margin": -0.03843092918395996,
    "min_raw_margin": -0.021088719367980957,
    "pair_count": 18,
    "pair_pass_count": 6,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 12,
    "signature_overlap_pair_count": 6,
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
      "pair_passes": 15
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.19196428571428573,
    "min_admission_margin": -0.028791030474047075,
    "min_delay_risk_margin": -0.03169843554496765,
    "min_raw_margin": -0.010199666023254395,
    "pair_count": 21,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 4,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 4,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 26
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.116,
    "min_admission_margin": -0.01946308940125202,
    "min_delay_risk_margin": -0.018169045448303223,
    "min_raw_margin": -0.012612700462341309,
    "pair_count": 30,
    "pair_pass_count": 26,
    "primary": "pair_passes",
    "raw_fail_count": 4,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.16883116883116883,
    "min_admission_margin": -0.0016841388969272009,
    "min_delay_risk_margin": -0.002316206693649292,
    "min_raw_margin": 0.0,
    "pair_count": 7,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "45baa40751a0bf77",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 1,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.2916666666666667,
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": 0.0,
    "pair_count": 6,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 4,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.01442122131808532,
    "min_delay_risk_margin": -0.003064364194869995,
    "min_raw_margin": -0.02657628059387207,
    "pair_count": 4,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
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
      "pair_passes": 28
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0859375,
    "min_admission_margin": 0.04961888345803461,
    "min_delay_risk_margin": 0.047936975955963135,
    "min_raw_margin": 0.019652128219604492,
    "pair_count": 28,
    "pair_pass_count": 28,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 28,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_focused_safety_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_focused_safety_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v110_focused_safety_5000_20260622/focused_pair_failure_contexts.jsonl
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
