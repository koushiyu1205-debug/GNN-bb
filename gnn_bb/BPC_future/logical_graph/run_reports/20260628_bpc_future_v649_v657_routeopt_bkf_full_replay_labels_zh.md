# V649-V657 RouteOpt-BKF Full Replay Label Summary

## 背景

本轮把 RouteOpt/BKF 风格的 branch-candidate testing 思路落到 `BPC_future` 自己的 branch replay 数据线上：

- V644/V648：从 V545 full60 branch logs 中选 RouteOpt-BKF alternative，先做 child-probe。
- V649/V653：把 V648 的 2 个 `positive_proxy` 做 600s full replay。
- V654/V656：把 V648 中 4 个接近正例的 `neutral_proxy` 做 600s full replay。
- V657：把 full replay delta rows 合成 GAT branch/action sanity dataset。

所有产物均为 diagnostic/offline：

```text
runs_bpc_or_pricing = false for audit/dataset builders
official_bound_effect = false
certificate_effect = false
production_ready = false
```

学习结果只能用于 branch/action 排序训练，不能作为 official bound、certificate 或剪枝依据。

## V648 Child-Probe 输入

```text
paired_group_count = 24
observed_alternative_entry_count = 48
label_counts = {
  positive_proxy: 2,
  neutral_proxy: 33,
  hard_negative_proxy: 13
}
```

解释：

- RouteOpt-BKF 选择能扩大反事实候选覆盖。
- 但 proxy 里 hard negative 很多，说明它不能裸上线，只能作为 testing/data-harvest controller。

## V649/V653：positive_proxy Full Replay

### seed61716

实例：

```text
apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716
```

对比：

| pair | status | wall | best primal | best dual | gap | node |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| selected `[4,12]` | OPTIMAL | 244.981626 | 513.110284 | 513.110284 | 0 | 5 |
| alt `[6,15]` | OPTIMAL | 143.136182 | 513.110284 | 513.110284 | 0 | 3 |

结论：

- `[6,15]` 是严格 full-run wall-time 正例。
- wall-time gain = `101.845444s`。
- 目标值一致，gap 均为 0，节点数从 5 降到 3。
- V653 标签：`strong_positive`，`usable_for_counterfactual_training=true`。

### seed61000

实例：

```text
apollo15_20km_random-wave_randomtw_tasks020_01_seed61000
```

对比：

| pair | status | wall | best primal | best dual | gap |
| --- | --- | ---: | ---: | ---: | ---: |
| selected `[8,18]` | EXTERNAL_TIME_LIMIT | 600.018917 | 660.220086 | 636.947957 | 0.035249 |
| alt `[17,18]` | EXTERNAL_TIME_LIMIT | 600.018114 | 659.957225 | 636.947957 | 0.034865 |

结论：

- `[17,18]` 只带来很小的 incumbent/gap 改善，没有闭环。
- V653 标签：`changed_timeout_no_effect_hard_negative`。
- 不能当 full-solve positive。

## V654/V656：near-positive Full Replay

V654 选择 4 个 child-probe `best_wall_time_gain >= 20s` 且非 hard-negative 的 neutral-proxy group。结果：

| group | selected | alt | selected status/wall | alt status/wall | V656 标签 |
| --- | --- | --- | --- | --- | --- |
| seed61635 d2 n5 | `[2,5]` | `[2,12]` | EXTERNAL_TIME_LIMIT / 600.021176 | EXTERNAL_TIME_LIMIT / 600.020764 | changed_timeout_no_effect_hard_negative |
| seed61000 sector d1 n2 | `[5,8]` | `[8,15]` | EXTERNAL_TIME_LIMIT / 600.020202 | EXTERNAL_TIME_LIMIT / 600.021157 | changed_timeout_no_effect_hard_negative |
| seed61103 d1 n2 | `[1,4]` | `[4,5]` | OPTIMAL / 453.773871 | EXTERNAL_TIME_LIMIT / 600.019852 | regression |
| seed61817 d1 n1 | `[1,2]` | `[3,15]` | OPTIMAL / 172.092765 | OPTIMAL / 153.358185 | below 30s threshold, skipped |

结论：

- child-probe 20-30s gain 不足以可靠 promotion。
- 其中一个 pair 从 OPTIMAL 退化为 EXTERNAL_TIME_LIMIT，是明确 hard negative。
- `[3,15]` 比 `[1,2]` 快约 18.7s，但低于当前 30s 主训练阈值；可作为后续低权重连续增益候选，不进入本轮主标签。

## V657 Dataset

输入：

- `journey_branch_counterfactual_delta_v653_v649_routeopt_bkf_positive_full_replay_20260628`
- `journey_branch_counterfactual_delta_v656_v654_near_positive_full600_20260628`

机器字段：

```text
raw_row_count = 5
sample_count = 5
instance_count = 5
family_count = 3
branch_priority_label_counts = {
  walltime_gain_positive: 1,
  not_walltime_gain: 4
}
row_kind_counts = {
  walltime_gain_target_wall_crossing: 1,
  changed_timeout_no_effect_hard_negative: 3,
  hard_negative_regression: 1
}
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
optin_training_dataset_ready = false
```

解释：

- 数据管线可以正确读取 full replay wall-time gain。
- 现在只有 1 条严格正例，不够正式训练。
- hard negative 明显多于 positive，说明 BKF-style testing 对“过滤坏 pair”很有价值。

## 对优化思路的影响

1. `positive_proxy` 必须 full replay 验证后才能进训练。

   V649 证明至少有一个 proxy 可以转成严格正例，但另一个 proxy 只改善 gap，没有闭环。

2. `neutral_proxy` 的 promotion 阈值要提高。

   V654 中 4 个 near-positive 只有一个低于 30s 的双方 OPTIMAL 小收益，其余不是无效就是退化。

3. RouteOpt-BKF 更适合做 branch-testing controller，而不是直接替代 branch score。

   当前最有用的是：用它主动找反事实 pair，并产生 positive/hard-negative 标签。

4. full replay 采样成本仍然很高。

   8 条 V654 replay 里 5 条跑到 600s。下一步需要 node snapshot / replay restore，否则训练数据采集速度太慢。

5. 20 规模 600s 全最优还远未达成。

   V545 仍是当前 full60 最强实测：`36/60 OPTIMAL`，capped mean `341.54s`。本轮只增加了训练标签和候选筛选证据，还没有改 production solver 行为。

## 下一步

1. 把 V653 的 `[6,15] over [4,12]` 加入 strict full-replay positive pool。
2. 把 V653/V656 的 4 条负例加入 hard-negative pool。
3. 调整 RouteOpt-BKF promotion gate：
   - child-probe wall gain 至少 `>=100s` 或 full-run closure proxy 更强；
   - 或要求同时具备 CB retry gain、fathom gain、gap/primal improvement；
   - 对 20-30s 局部 gain 只进入低优先级候选，不直接 full replay。
4. 继续扩展 full replay 正例，但优先选择：
   - `positive_proxy`；
   - child-probe gain `>=100s`；
   - baseline timeout 而 alternative child probe OPTIMAL；
   - 有 fathom/gap/CB retry 多指标一致改善的 pair。
5. 并行推进 replay snapshot / node restore，降低 full replay 标签采集成本。

