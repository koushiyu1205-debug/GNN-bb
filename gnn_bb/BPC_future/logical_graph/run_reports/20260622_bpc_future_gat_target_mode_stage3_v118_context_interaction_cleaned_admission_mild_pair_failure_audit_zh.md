# 2026-06-22 BPC_future GAT Stage 3 v118 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 217
failed_pair_count = 26
strict_pair_pass_rate = 0.880184331797235
raw_fail_rate = 0.11059907834101383
admission_fail_rate = 0.0967741935483871
delay_risk_fail_rate = 0.09216589861751152
all_failed_heads_near_rate_among_failed = 0.23076923076923078
any_failed_head_deep_rate_among_failed = 0.2692307692307692
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

- focused pair 总数：`217`，失败：`26`。
- near-margin 失败占失败 pair：`0.23076923076923078`。
- deep 失败占失败 pair：`0.2692307692307692`。
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
    "max": 0.20939171283664332,
    "mean": 0.11852240426429546,
    "median": 0.15292807226040842,
    "min": -0.1301142600090207
  },
  "delay_risk_margin_stats": {
    "count": 217,
    "max": 0.3871169686317444,
    "mean": 0.16765655913660604,
    "median": 0.20111989974975586,
    "min": -0.27487748861312866
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 7,
    "mixed_margin_failure": 4,
    "near_margin_loss_tuning_candidate": 3,
    "near_margin_with_shared_signature": 3,
    "pair_passes": 191,
    "shared_signature_confounder": 9
  },
  "raw_margin_stats": {
    "count": 217,
    "max": 0.48620819486677647,
    "mean": 0.22683095588662108,
    "median": 0.2958211451768875,
    "min": -0.3396847452968359
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "pair_passes": 6,
      "shared_signature_confounder": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 9,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.056,
    "min_admission_margin": -0.018826918512542173,
    "min_delay_risk_margin": -0.009014517068862915,
    "min_raw_margin": -0.03772914409637451,
    "pair_count": 15,
    "pair_pass_count": 6,
    "primary": "shared_signature_confounder",
    "raw_fail_count": 9,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 8,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 4,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 8,
    "diagnosis_counts": {
      "deep_structural_score_gap": 4,
      "mixed_margin_failure": 4,
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 8,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.013333333333333334,
    "min_admission_margin": -0.05408723988861172,
    "min_delay_risk_margin": -0.0726829469203949,
    "min_raw_margin": -0.06164652109146118,
    "pair_count": 12,
    "pair_pass_count": 4,
    "primary": "pair_passes",
    "raw_fail_count": 8,
    "signature_overlap_pair_count": 4,
    "task_count": 20
  },
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 1,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 5,
    "diagnosis_counts": {
      "deep_structural_score_gap": 1,
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 5,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.23636363636363636,
    "min_admission_margin": -0.1301142600090207,
    "min_delay_risk_margin": -0.165943443775177,
    "min_raw_margin": -0.18747875094413757,
    "pair_count": 5,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 3,
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
    "min_admission_margin": -0.09501586706782622,
    "min_delay_risk_margin": -0.27487748861312866,
    "min_raw_margin": -0.3396847452968359,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "deep_structural_score_gap",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "84ae11479ed592d4",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0015969261162825654,
    "min_delay_risk_margin": -0.0004502832889556885,
    "min_raw_margin": -0.0033068060874938965,
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
    "min_admission_margin": -0.0007483914731532537,
    "min_delay_risk_margin": -0.0009404420852661133,
    "min_raw_margin": -0.000748753547668457,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 1,
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
    "min_admission_margin": 0.01593082317094474,
    "min_delay_risk_margin": 0.036452293395996094,
    "min_raw_margin": 0.02556455135345459,
    "pair_count": 35,
    "pair_pass_count": 35,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 17,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 30
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.03680555555555556,
    "min_admission_margin": 0.017798339271464625,
    "min_delay_risk_margin": 0.04090341925621033,
    "min_raw_margin": 0.027014225721359253,
    "pair_count": 30,
    "pair_pass_count": 30,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 12,
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
    "min_admission_margin": 0.05849563668796784,
    "min_delay_risk_margin": 0.045717716217041016,
    "min_raw_margin": 0.04957014322280884,
    "pair_count": 28,
    "pair_pass_count": 28,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 28,
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
      "pair_passes": 15
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.02666666666666667,
    "min_admission_margin": 0.08544876242771794,
    "min_delay_risk_margin": 0.10560694336891174,
    "min_raw_margin": 0.11661368608474731,
    "pair_count": 15,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 10,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v118_context_interaction_cleaned_admission_mild_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v118_context_interaction_cleaned_admission_mild_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v118_context_interaction_cleaned_admission_mild_5000_20260622/focused_pair_failure_contexts.jsonl
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
