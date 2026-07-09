# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_002_seed929002`
- elapsed: `301.673772` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `2`
- added_column_count: `5`
- final_judge_call_count: `2`
- final_judge phase: `negative_feasibility_search`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `17.318425`
- resume source: ``
- resume initial columns: `0`
- active columns saved: `39`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 5 | -1.166929 | -2.119130268 |  |
| 2 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
