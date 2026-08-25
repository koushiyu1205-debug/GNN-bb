# P0V5 QG2 V3：GAT-First Admission Guidance 重构方案

## 1. 重构结论

V2 的 fresh-process calibration 已停止，已有结果只作为历史消融，不作为 V3 的训练或部署证据。V3 不改变 P0V4+V5 Exact control，也不改变 Native 的合法扩展、dominance、bound、reduced cost、停止条件或 certificate。

本次重构解决四个已由运行证据暴露的问题：

1. V2 的 activation heads 使用泄漏开发 oracle `QO2` 的收益标签训练，但运行时动作是 Linear/MLP/GAT 自己生成的 `QG2` 顺序，监督对象不一致。
2. V2 把 right-censored outcome 完全 mask，模型不会把“Q0 达到 admission、guided arm 超时”学习为退化风险。
3. V2 的 label pair 虽已对齐 Master-ready admission，但每条祖先 label 等权，不能表达 E64/E128 作为一个多样性集合的边际贡献。
4. QG2、QD1、QB1 分属串联 gate，可能由高置信但错误的 QG2 抢先覆盖更合适的确定性 arm。

因此 V3 明确拆成两个学习问题：

```text
Admission ranker
  GAT / MLP / Linear -> node, arc, state potentials -> Native same-bucket ordering

Runtime selector
  pre-action context + per-arm offline scores
    -> Q0 / QG2 / QD1 / QB1
```

ranker 不再输出 deployment activation authority。selector 必须使用各 arm 自己的 fresh-process matched outcomes；所有 arm 被拒绝时只能回到字面意义上的 Q0。

## 2. Admission ranker

### 2.1 动作与目标

学习动作仍是：

\[
(terminal\ first,\lfloor partialRC/w\rfloor,-g(l),partialRC,creationID).
\]

只在同一 terminal class 和 RC bucket 内改变 label 顺序。优化里程碑为冻结 selector 得到完整 Master-ready admission batch 的时间：

\[
\min T_{admission}=T_{search}+T_{audit}+T_{selector}.
\]

proof-completion context 仍以 exact proof completion 为目标，不能用 first raw negative 代替 admission。

### 2.2 特征与归一化

- 保留 V2 的 pre-action node、arc、context 和 15 维 Native label-state 特征；
- node、edge、context 三组连续特征只在 train instances 上拟合 mean/std；
- presence mask、布尔字段不做中心化，仅验证取值域；
- normalization statistics、feature names、split hash 写入 checkpoint；
- runtime 必须应用 checkpoint 内同一归一化，缺失、维数漂移、NaN/Inf 均 fail closed 到 Q0；
- Native `sizeof(State)==176`，不增加 per-label embedding 或字段。

### 2.3 GAT 结构

GAT 是第一训练和第一 fresh-process 实验对象：

- node/edge/context encoder：`Linear(32)+ReLU`；
- 两层 edge-aware attention，每层 residual + LayerNorm；
- graph pooling 使用 node mean 与 node max，避免单一 mean 抹平少数关键 task；
- node、arc、15 维 state coefficient 三个 rank heads；
- 不包含 benefit/gain heads。

MLP 和 Linear 使用完全相同的输入、监督、Native 动作面和输出 heads，只作为容量与图结构消融：

- MLP：不做 message passing；
- Linear：不做非线性和 message passing；
- 训练和 fresh replay 顺序固定为 GAT、MLP、Linear。

### 2.4 Set/diversity-aware supervision

每个 admission witness 保留 route identity、selected rank、task set 和 selector bucket。pair 权重按以下规则计算：

- 每条最终 selected route 获得相同总监督质量，避免长 route 因祖先多而支配 loss；
- `selected ancestor vs omitted raw-negative ancestor` 权重最高；
- selected route 的新 task coverage、与已选集合的 Jaccard distance、selector bucket 稀缺性形成 diversity multiplier；
- background admission pairs 次之；
- dominance/proof progress 只作为低权重 background；
- 每个 context 的总 pair weight 归一为 1，避免 scale50 或 label 多的 context 仅因样本数支配训练。

rank loss 为 weighted pairwise logistic loss。报告总 pair accuracy 之外，还必须报告 admission-hard、admission-background、dominance/proof 各类 weighted accuracy。

## 3. Runtime selector

### 3.1 训练数据

ranker checkpoint 冻结后，先强制执行 GAT/Q0 fresh-process matched replay。QG2 的 activation 只能由其自身实际 outcome 监督；不得用 leaked oracle 或 QD1/QB1 标签替代。如果固定 force-on screen 显示 QG2 全面退化，则把 QG2 作为显式但强制 veto 的失败 arm 保留，仍可用已经采集且 binding 一致的 QD1/QB1 matched outcomes训练 context-level GAT selector。此时研究主张必须改写为“GAT 选择 exact-safe queue policy”，不能再声称“GAT label ordering 获益”。

每个 arm 输出三项：

\[
p_a=P(\Delta T_a>0),\qquad
\mu_a=E[\Delta T_a/T_{Q0}\mid\Delta T_a>0],\qquad
r_a=P(harm\ or\ adverse\ censor).
\]

- Q0 达到同一里程碑而 arm 未达到：明确作为 adverse target，不再 mask；
- 两边均未达到且无法比较：survival/censor mask；
- unsafe、OOM、certificate blocker：adverse target；
- gain 使用相对比例，不用原始秒数，避免 scale50 数值支配。

### 3.2 选择规则

对每个非 Q0 arm：

\[
s_a=p_a\mu_a-\lambda r_a.
\]

只有 benefit、expected gain、risk、OOD 和 hash gate 全部通过才进入 eligible set；在 eligible arms 中选择安全分数最高者。空集合、异常、低置信、OOD、binding drift 均选择 Q0。在线只执行一个 arm，不并行执行多个 pricing。

阈值按 scale30/scale50 和 admission/proof milestone 分层校准，但冻结后不得按 instance 手工调节。取消“必须达到 5% 才允许进行正式实验”的硬约束：只要 calibration 和 heldout 都为正净收益且 exact-safe，就允许进入 development E2E；论文中的 5% 仍作为主张强优化效果的评价线，而不是阻止实验的先验门槛。

## 4. 训练、诊断和测试顺序

1. 冻结 V3 schema、instance split 和 train-only normalization；
2. 训练 GAT，逐 epoch 写 `training_curve.jsonl`；
3. 输出 train/calibration/heldout 的总 pair accuracy、weighted accuracy 和 per-kind accuracy；
4. 做 GAT feature-group permutation、edge shuffle/no-message 消融；
5. 用冻结 GAT 做 force-on fresh Q0/GAT calibration；
6. 若实际 QG2 存在可测正收益且无 correctness redline，把它纳入统一四臂 selector；若固定 screen 全面退化，则永久 hard-veto QG2，只训练 GAT 对 QD1/QB1 的 context-level 选择；
7. 再训练 MLP、Linear，并做相同 snapshot 对照；
8. selector fresh validation；
9. scale30/50 development E2E；
10. 通过后运行 scale5/10/20/30/50 full20。

force-on calibration 采用一次冻结的两级执行，不据中间结果更换模型或特征：先按 state hash 与 milestone 固定选择 scale30/50 各 2 个 context、各 1 次 blocked pair，验证 binding、安全性和是否至少存在可测 opportunity；安全审计为零且任一规模出现净收益后，扩展到完整 calibration split、每个 context 3 次。预筛只决定是否支付完整实验成本，不提供部署阈值或正式性能结论。

每个 ranker 每轮落盘：

```text
model, epoch, total_loss, rank_loss,
benefit_loss, positive_gain_loss, adverse_loss, epoch_wall_sec
```

ranker 的后三项固定为 0；它们保留在 schema 中是为了与后续 selector training curve 统一。selector 训练时分别填写真实值。

## 5. 必须通过的测试

- normalization 只拟合 train instances，checkpoint/runtime 数值一致；
- route-balanced weighting 不受祖先数量和重复 pair 数支配；
- omitted raw negative 不能被标为 admission positive；
- GAT/MLP/Linear 只比较同 terminal class、同 RC bucket labels；
- zero potential 与旧 Q0 逐项一致；
- GAT edge-shuffle 消融确实改变 message-passing 输入，MLP/Linear 不受影响；
- Q0-reached/arm-timeout 被标为 adverse，而不是 ordinary censor；
- selector action universe 恰为 Q0/QG2/QD1/QB1，拒绝全集时返回 Q0；
- checkpoint/config/engine/state hash drift、OOD、NaN/Inf 均回 Q0；
- 500 组小规模 differential test 的合法 universe、global minimum、RC reconstruction 和 certificate 与 Q0 一致；
- `sizeof(State)==176`，无额外 per-label 向量。

## 6. 实验判定

V3 训练准确率只说明是否学会 trace preference，不代表 wall-time 优化。最终以 fresh-process、同 snapshot、同预算、blocked replicates 的 admission/proof milestone wall 为准。

- scale5/10/20 不调用模型；
- scale30/50 exact 数不得低于 control；
- common-exact paired GM 小于 1 才能称为净优化；
- 达到 5% 才能称为达到预期优化幅度；
- GAT 若不优于 MLP/Linear，只能报告 learned ordering 有效，不能声称图结构带来优势；
- QG2 force-on 若退化而 context-level GAT selector 获益，只能把收益归因于 learned policy selection，不能归因于 label-state potential；
- 所有 correctness/certificate redline 必须为零。
