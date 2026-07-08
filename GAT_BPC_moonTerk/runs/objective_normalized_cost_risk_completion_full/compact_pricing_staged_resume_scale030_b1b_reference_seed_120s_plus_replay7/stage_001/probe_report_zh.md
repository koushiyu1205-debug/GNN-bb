# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `901.892043` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `2`
- final_judge_call_count: `3`
- final_judge phase: `negative_feasibility_search`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `17.400877`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_replay_plus6_stage001_round2_negative_feas_mtz_600s/plus6_stage001_plus_replay_probe.json`
- resume initial columns: `141`
- active columns saved: `143`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.805300006 | -0.805299748 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.796544569 | -1.341098527 |  |
| 3 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
