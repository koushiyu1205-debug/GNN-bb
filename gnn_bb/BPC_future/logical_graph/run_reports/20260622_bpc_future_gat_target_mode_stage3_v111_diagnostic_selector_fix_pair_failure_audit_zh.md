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
failed_pair_count = 118
strict_pair_pass_rate = 0.6927083333333334
raw_fail_rate = 0.2760416666666667
admission_fail_rate = 0.2265625
delay_risk_fail_rate = 0.2578125
all_failed_heads_near_rate_among_failed = 0.7288135593220338
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

- focused pair 总数：`384`，失败：`118`。
- near-margin 失败占失败 pair：`0.7288135593220338`。
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
    "max": 0.08818084103154275,
    "mean": 0.02003164049531736,
    "median": 0.011464944077530154,
    "min": -0.030872641542040224
  },
  "delay_risk_margin_stats": {
    "count": 384,
    "max": 0.09548637270927429,
    "mean": 0.02194369592082997,
    "median": 0.010431542992591858,
    "min": -0.02568832039833069
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 23,
    "near_margin_loss_tuning_candidate": 44,
    "near_margin_with_shared_signature": 42,
    "pair_passes": 266,
    "shared_signature_confounder": 9
  },
  "raw_margin_stats": {
    "count": 384,
    "max": 0.08278962969779968,
    "mean": 0.017711713754882414,
    "median": 0.009205669164657593,
    "min": -0.03601837158203125
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 28,
    "all_failed_heads_near_count": 17,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 28,
    "diagnosis_counts": {
      "mixed_margin_failure": 8,
      "near_margin_loss_tuning_candidate": 6,
      "near_margin_with_shared_signature": 11,
      "pair_passes": 24,
      "shared_signature_confounder": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 31,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.1970909090909091,
    "min_admission_margin": -0.030872641542040224,
    "min_delay_risk_margin": -0.025149226188659668,
    "min_raw_margin": -0.03601837158203125,
    "pair_count": 55,
    "pair_pass_count": 24,
    "primary": "pair_passes",
    "raw_fail_count": 31,
    "signature_overlap_pair_count": 29,
    "task_count": 20
  },
  {
    "admission_fail_count": 16,
    "all_failed_heads_near_count": 30,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 20,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 20,
      "near_margin_with_shared_signature": 10,
      "pair_passes": 35
    },
    "diagnostic_only": true,
    "failed_pair_count": 30,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.17419871794871794,
    "min_admission_margin": -0.00440054398266751,
    "min_delay_risk_margin": -0.001455456018447876,
    "min_raw_margin": -0.009504914283752441,
    "pair_count": 65,
    "pair_pass_count": 35,
    "primary": "pair_passes",
    "raw_fail_count": 26,
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
    "min_admission_margin": -0.0259945824572273,
    "min_delay_risk_margin": -0.02568832039833069,
    "min_raw_margin": -0.031440913677215576,
    "pair_count": 72,
    "pair_pass_count": 58,
    "primary": "pair_passes",
    "raw_fail_count": 14,
    "signature_overlap_pair_count": 30,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 10,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 14,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_loss_tuning_candidate": 8,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 4
    },
    "diagnostic_only": true,
    "failed_pair_count": 14,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.12,
    "min_admission_margin": -0.01331456545227841,
    "min_delay_risk_margin": -0.008527815341949463,
    "min_raw_margin": -0.02111220359802246,
    "pair_count": 18,
    "pair_pass_count": 4,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 8,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 8,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_loss_tuning_candidate": 1,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 22
    },
    "diagnostic_only": true,
    "failed_pair_count": 8,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.116,
    "min_admission_margin": -0.01552675460215508,
    "min_delay_risk_margin": -0.014524579048156738,
    "min_raw_margin": -0.018503904342651367,
    "pair_count": 30,
    "pair_pass_count": 22,
    "primary": "pair_passes",
    "raw_fail_count": 8,
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
    "min_admission_margin": -0.024165072643196894,
    "min_delay_risk_margin": -0.021653711795806885,
    "min_raw_margin": -0.030440330505371094,
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
    "min_admission_margin": -0.004859642170815359,
    "min_delay_risk_margin": -0.007098555564880371,
    "min_raw_margin": -0.005492866039276123,
    "pair_count": 4,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 4,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "0df8d5cea7864e69",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 3,
      "pair_passes": 25
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0859375,
    "min_admission_margin": 0.0005738127989813047,
    "min_delay_risk_margin": 0.0018329322338104248,
    "min_raw_margin": -0.0012447237968444824,
    "pair_count": 28,
    "pair_pass_count": 25,
    "primary": "pair_passes",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 28,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 1,
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
    "min_admission_margin": 0.0,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.0013723373413085938,
    "pair_count": 7,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddb0ce64af10976a",
    "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.00015701524184752458,
    "min_delay_risk_margin": -0.00014096498489379883,
    "min_raw_margin": -0.00025200843811035156,
    "pair_count": 4,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v111_diagnostic_selector_fix_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v111_diagnostic_selector_fix_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v111_diagnostic_selector_fix_5000_20260622/focused_pair_failure_contexts.jsonl
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
