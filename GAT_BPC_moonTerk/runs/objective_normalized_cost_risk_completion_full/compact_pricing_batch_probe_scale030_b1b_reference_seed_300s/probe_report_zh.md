# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `301.900636` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `2`
- added_column_count: `5`
- final_judge_call_count: `2`
- final_judge phase: `negative_feasibility_batch`
- final_judge negative_column_count: `2`
- compact batch found count: `2`
- compact batch search calls: `3`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.365212183`
- final_judge_wall_time: `127.289314`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 3 | -0.6131805 | -1.177230903 |  |
| 2 | FOUND_NEGATIVE | 2 | -0.365212183 | None | negative_feasibility_batch |
