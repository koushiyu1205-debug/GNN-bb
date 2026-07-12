# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `103.627853` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- root_engine: `b2b_r3_worker`
- worker_pricer_kind: `relaxed_labeling`
- tail_dual_stabilization_enabled: `True`
- pricing_round_count: `1`
- added_column_count: `780`
- final_judge_call_count: `1`
- final_judge phase: `None`
- final_judge profile: `None`
- final_judge formulation profile: `None`
- final_judge phase mode: `None`
- proof-only skipped negative feasibility: `None`
- full-space negative feasibility proof attempted: `None`
- full-space negative feasibility proof can certify: `None`
- final_judge negative_column_count: `2583`
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
- hidden_negative_count: `1024`
- hidden_negative_audit status: `None`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- optimization harvest target: `None`
- optimization harvest no-good scope: `None`
- optimization harvest found count: `None`
- forbidden task-set count: `None`
- can_certify_no_negative: `False`
- best_reduced_cost: `-0.328275847`
- final_judge_wall_time: `74.29841`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_3_spprc_round1_tailadaptive64_30_001_1800s_20260712_221000/pools/scale_030/instance_001/stage_003/probe.json`
- resume initial columns: `3106`
- active columns saved: `3884`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | FOUND_NEGATIVE | 780 | None | None |  |
