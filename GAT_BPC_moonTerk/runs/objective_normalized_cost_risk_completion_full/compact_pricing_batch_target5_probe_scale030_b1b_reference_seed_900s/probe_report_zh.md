# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `901.869275` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `4`
- added_column_count: `15`
- final_judge_call_count: `4`
- final_judge phase: `negative_feasibility_batch`
- final_judge negative_column_count: `4`
- compact batch found count: `4`
- compact batch search calls: `5`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.702748`
- final_judge_wall_time: `224.792724`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 5 | -0.6131805 | -1.287131994 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.951808835 | -2.573342394 |  |
| 3 | FOUND_NEGATIVE | 5 | -0.797246 | -1.619908553 |  |
| 4 | FOUND_NEGATIVE | 4 | -0.702748 | None | negative_feasibility_batch |
