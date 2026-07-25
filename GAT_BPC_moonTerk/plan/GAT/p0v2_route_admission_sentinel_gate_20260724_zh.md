# P0 V2 route-admission frozen sentinel 再审计与门控结果

日期：2026-07-24

## 结论

当前不允许训练 linear ranker。

冻结 sentinel 的实例样本门槛已经达到，但 matched end-to-end exact
paired sample 门槛没有达到，完美策略的整体净收益置信上界因而仍不可识别，
不能把缺失结果当作零收益。

分规模结论如下：

- scale20：542 个唯一 canonical harvest contexts，覆盖 24 个 frozen
  sentinel 实例；所有 context 的 addable route 都不超过实际 P0 admission
  limit 32。route promotion 不改变 admission set，属于 structural zero。
  在给完美策略免费 pre-import gate 的乐观条件下，净收益 UCB95 为 0，
  该规模的 route-admission 动作族应终止并保持 bypass。
- scale30：1897 个唯一 canonical contexts，覆盖 32 个 frozen sentinel
  实例；只有 18 个 context 的 addable route 超过实际 limit 64，分布在
  13 个实例。其余 1879 个 context 都是 structural zero。
- scale30 的 18 个有效 context 全部来自未 exact closure 的 P0 运行：
  16 个 context 对应 `BPC_INCOMPLETE_PRICING`，2 个对应
  `BPC_GAP_AVAILABLE`；有效实例中 exact-complete 数为 0。因此当前
  300 秒 P0 合同下不能生成合法的 exact wall-time benefit pairs。
- 整体决策是
  `BLOCK_LINEAR_MATCHED_END_TO_END_UNIDENTIFIABLE` /
  `CONTINUE_MATCHED_PAIRED_COLLECTION`，而不是 PASS，也不是把
  incomplete 强行解释为负收益后的提前终止。

## 这次修正的关键问题

### 1. 正式目标只有一个明确规格

正式 fixed-pool pressure 目标固定为：

```text
fixed_pool_pricing_pressure_auc.equal_mass_count.current_state.normalized.v1
```

每个轨迹点必须满足：

```text
rmp_progress =
    0.5 * fixed_pool_negative_mass_reduction
  + 0.5 * fixed_pool_negative_count_reduction
```

三个量都必须位于 `[0, 1]`，validator 会重新计算并拒绝不一致记录。
不再使用 running maximum 掩盖后续 pressure 回退。

exact solver 当前真正执行的成本目标固定标识为：

```text
normalized_operating_cost_1+risk_1+weighted_completion_0.4.v1
```

早期的 `alpha/beta/gamma/delta` 四个字段只为保持 frozen instance content
hash 而保留，并在 objective metadata 中明确标为 ignored；旧 sentinel
hash 没有被改写。

### 2. fixed-pool 单列 rollout 不再冒充在线 treatment

旧 probe 每一步只加入一列，隐式制造了 micro-batch 动作空间；当前 P0
则批量加入最多 32/64 条 route，并在下一次 RMP 前按 semantic signature
确定性排序。

因此旧 fixed-pool collector 现在强制写入：

```text
formal_first_stage_eligible = false
online_admission_semantics_match = false
```

它仍可用于诊断，但不能授权训练。

### 3. 在线 telemetry 区分“顺序变了”和“admission set 变了”

harvest 现在同时计算 P0 selection 和 guided selection，并记录：

```text
guidance_order_changed
guidance_admission_set_changed
guidance_admission_set_symmetric_difference_count
route_admission_treatment_effective
route_admission_structural_zero
```

若 promotion 只改变临时顺序但不改变 admission set，treatment 标记为：

```text
installed_but_behaviorally_equivalent
```

这类 context 不再生成可训练 action value。

### 4. matched end-to-end 证据合同收紧

正式 wall-time benefit 现在要求：

- 至少 3 个唯一 paired replicates；
- P0/action 均为 fresh process；
- pair 顺序随机化；
- action 在 outcome 前冻结；
- canonical action binding、RMP context、sentinel manifest、预算和 objective
  spec 完全一致；
- P0/action 都是 complete exact；
- objective、legal universe、certificate 语义一致；
- zero guidance filtering 和 zero extra incomplete。

signed paired LCB/UCB 会同时保存；完美策略可通过 no-op 将负收益截为零，
但停止规则使用未伪造的统计不确定性。

### 5. 统计单位和停止规则

- 唯一 context 身份为
  `selection_manifest_hash + scale + instance_content_hash + rmp_context_hash`；
- 重复 observation ID 或同一 canonical context 的伪重复不能增加样本量；
- bootstrap 单位仍是 instance，先做 instance 内 context 平均；
- scale20/30 等权形成整体净收益区间；
- 只有整体 LCB95 大于零且所有分规模 gate 通过，才写入
  `ALLOW_LINEAR_TRAINING`；
- 样本完整后整体 UCB95 不大于零，才写入
  `TERMINATE_ROUTE_ADMISSION`；
- 缺失有效 action 的 paired outcome 时，必须保持
  `CONTINUE_MATCHED_PAIRED_COLLECTION`。

## 新鲜求解复核

在修改后的真实求解路径上另做了两个 fresh P0 sentinel：

| scale | instance | 结果 | wall | context | 有效 admission context |
|---:|---|---|---:|---:|---:|
| 20 | instance 043 | `BPC_OPTIMAL` | 3.92 s | 18 | 0 |
| 30 | instance 007 | `BPC_INCOMPLETE_PRICING` | 301.61 s | 50 | 1 |

scale30 的有效 context 重现了 `83 addable / 64 admitted`，即 19 条 route
被容量延后。新的训练行同时保存 candidate IDs、P0 selected IDs、实际
selection limit、omitted count 和 structural-zero 标记。

## 当前不可越过的阻断

当前不是“模型还没训练好”，而是可识别的在线 treatment 太稀疏且只出现在
未闭合拖尾实例中。若不先定义可审计的 censored end-to-end trajectory
estimand，或在完全匹配的更长预算下让这些实例 exact closure，继续重复
300 秒 exact wall-time pair 仍不会产生正式 benefit 标签。

所以本轮没有启动 linear、MLP 或 GAT 训练，也没有用旧 fixed-pool 正信号
绕过门控。
