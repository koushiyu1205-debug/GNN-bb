# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_003_seed929003`
- elapsed: `301.512277` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `2`
- final_judge_call_count: `3`
- final_judge phase: `optimization_proof`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `49.737684`
- resume source: ``
- resume initial columns: `0`
- active columns saved: `36`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -1.023929 | -1.023929436 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.422827 | -0.422827311 |  |
| 3 | INCOMPLETE_LIMIT | 0 | None | None | optimization_proof |
