# P0V5 Counterfactual-Prefix Interaction-GAT QD1 Selector V8R1 Closeout

## 结论

V8R1 已按冻结 gate 合法终止：

```text
FAIL / COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE
immediate_cause = PREFIX_COST_GATE_FAILED_BEFORE_OOF
```

这里的 `NOT_IDENTIFIABLE` 是计划预定义的 terminal reason；实际未进入 representation OOF，直接原因是辅助 prefix 的逐 context 2% 开销门失败。不得把该结果解释为已经证明 GAT 分类能力不足。

## 为什么需要 V8R1

原 V8 把 cold fresh-process wall 当作 warm prefix wall，并让三个预算共享跑到 2048 的同一总 wall。其 negative terminal 已保持只读，但 `performance_authority=false`。V8R1 新建独立 evidence chain，重新采集全部 prefix，不复用原 V8 wall 或 graph。

## Exact-safe 和接口验证

- 新 engine：`5a13fa2dd18bfafc`；
- 旧 V7/new V8R1 500-case Q0 cross-binary differential：0 mismatch；
- CTest：2/2；V8 Python test：11/11；
- 100 个随机 triplet 的 PyTorch/C++ forward 误差 `<=1e-5` 且 action 一致；
- `sizeof(State)==176`；
- 76/76 prefix requests 均 routes 空、certificate 空、`exact=false`；
- 38/38 Q0/QD1 prefix base graph hash 一致；
- 114 个 triplets 使用各自 checkpoint 的 Native endpoint elapsed wall；
- 38/38 contexts 的 action-previsible lifecycle signal 已进入两臂 graph；
- probes 后 reject/error 会创建独立 formal exact Q0 request；probe 前 bypass 仍返回同一 request。

## 正确计时后的 gate

| B | warm paired p99 | 超过 QPF0 2% 的 contexts | 最坏比例 | taxed oracle GM s30 | taxed oracle GM s50 |
|---:|---:|---:|---:|---:|---:|
| 128 | 119.234 ms | 5 | 0.118223 | 0.844668 | 0.952201 |
| 512 | 137.553 ms | 5 | 0.138507 | 0.848260 | 0.952550 |
| 2048 | 174.287 ms | 6 | 0.178481 | 0.856056 | 0.953544 |

warm p99 `<=250 ms` 和两规模 taxed oracle `<=0.97` 均通过。唯一失败项是冻结的逐 context overhead fraction。最小预算 B=128 的五个失败 context 全部来自 scale30，其 QPF0 wall 仅约 0.389–1.614 s，而 paired prefix 仍需约 33.7–70.1 ms；最坏 context 为 45.98 ms / 388.92 ms = 11.82%。

## 根本原因

V8 的决策信息来自两个独立辅助 request。即使 rollout 只取 128 pops，也必须把同一个 pricing state 的前 4096 Q0 pops执行两遍，随后再执行一次 formal exact request。对长 context，这一固定税可能被潜在 QD1 收益覆盖；对本链中的快速 scale30 context，4096-pop 双前缀本身已远高于 2% 上限。该问题不能通过更换 GAT、threshold、训练 seed 或增加样本修复。

因此 V8R1 证明的是：

> 在固定“两次独立 4096-pop prefix + 逐 context 2% overhead gate”合同下，Counterfactual-Prefix candidate 不可进入 GAT 训练。

它没有证明 counterfactual features 无法区分收益，也没有产生任何 GAT 加速候选。

## 未启动阶段

以下阶段按 stop rule 全部未启动，outcome/artifact 数量为零：

- grouped-OOF GAT/MLP/Linear/no-message/shuffled-topology；
- fresh pilot 和 outcome-blind main census；
- calibration、candidate bundle 和 runtime manifest；
- selector-heldout；
- Development-E2E；
- formal full100。

不得在本 run root 中补写这些 artifacts，也不得放宽 2% gate 后续跑。

## 后续研究边界

若继续，必须另开新链并改变架构，而不是修补 V8 threshold。可检验方向只能减少固定双前缀成本，例如在同一 Native execution 内做可回滚/共享前缀的 counterfactual telemetry，或先用极低成本 Native statistic veto 快速 contexts，再只对慢 context启动第二前缀。任何新链都必须重新冻结 overhead contract，并重新证明辅助状态不会改变 exact route/certificate 语义。
