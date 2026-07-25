# P0 V2 GAT 无收益机制优化与首轮可行性检查

日期：2026-07-24

## 结论

本轮没有继续扩大 GAT，而是把监督目标改成了可归因的 route admission
动作。首轮证据表明：

- task/arc feature priority 的真实 Native 事件轨迹没有收益。它经常让同一
  best reduced cost 晚数毫秒出现；
- 仅预测“当前哪条 route 的 reduced cost 更负”仍不足以优化 RMP；
- scale20 的部分 context 存在另一种可学习信号：不同首列会以不同速度
  消除下一轮 true dual 下的 negative pricing pressure；
- 3 个 scale20 development context 的 oracle 优势分别约为
  `0.05418`、`0.02546`、`0.00244`，实例均衡均值约为 `0.02736`，
  但 bootstrap 95% 下界只有 `0.00244`，低于 `0.005` 门槛，因此当前
  仍禁止训练；
- scale5/001 与 scale10/001 的 oracle 上界为零，应走 pre-import
  bypass；scale30/017 在 45 秒和 110 秒 discovery 下均未形成两个合法
  route action，保持 censored，不作负样本。

因此，当前正确方向不是训练更复杂的 GAT，而是继续收集
`fixed_pool_pricing_pressure_auc` 金标签。达到跨实例 oracle gate 后只先
训练 linear ranker。

## 新训练目标

对同一个冻结 RMP context，先建立 deterministic P0 addable route
shortlist。每个 intervention 只把一条合法 route 提升到下一次 admission，
随后完全恢复 P0 顺序。所有 arm 使用相同：

- 初始 active columns；
- fresh RMP、无 basis 复用；
- objective mode、dual stabilization、worker、queue 与 cache 状态；
- shortlist universe；
- rollout admission horizon。

设固定 shortlist 在初始 true dual 下的负 reduced-cost 总质量和数量为
`M_0` 与 `N_0`，第 `t` 个 admission 后为 `M_t` 与 `N_t`。轨迹进度定义为：

```text
pressure_progress_t =
    0.5 * clip(1 - M_t / M_0, 0, 1)
  + 0.5 * clip(1 - N_t / N_0, 0, 1)
```

训练 utility 是该进度在固定 admission horizon 上的 AUC。动作标签仍为：

```text
advantage(action) = utility(action-first) - utility(P0_KEEP_ORDER)
conservative_value = mean(advantage) - 1.96 * standard_error
```

模型候选集合显式包含 `P0_KEEP_ORDER`。未 probe 的 route 不作为负样本；
oracle headroom 是所有被 probe 动作的最大非负 conservative value。

这个目标比当前 reduced-cost grade 更接近拖尾根因：某列即使不立即改变
RMP objective，也可能改变退化 dual，使后续负列质量和数量快速下降。

## 已实施代码

1. Native event-time telemetry

   - 在 sink solution 真正首次改善 best RC 时记录 wall time、extended
     labels、solution count、discovered RC 与 best RC；
   - 只记录 harvest 调用，exact proof 不使用事件轨迹；
   - Python 侧检查时间、labels、solution count、best RC 单调性及最终
     best RC 一致性；
   - malformed、truncated 或存在 Native audit blocker 的轨迹不能训练，
     但不会影响 certificate 字段。

2. 单次运行轨迹 collector

   - task/arc 诊断不再把 0.02/0.05 秒 restart horizon 当作发现时间；
   - 每个 arm 只运行一次，直接消费 Native 事件；
   - 记录真实 label 扩展位置，保留 task/arc 仅作机制诊断的边界。

3. U0 deferred micro-batch

   - 支持每轮仅 admission `K` 列；
   - 其余合法列进入 node-local deferred buffer；
   - 下一轮必须按新 true dual 重新计算 reduced cost；
   - 不允许 guidance-induced permanent drop；
   - deferred candidate 超出显式 resource limit 时，整个实验 legal
     incomplete，不能丢列后继续宣称结果。

4. fixed-P0 RMP rollout

   - 使用 deterministic P0 shortlist；
   - 比较 P0 和 single-route promotion；
   - 记录 RMP objective、固定池 negative mass/count、激活状态和 RMP
     wall-time diagnostic；
   - 输出正式 route-level counterfactual record。

5. oracle headroom gate

   - instance 是 bootstrap 单位，先在实例内平均 contexts；
   - 默认要求 scale20/30 各至少 20 个 formal contexts；
   - 默认要求 mean oracle gain 的 95% LCB 至少 `0.005`，positive-context
     fraction 的 95% LCB 至少 `0.10`；
   - 正式训练入口必须绑定同一 records JSONL 的 SHA-256；
   - gate 未通过时直接拒绝训练，并要求修改排序动作。

## 首轮实测

### Native task/arc 真实事件

scale20 的一个 development context 中：

- P0 在约 `0.00012 s` 已达到约 `-0.108821`；
- task006 promotion 到约 `0.009 s` 才达到相近 best RC；
- task020 会改变早期轨迹，但没有形成稳定优于 P0 的终值。

这解释了旧 restart 表中“结果相同但看不出为何无收益”的现象：旧表丢掉了
真实事件时间。

### 直接在线 U0

scale20/043，4 个 pricing rounds：

| 模式 | wall sec | added columns | 最终记录的 RMP objective |
|---|---:|---:|---:|
| 原 worker/P0 batch16 | 8.77 | 62 | 1.772634 |
| U0 micro16 | 18.63 | 64 | 1.772634 |
| U0 micro4 | 19.63 | 16 | 1.772634 |

U0 正确保留了所有 deferred 列，但第一轮便产生约 3500 条 deferred route。
这条路径在线开销过大，所以 U0 当前只用于离线因果 rollout，不进入部署。

### fixed-pool pricing-pressure oracle

| scale/context | conservative oracle gain | 当前结论 |
|---|---:|---|
| 5/001 | 0 | bypass 候选 |
| 10/001 | 0 | bypass 候选 |
| 20/022 | 0.05418 | 有 headroom |
| 20/043 | 0.02546 | 有 headroom |
| 20/055 | 0.00244 | 低于 practical threshold |
| 30/017 | censored | shortlist discovery 不足 |

3 个 scale20 contexts 的联合 gate 仍失败：

```text
instance-balanced mean oracle gain = 0.02736
bootstrap mean-gain LCB95          = 0.00244
positive-context fraction          = 2/3
positive-fraction LCB95            = 0
```

样本太少且最差实例信号太弱，不能据此启动训练。

## 下一步顺序

1. 从 development pool 收集 scale20 至少 20 个不同实例的 fixed-pool
   pricing-pressure rollout；
2. scale30 不重新跑完整 BPC，优先从已经发生负列 harvest 的 RMP
   snapshots 收集 shortlist；无法形成 action universe 的 context 保持
   censored；
3. 同步抽查 scale5/10；若 oracle LCB 继续为零，冻结为 pre-import
   bypass，不让共享训练造成退化；
4. oracle gate 通过后，只训练 linear ranker，并以 P0 no-op 为显式动作；
5. 只有 linear 的离线 pressure trajectory、真实 Native discovery 和
   端到端 Stage B 都通过，才比较 MLP；GAT 继续 shadow。

## 当前边界

- production 默认仍为 `no_cut`；
- P0 V2 control 与 exact certificate 语义未改变；
- 新 event trace、U0 和 RMP rollout 均不能生成 certificate；
- proof queue 与 branch 在线顺序仍未修改；
- full80 和现有 scale50/100 protected data 未参与本轮选择。

## 2026-07-24 稀疏机会补充门槛

本计划中的 oracle-headroom gate 现已升级为两道互相独立的门槛：

1. pressure/action headroom：排序动作是否存在机制差异；
2. opportunity ROI：无偏 sentinel 流中的作用点是否足够密集，且完美可弃权
   策略扣除完整调用成本后是否仍有净收益。

target-mode 富集样本不得用于第二道门槛。实现、文献依据和首轮 smoke 结果见
`P0V2_GAT_SPARSE_OPPORTUNITY_ROI_GATE_20260724_ZH.md`。在 matched
end-to-end 节时 LCB 缺失时，正式训练继续 fail closed。
