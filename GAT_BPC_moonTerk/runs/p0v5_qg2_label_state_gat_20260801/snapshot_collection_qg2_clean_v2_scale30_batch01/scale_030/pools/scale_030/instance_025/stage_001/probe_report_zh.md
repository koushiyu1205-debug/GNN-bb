# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_030_025_seed110748001`
- elapsed: `292.745613` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- root_engine: `b2b_r3_worker`
- worker_pricer_kind: `relaxed_labeling`
- tail_dual_stabilization_enabled: `True`
- pricing_round_count: `30`
- added_column_count: `1662`
- final_judge_call_count: `30`
- final_judge phase: `None`
- final_judge profile: `None`
- final_judge formulation profile: `None`
- final_judge phase mode: `None`
- proof-only skipped negative feasibility: `None`
- full-space negative feasibility proof attempted: `None`
- full-space negative feasibility proof can certify: `None`
- final_judge negative_column_count: `None`
- sortie slot-position bounds enabled: `None`
- sortie slot-position bounds rows: `None`
- single-task energy LB enabled: `None`
- single-task energy LB rows: `None`
- single-task shadow LB enabled: `None`
- single-task shadow LB rows: `None`
- triple time-window infeasible cut enabled: `None`
- triple time-window infeasible cut rows: `None`
- quad time-window infeasible cut enabled: `None`
- quad time-window infeasible cut rows: `None`
- hidden_negative_count: `5911`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `272.463385`
- resume source: ``
- resume initial columns: `34`
- active columns saved: `1696`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 64 | None | None |  |
| 2 | FOUND_NEGATIVE | 64 | None | None |  |
| 3 | FOUND_NEGATIVE | 64 | None | None |  |
| 4 | FOUND_NEGATIVE | 64 | None | None |  |
| 5 | FOUND_NEGATIVE | 64 | None | None |  |
| 6 | FOUND_NEGATIVE | 64 | None | None |  |
| 7 | FOUND_NEGATIVE | 64 | None | None |  |
| 8 | FOUND_NEGATIVE | 64 | None | None |  |
| 9 | FOUND_NEGATIVE | 64 | None | None |  |
| 10 | FOUND_NEGATIVE | 64 | None | None |  |
| 11 | FOUND_NEGATIVE | 64 | None | None |  |
| 12 | FOUND_NEGATIVE | 64 | None | None |  |
| 13 | FOUND_NEGATIVE | 64 | None | None |  |
| 14 | FOUND_NEGATIVE | 64 | None | None |  |
| 15 | FOUND_NEGATIVE | 64 | None | None |  |
| 16 | FOUND_NEGATIVE | 64 | None | None |  |
| 17 | FOUND_NEGATIVE | 64 | None | None |  |
| 18 | FOUND_NEGATIVE | 64 | None | None |  |
| 19 | FOUND_NEGATIVE | 64 | None | None |  |
| 20 | FOUND_NEGATIVE | 64 | None | None |  |
| 21 | FOUND_NEGATIVE | 64 | None | None |  |
| 22 | FOUND_NEGATIVE | 64 | None | None |  |
| 23 | FOUND_NEGATIVE | 64 | None | None |  |
| 24 | FOUND_NEGATIVE | 64 | None | None |  |
| 25 | FOUND_NEGATIVE | 8 | None | None |  |
| 26 | FOUND_NEGATIVE | 30 | None | None |  |
| 27 | FOUND_NEGATIVE | 18 | None | None |  |
| 28 | FOUND_NEGATIVE | 61 | None | None |  |
| 29 | FOUND_NEGATIVE | 9 | None | None |  |
| 30 | INCOMPLETE_LIMIT | 0 | None | None |  |
