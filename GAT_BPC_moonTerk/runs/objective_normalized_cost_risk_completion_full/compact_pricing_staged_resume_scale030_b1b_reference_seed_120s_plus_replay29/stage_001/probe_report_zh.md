# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `900.73988` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `4`
- added_column_count: `3`
- final_judge_call_count: `4`
- final_judge phase: `optimization_proof`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `17.42133`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_replay_plus28_stage001_round3_negative_feas_mtz_endpoint_pair_600s/plus28_stage001_plus_replay_probe.json`
- resume initial columns: `195`
- active columns saved: `198`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.080769275 | -0.080769542 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.038778276 | None |  |
| 3 | FOUND_NEGATIVE | 1 | -0.034545813 | -0.350936966 |  |
| 4 | INCOMPLETE_LIMIT | 0 | None | None | optimization_proof |
