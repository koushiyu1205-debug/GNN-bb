# 2026-06-22 BPC_future GAT Stage 3 v120 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 6
strict_pair_pass_rate = 0.9230769230769231
raw_fail_rate = 0.0641025641025641
admission_fail_rate = 0.0641025641025641
delay_risk_fail_rate = 0.05128205128205128
all_failed_heads_near_rate_among_failed = 0.6666666666666666
any_failed_head_deep_rate_among_failed = 0.16666666666666666
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

- focused pair 总数：`78`，失败：`6`。
- near-margin 失败占失败 pair：`0.6666666666666666`。
- deep 失败占失败 pair：`0.16666666666666666`。
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
    "max": 0.23808053036609247,
    "mean": 0.11874754538867544,
    "median": 0.07534302695805407,
    "min": -0.09526216512123742
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.5540948808193207,
    "mean": 0.21355800636303732,
    "median": 0.07116532325744629,
    "min": -0.014753192663192749
  },
  "diagnosis_counts": {
    "deep_structural_score_gap": 1,
    "mixed_margin_failure": 1,
    "near_margin_loss_tuning_candidate": 4,
    "pair_passes": 72
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.5299782062647864,
    "mean": 0.23439428140185414,
    "median": 0.05881522595882416,
    "min": -0.21994060277938843
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "5c522ff2995f86be",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0068868131792994,
    "min_delay_risk_margin": -0.0007857084274291992,
    "min_raw_margin": -0.01431584358215332,
    "pair_count": 3,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 1,
    "context_hash": "84ae11479ed592d4",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "deep_structural_score_gap": 1,
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.09526216512123742,
    "min_delay_risk_margin": -0.014753192663192749,
    "min_raw_margin": -0.21994060277938843,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "5368cf35ed6f06cb",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.015625,
    "min_admission_margin": -0.0010796759756535879,
    "min_delay_risk_margin": 0.0024506747722625732,
    "min_raw_margin": -0.005795001983642578,
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
    "min_admission_margin": 0.009275988739320423,
    "min_delay_risk_margin": 0.009051620960235596,
    "min_raw_margin": 0.008510470390319824,
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
    "min_admission_margin": 0.0306554176565573,
    "min_delay_risk_margin": 0.03545790910720825,
    "min_raw_margin": 0.023799240589141846,
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
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.05147648938954433,
    "min_delay_risk_margin": 0.058029115200042725,
    "min_raw_margin": 0.04548105597496033,
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
    "min_admission_margin": 0.23720293831376726,
    "min_delay_risk_margin": 0.5190110206604004,
    "min_raw_margin": 0.5277417694451287,
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
    "min_admission_margin": 0.22642296982927612,
    "min_delay_risk_margin": 0.465448260307312,
    "min_raw_margin": 0.5171160213649273,
    "pair_count": 3,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "1b5a36a64a700b58",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.03018728255705347,
    "min_delay_risk_margin": 0.03791409730911255,
    "min_raw_margin": 0.018536269664764404,
    "pair_count": 3,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "67925c0d2fd4abde",
    "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.07005206621668508,
    "min_delay_risk_margin": 0.023169249296188354,
    "min_raw_margin": 0.13349300622940063,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v120_v119_clean_focused_indices_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v120_v119_clean_focused_indices_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v120_v119_clean_focused_indices_20260622/focused_pair_failure_contexts.jsonl
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
