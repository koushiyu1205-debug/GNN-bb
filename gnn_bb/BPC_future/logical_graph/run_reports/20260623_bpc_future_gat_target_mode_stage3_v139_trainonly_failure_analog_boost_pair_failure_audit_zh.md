# 2026-06-23 BPC_future GAT Stage 3 v139 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 3
strict_pair_pass_rate = 0.9615384615384616
raw_fail_rate = 0.038461538461538464
admission_fail_rate = 0.038461538461538464
delay_risk_fail_rate = 0.038461538461538464
all_failed_heads_near_rate_among_failed = 0.3333333333333333
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

- focused pair 总数：`78`，失败：`3`。
- near-margin 失败占失败 pair：`0.3333333333333333`。
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
    "max": 0.3947633057539099,
    "mean": 0.17523058400641547,
    "median": 0.17797365741076004,
    "min": -0.04331384452440551
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.5922001302242279,
    "mean": 0.15414556287802184,
    "median": 0.11832073330879211,
    "min": -0.031283020973205566
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 2,
    "near_margin_loss_tuning_candidate": 1,
    "pair_passes": 75
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.7163294039200991,
    "mean": 0.23179107091019455,
    "median": 0.16991978883743286,
    "min": -0.029570043087005615
  }
}
```

## Top Contexts

```json
[
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "b36178f6655c5f75",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 3
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.11721611721611722,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.005948873492540974,
    "min_delay_risk_margin": -0.003044635057449341,
    "min_raw_margin": -0.008139073848724365,
    "pair_count": 4,
    "pair_pass_count": 3,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "84ae11479ed592d4",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.09090909090909091,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.021563636362821936,
    "min_delay_risk_margin": -0.012455075979232788,
    "min_raw_margin": -0.026709556579589844,
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
    "min_admission_margin": -0.04331384452440551,
    "min_delay_risk_margin": -0.031283020973205566,
    "min_raw_margin": -0.029570043087005615,
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
    "mean_path_token_jaccard": 0.11145510835913312,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": 0.13484283891794352,
    "min_delay_risk_margin": 0.09535819292068481,
    "min_raw_margin": 0.11497962474822998,
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
    "min_admission_margin": 0.1056875481967729,
    "min_delay_risk_margin": 0.04040604829788208,
    "min_raw_margin": 0.13447612524032593,
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
    "min_admission_margin": 0.23960427290181036,
    "min_delay_risk_margin": 0.19655543565750122,
    "min_raw_margin": 0.3783438801765442,
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
    "min_admission_margin": 0.03802402732726462,
    "min_delay_risk_margin": 0.032294780015945435,
    "min_raw_margin": 0.04291236400604248,
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
    "min_admission_margin": 0.06137148952778729,
    "min_delay_risk_margin": 0.032878875732421875,
    "min_raw_margin": 0.09253418445587158,
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
    "min_admission_margin": 0.04067382648410034,
    "min_delay_risk_margin": 0.03871062397956848,
    "min_raw_margin": 0.03724372386932373,
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
    "min_admission_margin": 0.1379119335733172,
    "min_delay_risk_margin": 0.11138606071472168,
    "min_raw_margin": 0.10081523656845093,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v139_trainonly_failure_analog_boost_20260623/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v139_trainonly_failure_analog_boost_20260623/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v139_trainonly_failure_analog_boost_20260623/focused_pair_failure_contexts.jsonl
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
