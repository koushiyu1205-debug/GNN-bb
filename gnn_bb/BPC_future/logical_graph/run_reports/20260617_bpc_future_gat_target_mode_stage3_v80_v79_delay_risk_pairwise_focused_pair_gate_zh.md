# GAT Batch Impact Individual Context Ranking 审计报告

日期：2026-06-16

## 目的

审计同一 RMP context 内 positive trajectory target 是否被当前模型排在 delay / hard-negative target 前面。该脚本只读 dataset 和 checkpoint，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
gat_batch_impact_individual_context_ranking = current
status = gat_batch_impact_individual_context_ranking_audited
focused_row_count = 9
context_count = 3
contexts_with_positive_and_negative = 2
positive_row_count = 2
negative_row_count = 7
pair_count = 4
raw_pair_pass_rate = 1.0
admission_pair_pass_rate = 1.0
delay_risk_pair_pass_rate = 0.5
strict_pair_pass_rate = 0.5
primary = delay_risk_head_context_ranking_failure
focused_pair_gate_pass = False
focused_pair_gate_reject_reasons = ['delay_risk_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
stage3_focused_pair_gate_ready = False
recommended_next_step = calibrate_delay_risk_head_with_context_local_positive_negative_pairs
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## Recommended Next Step

```json
{
  "primary": "calibrate_delay_risk_head_with_context_local_positive_negative_pairs",
  "reason": "positive_targets_have_delay_risk_not_lower_than_hard_negatives"
}
```

## Focused Pair Gate

```json
{
  "blocking_primary": "delay_risk_head_context_ranking_failure",
  "diagnostic_only": true,
  "gate_name": "focused_same_context_positive_negative_pair_gate",
  "gate_pass": false,
  "observed": {
    "admission_pair_pass_rate": 1.0,
    "delay_risk_pair_pass_rate": 0.5,
    "pair_count": 4,
    "raw_pair_pass_rate": 1.0,
    "strict_pair_pass_rate": 0.5
  },
  "production_ready": false,
  "reject_reasons": [
    "delay_risk_pair_pass_rate_below_threshold",
    "strict_pair_pass_rate_below_threshold"
  ],
  "selector_can_certificate": false,
  "thresholds": {
    "min_admission_pair_pass_rate": 1.0,
    "min_delay_risk_pair_pass_rate": 1.0,
    "min_focused_pair_count": 1,
    "min_raw_pair_pass_rate": 1.0,
    "min_strict_pair_pass_rate": 1.0
  }
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_focused_pair_gate_v80_v79_delay_risk_pairwise_smoke_20260617/summary.json
scored_rows = BPC_future/results/gat_batch_impact_focused_pair_gate_v80_v79_delay_risk_pairwise_smoke_20260617/scored_individual_rows.jsonl
context_rows = BPC_future/results/gat_batch_impact_focused_pair_gate_v80_v79_delay_risk_pairwise_smoke_20260617/context_ranking_rows.jsonl
pair_rows = BPC_future/results/gat_batch_impact_focused_pair_gate_v80_v79_delay_risk_pairwise_smoke_20260617/positive_negative_pair_rows.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
