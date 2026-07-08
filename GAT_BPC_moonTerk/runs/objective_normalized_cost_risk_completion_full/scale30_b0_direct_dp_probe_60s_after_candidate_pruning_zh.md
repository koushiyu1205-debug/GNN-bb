# 30-scale B0 Direct-DP 60s Probe After Candidate Pruning

## 结论

该 probe 在 exact-safe candidate generation pruning 和 30-scale bounded sortie cache 之后运行，只用于定位瓶颈和资源风险，不是 full 3600s row，也不是 official 30-scale exact solve。

首个 30-task 实例 `lunar_ice_sp50_030_001_seed929001` 在 60s solver wall limit 下返回：

- `status`: `DIRECT_DP_TIME_LIMIT`
- `certificate_scope`: `FEASIBLE_INCUMBENT_ONLY`
- `objective`: `None`
- `journeys`: 0
- `wall_time_sec`: 60.005288
- `note`: timed out during `sortie_candidate_generation:unknown`

关键计数：

| metric | value |
|---|---:|
| generated_journey_count | 38,629 |
| generated_sortie_count | 8,067,440 |
| route_template_count | 2,022,902 |
| pareto_label_count | 187,411 |
| set_partition_state_count | 0 |
| max RSS | about 0.6 GB |

## 与优化前 60s probe 的差异

优化前同样 60s probe 仍在 `sortie_candidate_generation` 超时，关键计数为：

| metric | before | after |
|---|---:|---:|
| generated_sortie_count | 90,643,490 | 8,067,440 |
| route_template_count | 1,395,377 | 2,022,902 |
| pareto_label_count | 144,072 | 187,411 |
| max RSS | about 0.6 GB | about 0.6 GB |

解释：前置 infeasibility lower-bound 剪掉了大量必不可行 path-type 尝试，所以 `generated_sortie_count` 大幅下降；同一时间内能推进到更多 feasible route templates 和 Pareto labels。但 30-scale 仍未进入 set partition，说明当前瓶颈仍在 direct journey universe/candidate generation 前段。

## 当前边界

这次优化改善了 30-scale probe 的资源安全和有效搜索比例，但还不能证明 30-scale 可闭合。现有 B3B 仍依赖 B0 direct baseline 和 task-subset representative universe；30-scale 若要正式 `BPC_TREE_OPTIMAL`，还需要新的 exact-safe 30-scale pricing/certificate path，不能只靠现有 direct universe 枚举。
