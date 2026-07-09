# 30-scale Compact Pricing Batch Probe

该 probe 只验证 batch negative discovery，不是 BPC certificate。

- instance: `lunar_ice_sp50_030_001_seed929001`
- elapsed: `54.964319` s
- algorithm_status: `BPC_INCOMPLETE_PRICING`
- certificate_scope: `DIAGNOSTIC_PRICING_FRONTIER`
- pricing_state: `INCOMPLETE_LIMIT`
- pricing_round_count: `1`
- added_column_count: `0`
- final_judge_call_count: `1`
- final_judge phase: `negative_feasibility_proof`
- final_judge profile: `V4`
- final_judge formulation profile: `B4V4_endpoint_pair_latest_start_time_window`
- final_judge phase mode: `feasibility_proof_only`
- proof-only skipped negative feasibility: `False`
- full-space negative feasibility proof attempted: `True`
- full-space negative feasibility proof can certify: `False`
- final_judge negative_column_count: `0`
- compact batch found count: `None`
- compact batch search calls: `None`
- compact no-good scope: `None`
- forbidden task-set count: `0`
- can_certify_no_negative: `False`
- best_reduced_cost: `None`
- final_judge_wall_time: `54.669812`
- resume source: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_merged_staged_resume/stage_004/probe.json`
- resume initial columns: `304`
- active columns saved: `304`

证书边界：restricted negative-feasibility discovery 只能返回人工 RC 审计过的负列；不能证明 no-negative。

## Pricing History

| round | state | added | best RC | dual bound | phase |
|---:|---|---:|---:|---:|---|
| 1 | INCOMPLETE_LIMIT | 0 | None | -0.192185417 | negative_feasibility_proof |
