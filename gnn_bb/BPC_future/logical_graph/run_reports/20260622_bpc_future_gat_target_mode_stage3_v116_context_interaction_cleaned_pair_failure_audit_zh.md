# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 217
failed_pair_count = 14
strict_pair_pass_rate = 0.9354838709677419
raw_fail_rate = 0.03225806451612903
admission_fail_rate = 0.059907834101382486
delay_risk_fail_rate = 0.03225806451612903
all_failed_heads_near_rate_among_failed = 0.7142857142857143
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.5023041474654378
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

- focused pair 总数：`217`，失败：`14`。
- near-margin 失败占失败 pair：`0.7142857142857143`。
- deep 失败占失败 pair：`0.0`。
- signature overlap pair rate：`0.5023041474654378`。
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
    "count": 217,
    "max": 0.08132033280317655,
    "mean": 0.033722276217591156,
    "median": 0.030857355920046126,
    "min": -0.015791686889067222
  },
  "delay_risk_margin_stats": {
    "count": 217,
    "max": 0.09920650720596313,
    "mean": 0.03951074917744931,
    "median": 0.029339849948883057,
    "min": -0.023166358470916748
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 4,
    "near_margin_loss_tuning_candidate": 5,
    "near_margin_with_shared_signature": 5,
    "pair_passes": 203
  },
  "raw_margin_stats": {
    "count": 217,
    "max": 0.108548104763031,
    "mean": 0.04255796563790141,
    "median": 0.03998282551765442,
    "min": -0.03030604124069214
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 4,
    "all_failed_heads_near_count": 4,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 2,
      "pair_passes": 31
    },
    "diagnostic_only": true,
    "failed_pair_count": 4,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.037797619047619045,
    "min_admission_margin": -0.0005898834321152457,
    "min_delay_risk_margin": 0.010726630687713623,
    "min_raw_margin": 0.004701972007751465,
    "pair_count": 35,
    "pair_pass_count": 31,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 17,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 2,
      "pair_passes": 28
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.03680555555555556,
    "min_admission_margin": -0.000285959866566321,
    "min_delay_risk_margin": 0.004737049341201782,
    "min_raw_margin": 0.006694912910461426,
    "pair_count": 30,
    "pair_pass_count": 28,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 12,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_with_shared_signature": 1,
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.23636363636363636,
    "min_admission_margin": -0.013527228021366716,
    "min_delay_risk_margin": -0.018723666667938232,
    "min_raw_margin": -0.01416286826133728,
    "pair_count": 5,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 3,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 14
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.02666666666666667,
    "min_admission_margin": 0.0031390769876034896,
    "min_delay_risk_margin": -0.003352344036102295,
    "min_raw_margin": 0.013907194137573242,
    "pair_count": 15,
    "pair_pass_count": 14,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 10,
    "task_count": 20
  },
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
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": -0.015046525758005136,
    "min_delay_risk_margin": -0.023166358470916748,
    "min_raw_margin": -0.01247316598892212,
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
    "context_hash": "1b5a36a64a700b58",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0024496303693452293,
    "min_delay_risk_margin": -0.0014658570289611816,
    "min_raw_margin": -0.0053445398807525635,
    "pair_count": 3,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "84ae11479ed592d4",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0005940151009810601,
    "min_delay_risk_margin": 0.0020290911197662354,
    "min_raw_margin": -0.00432625412940979,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "62c86745ed2b3aaa",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.015791686889067222,
    "min_delay_risk_margin": -0.016002118587493896,
    "min_raw_margin": -0.03030604124069214,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "5a812898b6327d87",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001|5a812898b6327d87",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.012956009742108032,
    "min_delay_risk_margin": -0.014901340007781982,
    "min_raw_margin": -0.017716705799102783,
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
    "min_admission_margin": 0.020416046424523687,
    "min_delay_risk_margin": 0.019356608390808105,
    "min_raw_margin": 0.027369141578674316,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v116_context_interaction_cleaned_5000_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v116_context_interaction_cleaned_5000_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v116_context_interaction_cleaned_5000_20260622/focused_pair_failure_contexts.jsonl
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
