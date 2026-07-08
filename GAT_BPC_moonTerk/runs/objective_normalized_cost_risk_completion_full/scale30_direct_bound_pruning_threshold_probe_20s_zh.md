# 30-scale Direct-DP Bound-Pruning Threshold Probe

## 目的

该 probe 检查一个低风险性能想法：把 direct-DP reference-upper-bound pruning 的激活门槛从 root lower-bound / incumbent UB >= `0.5` 临时降到 `0.4`。

该实验只通过运行时 monkey-patch 改动阈值，没有改源码默认值；它不是 full 3600s row，也不是 30-scale exact solve。

## 实例与设置

- instance: `lunar_ice_sp50_030_001_seed929001`
- wall limit: `20s`
- temporary `_DIRECT_BOUND_PRUNING_MIN_ROOT_RATIO`: `0.4`
- reference upper bound: `1.919465`
- direct-DP root pruning bound: `0.841965885`
- root bound / reference UB: `0.438646125`

## 结果

| field | value |
|---|---:|
| status | `DIRECT_DP_TIME_LIMIT` |
| active bound pruning | `true` |
| journey label bound-pruned count | `0` |
| generated journey count | `11,076` |
| generated sortie count | `3,363,413` |
| route template count | `354,937` |
| pareto label count | `42,417` |
| set partition state count | `0` |
| wall time | `20.084970s` |
| max RSS | about `607,820 KB` |

## 结论

降低激活门槛可以让 bound-pruning 逻辑进入 active 状态，但 20 秒内实际剪枝数仍为 `0`。这说明当前 direct-DP lower bound 太弱，问题不在激活门槛本身。

因此不建议把阈值下调作为主线优化；30-scale 闭合仍需要更强的 exact-safe lower bound、pricing certificate path，或能提供更强 product/root relaxation 的 formulation。
