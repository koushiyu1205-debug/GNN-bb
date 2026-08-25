# P0V5 QG2 V5 Trace-First GAT 优化方案

更新时间：2026-08-07

## 1. 本轮结论

旧 bounded Oracle、Random、leaked-QO2 bucket replay 和自动 handoff 已停止，
已落盘结果只读保留。正式训练尚未发生，因此不存在需要继续等待的旧模型。

本轮把学习问题明确拆成两个层次：

1. **Label GAT**：在同一 terminal class、同一 reduced-cost bucket 内重排
   exact SPPRC labels，形成 QG2 ordering；它只输出 node、arc 和15维
   label-state potential，不决定是否启用。
2. **Context GAT**：在完整 pre-action context 上预测 `QG2/QD1/QB1` 各 arm 的
   benefit probability、conditional positive gain 和 adverse probability；任何 arm
   未通过 threshold、risk、OOD 或 binding gate 时回 literal `Q0`。

MLP 与 Linear 不再抢在 GAT 前训练。它们仅在 GAT fresh-process 有严格净收益后，
使用相同数据、相同 split、相同动作面和相同 loss 训练，作为论文对照。

## 2. 为什么停止旧流程

旧流程的关键路径是：

```text
Q0 trace
  + Random x 3
  + QD1/QB1 initial
  + leaked-QO2 x 3 buckets
  + selected QO2/Q0 replicates
  -> performance Oracle gate
  -> Label GAT
```

这存在监督与门槛错位。Label GAT 实际只消费 Q0 完整 future trace 中的
action-reachable pairwise preferences，并不消费 Random 或 leaked-QO2 的性能结果。
训练后 QG2 是否有价值，必须由 fresh-process `Q0 vs QG2` 判断，而不能由另一个
leaked ranker 替它决定。

因此新关键路径为：

```text
Q0 future trace 数据充分性
  -> Label GAT smoke
  -> Label GAT formal training
  -> Q0/QG2 force-on
  -> 若 QG2 有跨实例信号，纳入动作面
  -> Q0/QD1/QB1 replicated matched outcomes
  -> Context GAT
  -> calibration threshold
  -> heldout fresh-process
  -> GAT 通过后再训练 MLP/Linear
```

Random 与 leaked-QO2 只保留为可选机制诊断，不再拥有训练阻断权，也不进入模型
输入、loss、threshold 或正式验收。

## 3. 模型结构

### 3.1 Label GAT

- 输入：静态 node/edge graph、true-dual 动态 node features、pre-action context；
- 主干：2层 edge-aware residual GAT，hidden 32，2 heads；
- 输出：每个 node potential、每条合法 arc potential、15维 state coefficient；
- Native priority：

  ```text
  terminal class
  -> floor(partialRC / frozen_bucket_width)
  -> -label_state_GAT_score
  -> partialRC
  -> creationID
  ```

- 约束：不改 label 生成、dominance、bound、RC、停止条件和 certificate；
- 监督：
  - `ADMISSION_BATCH_READY` 使用最终 master-admitted route ancestor；
  - `EXACT_PROOF_COMPLETION` 使用同 bucket dominance winner 和 terminal-progress pair；
  - 两类 milestone 分层报告，不把 proof pair 伪装成 admission positive。

### 3.2 Context GAT

- 输入与 Label GAT 使用同一 pre-action feature contract，但职责不同；
- 主干：2层 edge-aware residual GAT，hidden 32，2 heads；
- arms：`QG2/QD1/QB1`，`Q0` 是模型外强制 fallback；
- 每个 arm 三个 head：
  - `P(benefit)`；
  - `E[positive gain | benefit]`；
  - `P(adverse)`；
- risk-adjusted score：

  ```text
  P(benefit) * positive_gain - lambda * P(adverse)
  ```

- 同一 request 最多启用一个 ordering arm；下一 request 恢复正常 selector 决策；
- QG2 只有在 train force-on 跨规模、跨实例支持通过后才进入动作面。

### 3.3 MLP 与 Linear 对照

两层职责分别做对照，不能混成一个 accuracy：

- Label MLP/Linear：与 Label GAT 相同 pair、node/edge/context 输入和输出 heads；
- Context MLP/Linear：与 Context GAT 相同 matched arm outcome、三 heads 和 threshold；
- MLP 看到相同 mean/max graph information，但没有 message passing；
- Linear 使用相同归一化后的 mean/max graph summaries，无非线性 message passing；
- 参数量、pair accuracy、balanced accuracy、Brier、arm-vs-Q0、arm-vs-arm accuracy
  和 fresh wall 一并报告。

GAT 若不比最佳 MLP/Linear 至少好2%，只能宣称 learned ordering/selector 有效，
不能宣称 graph structure 产生额外优势；这不否定 GAT 候选本身的净加速。

## 4. 数据与训练

### 4.1 Trace supervision corpus

新 collector 只运行 literal Q0 future trace：

- scale30：复用旧 frozen pre-action order 的前33个完整 trace，覆盖10个实例；
- scale50：按同一 pre-action order 新采前20个 trace，目标至少10个实例；
- scale30/50 wall 分别为300/600秒，Native cap 10.867 GiB；
- train/calibration/heldout 继续使用 outcome 前冻结的 instance split；
- 每规模每 partition 至少2个 context、2个 instance；
- trace 必须达到 admission/proof milestone、无 label drop、无 guidance drop、
  engine/config/action-policy/state hash 完整一致。

该 gate 只证明“可以拟合 Label GAT”，没有性能或部署权威。它明确记录：

- `performance_oracle=false`；
- `random_or_leaked_qo2_outcomes_used=false`；
- 下一权威是 fresh `Q0 vs QG2`。

### 4.2 Label GAT 训练

- 先运行1 epoch smoke，验证 sampler、pair 构造、normalization、curve 和 checkpoint；
- 再冻结 corpus/view/split/trainer/source SHA；
- 正式最多40 epochs，patience 8，Adam lr 0.002；
- 每 epoch optimizer steps 按 instance 等权，同实例 context 确定性轮换；
- normalization 只拟合 train instances，并按 instance 等权；
- early stopping 使用 calibration instance-average pair accuracy；
- heldout 不参与 early stopping；
- 每轮原子追加 `training_curve.jsonl`：
  `model, epoch, total_loss, rank_loss, benefit_loss,
  positive_gain_loss, adverse_loss, epoch_wall_sec`；
- 最终报告 train/calibration/heldout pair accuracy、milestone 分层 accuracy、参数量、
  最大单实例 context 占比和 best epoch。

### 4.3 QG2 force-on 与 Context GAT

- train 首屏每规模5个 context，严格 instance round-robin；
- 首屏有正信号时只允许一次冻结 universe 的全 train 扩展；
- QG2 进入动作面至少要求：5个可判定 outcome、5个实例、两个规模各2个实例，
  至少2个正收益 outcome 来自2个实例；
- QD1/QB1 对同一 frozen context 各做3次 blocked replicate；
- Context GAT 最多200 epochs，patience 25；
- loss：benefit BCE + 0.5 positive-gain smooth-L1 + adverse BCE
  + 0.25 matched utility rank loss；
- class weights 只从 train outcomes 估计并裁剪到 `[0.25,4]`；
- right-censored outcome 不进入 magnitude/rank target，但进入合规 censor mask；
- threshold 只在 calibration instances 上选择；heldout 只使用一次。

## 5. 用户提出的三个判断

### 5.1 三种模型准确率接近

判断合理，但不能只凭 raw accuracy 下结论。可能原因包括：

- 某个 context feature 主导；
- 正负标签不平衡，模型都学到多数类；
- 动作面本身容易；
- GAT topology 对当前 label/action 没有额外信息；
- 数据量不足，复杂模型没有显现优势。

因此必须同时做 single-feature/group ablation、no-message、shuffle-topology、prevalence、
balanced accuracy、Brier 和真实 fresh wall。feature dominance 只是机制诊断，不能替代
fresh-process 性能证据。

### 5.2 动作面应含 Q0/QD1/QB1/QG2

采纳。准确说，模型预测非Q0 arms，Q0 始终放在模型外作为 fallback。QG2 先经自身
force-on 证明可测；若失败，Context GAT 的动作面自动收缩为 QD1/QB1，仍回 Q0。

### 5.3 阈值很重要

采纳。低阈值会放大 harmful activation，高阈值会增加 inference 后回 Q0 的比例。
阈值选择必须把推理开销计入 net wall，并按下列顺序选择：

1. correctness/safety 零红线；
2. harmful rate Wilson 上界；
3. beneficial precision Wilson 下界；
4. instance-balanced net GM；
5. activation coverage；
6. inference p99。

若没有可行阈值，显式冻结所有 arms veto，执行 Q0；不使用非法概率或无穷阈值模拟。

## 6. 额外风险

- **两层误差叠加**：Label GAT 有潜力不等于 Context GAT 能识别何时启用；两层必须
  分别 fresh test。
- **只优化 pair accuracy**：pair accuracy 提升不保证 wall 下降；force-on 是第一性能
  权威。
- **milestone 混合**：admission 和 proof 的有效 ordering 可能相反；报告与 threshold
  必须分层检查。
- **censor bias**：重尾 context 容易 timeout，不能将双方 censor 当负样本。
- **inference tax**：即使回 Q0，tensorization/inference 仍耗时；必须计入 net wall。
- **OOD 假安全**：不能扩大 envelope 来提高激活率；OOD 必须回 Q0。
- **小样本阈值不稳**：heldout 不得反复用于调 threshold；最终由 development E2E 和
  formal full20 裁决。

## 7. 测试顺序

1. trace selection freeze、hash、Q0-only、label/drop/milestone 单元测试；
2. 1 epoch Label GAT smoke；
3. Q0/QG2 legal universe、global minimum、certificate differential；
4. 500组可穷举随机 differential，`sizeof(State)==176`；
5. Label GAT train/calibration/heldout diagnostics；
6. QG2 force-on matched wall；
7. Context GAT threshold calibration 与 heldout fresh；
8. GAT 通过后才运行 MLP/Linear；
9. development E2E；
10. formal scale5/10/20/30/50 full20。

## 8. 最终实验矩阵

算法消融：

1. `P0V4 + V5 Exact (Q0)`；
2. Exact + `QD1` fixed；
3. Exact + `QB1` fixed；
4. Exact + Label GAT force-on QG2；
5. Exact + Context GAT selective arms；
6. 若 GAT fresh 为正：对应 MLP；
7. 若 GAT fresh 为正：对应 Linear。

正式性能门槛：

- scale5/10/20：20/20 exact，模型调用0，ratio <= 1.01；
- scale30：20/20 exact，common-exact GM < 1.0；
- scale50：exact 数不低于 Exact control，common-exact GM < 1.0；
- inference p99 <= 10 ms；
- objective、true RC、global minimum、certificate、legal universe 全一致；
- production、P0V4/P0V5 Exact control 和正式基准不覆盖。

不再用“必须先达到5%”阻止 development E2E；只要 heldout fresh 严格净收益为正、
exact 不减少且零红线，就进入正式实例验证。5%继续作为论文意义上的强收益参考。

## 9. 当前执行状态

- Q0 trace corpus已冻结45个完整context：scale30为33、scale50为12；
- Label `QG2TinyGAT`已完成27 epochs训练，最佳epoch 19，checkpoint保持
  development-only；
- calibration/heldout instance-balanced pair accuracy分别约`0.8746/0.8791`，但
  pair accuracy没有转化为求解加速；
- 三个完整force-on context的QG2/Q0 paired GM为`1.2969`，正收益`0/3`；
- 重尾context中Q0两次在`278.956/290.750 s`完成，TinyGAT三次均在约`301 s`
  超时，构成adverse censor；
- 用户据此决定停止当前TinyGAT方向。剩余force-on、scale50、窄bucket、QD1/QB1
  新采集、Context GAT、MLP/Linear和E2E/full20均未启动；
- 该停止符合本方案的性能权威边界：fresh-process wall否决pair accuracy，失败模型
  不进入后续动作面或正式基准；
- `TINYGAT_TERMINAL_DECISION.json`已经冻结负结果，production、P0V4/P0V5 Exact
  control均未改变。
