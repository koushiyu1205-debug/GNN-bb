# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_010_004_seed729004`
- elapsed: `0.336532` s
- algorithm_status: `BPC_GAP_AVAILABLE`
- certificate_scope: `BPC_NODE_LP_CERTIFIED`
- pricing_state: `CERTIFIED_NO_NEGATIVE`
- root_engine: `b2b_r3_worker`
- worker_pricer_kind: `relaxed_labeling`
- tail_dual_stabilization_enabled: `True`
- pricing_round_count: `7`
- added_column_count: `81`
- final_judge_call_count: `7`
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
- hidden_negative_count: `81`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `None`
- can_certify_no_negative: `True`
- best_reduced_cost: `None`
- final_judge_wall_time: `0.009038`
- resume source: ``
- resume initial columns: `12`
- active columns saved: `84`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 16 | None | None |  |
| 2 | FOUND_NEGATIVE | 16 | None | None |  |
| 3 | FOUND_NEGATIVE | 16 | None | None |  |
| 4 | FOUND_NEGATIVE | 16 | None | None |  |
| 5 | FOUND_NEGATIVE | 16 | None | None |  |
| 6 | FOUND_NEGATIVE | 1 | None | None |  |
| 7 | CERTIFIED_NO_NEGATIVE | 0 | None | None |  |
