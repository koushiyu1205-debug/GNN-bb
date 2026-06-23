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
failed_pair_count = 109
strict_pair_pass_rate = 0.7161458333333334
raw_fail_rate = 0.2578125
admission_fail_rate = 0.24739583333333334
delay_risk_fail_rate = 0.22135416666666666
all_failed_heads_near_rate_among_failed = 0.8348623853211009
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

- focused pair 总数：`384`，失败：`109`。
- near-margin 失败占失败 pair：`0.8348623853211009`。
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
    "max": 0.05603804345424884,
    "mean": 0.016273532893353,
    "median": 0.014669490703790228,
    "min": -0.02596728713966001
  },
  "delay_risk_margin_stats": {
    "count": 384,
    "max": 0.0469231903553009,
    "mean": 0.013577995045731464,
    "median": 0.01384533941745758,
    "min": -0.03003177046775818
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 11,
    "near_margin_loss_tuning_candidate": 50,
    "near_margin_with_shared_signature": 41,
    "pair_passes": 275,
    "shared_signature_confounder": 7
  },
  "raw_margin_stats": {
    "count": 384,
    "max": 0.07564949989318848,
    "mean": 0.022637353433916967,
    "median": 0.017930030822753906,
    "min": -0.032613009214401245
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 28,
    "all_failed_heads_near_count": 20,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 28,
    "diagnosis_counts": {
      "mixed_margin_failure": 4,
      "near_margin_loss_tuning_candidate": 12,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 25,
      "shared_signature_confounder": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 30,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.1970909090909091,
    "min_admission_margin": -0.025311529593138954,
    "min_delay_risk_margin": -0.021979093551635742,
    "min_raw_margin": -0.032613009214401245,
    "pair_count": 55,
    "pair_pass_count": 25,
    "primary": "pair_passes",
    "raw_fail_count": 28,
    "signature_overlap_pair_count": 29,
    "task_count": 20
  },
  {
    "admission_fail_count": 16,
    "all_failed_heads_near_count": 20,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 8,
      "near_margin_with_shared_signature": 12,
      "pair_passes": 45
    },
    "diagnostic_only": true,
    "failed_pair_count": 20,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.17419871794871794,
    "min_admission_margin": -0.0027471141513423503,
    "min_delay_risk_margin": -0.0020480751991271973,
    "min_raw_margin": -0.001298278570175171,
    "pair_count": 65,
    "pair_pass_count": 45,
    "primary": "pair_passes",
    "raw_fail_count": 20,
    "signature_overlap_pair_count": 31,
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
    "min_admission_margin": -0.00021834613098128952,
    "min_delay_risk_margin": -0.0009275078773498535,
    "min_raw_margin": -0.0006510615348815918,
    "pair_count": 72,
    "pair_pass_count": 56,
    "primary": "pair_passes",
    "raw_fail_count": 12,
    "signature_overlap_pair_count": 30,
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
    "min_admission_margin": -0.01652345913854622,
    "min_delay_risk_margin": -0.01438760757446289,
    "min_raw_margin": -0.022181272506713867,
    "pair_count": 30,
    "pair_pass_count": 22,
    "primary": "pair_passes",
    "raw_fail_count": 8,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 7,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 14
    },
    "diagnostic_only": true,
    "failed_pair_count": 7,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.19196428571428573,
    "min_admission_margin": -0.00221935729971115,
    "min_delay_risk_margin": -0.002084702253341675,
    "min_raw_margin": -0.00548398494720459,
    "pair_count": 21,
    "pair_pass_count": 14,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 15,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 6,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 12
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.12,
    "min_admission_margin": -0.00015431639870561176,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.004001140594482422,
    "pair_count": 18,
    "pair_pass_count": 12,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 5,
    "all_failed_heads_near_count": 5,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 4,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 5,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.16883116883116883,
    "min_admission_margin": -0.0014346686739481473,
    "min_delay_risk_margin": -0.0021668970584869385,
    "min_raw_margin": -0.003025949001312256,
    "pair_count": 7,
    "pair_pass_count": 2,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 5,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "0df8d5cea7864e69",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
    "delay_risk_fail_count": 3,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 3,
      "pair_passes": 25
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0859375,
    "min_admission_margin": -0.00027972744021023677,
    "min_delay_risk_margin": -0.001895219087600708,
    "min_raw_margin": -0.0006590485572814941,
    "pair_count": 28,
    "pair_pass_count": 25,
    "primary": "pair_passes",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 28,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac056820151e9ad7",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2,
      "pair_passes": 15,
      "shared_signature_confounder": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.18556397306397307,
    "min_admission_margin": -0.011750849372309413,
    "min_delay_risk_margin": -0.003125101327896118,
    "min_raw_margin": -0.01676347851753235,
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
    "min_admission_margin": -0.007789942195552291,
    "min_delay_risk_margin": -0.0045868754386901855,
    "min_raw_margin": -0.013882875442504883,
    "pair_count": 6,
    "pair_pass_count": 4,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 4,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v114_context_feature_fix_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v114_context_feature_fix_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v114_context_feature_fix_5000_20260622/focused_pair_failure_contexts.jsonl
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
