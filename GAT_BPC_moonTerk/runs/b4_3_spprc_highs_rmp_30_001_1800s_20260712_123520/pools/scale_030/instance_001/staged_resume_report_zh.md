# Compact Pricing Staged Resume Report

该 staged run 只复用 active column pool；每个 stage 都重新解 RMP 和 final judge。
因此 staged resume 不是证书放松，也不会把上一阶段 dual/certificate 带入下一阶段。

- instance: `/home/kai/work/GAT_BPC_moonTerk/data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json`
- latest_probe: `/home/kai/work/GAT_BPC_moonTerk/runs/b4_3_spprc_highs_rmp_30_001_1800s_20260712_123520/pools/scale_030/instance_001/stage_017/probe.json`
- stage_count: `17`
- compact_final_judge_profile: `V4SZ`
- compact_final_judge_phase_mode: `harvest_then_proof`
- compact_optimization_harvest_target: `1024`
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
- compact_triple_time_window_infeasible_cut: `True`
- compact_quad_time_window_infeasible_cut: `False`
- compact_triple_shadow_infeasible_cut: `False`
- compact_triple_energy_infeasible_cut: `False`

| stage | profile | mode | opt harvest | opt scope | opt found | opt exact neg | opt tl neg | opt tl no-neg | feas status | feas neg | feas cert | feas RC | feas bound | batch | round cap | resume cols | active cols | added | rounds | state | scope | best neg RC | final phase | final RC | final bound | elapsed s |
|---:|---|---|---:|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|---:|---:|
| 1 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 34 | 1058 | 1024 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.170673 | None | 13.291024 |
| 2 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 1058 | 2082 | 1024 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.149507334 | None | 13.871858 |
| 3 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 2082 | 3106 | 1024 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.057350079 | None | 15.020826 |
| 4 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 3106 | 4130 | 1024 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.059658 | None | 16.234695 |
| 5 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 4130 | 5154 | 1024 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.103154072 | None | 46.517632 |
| 6 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 5154 | 6174 | 1022 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.14540575 | None | 78.195165 |
| 7 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 6174 | 6591 | 419 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.127968327 | None | 112.020511 |
| 8 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 6591 | 6982 | 393 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.100496127 | None | 126.85606 |
| 9 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 6982 | 7378 | 401 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.1219071 | None | 138.938995 |
| 10 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 7378 | 7857 | 479 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.205898333 | None | 157.016427 |
| 11 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 7857 | 8258 | 401 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.344837913 | None | 197.292536 |
| 12 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8258 | 8435 | 189 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.09573836 | None | 216.330728 |
| 13 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8435 | 8672 | 243 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.122555 | None | 287.521223 |
| 14 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8672 | 8798 | 126 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | -0.028697668 | None | 343.867543 |
| 15 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8798 | 8798 | 0 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | None | None | 11.408647 |
| 16 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8798 | 8798 | 0 | 1 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | None | None | 4.547744 |
| 17 | V4SZ | harvest_then_proof | 1024 | task_set | None | 0 | 0 | 0 |  | False | False | None | None | 1024 | 1 | 8798 | 8798 | 0 | 0 | INCOMPLETE_LIMIT | DIAGNOSTIC_PRICING_FRONTIER | None | None | None | None | 2.769573 |
