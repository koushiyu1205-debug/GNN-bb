# GAT Online Target Intervention Protocol 报告

日期：2026-06-14

## 目的

本报告把 GAT ROI 样本采集收紧为同上下文目标干预协议。它只写协议，
不运行 BPC / pricing / RMP / Pulse / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_online_target_intervention_protocol = current
status = gat_online_target_intervention_protocol_ready
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
required_exact_context_component_count = 11
required_worker_diagnostic_count = 14
all_checks_pass = true
```

## 为什么当前有效样本稀疏

- 离线 A/B 很难回到候选出现时的同一个 dual / cuts / branch / pool 上下文；
- worker 经常因为 context mismatch 没有真实处理目标候选；
- 有些表面正 ROI 来自旁支 harvested column，不能归因到目标候选；
- 因此这些记录必须进 invalid bucket，不能当 GAT 正负标签。

## Required Exact Context Components

- `context_hash`
- `true_dual_hash`
- `cuts_hash`
- `branch_hash`
- `forbidden_signature_hash`
- `pool_signature_hash`
- `active_hash_before`
- `pricing_config_hash`
- `target_sequence`
- `target_arc_option_sequence`
- `worker_context_hash`

## Required Worker Diagnostics

- `journey_sharded_pulse_hidden_negative_worker_log_skips`
- `journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled`
- `journey_sharded_pulse_hidden_negative_worker_expected_context_hash`
- `pulse_worker_context_hash`
- `pulse_worker_enabled`
- `pulse_worker_skipped`
- `pulse_worker_skip_reason`
- `pulse_worker_target_transition_priority_sequence`
- `pulse_worker_target_arc_option_priority_sequence`
- `pulse_worker_target_sequence_completed`
- `pulse_worker_target_sequence_materialized`
- `pulse_worker_target_sequence_negative`
- `pulse_worker_returned_candidate_sequence_samples`
- `pulse_worker_harvested_sequence_samples`

## Label Acceptance Rules

```json
{
  "invalid_not_label": [
    "context_mismatch",
    "worker_context_mismatch",
    "missing_worker_diagnostics",
    "no_worker_target_intervention_observed",
    "positive_roi_without_target_causal_match",
    "roi_without_target_causal_match",
    "certificate_or_official_bound_effect",
    "missing_baseline_or_worker_result"
  ],
  "no_observed_or_negative_roi": [
    "all required exact context components match",
    "worker target intervention is observed",
    "target causal match is observed in worker diagnostics",
    "target column is true-RC negative under the same context",
    "fixed follow-up horizon shows no RMP/tail improvement"
  ],
  "positive_roi": [
    "all required exact context components match",
    "worker target intervention is observed",
    "target causal match is observed in worker diagnostics",
    "target column is true-RC negative under the same context",
    "follow-up RMP/tail metric improves without certificate or official-bound effect"
  ]
}
```

## Collection Steps

- capture candidate and full context before the RMP basis changes
- run the target worker/probe in the same context, or mark the row invalid
- require exact component match before assigning any ROI label
- require worker target diagnostics and target causal match for every training label
- record context mismatch as invalid/unreachable, never as a negative label
- keep true-RC negative columns in HIGH_PRIORITY or DELAY_QUEUE only; never discard them

## Current ROI Dataset Fields

```json
{
  "no_worker_target_intervention_count": 10,
  "positive_roi_without_target_causal_match_count": 2,
  "roi_without_target_causal_match_count": 0,
  "row_count": 13,
  "target_causal_match_count": 0,
  "target_diag_available_count": 3,
  "target_intervention_observed_count": 2,
  "training_ready": false,
  "training_row_count": 0,
  "unique_training_row_count": 0,
  "worker_context_match_count": 2,
  "worker_context_mismatch_count": 1
}
```

## Checks

```json
{
  "context_mismatch_is_not_a_negative_label": true,
  "default_enabled_false": true,
  "delay_queue_preserves_completeness": true,
  "diagnostic_only": true,
  "no_certificate_or_official_bound_effect": true,
  "requires_dual_cut_branch_context": true,
  "requires_target_causal_match_for_positive_and_negative_labels": true,
  "requires_worker_log_skips_and_target_diagnostics": true,
  "roi_dataset_guard_fields_present": true,
  "runs_bpc_or_pricing_false": true,
  "selector_context_protocol_available": true
}
```

## 结论

- 有效样本必须是同上下文、目标候选真实干预、目标因果匹配后的 ROI 观察；
- `context_mismatch` / 未干预 / 非目标收益都不是负样本；
- 通过安全壳的 true-RC negative 可进 HIGH_PRIORITY，未通过的进 DELAY_QUEUE；
- DELAY_QUEUE 不能永久丢弃负列，也不能参与证书或官方下界。
