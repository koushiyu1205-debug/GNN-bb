# 2026-06-23 BPC_future GAT Stage 3 v138 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 4
strict_pair_pass_rate = 0.9487179487179487
raw_fail_rate = 0.038461538461538464
admission_fail_rate = 0.05128205128205128
delay_risk_fail_rate = 0.05128205128205128
all_failed_heads_near_rate_among_failed = 0.25
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

- focused pair 总数：`78`，失败：`4`。
- near-margin 失败占失败 pair：`0.25`。
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
    "max": 0.18672148156409962,
    "mean": 0.07770578048350546,
    "median": 0.07430469907564967,
    "min": -0.031347909818833175
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.20311778783798218,
    "mean": 0.05654855913076645,
    "median": 0.046904057264328,
    "min": -0.019684791564941406
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 3,
    "near_margin_loss_tuning_candidate": 1,
    "pair_passes": 74
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.3401724398136139,
    "mean": 0.10591574089649396,
    "median": 0.08458253741264343,
    "min": -0.04034256935119629
  }
}
```

## Top Contexts

```json
[
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
    "mean_path_token_jaccard": 0.11721611721611722,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.031347909818833175,
    "min_delay_risk_margin": -0.019684791564941406,
    "min_raw_margin": -0.04034256935119629,
    "pair_count": 4,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "7cb380a02e30e5a8",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.08333333333333333,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0008424084020914047,
    "min_delay_risk_margin": -0.007609456777572632,
    "min_raw_margin": 0.008551836013793945,
    "pair_count": 3,
    "pair_pass_count": 2,
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
    "min_admission_margin": -0.02146311756083666,
    "min_delay_risk_margin": -0.008261919021606445,
    "min_raw_margin": -0.03520697355270386,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
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
    "mean_path_token_jaccard": 0.11145510835913312,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": 0.051894709095517744,
    "min_delay_risk_margin": 0.042495280504226685,
    "min_raw_margin": 0.045614004135131836,
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
    "mean_path_token_jaccard": 0.3125,
    "mean_signature_jaccard": 0.4166666666666667,
    "min_admission_margin": 0.07865771878832362,
    "min_delay_risk_margin": 0.05428615212440491,
    "min_raw_margin": 0.10290998220443726,
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
    "mean_path_token_jaccard": 0.025,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.16596666124348042,
    "min_delay_risk_margin": 0.13515466451644897,
    "min_raw_margin": 0.27337974309921265,
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
    "min_admission_margin": 0.032342802824151695,
    "min_delay_risk_margin": 0.024847179651260376,
    "min_raw_margin": 0.044454604387283325,
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
    "min_admission_margin": 0.024844595135291497,
    "min_delay_risk_margin": 0.02257785201072693,
    "min_raw_margin": 0.03269067406654358,
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
    "mean_path_token_jaccard": 0.027777777777777776,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.04225451212284992,
    "min_delay_risk_margin": 0.03295740485191345,
    "min_raw_margin": 0.057858556509017944,
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
    "context_hash": "5c522ff2995f86be",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.03793888640342438,
    "min_delay_risk_margin": 0.011147111654281616,
    "min_raw_margin": 0.07471683621406555,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v138_action_priority_residual_20260623/focused_pair_failure_contexts.jsonl
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
