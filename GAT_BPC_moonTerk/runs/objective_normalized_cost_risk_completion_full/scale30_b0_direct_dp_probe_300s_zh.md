# 30-scale B0 Direct-DP 300s Probe

## 结论

该 probe 只用于定位 30-scale 当前瓶颈，不是 full 3600s row，也不是 official 30-scale exact solve。

首个 30-task 实例 `lunar_ice_sp50_030_001_seed929001` 在 300s solver wall limit 下返回：

- `status`: `DIRECT_DP_TIME_LIMIT`
- `certificate_scope`: `FEASIBLE_INCUMBENT_ONLY`
- `objective`: `None`
- `journeys`: 0
- `wall_time_sec`: 300.014932
- `note`: timed out during `sortie_candidate_generation:unknown`

关键计数：

| metric | value |
|---|---:|
| generated_journey_count | 147,249 |
| generated_sortie_count | 417,487,274 |
| route_template_count | 9,070,111 |
| pareto_label_count | 776,118 |
| set_partition_state_count | 0 |
| max RSS | about 4.7 GB |

## 解释

这次证据推翻了旧报告里的“约 10 分钟后卡在 `fleet_set_partition`”描述。当前代码下，30-scale B0 首实例在 300s 内还没有进入 set-partition 阶段；主要成本已经在 sortie candidate generation / route template / label expansion 前段爆开。

因此，30-scale 全量计划目前不能靠简单延长 row limit 来视为已完成。下一步如果要推进 30-scale，需要先做 exact-safe 的 candidate generation/cache/representative certificate 优化，再重新启动真实 3600s row-limit 实验。
