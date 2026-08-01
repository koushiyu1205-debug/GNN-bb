# P0 V3 内存压缩候选：scale30/50 实施与验证状态

日期：2026-07-29

## 结论

本轮候选已经证明：

- Native SPPRC 的紧凑状态表示不会使 scale30 整体退化；正式 full20 冷启动回归为 20/20 exact，mean、p50、paired geometric mean 和最大值均优于冻结 P0 V3。
- scale50/001 可以在当前约 15.5 GiB 主机上稳定运行至 3600 秒，不再因为 Native host 跨轮保留已释放堆页而提前内存失败。
- 但 scale50/001 在 3600 秒内仍未完成 root exact closure。因此该候选不能宣称“scale50 可求解”，也不构成六规模 promotion 证据。

在上述边界已写入不可变清单的前提下，用户于 2026-07-29 明确授权将该候选冻结为新的 active 实验基准：

```text
FROZEN_NATIVE_LIVE_SRI_P0_MEMORY_COMPACT_BASELINE_V4
```

原 P0 V3 作为 historical control 保留，production `no_cut` 默认和所有数学/certificate 规则均未修改。

## 主机与预算边界

- 主机物理内存：约 15.52 GiB。
- 配置名义内存：16 GiB。
- 为给 Python 父进程、RMP、系统和 WSL 保留安全余量，单个 Native 进程的实际限制被统一夹到 10.867122 GiB。
- 不能在这台主机上把完整 16 GiB 全部分配给 Native 子进程；这会使父进程与系统没有可用余量，并可能触发 WSL 级 OOM。

## 已实现的候选优化

### Native label 内存

- `JourneyValue` 改为只保存当前需要的 state 或 action，不再同时保存两份。
- 删除恒为零的 `RealResource` 组合分量。
- 五个任务计数器改为 `uint16_t`；当前最大规模 100，范围安全。
- `State` 从约 200 bytes 降至 176 bytes，`JourneyValue` 降至约 184 bytes。
- dominance bucket 不再为每条 label 维护额外的哈希定位表；bucket 直接保存稳定 iterator。
- DSSR pressure 数组和摘要只在对应 policy 实际启用时分配。

### Host 生命周期

- 仅对 task count 不小于 50、且一次响应峰值 RSS 达到阈值的 Native host 做确定性回收。
- 下一轮重新创建 host，防止 C++ allocator 已释放但没有归还操作系统的堆页跨轮常驻。
- scale5/10/20/30 不触发该路径。
- 回收不改变请求、候选宇宙、RC、bound、pruning 或 certificate。

### Python admission 选择

- 多样性选择由反复重算所有已选集合的近似 `O(C*K^2)` 实现，改为增量维护最大 Jaccard/containment 的 `O(C*K)` 实现。
- 250 组确定性随机输入与旧实现逐项输出一致。
- 该改动只减少重复计算，不改变排序 key、选择结果或合法列集合。

## 测试

- Native C++：2/2 通过。
- 相关 Python：169 项通过，另有 29 个子测试通过。
- 增量 admission 选择器：250 组新旧实现逐项一致。
- safety telemetry：
  - certificate leak = 0；
  - manual RC failure = 0；
  - pricing RC failure = 0；
  - true-dual recompute missing = 0；
  - no-cheat failure = 0。

## scale30 full20 配对回归

运行：

```text
runs/p0v3_memory_compact_candidate_20260729/scale30_full20_v3
```

| 指标 | 冻结 P0 V3 | memory-compact V3 | candidate / P0 |
|---|---:|---:|---:|
| exact | 20/20 | 20/20 | 相同 |
| incomplete | 0 | 0 | 相同 |
| 总 cold solve time | 3946.270 s | 3024.332 s | 0.766 |
| mean | 197.313 s | 151.217 s | 0.766 |
| p50 | 79.579 s | 63.373 s | 0.796 |
| max | 1157.471 s | 846.963 s | 0.732 |
| paired geometric mean ratio | — | — | 0.763 |
| 改善/退化实例数 | — | 19 / 1 | — |

主要实例：

| instance | P0 V3 | candidate | ratio |
|---|---:|---:|---:|
| 001 | 140.310 s | 105.631 s | 0.753 |
| 005 | 195.483 s | 169.376 s | 0.866 |
| 009 | 304.982 s | 194.910 s | 0.639 |
| 012 | 256.122 s | 345.147 s | 1.348 |
| 013 | 536.924 s | 312.542 s | 0.582 |
| 016 | 1157.471 s | 846.963 s | 0.732 |

instance012 是唯一明确退化例，但整体 mean、p50、paired geometric mean 和 max 均改善，且 zero extra incomplete。

instance017 的报告 objective 分别显示为 `1.696362` 和 `1.696363`。两个运行在相同分支树的 node_005 找到两组不同的近等价整数路线；各自满足：

- `global_gap = 0`；
- global lower bound = incumbent objective；
- certificate ledger valid；
- true-dual exact pricing closure。

差值为固定数值容差量级的 `1e-6`，不是 certificate 泄漏或漏搜。若未来要求跨实现逐 bit 相同的 incumbent，需要另设确定性 tie-breaking/高精度 objective 审计；这不是当前 exact-safe gate 的语义。

## scale50/001 结果

最终候选：

```text
runs/p0v3_memory_compact_candidate_20260729/
  scale50_instance001_v5_batch128_fast_selector
```

正式结果：

- solver wall：3594.280 s；
- root CG：3590.835 s；
- 状态：`BPC_INCOMPLETE_PRICING`；
- pricing state：`INCOMPLETE_LIMIT`；
- pricing rounds：111；
- root 新增列：13173；
- active columns：13201；
- root RMP objective：1.542193；
- 最后一轮 Native engine status：`TIMEOUT`；
- `can_certify_no_negative = false`；
- exact count：0；
- 所有 safety redline：0；
- 进程树峰值 RSS：约 11.27 GiB；
- 未进入 B&B tree。

对比演化：

| 候选 | 结果 |
|---|---|
| 冻结 P0 V3，8 GiB | 约 711 s 内存失败 |
| compact、无 host recycle | 约 672 s 后仍因跨轮常驻内存失败 |
| 96 列 + recycle | 跑满 3600 s；104 轮、9525 列；root 未闭合 |
| 256 Native target | 与 admission 生命周期不匹配，搜索和 Python 后处理浪费；拒绝 |
| 128 target + fast selector + recycle | 跑满 3600 s；111 轮、13173 列；root 未闭合 |

最终候选把失败边界从“内存不足”推进到“时间耗尽”，但没有满足 scale50 exact root closure 门槛。

## 当前真正的问题

### scale50

跨轮 allocator 常驻问题已经解决，但单次困难 dual 下的 label frontier 仍可接近 10.8 GiB。更关键的是，3600 秒后仍持续发现大量负列：

- 根 RMP 需要的列生成轮数过多；
- 每个大批次既有 Native 搜索成本，也有列审计/admission/RMP 更新成本；
- host recycle 控制峰值，但不能复用上轮 label frontier，因此会以时间换内存；
- 单纯继续压缩几个字段不足以使 root 在一小时内 exact 闭合。

### scale30 proof tail

instance016 的根 CG 只约 66 秒，主要耗时约 780 秒在 tree closure。其瓶颈是多个分支节点的重复 exact pricing/proof，而不是根内存。因此 scale30 拖尾和 scale50 根 frontier 不能用同一个工程补丁解释。

## 决策

- 不覆盖或删除冻结 P0 V3；将其登记为 preserved historical experiment baseline。
- memory-compact V3 已按用户明确授权冻结为 active 实验基准 V4：
  `runs/frozen_native_live_sri_p0_memory_compact_baseline_v4_20260729`。
- 不宣称 scale50 可求解。
- 按用户指示不运行 scale50 全量。V4 是有限验证范围的新实验基准，不是六规模 promotion 完成声明。
- V4 二进制上的 scale5/10/20 full20 与 scale100 尚未正式重跑；freeze manifest 和 registry 必须持续显示该边界。
- 下一轮若继续，应优先验证一个 exact-safe 的自适应 root harvest/admission policy：
  - 早期负列充足、搜索便宜时允许更大批次；
  - 单轮 RSS/时间升高时自动缩小批次；
  - 所有阈值进入 config/engine hash；
  - 永不以未穷尽结果签发 no-negative certificate；
  - 首先在相同 scale50/001 上验证 3600 秒 root closure，再谈更广验证。
