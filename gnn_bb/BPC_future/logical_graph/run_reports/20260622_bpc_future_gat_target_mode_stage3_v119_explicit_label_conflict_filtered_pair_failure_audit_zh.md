# 2026-06-22 BPC_future GAT Stage 3 v119 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 10
strict_pair_pass_rate = 0.8717948717948718
raw_fail_rate = 0.10256410256410256
admission_fail_rate = 0.10256410256410256
delay_risk_fail_rate = 0.11538461538461539
all_failed_heads_near_rate_among_failed = 0.5
any_failed_head_deep_rate_among_failed = 0.3
signature_overlap_pair_rate = 0.2564102564102564
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

- focused pair 总数：`78`，失败：`10`。
- near-margin 失败占失败 pair：`0.5`。
- deep 失败占失败 pair：`0.3`。
- signature overlap pair rate：`0.2564102564102564`。
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
    "count": 78,
    "max": 0.24925760585599305,
    "mean": 0.10127315023629721,
    "median": 0.07060229989440982,
    "min": -0.13795649777861807
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.5116224586963654,
    "mean": 0.14078581256744188,
    "median": 0.059181153774261475,
    "min": -0.3577122688293457
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 3,
    "mixed_margin_failure": 2,
    "near_margin_loss_tuning_candidate": 3,
    "near_margin_with_shared_signature": 2,
    "pair_passes": 68
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.5888388962484896,
    "mean": 0.20419956668196484,
    "median": 0.11095291376113892,
    "min": -0.27807631017640233
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 2,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "deep_structural_score_gap": 2,
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.13795649777861807,
    "min_delay_risk_margin": -0.1571989357471466,
    "min_raw_margin": -0.18759992718696594,
    "pair_count": 4,
    "pair_pass_count": 1,
    "primary": "deep_structural_score_gap",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 1,
    "context_hash": "62c86745ed2b3aaa",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "deep_structural_score_gap": 1,
      "mixed_margin_failure": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.06814963247780628,
    "min_delay_risk_margin": -0.3577122688293457,
    "min_raw_margin": -0.27807631017640233,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "9f80ae35ea87da5b",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.015625,
    "min_admission_margin": -0.004013504833208614,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.009573698043823242,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 1,
    "task_count": 30
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "a0f80eb374f29f44",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
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
    "min_admission_margin": 0.017500562520620877,
    "min_delay_risk_margin": -0.005692988634109497,
    "min_raw_margin": 0.040862083435058594,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 1,
    "task_count": 30
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "9a2ca522ff49991c",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.03125,
    "min_admission_margin": 0.016792027459150094,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": 0.04005521535873413,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 1,
    "task_count": 50
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
    "min_admission_margin": -0.022829390409864064,
    "min_delay_risk_margin": -0.01484447717666626,
    "min_raw_margin": -0.036005496978759766,
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
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 10
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": 0.020928572097557746,
    "min_delay_risk_margin": 0.013299554586410522,
    "min_raw_margin": 0.033676862716674805,
    "pair_count": 10,
    "pair_pass_count": 10,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 8,
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
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.4166666666666667,
    "min_admission_margin": 0.04335031335071146,
    "min_delay_risk_margin": 0.03031417727470398,
    "min_raw_margin": 0.05937385559082031,
    "pair_count": 6,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 5,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddb0ce64af10976a",
    "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.16457424011075594,
    "min_delay_risk_margin": 0.1573125123977661,
    "min_raw_margin": 0.2983209490776062,
    "pair_count": 4,
    "pair_pass_count": 4,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "7db256d4f7224cc6",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.22231084608889176,
    "min_delay_risk_margin": 0.4925815761089325,
    "min_raw_margin": 0.5449394755996764,
    "pair_count": 3,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v119_explicit_label_conflict_filtered_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v119_explicit_label_conflict_filtered_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v119_explicit_label_conflict_filtered_20260622/focused_pair_failure_contexts.jsonl
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
