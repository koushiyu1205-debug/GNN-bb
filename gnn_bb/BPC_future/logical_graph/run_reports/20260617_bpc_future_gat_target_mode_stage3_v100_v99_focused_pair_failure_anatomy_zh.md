# 2026-06-17 BPC_future GAT Stage 3 v98 Focused Pair Failure Anatomy 报告

## 目的

对 v96 explicit focused tranche 的 same-context pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
 表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 145
failed_pair_count = 80
strict_pair_pass_rate = 0.4482758620689655
raw_fail_rate = 0.5241379310344828
admission_fail_rate = 0.5241379310344828
delay_risk_fail_rate = 0.36551724137931035
all_failed_heads_near_rate_among_failed = 0.9625
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.4689655172413793
path_token_jaccard_median = 0.09259259259259259
primary = pair_passes
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`145`，失败：`80`。
- near-margin 失败占失败 pair：`0.9625`。
- deep 失败占失败 pair：`0.0`。
- signature overlap pair rate：`0.4689655172413793`。
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
    "count": 145,
    "max": 0.005796074867248535,
    "mean": 2.0389104711598364e-05,
    "median": 0.0,
    "min": -0.009619653224945068
  },
  "delay_risk_margin_stats": {
    "count": 145,
    "max": 0.46058884263038635,
    "mean": 0.11645955178115902,
    "median": 0.0031138956546783447,
    "min": -0.012245118618011475
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 3,
    "near_margin_loss_tuning_candidate": 34,
    "near_margin_with_shared_signature": 43,
    "pair_passes": 65
  },
  "raw_margin_stats": {
    "count": 145,
    "max": 0.005796074867248535,
    "mean": 2.0389104711598364e-05,
    "median": 0.0,
    "min": -0.009619653224945068
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 20,
    "all_failed_heads_near_count": 20,
    "any_failed_head_deep_count": 0,
    "context_hash": "79fde658840fe2b8",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
    "delay_risk_fail_count": 18,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 12,
      "near_margin_with_shared_signature": 8,
      "pair_passes": 15
    },
    "diagnostic_only": true,
    "failed_pair_count": 20,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.22936700103770322,
    "mean_signature_jaccard": 0.15089285714285713,
    "min_admission_margin": -0.002291738986968994,
    "min_delay_risk_margin": -0.00494539737701416,
    "min_raw_margin": -0.002291738986968994,
    "pair_count": 35,
    "pair_pass_count": 15,
    "primary": "pair_passes",
    "raw_fail_count": 20,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 17,
    "all_failed_heads_near_count": 20,
    "any_failed_head_deep_count": 0,
    "context_hash": "b6d808ebac2a6dd8",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
    "delay_risk_fail_count": 12,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 10,
      "near_margin_with_shared_signature": 10,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 20,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2658611111111111,
    "mean_signature_jaccard": 0.2112,
    "min_admission_margin": -0.0020620226860046387,
    "min_delay_risk_margin": -0.005322575569152832,
    "min_raw_margin": -0.0020620226860046387,
    "pair_count": 25,
    "pair_pass_count": 5,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 17,
    "signature_overlap_pair_count": 12,
    "task_count": 20
  },
  {
    "admission_fail_count": 19,
    "all_failed_heads_near_count": 19,
    "any_failed_head_deep_count": 0,
    "context_hash": "ac15bc4e7e3d6fff",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
    "delay_risk_fail_count": 14,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 10,
      "near_margin_with_shared_signature": 9,
      "pair_passes": 16
    },
    "diagnostic_only": true,
    "failed_pair_count": 19,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.2544662993402489,
    "mean_signature_jaccard": 0.1681547619047619,
    "min_admission_margin": -0.0071694254875183105,
    "min_delay_risk_margin": -0.0044744014739990234,
    "min_raw_margin": -0.0071694254875183105,
    "pair_count": 35,
    "pair_pass_count": 16,
    "primary": "pair_passes",
    "raw_fail_count": 19,
    "signature_overlap_pair_count": 14,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 5,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 6,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "near_margin_loss_tuning_candidate": 2,
      "near_margin_with_shared_signature": 3,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 7,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.27046783625730997,
    "mean_signature_jaccard": 0.2578125,
    "min_admission_margin": -0.0016404986381530762,
    "min_delay_risk_margin": -0.012245118618011475,
    "min_raw_margin": -0.0016404986381530762,
    "pair_count": 12,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 6,
    "all_failed_heads_near_count": 6,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 6,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.07407407407407407,
    "mean_signature_jaccard": 0.04,
    "min_admission_margin": -0.007351309061050415,
    "min_delay_risk_margin": 0.3935989439487457,
    "min_raw_margin": -0.007351309061050415,
    "pair_count": 6,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 6,
    "signature_overlap_pair_count": 6,
    "task_count": 20
  },
  {
    "admission_fail_count": 3,
    "all_failed_heads_near_count": 3,
    "any_failed_head_deep_count": 0,
    "context_hash": "0df8d5cea7864e69",
    "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 3,
      "pair_passes": 6
    },
    "diagnostic_only": true,
    "failed_pair_count": 3,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.08333333333333334,
    "mean_signature_jaccard": 0.03125,
    "min_admission_margin": -0.0013559460639953613,
    "min_delay_risk_margin": 0.4405110441148281,
    "min_raw_margin": -0.0013559460639953613,
    "pair_count": 9,
    "pair_pass_count": 6,
    "primary": "pair_passes",
    "raw_fail_count": 3,
    "signature_overlap_pair_count": 9,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "67c11b5ec80925ec",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 2,
      "pair_passes": 5
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.2730414746543779,
    "mean_signature_jaccard": 0.15584415584415584,
    "min_admission_margin": -0.003728210926055908,
    "min_delay_risk_margin": 0.0,
    "min_raw_margin": -0.003728210926055908,
    "pair_count": 7,
    "pair_pass_count": 5,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 2,
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
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.42857142857142855,
    "mean_signature_jaccard": 0.3333333333333333,
    "min_admission_margin": -0.0009557008743286133,
    "min_delay_risk_margin": -0.010742723941802979,
    "min_raw_margin": -0.0009557008743286133,
    "pair_count": 3,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 1,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "9a2ca522ff49991c",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_with_shared_signature": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.13725490196078433,
    "mean_signature_jaccard": 0.03125,
    "min_admission_margin": -0.009619653224945068,
    "min_delay_risk_margin": 0.4142719805240631,
    "min_raw_margin": -0.009619653224945068,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "near_margin_with_shared_signature",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 1,
    "task_count": 50
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "d519291840dd7000",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "pair_passes": 10
    },
    "diagnostic_only": true,
    "failed_pair_count": 0,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.032432432432432434,
    "mean_signature_jaccard": 0.008,
    "min_admission_margin": 0.0015083849430084229,
    "min_delay_risk_margin": 0.011526674032211304,
    "min_raw_margin": 0.0015083849430084229,
    "pair_count": 10,
    "pair_pass_count": 10,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 2,
    "task_count": 20
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v100_v99_20260617/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v100_v99_20260617/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v100_v99_20260617/focused_pair_failure_contexts.jsonl
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
