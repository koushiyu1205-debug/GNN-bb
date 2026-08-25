# P0V5 Base-Label Frontier V9R0 Closeout

## 结论

V9R0 已形成合法 diagnostic negative：

```text
FAIL / BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE
```

对应机器可读证据位于：

```text
runs/p0v5_base_label_frontier_observability_v9r0_20260818/
```

本链没有产生新的 arm outcome，没有读取 heldout/E2E/formal outcome，也没有
实现或授权 runtime candidate。

## 相对 V7R3 的进步

256-label base graph 确实提高了 scale50 的部分可辨识性：

| 指标 | V7R3 64-cell | V9R0 256-label | 变化 |
|---|---:|---:|---:|
| GAT instance benefit BA | 0.60909 | 0.66364 | +0.05455 |
| GAT instance rank accuracy | 0.52500 | 0.68750 | +0.16250 |
| 最近10%签名对相反标签比例 | 0.64706 | 0.41176 | -0.23530 |

此外：

- GAT rank 不低于 no-message/shuffled-topology；
- topology rank drop 为 `0.0625`，超过冻结的 `0.02`；
- Native base graph build + Python tensorization + 三 seed forward 的 warm p99
  为 `9.796 ms`；
- 最坏单 context 成本/QPF0 wall 为 `1.202%`；
- 因而 rank、topology 和两项成本门都通过。

但安全激活需要的两个门没有通过：

- scale50 instance benefit BA 为 `0.66364 < 0.70`；
- 相似图相反 benefit 标签比例为 `0.41176 > 0.35`。

特别要注意：shuffled-topology 的 scale50 benefit BA 为 `0.71818`，高于 full
GAT 的 `0.66364`，尽管其 rank accuracy 只有 `0.625`。因此 message passing
对连续排序有贡献，但对安全 benefit 分类的优势尚不稳定，不能据此冻结 GAT。

## 根因审计

### 1. 不是三重复 wall 噪声主导

读取 V7R2 的冻结 matched blocks 后：

- scale50 的 19/19 contexts 均有三个可比 block；
- 只有 1 个 context 的三次 ratio 跨越 `0.98` benefit 阈值；
- 只有 2 个跨越 `1.0`；
- 没有 context 跨越 `1.05` adverse 阈值；
- context 内 `max(ratio)/min(ratio)` 的中位数为 `1.01491`。

因此标签边界虽有少量噪声，但不足以解释主要冲突。

### 2. 256-label sample 没有覆盖完整 frontier

scale50 的 19/19 contexts 全部达到 256-label cap：

- 完整 frontier size 中位数约 `1,242`，最大约 `6,437`；
- benefit contexts 的 sampled-label 覆盖率中位数约 `14.4%`；
- adverse contexts 中位数约 `18.9%`；
- 最低覆盖率约 `4%`。

QD1 的最终收益取决于后续哪些深 label 被扩展、哪些新 label 被 dominance
删除，以及负列/证明里程碑何时到达。当前 sample 保留 terminal、Q0 top、QD1
top、deepest、cell representatives 和 bottom-k，但没有保留各类 label 在完整
frontier 中的质量与 parent/surface mass。模型因而能学到粗略排序，却无法稳定
推断未观测多数 label 的后续竞争。

### 3. 单一时点没有真实 counterfactual dynamics

4096-pop base graph 只描述“现在有什么”，不描述切到 QD1 后：

- base labels 的 survival；
- 新 label 产生速度；
- frontier churn；
- dominance checks/wall 的增长率；
- Q0/QD1 排名差异是否转化为里程碑 wall 收益。

V8R1 的双 prefix 能提供这些量，但其 B=128 paired prefix warm p99 约 119 ms，
且 5 个 scale30 context 超过 2% 成本门，最坏约 11.82%，因此不能作为候选
路径。

### 4. 样本量放大了不稳定性，但不是唯一原因

scale50 只有 16 个实例，其中 instance-level benefit 为 5、non-benefit 为11。
一个实例的判断变化就会明显改变 BA。然而重复 outcome 稳定、近邻冲突仍高、
shuffled topology 分类反而更高，说明简单扩大 epoch 或换 seed不能解决问题；
需要改变可观测状态。

## 下一步边界

不得继续在 V9R0 上调 gate、换 seed、改 pooling 或重跑。推荐顺序为：

1. **低成本 multi-resolution diagnostic**：把 V7 的完整 64-cell mass graph 与
   V9R0 的 256-label sample graph联合编码。前者补全全 frontier 分布，后者保留
   label/parent/task 局部结构；不增加 label pop，也不运行辅助 prefix。仍先用
   当前 diagnostic corpus 做 grouped-OOF，只用于判断 representation。
2. 若 multi-resolution 仍不能使 fresh-development BA/rank通过，停止“单时点
   selector”路线，转向**同一正式请求内的多时点观测**：在 4096/8192/16384
   只记录 telemetry，不重复 label generation；先测不同 late-switch boundary 的
   force-on oracle，再决定是否训练 temporal GAT。
3. scale30 继续视为 QD1 高收益规模；scale50 必须保持高置信选择性激活。
   现有 fresh 证据不支持复活 QB1 或 QGR1。

任何下一链仍需 fresh pilot、独立 calibration/heldout、完整 BPC 和 formal
验证。当前结果只能说明 representation 比 V7R3 有改善，不能声明求解加速。
