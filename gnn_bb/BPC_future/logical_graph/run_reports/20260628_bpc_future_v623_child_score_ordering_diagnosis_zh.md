# 20260628 V623：Child Score Ordering 诊断

## 目的

V622 已经说明：completion-bound / final-judge retry gate 可以减少一部分 retry CPU，但不能让 4 个 hard 20-scale 实例闭环；全局 gate 还会把压力转移成更多 branch/search。

本轮测试一个更靠近 proof tree 的 exact-safe 杠杆：只改变同一个 Ryan-Foster pair 下两个 child 的入队顺序，即：

```text
journey_child_priority_mode=child_score
```

该机制只影响 child queue order，不改变 lower bound、branch constraint、pricing closure、fathom/prune 依据。

## 输入

共同设置：

- 实例：V622 同一批 4 个 hard random-TW 20-scale 实例。
- 配置：`moon_trek_20_smoke.yaml`
- 外部时限：600s
- 并行度：4
- branch pair：V617 depth2 score map
- admission：off
- early branch：off
- ordinary incomplete/no-column retry：on
- completion-bound final-judge retry：on
- retry gate / budget cap：off

基线：

```text
BPC_future/results/20260628_v622_retry_on_off_gate_smoke4_tasks20/retry_on/
```

V623c 输出：

```text
BPC_future/results/20260628_v623c_child_score_paironly_local_fathom_smoke4_tasks20/
```

## 过程发现

### 1. rows 文件直接使用是 no-op

先使用：

```text
BPC_future/results/journey_child_score_map_v589_v588_local_fathom_child_order_20260628/journey_child_score_rows.json
```

日志显示：

```text
child_score_entry_count = 0
```

原因是 rows 带 context scope，当前实例上下文没有匹配上。因此该 run 被停止，不作为性能结果。

### 2. legacy map 仍然过度绑定 node/depth

改用：

```text
BPC_future/results/journey_child_score_map_v589_v588_local_fathom_child_order_20260628/journey_child_score_map.json
```

虽然 `child_score_entry_count=6`，但 key 仍是：

```text
node:0:depth:0:1,3:same_vehicle
```

这类强绑定 key。当前 hard path 中出现同样 pair 时，通常 node/depth 不同，所以仍几乎不命中。该 run 也被停止，不作为性能结果。

### 3. V623c 使用 pair-only 诊断 map

为验证 child-order 信号本身是否有泛化价值，构造 pair-only 诊断 map：

```text
BPC_future/results/journey_child_score_map_v623c_paironly_local_fathom_20260628/journey_child_score_paironly_map.json
```

内容：

```json
{
  "1,11:same_vehicle": -3.013593293,
  "1,3:same_vehicle": 4.353985533,
  "1,9:same_vehicle": 0.812192492,
  "2,18:same_vehicle": 0.964524142,
  "3,17:same_vehicle": -8.685079925,
  "4,8:separate_vehicle": 1.356317333
}
```

该 map 标记为：

```text
diagnostic_only = true
production_ready = false
usable_as_certificate = false
```

## 结果

### V622 retry_on

```text
status = 4/4 EXTERNAL_TIME_LIMIT
mean wall = 600.021s
mean gap = 0.047618
branch = 162
child queued = 324
completion-bound retry = 175
ordinary retry = 3
fathom = 8
```

### V623c child_score_paironly

```text
status = 4/4 EXTERNAL_TIME_LIMIT
mean wall = 600.021s
mean gap = 0.047618
branch = 163
child queued = 326
completion-bound retry = 176
ordinary retry = 3
fathom = 8
child score hits = 18
```

按实例：

| instance | V622 branch | V623c branch | V622 CB retry | V623c CB retry | child score hits | gap |
|---|---:|---:|---:|---:|---:|---:|
| seed61311 greedy-anchor | 26 | 26 | 29 | 29 | 4 | 0.051215 |
| seed61635 greedy-anchor | 38 | 38 | 39 | 39 | 10 | 0.061278 |
| seed61410 sector-wave | 41 | 42 | 43 | 44 | 3 | 0.034203 |
| seed61718 sector-wave | 57 | 57 | 64 | 64 | 1 | 0.043777 |

## 有效改序统计

V623c 中共有 18 个 parent 命中 child score，但只有 3 个 parent 可能真正改变了 child 顺序：

```text
parents_with_score = 18
first_child_scored = 18
scored_separate_first_likely_reordered = 3
```

解释：

- 大多数命中是 `same_vehicle` child，而默认声明顺序本来就是 same 在前；
- 这类命中只记录了 score，没有实际改变搜索顺序；
- 真正可能改序的是 `4,8:separate_vehicle`，只出现 3 次；
- 3 次改序不足以改变 600s proof tail。

## 判断

V623c 没有优化效果。

这不是因为 child-score ordering 代码入口无效；入口有效，日志也记录了 `priority_mode=child_score` 和非空 `child_priority_score`。

真正问题是训练/诊断数据不够：

1. 原始 child score map 的 context / node / depth 绑定过强，换一条 hard path 就不命中。
2. pair-only 放宽后虽然能命中，但命中集中在少数 pair 上。
3. 大部分命中没有实际改序，因为 scored child 已经是默认 first child。
4. 当前 child labels 来自 local-fathom / right-censored 片段，不等价于完整求解 wall-time / proof-cost 反事实。

## 对当前优化方向的影响

retry gate 不是主线，child-order 也暂时不是主线。

当前主线应回到更上层的 branch pair decision：

1. 继续保留 V617/V613 类 branch score，但不能只靠 root/depth2 overlay。
2. 需要在 hard path 深层节点采集成对 child 反事实：
   - same child proof CPU
   - separate child proof CPU
   - child corrected LB gain
   - child exact pricing events
   - child completion-bound retry
   - child time-to-certificate
   - child fathom reason
3. child-order 标签必须同时包含两个 child，不能只记录“某个 child 曾经 local fathom”。
4. score map 导出应明确区分：
   - strict context/node/depth score
   - depth/pair fallback
   - pair-only diagnostic fallback
   - production_ready=false 的诊断行
5. solver 日志应增加直接字段：
   - `child_order_changed`
   - `child_order_change_reason`
   - `child_order_score_hit_count`
   - `child_order_effective_hit_count`

## 下一步

最值得做的是构建 hard-path paired child replay，而不是继续调这 6 个 child-score 条目。

建议下一轮：

1. 从 V622/V623c 的 actual branch nodes 中抽样：
   - high CB retry node
   - high depth node
   - no fathom before timeout node
   - branch score selected but unresolved node
2. 对同一个 parent 强制分别先跑 same / separate child，并记录固定预算下：
   - exact pricing closure 状态
   - completion-bound retry 次数
   - corrected LB gain
   - proof CPU
   - 是否快速 fathom
3. 训练 child ordering 只学习“same/separate 谁先更省 proof”，不要和 branch pair selection 混在一个标签里。
4. 如果 paired child replay 仍找不到差异，就暂停 child-order 线，把资源集中到 branch pair score 和 proof reuse / branch tree width 控制。

## Exact-Safe 边界

V623/V623c 只改变 child 入队顺序：

- 不提供 official bound；
- 不修改 lower bound；
- 不用 score 剪枝；
- 不跳过 exact pricing closure；
- 不改变 integer incumbent 逻辑。

因此本轮没有破坏精确性，但也没有达成 20-scale 加速。
