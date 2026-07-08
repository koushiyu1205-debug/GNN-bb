# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `901.937349` s
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
- final_judge_wall_time: `1.8e-05`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_replay_plus_stage001_round3_mtz_proof_600s_payload/plus_stage001_plus_replay_probe.json`
- resume initial columns: `123`
- active columns saved: `125`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.431579839 | -0.894632323 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.08655695 | None |  |
| 3 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
