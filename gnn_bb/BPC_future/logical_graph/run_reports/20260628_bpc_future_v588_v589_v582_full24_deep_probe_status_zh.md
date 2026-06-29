# 20260628：V582 Full24 深层 Probe、Risk Map 与 Local-Fathom 信号

## 结论

V582 中等 child-probe 已从 12 条扩展到完整 24 条。它是目前较合理的深层 proof-tail 采样档位：

- 单条 wall time 控制在 `54.99s` 到 `176.35s`。
- 24 条全部有可用 gap。
- 能稳定产生 branch / child / completion-bound retry 标签。
- 仍然没有 strict branch positive，不能作为完整 branch score 正例。
- 产出的主要价值是 proof-tail hard negative 和 local child-fathom ordering 信号。

## V582 Full24 运行结果

Runbook：

`BPC_future/results/journey_branch_candidate_replay_runbook_v582_v573_v545_early_high_retry_mid_child_probe_20260628/`

运行配置：

```text
time_limit = 240
max_source_event_time = 120
probe_extra_nodes_after_branch = 2
probe_max_cg_iterations = 36
max_events_per_instance = 1
max_workers = 2
```

结果：

```text
runs = 24
status = {'TIME_LIMIT': 24}
wall_time_min = 54.990777
wall_time_mean = 119.503825
wall_time_max = 176.346492
solving_time_mean = 117.341896
gap_available = 24/24
gap_min = 0.005027
gap_mean = 0.039651
gap_max = 0.068703
```

判断：

- 这不是完整求解实验；`TIME_LIMIT` 是 probe 截断状态。
- 但它不是无效空跑，因为 24 条都有 gap，且能到达深层 branch/proof-tail。
- 作为采样档位，V582 明显优于 V574 的 500 秒级重 probe，也优于 V577/V580 的 root 截断空跑。

## V588 Branch-Impact 审计

输出：

`BPC_future/results/journey_branch_impact_v588_v582_full24_mid_child_probe_20260628/`

关键字段：

```text
log_count = 24
branch_count = 98
right_censored_branch_count = 98
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
tail_class_counts = {'completion_bound_tail': 50, 'unprocessed_children': 48}
forced_pair_branch_count = 54
forced_pair_matched_branch_count = 54
active_touch_branch_count = 13
inactive_only_branch_count = 32
total_child_completion_bound_retries = 341
total_child_exact_pricing_events = 387
total_child_negative_pricing_events = 315
total_child_certificate_pricing_events = 82
total_child_fathom_events = 8
unprocessed_child_count = 114
max_child_corrected_bound_gain = 18.502833
```

解释：

- `usable_branch_impact_training_count=0`：仍无 strict branch positive。
- `total_child_completion_bound_retries=341`：提供大量 proof-tail risk / hard-negative 信号。
- `total_child_fathom_events=8`：提供 local child-ordering 信号，但不能升级为完整 branch pair 正例。

## V589 Complete / Risk / Local-Fathom Maps

### Complete-only

输出：

`BPC_future/results/journey_child_score_map_v589_v588_complete_only_20260628/`

```text
raw_child_probe_row_count = 196
child_score_row_count = 0
production_ready = False
```

说明：

默认 fail-closed 正确生效；没有完整 child 标签时不导出 production score。

### Right-Censored Risk

输出：

`BPC_future/results/journey_child_score_map_v589_v588_rightcensored_mid_risk_20260628/`

```text
raw_child_probe_row_count = 196
child_probe_row_count = 82
child_score_row_count = 82
child_score_map_entry_count = 43
production_ready = False
```

Top risk / low-risk examples：

| key | score | CB retry | negative | proof CPU | fathom |
|---|---:|---:|---:|---:|---:|
| `node:0:depth:0:1,3:same_vehicle` | `1.354` | `3` | `3` | `11.6s` | `1` |
| `node:0:depth:0:4,8:separate_vehicle` | `-1.64` | `3` | `4` | `21.0s` | `1` |
| `node:1:depth:1:7,14:same_vehicle` | `-13.63` | `18` | `8` | `77.6s` | `0` |
| `node:1:depth:1:3,17:same_vehicle` | `-11.69` | `18` | `12` | `51.3s` | `1` |

解释：

- `[1,3] same` 是当前最好的 local child signal。
- `[7,14] same` 是高 retry / high proof CPU / no fathom 的 hard negative。
- `[3,17] same` 即使 fathom，也因为 retry 和负列链过重而是差风险。

### Local-Fathom Child Ordering

输出：

`BPC_future/results/journey_child_score_map_v589_v588_local_fathom_child_order_20260628/`

```text
raw_child_probe_row_count = 196
child_probe_row_count = 8
fathomed_right_censored_included_count = 8
child_score_row_count = 8
child_score_map_entry_count = 6
production_ready = False
```

Top local-fathom rows：

| key | score | CB retry | negative | proof CPU | gain | fathom |
|---|---:|---:|---:|---:|---:|---:|
| `node:0:depth:0:1,3:same_vehicle` | `4.354` | `3` | `3` | `11.6s` | `18.502833` | `1` |
| `node:0:depth:0:4,8:separate_vehicle` | `1.356` | `3` | `4` | `20.9s` | `5.152441` | `1` |
| `node:1:depth:1:2,18:same_vehicle` | `0.965` | `3` | `4` | `33.3s` | `3.711604` | `1` |
| `node:1:depth:1:1,9:same_vehicle` | `0.812` | `3` | `2` | `24.1s` | `0.066067` | `1` |
| `node:1:depth:1:3,17:same_vehicle` | `-8.685` | `18` | `12` | `51.3s` | `3.711604` | `1` |

解释：

- Local fathom 并不自动代表好 child；如果 retry/proof cost 太高，仍应降分。
- 该 map 只适合 child-ordering shadow / opt-in，不适合作为 branch-pair score。

## 当前训练材料分层

### 1. Strict Branch Positive

仍然没有。

证据：

```text
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
```

这意味着不能用 V588 来训练“完整求解更快闭环”的强正例。

### 2. Proof-Tail Hard Negative / Risk

明显增加。

证据：

```text
child_score_row_count = 82
child_score_map_entry_count = 43
total_child_completion_bound_retries = 341
```

这批可以训练模型识别：

- high completion-bound retry；
- high proof CPU；
- negative chain continues；
- no fathom；
- unprocessed child tail。

### 3. Local Child-Fathom Ordering

开始有可用信号。

证据：

```text
total_child_fathom_events = 8
local_fathom_child_score_row_count = 8
```

这批可以训练或 shadow-test：

- same/separate child 入队顺序；
- child proof-cost 风险；
- 哪类 child 更可能先被 exact-safe fathom。

## 下一步建议

1. 不再跑 V574 重 probe。

V582 已证明能用更低成本采集深层标签。

2. 暂时不要把 V589 接入生产求解。

所有 maps 都是 `production_ready=False`。下一步应先做 shadow / opt-in child-ordering smoke。

3. 开始构造训练数据：

- V589 risk rows -> hard negative / risk auxiliary head；
- V589 local-fathom rows -> child-ordering auxiliary head；
- V588 branch rows -> right-censored branch risk，不当正例。

4. 单独启动 positive-mining。

当前最缺的是 strict positive。应从 V545/V543 已 OPTIMAL 且 proof-tail 短的日志中找：

- `child_fathom_events > 0`
- low completion-bound retry
- low proof CPU
- active-support changing branch
- 同 context 可比较 alternative pair

然后做小规模 replay，优先收集：

- full run wall-time gain；
- `time_to_certificate` 降低；
- child fathom 更快；
- branch tree 更窄。

5. 后续验收仍不能放松。

最终目标仍是 random-TW 20-scale 全部 600s 内 OPTIMAL。V588/V589 只是训练材料推进，不是求解性能达标。

## Exact-Safe 边界

本轮所有新增产物：

- 不产生 official bound；
- 不产生 certificate；
- 不改变 lower bound；
- 不改变剪枝；
- 不把 right-censored branch 当正例；
- local-fathom 只影响 child ordering 的 opt-in/shadow 诊断。
