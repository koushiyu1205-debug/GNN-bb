# 20260628：V585-V587 中等 Probe 扩展与 Local-Fathom Child 信号

## 结论

本轮把 V582 中等 child-probe 从前 2 条扩展到前 12 条，并补了一个离线 score-map 构建能力：

- 默认仍 fail-closed：right-censored child rows 不进入 complete-only score map。
- 新增显式 opt-in：`--include-fathomed-right-censored`，只纳入已经 observed child fathom 的右删失 child。
- 该信号只用于 local child ordering 诊断，不是完整 branch pair 正例，也不是 production-ready。

## V582 前 12 条运行概况

运行范围：

`BPC_future/results/journey_branch_candidate_replay_runbook_v582_v573_v545_early_high_retry_mid_child_probe_20260628/`

配置：

```text
time_limit = 240
max_source_event_time = 120
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 36
max_events_per_instance = 1
```

结果：

```text
runs = 12
status = {'TIME_LIMIT': 12}
wall_time_min = 88.458494
wall_time_mean = 133.384878
wall_time_max = 176.346492
gap_available = 12/12
gap_min = 0.005027
gap_mean = 0.038812
gap_max = 0.068703
```

判断：

- 这批仍不是完整求解正例，全部是 `TIME_LIMIT`。
- 但它不是 V577/V580 那种无效空跑：12 条都有可用 gap，且产生了 branch / child / completion-bound 事件。
- 单条成本约 1.5 到 3 分钟，比 V574 的 500 秒级 probe 更适合扩展采样。

## V585 Branch-Impact 审计

审计目录：

`BPC_future/results/journey_branch_impact_v585_v582_first12_mid_child_probe_20260628/`

关键字段：

```text
log_count = 12
branch_count = 46
right_censored_branch_count = 46
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 24, 'unprocessed_children': 22}
forced_pair_branch_count = 26
forced_pair_matched_branch_count = 26
active_touch_branch_count = 9
inactive_only_branch_count = 14
total_child_completion_bound_retries = 174
total_child_exact_pricing_events = 195
total_child_negative_pricing_events = 173
total_child_certificate_pricing_events = 38
total_child_fathom_events = 4
unprocessed_child_count = 54
```

解释：

- 46 个 branch row 全部右删失，因此 `usable_branch_impact_training_count=0`。
- 这批不能训练“哪个 pair 能让完整求解闭环”的 strict positive。
- 但 `total_child_completion_bound_retries=174` 和 `total_child_negative_pricing_events=173` 给出了大量 proof-tail hard-negative / risk 信号。
- 4 个 `child_fathom_events` 是局部 child-level 证据，可以用于 child ordering 诊断。

## V586：Right-Censored Risk Map

complete-only：

```text
raw_child_probe_row_count = 92
child_score_row_count = 0
production_ready = False
```

right-censored risk：

```text
raw_child_probe_row_count = 92
child_probe_row_count = 38
child_score_row_count = 38
child_score_map_entry_count = 22
production_ready = False
```

最差风险示例：

| key | score | CB retry | negative | proof CPU | fathom |
|---|---:|---:|---:|---:|---:|
| `node:1:depth:1:7,14:same_vehicle` | `-13.6282` | `18` | `8` | `77.58s` | `0` |
| `node:1:depth:1:6,15:same_vehicle` | `-10.4213` | `13` | `6` | `52.76s` | `0` |
| `node:0:depth:0:1,5:same_vehicle` | about `-7.64` | `8` | `5` | about `48s` | `0` |

用途：

- 训练或约束模型避开 high retry / high proof CPU / no fathom 的 child order。
- 不能作为正向 closure 标签。

## 新增脚本能力：Local-Fathom Right-Censored Opt-In

修改文件：

- `BPC_future/scripts/build_journey_child_score_map.py`
- `BPC_future/tests/test_journey_child_score_map.py`

新增参数：

```text
--include-fathomed-right-censored
```

语义：

- 默认不变：right-censored rows 全部过滤。
- 如果显式开启该参数，只允许 `child_fathomed > 0` 的 right-censored child rows 进入 map。
- 这些行仍然 `production_ready=False`。
- 它们只是 local child-ordering 信号，不是完整 branch-impact 标签。

验证：

```text
python -m py_compile \
  BPC_future/scripts/build_journey_child_score_map.py \
  BPC_future/tests/test_journey_child_score_map.py

python -m unittest BPC_future.tests.test_journey_child_score_map
```

结果：

```text
Ran 5 tests in 0.003s
OK
```

## V587：Local-Fathom Child-Ordering Map

输出：

`BPC_future/results/journey_child_score_map_v587_v585_local_fathom_child_order_20260628/`

配置：

```text
include_right_censored = False
include_fathomed_right_censored = True
right_censored_penalty = 2.0
fathom_bonus = 5.0
completion_retry_penalty = 0.5
negative_pricing_penalty = 0.25
proof_cpu_scale = 120.0
```

汇总：

```text
raw_child_probe_row_count = 92
child_probe_row_count = 4
fathomed_right_censored_included_count = 4
right_censored_filter_skip_count = 34
child_score_row_count = 4
child_score_map_entry_count = 3
production_ready = False
```

Score rows：

| key | score | CB retry | negative | proof CPU | max corrected gain | fathom |
|---|---:|---:|---:|---:|---:|---:|
| `node:0:depth:0:4,8:separate_vehicle` | `1.3563` | `3` | `4` | `20.90s` | `5.152441` | `1` |
| `node:0:depth:0:4,8:separate_vehicle` | `1.3554` | `3` | `4` | `21.01s` | `5.152441` | `1` |
| `node:1:depth:1:1,9:same_vehicle` | `0.8122` | `3` | `2` | `24.12s` | `0.066067` | `1` |
| `node:1:depth:1:1,11:same_vehicle` | `-3.0136` | `8` | `7` | `46.79s` | `0.631503` | `1` |

解释：

- `[4,8] separate` 和 `[1,9] same` 是局部 child fathom 的正向排序信号。
- `[1,11] same` 虽然 fathom，但 proof cost 和 retry 明显更高，因此仍是负分。
- 这些只能帮助 child ordering，不代表 forced branch pair 能让完整实例求到 OPTIMAL。

## 对 Branch Score 主线的影响

当前训练材料分三层：

1. Strict branch positive：仍然不足。
   - V585 没有完整 branch-impact row。
   - 不能把 right-censored TIME_LIMIT 当正例。

2. Proof-tail hard negative：明显增加。
   - V586 给出 38 条 right-censored risk rows。
   - 可以让模型避开会制造大量 completion-bound retry 的 child/branch。

3. Local child fathom：开始出现。
   - V587 给出 4 条 local fathom rows。
   - 可用于 child ordering shadow / opt-in。
   - 需要更多样本后再考虑接入 solver 实测。

## 下一步建议

1. 不继续跑 V574 重 probe。

2. 用 V582 档位继续扩到 24 条，前提是仍保持：
   - `source_event_time <= 120`
   - `max_cg_iterations = 36`
   - `extra_nodes_after_branch = 2`
   - `max-workers = 2`

3. 同时启动 positive-mining：
   - 从 V545/V543 已 OPTIMAL 的实例里找 proof-tail 较短、child fathom 较多的 context；
   - 只对同 context alternative pair 做 replay；
   - 标签优先用 `child_time_to_fathom`、`time_to_certificate` 和完整 OPTIMAL wall-time gain。

4. 训练时不要混淆：
   - V586 是 hard-negative / risk；
   - V587 是 local child-ordering；
   - strict branch score 仍需要完整或至少成对可比较的 branch-impact 标签。

## Exact-Safe 边界

本轮所有新能力都是离线诊断：

- 不运行 pricing；
- 不改 RMP；
- 不产生 official bound；
- 不产生 certificate；
- 不改变剪枝；
- score map 只改变 child 入队顺序，且必须 opt-in。
