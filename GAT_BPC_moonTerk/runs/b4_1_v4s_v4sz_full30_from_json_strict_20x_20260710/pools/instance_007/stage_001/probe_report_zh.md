# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_007_seed929007`
- elapsed: `41.048882` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `1`
- added_column_count: `5`
- final_judge_call_count: `1`
- final_judge phase: `optimization_harvest`
- final_judge profile: `V4S`
- final_judge formulation profile: `B4V4_strengthened_pair_weighted_final_tail`
- final_judge phase mode: `proof_only`
- proof-only skipped negative feasibility: `True`
- full-space negative feasibility proof attempted: `False`
- full-space negative feasibility proof can certify: `False`
- final_judge negative_column_count: `5`
- sortie slot-position bounds enabled: `True`
- sortie slot-position bounds rows: `44`
- single-task energy LB enabled: `False`
- single-task energy LB rows: `0`
- single-task shadow LB enabled: `False`
- single-task shadow LB rows: `0`
- triple time-window infeasible cut enabled: `True`
- triple time-window infeasible cut rows: `40`
- quad time-window infeasible cut enabled: `False`
- quad time-window infeasible cut rows: `0`
- hidden_negative_count: `None`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `arc`
- optimization harvest target: `5`
- optimization harvest no-good scope: `task_set`
- optimization harvest found count: `5`
- forbidden task-set count: `5`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.556646335`
- final_judge_wall_time: `41.02279`
- resume source: ``
- resume initial columns: `0`
- active columns saved: `39`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 5 | -0.556646335 | -0.556646116 | optimization_harvest |
