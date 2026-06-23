# 2026-06-22 BPC_future GAT Stage 3 v122 Focused Pair Failure Anatomy 报告

## 目的

对指定 checkpoint 的 focused same-context positive/negative pair failures 做离线分类，
判断失败更像 near-margin loss tuning 问题，还是 candidate/action-consequence
表示结构性不可分问题。该审计只读 metrics / dataset，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_focused_pair_failure_audit = current
status = gat_batch_impact_focused_pair_failures_audited
pair_count = 78
failed_pair_count = 19
strict_pair_pass_rate = 0.7564102564102564
raw_fail_rate = 0.21794871794871795
admission_fail_rate = 0.19230769230769232
delay_risk_fail_rate = 0.21794871794871795
all_failed_heads_near_rate_among_failed = 0.7368421052631579
any_failed_head_deep_rate_among_failed = 0.0
signature_overlap_pair_rate = 0.2564102564102564
path_token_jaccard_median = 0.05263157894736842
primary = pair_passes
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused pair 总数：`78`，失败：`19`。
- near-margin 失败占失败 pair：`0.7368421052631579`。
- deep 失败占失败 pair：`0.0`。
- signature overlap pair rate：`0.2564102564102564`。
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
    "count": 78,
    "max": 0.05849898839555098,
    "mean": 0.013989812300061067,
    "median": 0.013227632952211285,
    "min": -0.01917585212699341
  },
  "delay_risk_margin_stats": {
    "count": 78,
    "max": 0.06510946154594421,
    "mean": 0.015786963013502266,
    "median": 0.010897815227508545,
    "min": -0.02293318510055542
  },
  "diagnosis_counts": {
    "mixed_margin_failure": 5,
    "near_margin_loss_tuning_candidate": 14,
    "pair_passes": 59
  },
  "raw_margin_stats": {
    "count": 78,
    "max": 0.04675754904747009,
    "mean": 0.012507487566043168,
    "median": 0.012074634432792664,
    "min": -0.03585183620452881
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
    "context_hash": "5c522ff2995f86be",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 2,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.017361188770361524,
    "min_delay_risk_margin": -0.011590391397476196,
    "min_raw_margin": -0.03585183620452881,
    "pair_count": 3,
    "pair_pass_count": 1,
    "primary": "mixed_margin_failure",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "f9d0b6b18a0a28d3",
    "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.005740998284416016,
    "min_delay_risk_margin": -0.007439136505126953,
    "min_raw_margin": -0.004982262849807739,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "62c86745ed2b3aaa",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0036396177893962822,
    "min_delay_risk_margin": -0.002619236707687378,
    "min_raw_margin": -0.006235480308532715,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 2,
    "any_failed_head_deep_count": 0,
    "context_hash": "4575716b3939cb89",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.001441481579259829,
    "min_delay_risk_margin": -0.001836538314819336,
    "min_raw_margin": -0.001373291015625,
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
    "context_hash": "ff6827bb236f4831",
    "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.0,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.015994653986089236,
    "min_delay_risk_margin": -0.02293318510055542,
    "min_raw_margin": -0.009389936923980713,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 2,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "9eb0dc7839bf91ec",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
    "delay_risk_fail_count": 2,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "near_margin_loss_tuning_candidate": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 2,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.045454545454545456,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.009791765590767526,
    "min_delay_risk_margin": -0.007726222276687622,
    "min_raw_margin": -0.01520487666130066,
    "pair_count": 2,
    "pair_pass_count": 0,
    "primary": "near_margin_loss_tuning_candidate",
    "raw_fail_count": 2,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "4e481a6307fca228",
    "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 9
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "sector-wave",
    "mean_path_token_jaccard": 0.11145510835913312,
    "mean_signature_jaccard": 0.06875,
    "min_admission_margin": 0.00017500445305251855,
    "min_delay_risk_margin": -0.007517814636230469,
    "min_raw_margin": 0.007263839244842529,
    "pair_count": 10,
    "pair_pass_count": 9,
    "primary": "pair_passes",
    "raw_fail_count": 0,
    "signature_overlap_pair_count": 8,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "67925c0d2fd4abde",
    "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "greedy-anchor",
    "mean_path_token_jaccard": 0.027777777777777776,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": -0.0027128307924813855,
    "min_delay_risk_margin": -0.0034747421741485596,
    "min_raw_margin": -0.0022405385971069336,
    "pair_count": 3,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 0,
    "all_failed_heads_near_count": 1,
    "any_failed_head_deep_count": 0,
    "context_hash": "7cb380a02e30e5a8",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
    "delay_risk_fail_count": 0,
    "diagnosis_counts": {
      "near_margin_loss_tuning_candidate": 1,
      "pair_passes": 2
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.08333333333333333,
    "mean_signature_jaccard": 0.0,
    "min_admission_margin": 0.00917548445597935,
    "min_delay_risk_margin": 0.018236994743347168,
    "min_raw_margin": -0.0018843114376068115,
    "pair_count": 3,
    "pair_pass_count": 2,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 0,
    "task_count": 20
  },
  {
    "admission_fail_count": 1,
    "all_failed_heads_near_count": 0,
    "any_failed_head_deep_count": 0,
    "context_hash": "5368cf35ed6f06cb",
    "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
    "delay_risk_fail_count": 1,
    "diagnosis_counts": {
      "mixed_margin_failure": 1,
      "pair_passes": 1
    },
    "diagnostic_only": true,
    "failed_pair_count": 1,
    "family": "random-wave",
    "mean_path_token_jaccard": 0.018292682926829267,
    "mean_signature_jaccard": 0.015625,
    "min_admission_margin": -0.01917585212699341,
    "min_delay_risk_margin": -0.01647120714187622,
    "min_raw_margin": -0.023053646087646484,
    "pair_count": 2,
    "pair_pass_count": 1,
    "primary": "pair_passes",
    "raw_fail_count": 1,
    "signature_overlap_pair_count": 1,
    "task_count": 30
  }
]
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v122_train_only_targeted_repair_20260622/summary.json
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v122_train_only_targeted_repair_20260622/focused_pair_failure_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v122_train_only_targeted_repair_20260622/focused_pair_failure_contexts.jsonl
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
