# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `900.775941` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `4`
- added_column_count: `7`
- final_judge_call_count: `4`
- final_judge phase: `negative_feasibility_search`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `3.025248`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/objective_normalized_cost_risk_completion_full/compact_pricing_staged_resume_scale030_b1b_reference_seed_120s_plus_replay20/stage_001/probe.json`
- resume initial columns: `168`
- active columns saved: `175`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.402817848 | -0.402818291 |  |
| 2 | FOUND_NEGATIVE | 5 | -0.160621029 | -1.5601912 |  |
| 3 | FOUND_NEGATIVE | 1 | -0.028621121 | -3.450557979 |  |
| 4 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
