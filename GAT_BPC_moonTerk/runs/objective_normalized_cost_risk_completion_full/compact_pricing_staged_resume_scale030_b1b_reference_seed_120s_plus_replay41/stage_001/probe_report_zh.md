# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `895.400819` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `4`
- added_column_count: `6`
- final_judge_call_count: `4`
- final_judge phase: `negative_feasibility_batch`
- final_judge negative_column_count: `2`
- compact batch found count: `2`
- compact batch search calls: `3`
- compact no-good scope: `arc`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.026865981`
- final_judge_wall_time: `149.220157`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_replay_plus40_stage001_round3_negative_feas_mtz_endpoint_pair_600s/plus40_stage001_plus_replay_probe.json`
- resume initial columns: `230`
- active columns saved: `236`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.002100312 | -0.645448832 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.032724104 | -0.032723716 |  |
| 3 | FOUND_NEGATIVE | 2 | -0.032337157 | -0.646345029 |  |
| 4 | FOUND_NEGATIVE | 2 | -0.026865981 | -0.764124152 | negative_feasibility_batch |
