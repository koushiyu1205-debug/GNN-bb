# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_1_true_dual_proof_tail_stage_b_30_v4_optimization_harvest_taskset_after_330_600s/stage_001/probe.json`
- stage_count: `1`
- compact_final_judge_profile: `V4`
- compact_final_judge_phase_mode: `proof_only`
- compact_optimization_harvest_target: `5`
- compact_optimization_harvest_no_good_scope: `task_set`
- compact_service_start_depot_travel_lb: `True`
- compact_task_to_depot_return_travel_lb: `True`
- compact_pair_route_duration_lb: `True`
- compact_sortie_slot_position_bounds: `True`
- compact_demand_cover_cut: `False`
- compact_single_task_energy_lb: `False`
- compact_single_task_shadow_lb: `False`
- compact_pair_energy_lb: `False`
- compact_pair_energy_infeasible_cut: `True`
- compact_pair_shadow_infeasible_cut: `False`
- compact_triple_shadow_infeasible_cut: `False`
- compact_triple_energy_infeasible_cut: `False`

| stage | profile | mode | opt harvest | opt scope | opt found | opt exact neg | opt tl neg | opt tl no-neg | batch | round cap | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final RC | final bound | elapsed s |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|
| 1 | V4 | proof_only | 5 | task_set | 3 | 2 | 1 | 1 | 1 | 1 | 330 | 333 | 3 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | -0.002031375 | optimization_harvest | -0.002031375 | -0.002031064 | 597.64609 |
