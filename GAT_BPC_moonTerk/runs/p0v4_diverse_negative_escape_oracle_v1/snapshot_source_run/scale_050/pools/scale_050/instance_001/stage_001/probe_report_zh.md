# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_050_001_seed1129001`
- elapsed: `3604.541139` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- root_engine: `b2b_r3_worker`
- worker_pricer_kind: `relaxed_labeling`
- tail_dual_stabilization_enabled: `True`
- pricing_round_count: `110`
- added_column_count: `13132`
- final_judge_call_count: `110`
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
- hidden_negative_count: `105458`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.002287`
- final_judge_wall_time: `78.650846`
- resume source: ``
- resume initial columns: `55`
- active columns saved: `13174`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 128 | None | None |  |
| 2 | FOUND_NEGATIVE | 128 | None | None |  |
| 3 | FOUND_NEGATIVE | 128 | None | None |  |
| 4 | FOUND_NEGATIVE | 128 | None | None |  |
| 5 | FOUND_NEGATIVE | 128 | None | None |  |
| 6 | FOUND_NEGATIVE | 128 | None | None |  |
| 7 | FOUND_NEGATIVE | 128 | None | None |  |
| 8 | FOUND_NEGATIVE | 128 | None | None |  |
| 9 | FOUND_NEGATIVE | 128 | None | None |  |
| 10 | FOUND_NEGATIVE | 128 | None | None |  |
| 11 | FOUND_NEGATIVE | 128 | None | None |  |
| 12 | FOUND_NEGATIVE | 128 | None | None |  |
| 13 | FOUND_NEGATIVE | 128 | None | None |  |
| 14 | FOUND_NEGATIVE | 128 | None | None |  |
| 15 | FOUND_NEGATIVE | 128 | None | None |  |
| 16 | FOUND_NEGATIVE | 128 | None | None |  |
| 17 | FOUND_NEGATIVE | 128 | None | None |  |
| 18 | FOUND_NEGATIVE | 128 | None | None |  |
| 19 | FOUND_NEGATIVE | 128 | None | None |  |
| 20 | FOUND_NEGATIVE | 128 | None | None |  |
| 21 | FOUND_NEGATIVE | 128 | None | None |  |
| 22 | FOUND_NEGATIVE | 128 | None | None |  |
| 23 | FOUND_NEGATIVE | 128 | None | None |  |
| 24 | FOUND_NEGATIVE | 128 | None | None |  |
| 25 | FOUND_NEGATIVE | 128 | None | None |  |
| 26 | FOUND_NEGATIVE | 128 | None | None |  |
| 27 | FOUND_NEGATIVE | 128 | None | None |  |
| 28 | FOUND_NEGATIVE | 128 | None | None |  |
| 29 | FOUND_NEGATIVE | 128 | None | None |  |
| 30 | FOUND_NEGATIVE | 128 | None | None |  |
| 31 | FOUND_NEGATIVE | 128 | None | None |  |
| 32 | FOUND_NEGATIVE | 128 | None | None |  |
| 33 | FOUND_NEGATIVE | 128 | None | None |  |
| 34 | FOUND_NEGATIVE | 128 | None | None |  |
| 35 | FOUND_NEGATIVE | 128 | None | None |  |
| 36 | FOUND_NEGATIVE | 128 | None | None |  |
| 37 | FOUND_NEGATIVE | 128 | None | None |  |
| 38 | FOUND_NEGATIVE | 128 | None | None |  |
| 39 | FOUND_NEGATIVE | 128 | None | None |  |
| 40 | FOUND_NEGATIVE | 128 | None | None |  |
| 41 | FOUND_NEGATIVE | 128 | None | None |  |
| 42 | FOUND_NEGATIVE | 128 | None | None |  |
| 43 | FOUND_NEGATIVE | 128 | None | None |  |
| 44 | FOUND_NEGATIVE | 128 | None | None |  |
| 45 | FOUND_NEGATIVE | 128 | None | None |  |
| 46 | FOUND_NEGATIVE | 128 | None | None |  |
| 47 | FOUND_NEGATIVE | 128 | None | None |  |
| 48 | FOUND_NEGATIVE | 12 | None | None |  |
| 49 | FOUND_NEGATIVE | 128 | None | None |  |
| 50 | FOUND_NEGATIVE | 5 | None | None |  |
| 51 | FOUND_NEGATIVE | 128 | None | None |  |
| 52 | FOUND_NEGATIVE | 128 | None | None |  |
| 53 | FOUND_NEGATIVE | 128 | None | None |  |
| 54 | FOUND_NEGATIVE | 128 | None | None |  |
| 55 | FOUND_NEGATIVE | 60 | None | None |  |
| 56 | FOUND_NEGATIVE | 128 | None | None |  |
| 57 | FOUND_NEGATIVE | 128 | None | None |  |
| 58 | FOUND_NEGATIVE | 128 | None | None |  |
| 59 | FOUND_NEGATIVE | 128 | None | None |  |
| 60 | FOUND_NEGATIVE | 128 | None | None |  |
| 61 | FOUND_NEGATIVE | 128 | None | None |  |
| 62 | FOUND_NEGATIVE | 128 | None | None |  |
| 63 | FOUND_NEGATIVE | 128 | None | None |  |
| 64 | FOUND_NEGATIVE | 128 | None | None |  |
| 65 | FOUND_NEGATIVE | 128 | None | None |  |
| 66 | FOUND_NEGATIVE | 128 | None | None |  |
| 67 | FOUND_NEGATIVE | 128 | None | None |  |
| 68 | FOUND_NEGATIVE | 128 | None | None |  |
| 69 | FOUND_NEGATIVE | 128 | None | None |  |
| 70 | FOUND_NEGATIVE | 128 | None | None |  |
| 71 | FOUND_NEGATIVE | 128 | None | None |  |
| 72 | FOUND_NEGATIVE | 128 | None | None |  |
| 73 | FOUND_NEGATIVE | 128 | None | None |  |
| 74 | FOUND_NEGATIVE | 128 | None | None |  |
| 75 | FOUND_NEGATIVE | 128 | None | None |  |
| 76 | FOUND_NEGATIVE | 95 | None | None |  |
| 77 | FOUND_NEGATIVE | 128 | None | None |  |
| 78 | FOUND_NEGATIVE | 128 | None | None |  |
| 79 | FOUND_NEGATIVE | 128 | None | None |  |
| 80 | FOUND_NEGATIVE | 128 | None | None |  |
| 81 | FOUND_NEGATIVE | 128 | None | None |  |
| 82 | FOUND_NEGATIVE | 45 | None | None |  |
| 83 | FOUND_NEGATIVE | 28 | None | None |  |
| 84 | FOUND_NEGATIVE | 128 | None | None |  |
| 85 | FOUND_NEGATIVE | 128 | None | None |  |
| 86 | FOUND_NEGATIVE | 128 | None | None |  |
| 87 | FOUND_NEGATIVE | 128 | None | None |  |
| 88 | FOUND_NEGATIVE | 128 | None | None |  |
| 89 | FOUND_NEGATIVE | 128 | None | None |  |
| 90 | FOUND_NEGATIVE | 128 | None | None |  |
| 91 | FOUND_NEGATIVE | 128 | None | None |  |
| 92 | FOUND_NEGATIVE | 128 | None | None |  |
| 93 | FOUND_NEGATIVE | 128 | None | None |  |
| 94 | FOUND_NEGATIVE | 128 | None | None |  |
| 95 | FOUND_NEGATIVE | 128 | None | None |  |
| 96 | FOUND_NEGATIVE | 47 | None | None |  |
| 97 | FOUND_NEGATIVE | 54 | None | None |  |
| 98 | FOUND_NEGATIVE | 128 | None | None |  |
| 99 | FOUND_NEGATIVE | 63 | None | None |  |
| 100 | FOUND_NEGATIVE | 128 | None | None |  |
| 101 | FOUND_NEGATIVE | 128 | None | None |  |
| 102 | FOUND_NEGATIVE | 128 | None | None |  |
| 103 | FOUND_NEGATIVE | 128 | None | None |  |
| 104 | FOUND_NEGATIVE | 128 | None | None |  |
| 105 | FOUND_NEGATIVE | 128 | None | None |  |
| 106 | FOUND_NEGATIVE | 128 | None | None |  |
| 107 | FOUND_NEGATIVE | 81 | None | None |  |
| 108 | FOUND_NEGATIVE | 86 | None | None |  |
| 109 | FOUND_NEGATIVE | 12 | None | None |  |
| 110 | FOUND_NEGATIVE | 128 | None | None |  |
