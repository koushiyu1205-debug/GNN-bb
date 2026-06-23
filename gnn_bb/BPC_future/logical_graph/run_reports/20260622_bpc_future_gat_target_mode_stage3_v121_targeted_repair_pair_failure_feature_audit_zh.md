# 2026-06-22 BPC_future GAT Stage 3 v121 Focused Pair Failure Anatomy 报告

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
raw_fail_rate = 0.02564102564102564
admission_fail_rate = 0.02564102564102564
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
    "max": 0.3481724366394905,
    "mean": 0.16373979348678716,
    "median": 0.1536277553812741,
    "min": -0.0450292435463035
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.48104408383369446,
    "mean": 0.1477065846706048,
    "median": 0.10039547085762024,
    "min": -0.020606905221939087
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 1,
    "near_margin_loss_tuning_candidate": 1,
    "pair_passes": 75,
    "shared_signature_confounder": 1
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.6885287836194038,
    "mean": 0.2692128212477725,
    "median": 0.1704425811767578,
    "min": -0.041422486305236816
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
    "context_hash": "9f80ae35ea87da5b",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "shared_signature_confounder": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.05102040816326531,
    "mean_signature_jaccard": 0.015625,
    "min_admission_margin": -0.0450292435463035,
    "min_delay_risk_margin": -0.020606905221939087,
    "min_raw_margin": -0.041422486305236816,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "shared_signature_confounder",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 1,
    "task_count": 30
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "ddcb5387bef3bf63",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.2,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.001989144208003335,
    "min_delay_risk_margin": -0.004725515842437744,
    "min_raw_margin": 0.011774718761444092,
    "pair_count": 1,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 0,
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
    "min_admission_margin": 0.10430942664950221,
    "min_delay_risk_margin": 0.07208344340324402,
    "min_raw_margin": 0.10648643970489502,
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
    "min_admission_margin": 0.061074683221435194,
    "min_delay_risk_margin": 0.022164523601531982,
    "min_raw_margin": 0.09403914213180542,
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
    "min_admission_margin": 0.02154872865931845,
    "min_delay_risk_margin": 0.01654738187789917,
    "min_raw_margin": 0.0168989896774292,
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
    "min_admission_margin": 0.24133429046314103,
    "min_delay_risk_margin": 0.1893036961555481,
    "min_raw_margin": 0.47313670814037323,
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
    "min_admission_margin": 0.2248708350311064,
    "min_delay_risk_margin": 0.21110457181930542,
    "min_raw_margin": 0.44566862285137177,
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
    "min_admission_margin": 0.04286225354495629,
    "min_delay_risk_margin": 0.020099490880966187,
    "min_raw_margin": 0.07139438390731812,
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
    "min_admission_margin": 0.1114109038175859,
    "min_delay_risk_margin": 0.07090213894844055,
    "min_raw_margin": 0.18927541375160217,
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
    "min_admission_margin": 0.15011850862382187,
    "min_delay_risk_margin": 0.06231546401977539,
    "min_raw_margin": 0.2843174338340759,
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
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v121_targeted_repair_features_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v121_targeted_repair_features_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v121_targeted_repair_features_20260622/focused_pair_failure_contexts.jsonl
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
