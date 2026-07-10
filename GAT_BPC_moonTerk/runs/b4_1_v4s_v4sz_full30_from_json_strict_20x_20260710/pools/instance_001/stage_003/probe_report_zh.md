# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `541.376706` s
- algorithm_status: `BPC_GAP_AVAILABLE`
- certificate_scope: `BPC_NODE_LP_CERTIFIED`
- pricing_state: `CERTIFIED_NO_NEGATIVE`
- pricing_round_count: `4`
- added_column_count: `48`
- final_judge_call_count: `4`
- final_judge phase: `optimization_proof`
- final_judge profile: `V4S`
- final_judge formulation profile: `B4V4_strengthened_pair_weighted_final_tail`
- final_judge phase mode: `proof_only`
- proof-only skipped negative feasibility: `True`
- full-space negative feasibility proof attempted: `False`
- full-space negative feasibility proof can certify: `False`
- final_judge negative_column_count: `0`
- sortie slot-position bounds enabled: `True`
- sortie slot-position bounds rows: `62`
- single-task energy LB enabled: `False`
- single-task energy LB rows: `0`
- single-task shadow LB enabled: `False`
- single-task shadow LB rows: `0`
- triple time-window infeasible cut enabled: `True`
- triple time-window infeasible cut rows: `24`
- quad time-window infeasible cut enabled: `False`
- quad time-window infeasible cut rows: `0`
- hidden_negative_count: `None`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `True`
- best_reduced_cost: `0.0`
- final_judge_wall_time: `15.955575`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_v4s_v4sz_full30_from_json_strict_20x_20260710/pools/instance_001/stage_002/probe.json`
- resume initial columns: `103`
- active columns saved: `151`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 16 | -0.081925 | -0.081925439 |  |
| 2 | FOUND_NEGATIVE | 16 | -0.030283 | -0.030282692 |  |
| 3 | FOUND_NEGATIVE | 16 | -0.011096 | -0.011095638 |  |
| 4 | CERTIFIED_NO_NEGATIVE | 0 | 0.0 | -3.68e-07 | optimization_proof |
