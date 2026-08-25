# P0V5 Base-Label Frontier Observability V9R0

## 1. 目的

本链回答一个比继续设计 V9 求解器更靠前的问题：在第 4096 次 label pop
时，只观察一次最多 256 个 label 的原始 frontier，是否已经能把 scale50 上
QD1 的收益 context 与伤害 context 分开。

V9R0 是 `diagnostic_only` 链，不产生新的 arm wall outcome，不读取 heldout、
E2E 或 formal outcome，也不授权运行时或性能声明。只有 instance-grouped OOF
门通过，才允许另行实现 Native 单请求 selector。

## 2. 已定位的两类失败

- V7R3 的 64-cell depth-RC 聚合图仍有明显的信息碰撞。scale50 GAT benefit
  balanced accuracy 为 `0.60909`，rank accuracy 为 `0.525`，最近 10% 图对中
  相反 benefit 标签比例为 `0.64706`。这不是 oracle 不存在：同一批数据的
  scale50 Q0/QD1 oracle GM 为 `0.94964`。
- V8R1 的 counterfactual 三视图没有进入 OOF，因为两个辅助 prefix 的真实
  Native warm wall 已先违反每个 context 2% 成本门。最小预算 B=128 的 p99
  为约 119 ms，5 个 scale30 context 超门，最坏比例约 11.82%。

因此不能继续用“增加辅助求解工作”换特征，也不能回到 64-cell 聚合图。
V9R0 使用 V8R1 已经合法采到的 4096-pop base label graph，但丢弃 Q0/QD1
endpoint 和 counter deltas。

## 3. 输入与 exact 边界

- 每个 context 一张 base graph，最多 256 个 label nodes，加 `scale` 个 task
  nodes。
- label node 保留 15 维 label-state、terminal、creation age、Q0/QD1 rank、
  parent、last-task 和 branch feasibility；task node保留静态、true-dual、
  branch/cut 信息。
- 边保留 self、parent-child、dominance-surface、label-task 和 task-interaction。
- context 保留 4096-pop 时 action 前可见的 frontier、dominance、dual、round、
  branch/cut 特征。
- 不输入 full-run wall、最终 processed labels、winner、objective、certificate、
  endpoint trajectory 或 counterfactual deltas。

来源是 V8R1 的 38 个历史诊断 context：scale30 为 19 context/15 instance，
scale50 为 19 context/16 instance。每个 context 的三个 rollout budget 共享同一
base graph，V9R0 只取 B=128 行作为确定性去重载体。标签来自已冻结的
QPF0/QPD1 matched outcome，因此本链只可用于 representation development。

## 4. 模型与公平对照

唯一研究候选为两层 edge-aware Interaction-GAT：hidden 16、2 heads、
residual、LayerNorm、ReLU、dropout 0.1。label nodes 和 task nodes分别做
mean/max/attention pooling，edge做 mean/max pooling，再拼接 context embedding。
每 seed 参数少于 20k。

独立训练：

- `gat`
- `mlp`
- `linear`
- `no_message`
- `shuffled_topology`

五种模型获得相同 node、edge、context 数值、相同 folds、instance weights 和
seeds。`no_message` 与 `shuffled_topology` 不是临时修改 GAT checkpoint。

训练使用五折 instance-grouped OOF，seeds 为 `61635/91267/170141`。每个实例
总 loss 权重为 1；normalization、class weights 和 early stopping 只使用当前
fold 的 train instances。ensemble 使用 benefit mean、gain min、adverse max。

## 5. 冻结 gate

V9R0 只有同时满足以下条件才进入 `RUNTIME_IMPLEMENTATION/READY`：

- scale50 instance-level benefit balanced accuracy `>=0.70`；
- scale50 instance-level rank accuracy `>=0.65`；
- benefit BA 不低于最佳 MLP/Linear 超过 `0.02`；
- rank 不低于 no-message 和 shuffled-topology；
- 至少一个 topology control 的 rank 下降 `>=0.02`；
- 最近 10% 数值签名图对的相反 benefit 标签比例 `<=0.35`；
- Native base graph build + Python tensorization + 三 seed GAT inference 的 warm
  p99 `<=10 ms`；
- 每个 context 的上述成本/QPF0 wall 均 `<=2%`。

成本测量用 Python tensorization 和三模型 forward，是未来手写 Native forward
的保守诊断；base graph build wall取 V8R1 Native 原始 telemetry。

任一门失败即写：

```text
FAIL / BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE
```

不得在同一链放宽门槛或改结构后重跑。

## 6. 通过后的最短实现边界

若且仅若 V9R0 通过，后续 runtime 使用单个正式 exact request：

```text
literal Q0 pop 到 4096
→ 构造一次 256-label base graph
→ portable Native GAT
→ CONTINUE_Q0 或原位 SWITCH_QD1
→ 同一 request 完成 exact pricing
```

它不运行 Q0_PREFIX/QD1_PREFIX，不重启 pricing，不返回辅助 route/certificate。
小规模、tree、非 root fallback 和任何校验失败仍 literal Q0。该 runtime 仍需
单独完成 migration hash、500-case exact differential、cold/warm cost、fresh
pilot、heldout、E2E 和 formal gates；V9R0 通过本身不是加速证据。
