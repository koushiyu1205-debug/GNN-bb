# P0 V2 GAT route-admission 边界换入测试（2026-07-24）

## 结论

本轮已经把 route-admission 监督从“人为单列扩展”改为当前 P0 真实执行的
批次录取动作，并完成一次冻结 scale30 sentinel 的同代码重采集和 exact RMP
回放。

当前结论仍是：

```text
route_admission_decision =
    BLOCK_LINEAR_MATCHED_END_TO_END_UNIDENTIFIABLE
linear_training_authorized = false
```

原因不是代码无法产生标签，而是现有总体样本尚未达到 matched end-to-end
门槛；本次新采集的一个真实活动边界也没有发现优于 P0 的局部动作。

## 已实现的动作和目标

### 动作

每个活动边界保存：

- 完整 canonical binding；
- 排序前全部合法 addable 候选；
- P0 全排序和 P0 实际录取批次；
- 当前 RMP 的全部 `JourneyColumn`；
- 候选列 payload；
- branch/cut context；
- zero-filter telemetry。

control 是 `P0_KEEP_BATCH`。干预动作只把 P0 批次边界的一列换成一列
omitted candidate。contest 只限制离线测量量，不改变合法候选宇宙；所有未测
候选仍保留。

结构零上下文不会写 route-admission 大快照。只有：

```text
addable_candidate_count > P0 admission limit
```

且处于 official objective mode 时才序列化完整 RMP。

### 训练目标

第一关键字是同一 context 内的原始下一次 RMP objective，越小越好。若目标
完全相同，再使用固定候选池上的字典序机制信号：

```text
1. deferred negative RC count      越小越好
2. deferred negative RC mass       越小越好
3. deferred best/min true RC       越大越好
```

这些量不相加，不做跨 context 归一化，不使用早期四系数，也不使用
`0.5 * mass + 0.5 * count`。incomplete arm 保持 censored/masked，不添加
固定罚项。

该目标只提供机制监督，不能单独授权训练或部署。linear 仍要求冻结 sentinel
上的 matched end-to-end perfect-policy net-gain gate 通过。

## 冻结数据审计

历史全集重新扫描结果：

| scale | canonical contexts | 活动边界 | 活动实例 | 可 replay |
|---:|---:|---:|---:|---:|
| 20 | 542 | 0 | 0 | 0 |
| 30 | 1897 | 18 | 13 | 0 |

历史 18 个 scale30 活动边界产生于旧格式，缺少 P0 batch identity 和列
payload，不能事后伪造 lookahead 标签。

fresh 旧格式结果：

| scale | contexts | 活动边界 | P0 batch identity | 可 replay |
|---:|---:|---:|---:|---:|
| 20 | 18 | 0 | 0 | 0 |
| 30 | 50 | 1 | 1 | 0 |

## 新格式真实 scale30 测试

冻结 sentinel：

```text
instance_content_hash = c1e4e704fd4a8e69
scale/index = 30/007
P0 status = BPC_INCOMPLETE_PRICING
P0 wall = 301.651892 sec
redline failures = 0
```

捕获的活动边界：

```text
binding_hash = 38eb3b5e649ca94ec83a622ecb4bd42ae9b8d192c815b869825260c162b48e95
legal candidates = 83
P0 admitted batch = 64
omitted candidates = 19
active RMP columns = 2871
guidance filter count = 0
```

对 P0 control 和 24 个单列 boundary swap 做 exact next-RMP replay：

```text
RMP_OPTIMAL = 25 / 25
censored = 0
next RMP objective = 1.47494（25 / 25 相同）
P0 deferred negative count = 0
P0 deferred negative mass = 0
pairwise positive / harmful / tie = 0 / 12 / 12
```

12 个 harmful 标签由正的 deferred RC margin 变差决定；其余 12 个完全
相同。没有发现相对 P0 的正动作。因此该 context 能证明新采集和 replay
闭环可工作，但不能支持“route-admission 存在正 oracle headroom”的结论。

## 测试

本轮通过：

```text
tests/test_p0v2_gat_route_admission.py                  3 passed
tests/test_p0v2_gat_counterfactual_targets.py
tests/test_p0v2_gat_opportunity_gate.py
三文件合计                                             26 passed
tests/test_p0v2_gat_foundation.py                       39 passed
既有 harvest / micro-batch 定向回归                     3 passed
总计                                                   68 passed
```

覆盖了：

- structure-zero 不写大快照；
- active boundary 完整 snapshot；
- 合法宇宙和 zero-filter；
- P0 control 与 boundary swap exact RMP replay；
- raw/lexicographic 目标；
- censored arm 不变成负样本；
- linear training gate 保持关闭。

## 下一步门槛

1. 继续在预先冻结的 scale30 sentinel 上收集新格式活动边界；scale20 当前
   活动边界为零，不应逐 context 调模型。
2. 每个活动边界先做低成本 local replay；只有存在正局部动作的 context
   才进入昂贵的 matched end-to-end paired trajectory。
3. population ROI 仍使用全部 sentinel context 作为分母，不能用 targeted
   positives 抬高机会率。
4. 样本达到门槛后：
   - perfect-policy net-gain UCB 不大于 0：终止 route-admission；
   - LCB 大于 0：才允许 linear ranker；
   - 介于两者之间：继续采集，不能训练。
5. 如果后续活动边界仍表现为 P0 已关闭全部固定池负 RC，应把主要注意力
   转向 pricing 内部 task/arc discovery 或 proof-tail，而不是用更复杂 GAT
   掩盖 action-family 本身没有 headroom。
