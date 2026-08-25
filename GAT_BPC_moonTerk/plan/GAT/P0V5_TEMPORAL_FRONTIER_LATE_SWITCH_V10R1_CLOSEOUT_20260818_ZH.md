# P0V5 Temporal Frontier Late-Switch V10R1 Closeout

## 最终结论

V10 的 240 个 fresh blocked tasks 已全部完成，Native/exact correctness redline
为零。V10 冻结 analyzer 的 instance metadata 传播存在错误，因此 V10R1 在独立目录
完成只读修正审计；V10 原 terminal 和全部 wall evidence 均未重写。

修正后的结论为：

```text
FAIL / SCALE50_LATE_SWITCH_SUPPORT_GATE_FAILED
```

因此：

- scale30 的 QD1 高激活命题通过本轮 diagnostic；
- scale50 在 16384 boundary 存在 measured oracle headroom，但收益没有分布到足够多
  的 strong-benefit instances；
- 不授权训练 temporal GAT；
- 不读取或生成 heldout、Development-E2E、formal outcome；
- QB1、QGR1 继续 veto。

## 修正后指标

### scale30 / 4096

| 指标 | 结果 |
|---|---:|
| determined instances | 8/8 |
| fixed QPD1 net GM | 0.820842 |
| net oracle GM | 0.820842 |
| QPD1 winner instances | 8 |
| strong-benefit instances | 8 |
| probe overhead GM | 1.003691 |
| correctness/resource redline | 0 |

scale30 通过全部原冻结 gate。它进一步确认 scale30 应继续采用 QD1 高激活，而不是
为证明 GAT 必要性人为制造 Q0 negative examples。

### scale50

| Boundary | Determined | Fixed QPD1 GM | Oracle GM | Winners | Strong benefit | Neutral/harm | Harm | Gate |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 4096 | 7/8 | 1.262341 | 0.987423 | 4 | 0 | 5 | 3 | FAIL |
| 8192 | 7/8 | 1.260554 | 0.982355 | 3 | 1 | 4 | 3 | FAIL |
| 16384 | 8/8 | 1.160861 | 0.936561 | 4 | 1 | 4 | 3 | FAIL |

16384 是唯一达到 `oracle GM <= 0.95` 的 boundary，但原冻结 gate 同时要求至少两个
不同 strong-benefit instances（net ratio `<=0.95`）。实际只有一个：

```text
instance 23cc0c6fee9f1fa0: net ratio 0.654282
```

其余三个 QPD1 winner 的 ratio 为约 `0.95970 / 0.97031 / 0.97158`，属于小幅收益，
不足以通过预冻结的 strong-support gate。另有三个 harmful instances，其中两个约为
`1.70941` 与 `3.03615`，tail risk 很高。

## 为什么不继续训练 temporal GAT

本轮不是“完全没有 oracle headroom”，而是“oracle headroom 由一个强收益长尾实例
主导”。在只有一个 strong-benefit instance 的情况下训练 message-passing GAT，模型
容易学习该实例身份或偶然 telemetry pattern，无法支撑 scale50 fresh heldout 的
高置信安全激活。按 outcome 结果降低 `minimum_strong_benefit_instances=2` 会构成
post-outcome gate relaxation，因此禁止。

这也解释了此前多次 GAT negative 的共同根因：排序 arm 的真实收益高度异质，且可安全
利用的强正例分布不足；问题首先是 action support 与 observability，而不是 GAT hidden
dimension、seed 或 pooling 不够。

## 证据位置

原始 V10 只读链：

```text
runs/p0v5_temporal_frontier_late_switch_oracle_v10_20260818/
```

修正审计链：

```text
runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818/
```

关键文件：

- `corrected_collapsed.json`；
- `corrected_oracle.decision.json`；
- `terminal_decision.json`；
- `verification.report.json`。

## 后续边界

当前 objective 的 conditional gate 已触发 negative：不得在该 corpus 上训练 temporal
GAT，也不得继续调 boundary、放宽 strong-benefit 门槛或复活 QB1/QGR1。若未来重新
研究，只能新建完全独立、outcome-blind 的 larger fresh scale50 support census，先验证
至少两个以上 strong-benefit instances 可复现，再决定是否恢复 temporal GAT；不能把
本轮 8 个实例继续按 outcome 扩样成训练集。
