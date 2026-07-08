# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `3601.909562` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `15`
- added_column_count: `54`
- final_judge_call_count: `15`
- final_judge phase: `negative_feasibility_search`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `1.9e-05`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 5 | -0.6131805 | -1.287131994 |  |
| 2 | FOUND_NEGATIVE | 1 | -0.951808835 | -2.573342394 |  |
| 3 | FOUND_NEGATIVE | 5 | -0.797246 | -1.61955596 |  |
| 4 | FOUND_NEGATIVE | 5 | -0.702748 | -1.238773359 |  |
| 5 | FOUND_NEGATIVE | 5 | -0.437801124 | -1.448835622 |  |
| 6 | FOUND_NEGATIVE | 5 | -0.8088484 | -1.772190625 |  |
| 7 | FOUND_NEGATIVE | 1 | -1.074414574 | -1.074414672 |  |
| 8 | FOUND_NEGATIVE | 2 | -0.427382613 | -1.075781302 |  |
| 9 | FOUND_NEGATIVE | 5 | -0.42815992 | -1.03426661 |  |
| 10 | FOUND_NEGATIVE | 5 | -0.355777582 | -1.160644788 |  |
| 11 | FOUND_NEGATIVE | 5 | -0.64046483 | -1.823567144 |  |
| 12 | FOUND_NEGATIVE | 5 | -1.040323819 | -1.729772461 |  |
| 13 | FOUND_NEGATIVE | 1 | -0.061620685 | -1.121657769 |  |
| 14 | FOUND_NEGATIVE | 4 | -0.434447059 | None |  |
| 15 | INCOMPLETE_LIMIT | 0 | None | None | negative_feasibility_search |
