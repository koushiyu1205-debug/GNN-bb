# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `301.312432` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `3`
- added_column_count: `3`
- final_judge_call_count: `3`
- final_judge phase: `negative_feasibility_batch`
- final_judge negative_column_count: `1`
- compact batch found count: `1`
- compact batch search calls: `2`
- compact no-good scope: `arc`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.272798`
- final_judge_wall_time: `59.762075`
- resume source: ``
- resume initial columns: `0`
- active columns saved: `37`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 1 | -0.6281595 | -0.628159107 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.487677145 | -0.487677531 |  |
| 3 | FOUND_NEGATIVE | 1 | -0.272798 | None | negative_feasibility_batch |
