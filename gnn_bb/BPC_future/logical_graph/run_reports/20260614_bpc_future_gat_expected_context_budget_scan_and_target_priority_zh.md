# GAT Expected-context Budget Scan 与 Target-priority Probe 报告

日期：2026-06-14

## 目标

继续验证 GAT / kNN / OOD 主线的真实作用边界：

- GAT 负责 embedding / trajectory impact / residual family 表达；
- kNN/OOD 负责安全壳；
- 通过的 true-RC negative 可 `HIGH_PRIORITY`；
- 未通过的 true-RC negative 只能进 `DELAY_QUEUE`，不能永久丢弃；
- 所有 worker / GAT / kNN / OOD 结果都不能产生 certificate 或 official lower bound；
- 默认 benchmark 不启用。

本轮问题是：

```text
仅有 expected-context hash 是否足够？
还是必须把 GAT/family 信号进一步转成 target-priority？
```

## 前置结论

上一轮已经证明：

```text
expected_context = c488c428ee5822de
cg_iter = 7
worker_signal_source = expected_context_current_probe
```

可以让 branch-price current-probe worker 在非 certificate-candidate 轮次运行。

但 0.5s 小预算下：

```text
status = INCOMPLETE_LIMIT
returned_journeys = 0
certificate_effect = false
```

## Budget Scan

### 0.5s expected-context

| metric | value |
|---|---:|
| worker status | INCOMPLETE_LIMIT |
| returned journeys | 0 |
| recursions | 1018 |
| shards incomplete | 20 |
| shards negative | 0 |
| time-window pruned | 53208 |
| worker time | 0.52s |

### 2s expected-context

| metric | value |
|---|---:|
| worker status | INCOMPLETE_LIMIT |
| returned journeys | 0 |
| recursions | 3734 |
| shards incomplete | 18 |
| shards negative | 0 |
| time-window pruned | 188650 |
| worker time | 2.01s |

Run result:

```text
status = TIME_LIMIT
primal = 740.122399
dual = None
wall = 80.58s
columns = 257
```

### 5s expected-context

| metric | value |
|---|---:|
| worker status | INCOMPLETE_LIMIT |
| returned journeys | 0 |
| recursions | 10052 |
| shards certified | 2 |
| shards incomplete | 18 |
| shards negative | 0 |
| time-window pruned | 497123 |
| worker time | 5.03s |

Run result:

```text
status = TIME_LIMIT
primal = 740.122399
dual = None
wall = 80.51s
columns = 257
```

### Budget scan 判断

单纯把 expected-context worker 从 0.5s 加到 5s，仍然没有找到可加入的
true-RC negative journey。

这说明当前瓶颈不是“预算稍微不够”，而是：

```text
expected-context 只告诉 worker 何时跑；
没有告诉 worker 应该优先搜索哪个 residual family。
```

## Capture 中的 GAT/Families 信息

离线 capture 的 cg_iter=7 exact pricing 返回 20 个负列，典型样本：

```text
negative_journey_sequence_samples:
  [[20,17,16]]
  [[20,17,12]]
  [[20], [3,10,9,2]]
  [[20], [3,10,13,2]]
  [[20], [3,9,2]]
  [[20], [3,13,2]]
  [[20,3,11,9]]
  [[20,17,11,13]]

negative_journey_task_set_samples:
  [2,3,20]
  [2,13,19]
  [3,10,20]
  [3,13,20]
  [11,17,20]
  [12,17,20]
  [16,17,20]
  [2,3,9,20]
```

共同结构：

```text
大量 high-impact negative family 包含 task 20，
并且常见首个 sortie/sequence 从 20 开始。
```

## Target-priority Probe

使用同一个 expected context：

```text
context_hash = c488c428ee5822de
```

增加 target priority：

```text
target_sequence = 20,17,16
target_first_task_priority_sequence = 20,17,16
target_transition_priority_sequence = 20,17,16
target_arc_option_priority_sequence =
  0->20:low_risk:2,
  20->17:low_risk:2,
  17->16:low_risk:2,
  16->0:low_risk:2
```

worker budget：

```text
current_probe_time_limit = 1.0s
max_recursions = 50000
```

结果：

| metric | value |
|---|---:|
| worker status | FOUND_NEGATIVE |
| returned journeys | 1 |
| recursions | 1380 |
| shards negative | 1 |
| shards incomplete | 19 |
| worker time | 1.03s |
| added journeys | 1 |
| new task set | [2,3,9,20] |
| pricing best RC | -1.85699125 |

Run result:

```text
status = TIME_LIMIT
primal = 739.158736
dual = None
wall = 80.48s
columns = 259
```

对比同口径 expected-context 0.5/2/5s：

```text
expected-context only:
  primal = 740.122399
  returned_journeys = 0

expected-context + target-priority:
  primal = 739.158736
  returned_journeys = 1
  added_new_task_set = [2,3,9,20]
```

## 解释

这次正信号不是来自“GAT 直接选列”，而是来自：

```text
GAT/kNN/OOD 识别出高优先级 context
    +
capture family 信息把 Pulse 搜索顺序推向 task-20 residual family
```

target sequence 本身 `[20,17,16]` 没有完整 materialize：

```text
target_sequence_reached_prefix_len = 1
target_sequence_blocked_reason = deadline
```

但优先进入 task 20 shard 后，worker 找到了另一个同族负列：

```text
[[20], [3], [9,2]]
task_set = [2,3,9,20]
```

这说明当前有价值的不是单条硬编码 sequence，而是 residual family priority：

```text
优先搜索 task 20 family / transition family
```

## Exactness 边界

本轮没有改变：

- no-negative certificate 规则；
- official dual bound；
- 5/10 默认路径；
- true-RC filter；
- negative 不通过 gate 时进入 delay，不永久丢弃。

所有 worker 结果仍然只是普通加列：

```text
pricing_kind = sharded_pulse_hidden_negative_worker
pricing_state = FOUND_NEGATIVE
certificate_effect = false
```

## 结论

现在的判断比上一轮更清楚：

```text
expected-context hash alone is not enough.
GAT must provide residual-family / target-priority signal.
```

单纯提高 worker 预算：

```text
0.5s -> 2s -> 5s
```

没有找到列。

加入 family/target priority 后：

```text
1s 找到 1 个 true-RC negative 新 task-set，
primal 从 740.122399 改到 739.158736。
```

因此下一步不应该继续盲目加 worker time limit，而应该做：

```text
GAT residual-family priority head / scheduler
```

最小工程方向：

1. 从 capture 中把 high-priority action 的 task-set / sequence family 提取为 target family；
2. 转成 Pulse `target_first_task_priority` / `target_transition_priority`；
3. 仍然 audit-only；
4. 做 20-task 多实例 ROI A/B；
5. 只有在 5/10 no-regression 且 20-task tail 稳定改善后，才考虑更严格的 production gate。

