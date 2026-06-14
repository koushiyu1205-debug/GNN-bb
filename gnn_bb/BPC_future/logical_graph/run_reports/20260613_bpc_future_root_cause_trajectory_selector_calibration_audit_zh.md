# BPC_future 根因审计补充：trajectory selector calibration audit

日期：2026-06-13

## 目标

上一轮 downstream trajectory label audit 已经说明：

- immediate RMP movement 不是有效目标；
- downstream `incumbent_within2` / `zero_within2` 更贴近 final outcome；
- 但这些 downstream 标签是事后信号，不能直接在线使用。

本轮继续做只读校准：

> 只使用 addition 前可见的 returned-batch 特征，检查它们能否预测 downstream trajectory 标签或 final outcome；如果不能稳定泛化，就不能把这些特征写成 production selector。

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`

分析集：

```text
runs = 18
stage rows = 64
instances = 3
```

标签：

```text
incumbent_within2:
  True  = 26
  False = 38

zero_within2:
  True  = 26
  False = 38

outcome_improved:
  True  = 40
  False = 24
```

只使用 addition 前可见特征：

- `active_avg_overlap`
- `active_avg_jaccard`
- `active_redundant_frac`
- `active_bridge_frac`
- `pair_overlap`
- `pair_jacc`
- `union_size`
- `best_rc`
- `returned_count`

注意：

- `active_*` 特征只来自当前 CG stage 的 active top samples，是 capped diagnostics；
- `incumbent_within2` / `zero_within2` / final outcome 都是事后标签；
- 本轮只判断 selector 可分性，不上线任何规则。

## 单特征规则：有信号，但不够

### 预测 `incumbent_within2`

最好的单特征规则：

```text
active_avg_jaccard <= 0.3055555555555555
accuracy = 0.78125
tp = 20
fp = 8
tn = 30
fn = 6
n = 64
```

解释：

- 与当前 active top samples 的平均 Jaccard 较低，确实更可能进入 downstream incumbent path；
- 但仍有 8 个 false positive 和 6 个 false negative；
- 这只能作为弱校准信号，不能作为 production gate。

### 预测 final outcome

最好的单特征规则之一：

```text
active_avg_overlap <= 0.5555555555555556
accuracy = 0.765625
tp = 32
fp = 7
tn = 17
fn = 8
n = 64
```

另一个同精度规则：

```text
best_rc >= -62.6272465
accuracy = 0.765625
tp = 38
fp = 13
tn = 11
fn = 2
n = 64
```

这里 `best_rc >= -62.6272465` 的方向本身很重要：

- 在这个样本里，“不那么负”的 batch 反而更常对应 improved；
- 这再次证伪“更负 RC 更好”的直觉；
- 但该规则 false positive 很多，不能生产使用。

## 两特征规则：同样本更强，但仍不安全

### 预测 `incumbent_within2`

最好的二特征合取规则：

```text
active_redundant_frac <= 0.16666666666666666
and pair_overlap >= 0.25

accuracy = 0.84375
tp = 19
fp = 3
tn = 35
fn = 7
n = 64
```

这条规则的含义比较合理：

- batch 不能太 active-redundant；
- 但 batch 内也不能完全散掉，需要有一定结构 coherence；
- 这是当前最接近“active-family bridge”的弱形式。

但它仍漏掉 7 个 true downstream incumbent rows，因此不能直接作为 selector。

### 预测 final outcome

最好的二特征合取规则：

```text
active_redundant_frac <= 0.5833333333333334
and pair_overlap <= 0.5416666666666666

accuracy = 0.84375
tp = 36
fp = 6
tn = 18
fn = 4
n = 64
```

这说明：

- 低 active redundancy 和不过高的内部 overlap 对 final outcome 有解释力；
- 但仍有 6 个 false positive；
- 在 exact solver 主线里，false positive 会直接带来 5/10 退化或 20 bad trajectory 风险。

## Leave-one-run 与 leave-one-instance 检查

### Leave-one-run

用 17 个 runs 拟合最佳单特征阈值，预测剩下 1 个 run：

```text
incumbent_within2:
  accuracy = 0.78125
  tp = 20
  fp = 8
  tn = 30
  fn = 6

outcome_improved:
  accuracy = 0.5625
  tp = 29
  fp = 17
  tn = 7
  fn = 11
```

解释：

- downstream incumbent 标签在同分布 repeat 间还算稳定；
- final outcome 标签已经明显不稳定；
- 这说明 outcome 受 run-level / instance-level trajectory 强烈影响，不是单 batch 阈值能解释。

### Leave-one-instance

用 2 个 instances 拟合最佳单特征阈值，预测剩下 1 个 instance：

```text
incumbent_within2:
  accuracy = 0.546875
  tp = 8
  fp = 11
  tn = 27
  fn = 18

outcome_improved:
  accuracy = 0.296875
  tp = 10
  fp = 15
  tn = 9
  fn = 30
```

这是本轮最重要的负证据：

- 同样本阈值看起来不错；
- 留同 instance 的 repeat 也还能维持一部分；
- 但一旦跨 instance，单特征规则基本失效；
- 当前 pre-observable 特征还不能形成可泛化 selector。

## 误判结构

`incumbent_within2` 最好的单特征规则：

```text
active_avg_jaccard <= 0.3055555555555555
```

典型 false negative：

```text
tranq20_01 / return8 / cg2
active_avg_overlap = 0.5833333333333334
active_redundant_frac = 0.25
pair_overlap = 0.5357142857142857
union_size = 9
best_rc = -53.8599425
next_incomplete_count = 0
```

这类 batch 看起来 active overlap 偏高，但后续确实进入 incumbent-producing path。

典型 false positive：

```text
mt20_greedy_apollo_01 / return8 / cg2
active_avg_overlap = 0.6875
active_redundant_frac = 0.375
best_rc = -123.353561
next_incomplete_count = 3
```

这类 batch RC 很强，但后续进入 incomplete-heavy path。

另一个 false positive family：

```text
mt20_greedy_tranq_01 / return12 / cg4
active_avg_overlap = 0.25
active_redundant_frac = 0.0
pair_overlap = 0.0
union_size = 4
best_rc = -3.540581857
next_incomplete_count = 3
```

这类 batch看起来非常不冗余，但 batch 内结构太散、RC 太弱，后续仍进入 incomplete tail。

因此，单纯“低 active overlap”不够；还需要：

- stage；
- batch internal coherence；
- residual tail state；
- next pricing incomplete risk；
- concrete signature / timing / sequence family；
- instance context。

## 当前根因判断

本轮把根因边界进一步收紧：

> addition 前可见的 active-relation 特征确实有信号，但它们目前只能解释同一小样本，不能跨 instance 泛化。当前缺少的是一个 stage-aware、instance/context-aware、能同时考虑 active bridge 与 residual incomplete risk 的 trajectory selector。

这说明为什么“做了这么多仍不行”：

1. Pulse / profile-DP / return12 都能产生更多候选，但没有解决 selector；
2. low-overlap / low-redundancy 能过滤一部分坏 batch，但会漏掉有益 batch；
3. best RC 方向甚至可能反向，不能作为主排序；
4. batch 内完全分散也不行，会变成弱、无结构、incomplete-heavy 的扰动；
5. 5/10 不能承担这种试错成本；
6. 20 要优化必须先解决 trajectory selector 的泛化问题。

## 对下一步的约束

不能把以下任何规则直接接入主线：

- `active_avg_jaccard <= 0.305555...`
- `active_avg_overlap <= 0.555...`
- `active_redundant_frac <= 0.166...`
- `best_rc >= -62.627...`
- 任意同样本最优二特征规则

原因：

- false positive / false negative 仍明显；
- leave-one-instance 泛化失败；
- 特征来自 capped active top samples；
- 样本只有 3 个 20-task instance；
- 还没有 5/10 guard 证明。

下一步仍应是 calibration-only：

1. 扩展 returned-batch trajectory dataset 到更多 20-task logs；
2. 加入 stage、instance、profile、residual-tail context；
3. 加入 concrete signature / start-time / arc-option diversity；
4. 把 `next_incomplete_count` 纳入负标签；
5. 做按 instance 留出验证；
6. 只有当 selector 在跨 instance 验证中稳定，并通过 5/10 no-regression smoke，才允许 opt-in experiment。

## 目标状态

目标仍未完成。

本轮明确证据是：

- 我们已经找到了当前最强的 pre-observable 信号类别：active-relation + batch coherence；
- 但这些信号还不能跨 instance 泛化；
- 因此当前不能宣称已经找到能保证精确性、5/10 不退化、20 大幅加速的优化方向。

