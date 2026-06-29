# Branch Score v446: Child-Score 与 Forced Root Replay 阶段结论

日期：2026-06-26

## 目的

在 v438/v439 proof-risk gated branch score 之后，继续验证两个可能的加速方向：

1. 只改变同一 Ryan-Foster pair 下 same/separate child 的处理顺序。
2. 对 v442 child-probe 中 proof-cost 信号较强的 root pair 做完整 forced replay，寻找真实 wall-time gain 标签。

所有实验仍保持 exact-safe：学习信号只改变分支/队列顺序，不提供 official bound、certificate 或剪枝依据。

## v443 Child Score Map

产物：

```text
BPC_future/results/journey_child_score_map_v443_v441_v442_rightcensored_diag_20260626/
```

关键字段：

```text
raw_child_probe_row_count = 168
child_probe_row_count = 60
child_score_row_count = 60
child_score_map_entry_count = 56
include_right_censored = True
production_ready = False
diagnostic_only = True
official_bound_effect = False
certificate_effect = False
```

解释：

v443 覆盖了 v438 失败实例的 root child same/separate 分数，但这些行全部来自 right-censored probe。因此它不能作为 production score map，只能用于 shadow/opt-in 诊断。

## v444 Targeted Child-Score Smoke

配置：

```text
instances = 3 个 v438 失败实例
branch score = v439 proof-risk postprocessor
child priority = child_score
child score path = v443 journey_child_score_rows.json
early branch = off
admission = off
time limit = 600s
```

结果对比：

| instance | v438 | v444 | gain |
|---|---:|---:|---:|
| tranq greedy seed61414 | TIME_LIMIT 556.130s | TIME_LIMIT 556.174s | -0.043s |
| tranq greedy seed61206 | EXTERNAL_TIME_LIMIT 600.018s | EXTERNAL_TIME_LIMIT 600.019s | -0.002s |
| tranq random-wave seed61001 | EXTERNAL_TIME_LIMIT 600.022s | EXTERNAL_TIME_LIMIT 600.018s | +0.003s |

日志确认 child-score 确实命中 root child：

```text
seed61414: RF(13,16) separate score -4.024, same score -6.714
seed61206: RF(5,9) separate score -5.821, same score -7.093
seed61001: RF(8,13) separate score -7.036, same score -7.473
```

结论：

只调整 same/separate child 顺序不能解决当前 hard proof tail。v443 的信号可保留为诊断特征，但不应扩展为主加速线。

## v445 Forced Root Replay

配置：

```text
instances = 3 个 v438/v442 高 proof-cost 信号实例
branch candidate priority = force_pair_path:0:<pair>
child priority = declared
early branch = off
admission = off
time limit = 600s
```

结果：

| instance | forced pair | v438 | v445 | gain |
|---|---:|---:|---:|---:|
| tranq greedy seed61414 | [13,17] | TIME_LIMIT 556.130s | TIME_LIMIT 427.521s | +128.610s |
| tranq greedy seed61103 | [15,19] | EXTERNAL_TIME_LIMIT 600.017s | EXTERNAL_TIME_LIMIT 600.017s | +0.000s |
| tranq greedy seed61520 | [4,8] | EXTERNAL_TIME_LIMIT 600.017s | EXTERNAL_TIME_LIMIT 600.016s | +0.001s |

seed61414 的 `[13,17]` 是有效的连续正例：没有达到 OPTIMAL，但真实 wall time 减少超过 100 秒，符合平均时间优化目标。seed61103 `[15,19]` 和 seed61520 `[4,8]` 没有带来收益，应进入 no-effect / hard-negative 池。

## 当前判断

1. v442 的短 probe corrected-bound gain 不是充分标签。
   它能发现一些有潜力的 pair，例如 seed61414 `[13,17]`，但也会给出无效 pair，例如 `[15,19]`、`[4,8]`。

2. 训练标签必须继续以完整 replay wall-time gain 为主。
   `>100s gain` 即使没有 OPTIMAL，也应该作为连续正例/弱强正例参与回归排序；`600s -> 600s` 应作为 no-effect 或 hard negative。

3. child-score ordering 单独不值得进入全量。
   它已经被实际命中验证，但没有改变 v444 的求解状态和时间。

4. branch score 主线仍然成立，但要从“分类过 200 秒”转成“回归平均 wall-time gain + hard negative 抑制”。

## 下一步

1. 从 v442 中继续选 top proof-cost 候选做小批量 full replay，但每批必须包含：
   - 高 gain 候选；
   - 低/零 gain 候选；
   - 不同 family 和不同 seed；
   - 不再扩大 right-censored-only child-score map。

2. 重新训练 branch action GAT 时，提高连续 wall-time gain 回归权重：
   - `gain >= 100s` 高权重；
   - `gain >= 30s` 中权重；
   - `600s -> 600s` 和 proof CPU/CB retry 变差作为 hard negative；
   - `<=200s OPTIMAL` 只保留为评估指标，不作为训练硬阈值。

3. 下一轮 opt-in 不应启用 child-score 全量，只测试更新后的 root branch score gate。

## v447/v448 后续处理

已完成 v447 delta rows：

```text
BPC_future/results/journey_branch_counterfactual_delta_v447_v445_forced_root_top3_walltime_20260626/
```

结果：

```text
row_count = 3
observed_walltime_gain = 1
changed_timeout_no_effect_hard_negative = 2
```

其中 seed61414 `[13,17]` 作为非最优但真实 wall-time gain 正例进入数据：

```text
baseline:    TIME_LIMIT 556.130s, pair [13,16]
alternative: TIME_LIMIT 427.521s, pair [13,17]
gain:        +128.610s
```

为了让这类样本可训练，`build_gat_branch_action_sanity_dataset.py` 已修正旧口径：`capped_wall_time_gain` 使用实际 wall time capped 到 600 秒，不再因为 alternative 非 `OPTIMAL` 就强行记为 600 秒。`strict_full_replay_positive` 和 `target_wall_crossing_positive` 仍要求 `OPTIMAL`，所以精确性边界不变。

已完成 v448 合并数据集：

```text
BPC_future/data/gat_branch_action_sanity/v448_v437_plus_v447_walltime_20260626/
raw_row_count = 204
sample_count = 122
walltime_gain_positive = 46
not_walltime_gain = 64
aux_only_weak_positive = 12
```

已完成 v448 sanity training：

```text
checkpoint = BPC_future/data/gat_branch_action_sanity/v448_v437_plus_v447_walltime_20260626/gat_branch_action_v448.pt
metrics = BPC_future/results/gat_branch_action_v448_v437_plus_v447_walltime_20260626/summary.json
production_ready = false
optin_training_ready = false
validation_f1 = 0.0
```

结论：

v448 证明新标签口径和训练管线可以跑通，但模型泛化还不够，不能导出为真实 opt-in score map。下一步应该继续补 full replay 标签，而不是用 v448 checkpoint 跑全量。

## 验证

```text
python -m unittest BPC_future.tests.test_journey_child_score_map \
  BPC_future.tests.test_gat_branch_score_proofrisk_overlay \
  BPC_future.tests.test_gat_branch_action_sanity_dataset \
  BPC_future.tests.test_gat_branch_action_sanity_training

Ran 7 tests: OK

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_child_min_iter_and_child_order \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_selection_gate_falls_back_on_width_cap \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_score_gate_requires_confident_scored_pair

Ran 3 tests: OK
```
