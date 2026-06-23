# 2026-06-23 BPC_future GAT Stage 3 v145 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 5
strict_pair_pass_rate = 0.9358974358974359
raw_fail_rate = 0.02564102564102564
admission_fail_rate = 0.0641025641025641
delay_risk_fail_rate = 0.0641025641025641
all_failed_heads_near_rate_among_failed = 0.6
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.2564102564102564
path_token_jaccard_median = 0.05263157894736842
primary = pair_passes
recommended_next_step = add_or_repair_context_action_consequence_features_before_more_sweeps
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`78`，失败：`5`。
- near-margin 失败占失败 pair：`0.6`。
- deep 失败占失败 pair：`0.0`。
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
    "max": 0.10774406694580255,
    "mean": 0.04046043362520789,
    "median": 0.03187063294930001,
    "min": -0.011700392967062101
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.10868588089942932,
    "mean": 0.03678996020402664,
    "median": 0.03023342788219452,
    "min": -0.01185065507888794
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 2,
    "near_margin_loss_tuning_candidate": 3,
    "pair_passes": 73
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.14569219946861267,
    "mean": 0.03594201153669602,
    "median": 0.033261120319366455,
    "min": -0.01954549551010132
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.11145510835913312,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": -0.011309147720897389,
    "min_delay_risk_margin": -0.01185065507888794,
    "min_raw_margin": -0.010447859764099121,
    "pair_count": 10,
    "pair_pass_count": 9,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 8,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "9eb0dc7839bf91ec",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.045454545454545456,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0015034401449821044,
    "min_delay_risk_margin": -0.00305292010307312,
    "min_raw_margin": 0.0009081363677978516,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.2,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.011700392967062101,
    "min_delay_risk_margin": -0.007226526737213135,
    "min_raw_margin": -0.01954549551010132,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "be33b2560df0147a",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306|be33b2560df0147a",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.00019704337265080696,
    "min_delay_risk_margin": -0.0005104243755340576,
    "min_raw_margin": 0.00031507015228271484,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 30
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "5a812898b6327d87",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001|5a812898b6327d87",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0005372865636049384,
    "min_delay_risk_margin": -0.0010126233100891113,
    "min_raw_margin": 0.00014722347259521484,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 0,
    "task_count": 30
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
    "mean_path_token_jaccard": 0.3125,
    "mean_signature_jaccard": 0.4166666666666667,
    "min_admission_margin": 0.01972517779458563,
    "min_delay_risk_margin": 0.019019991159439087,
    "min_raw_margin": 0.017657101154327393,
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
    "mean_path_token_jaccard": 0.11721611721611722,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.0259955491007946,
    "min_delay_risk_margin": 0.028506577014923096,
    "min_raw_margin": 0.022619426250457764,
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
    "mean_path_token_jaccard": 0.025,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.017563086225287877,
    "min_delay_risk_margin": 0.020503729581832886,
    "min_raw_margin": 0.013843059539794922,
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
    "mean_path_token_jaccard": 0.0735042735042735,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.01898751124617179,
    "min_delay_risk_margin": 0.01961272954940796,
    "min_raw_margin": 0.020172536373138428,
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
    "mean_path_token_jaccard": 0.1037037037037037,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.016953084151628717,
    "min_delay_risk_margin": 0.01773369312286377,
    "min_raw_margin": 0.018751978874206543,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v145_no_path_token_ablation_20260623/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v145_no_path_token_ablation_20260623/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v145_no_path_token_ablation_20260623/focused_pair_failure_contexts.jsonl
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
