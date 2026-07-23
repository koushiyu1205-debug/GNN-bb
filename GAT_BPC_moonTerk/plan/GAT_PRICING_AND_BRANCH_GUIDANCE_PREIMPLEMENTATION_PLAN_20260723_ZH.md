# GAT 定价引导与分支候选排序：正式实施前计划

日期：2026-07-23

基准：`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`

## 1. 已锁定的总体决策

GAT 只承担两个正式目标：

1. 引导定价，缓解负列发现和 true-dual exact pricing proof tail；
2. 对合法 Ryan–Foster 分支候选进行排序。

GAT 不承担以下职责：

- 不分离、选择、加入或删除 cuts；
- 不触发 node-level cut separation；
- 不永久删除可行 arc、label、task set 或 column；
- 不提供 lower bound；
- 不剪枝、fathom 或证明 infeasible；
- 不签发 `CERTIFIED_NO_NEGATIVE`、node certificate 或 tree certificate。

cuts 固定使用新基准的 root-only P0 SRI-3。node-level cuts 默认关闭，整个首轮 GAT
开发和 promotion 均不得改变这一点。

## 2. 精确性边界

项目采用：

> Learning-guided discovery, exact-certified closure.

GAT 输出只能作为 immutable typed hints。所有 hints 必须绑定：

- instance/model/config hash；
- RMP iteration；
- true-dual binding hash；
- branch context hash；
- active-cut context hash；
- objective mode；
- guidance graph schema；
- GAT checkpoint、feature schema 和 normalization version。

RMP 重求解、dual 改变、分支改变、active-cut context 改变、Phase-I/II 切换或 checkpoint
不匹配时，旧 hints 必须失效。

最终 official no-negative 结论仍要求：

```text
search_exhaustive = true
frontier_empty = true
labels_dropped = false
certificate_blockers = empty
rc_mismatch_count = 0
```

任何被 GAT 延后的 true-negative column 都进入 proof-debt accounting；证书前必须全部释放并
使用当前 true dual 复查。无法释放时返回 `INCOMPLETE`，不得剪枝。

## 3. Stage G0：基准与测量协议固定

### G0.1 基准

后续 GAT 实验的主要 control 固定为：

`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`

历史 no-cut control 继续保留：

`FROZEN_NATIVE_NO_CUT_BASELINE_V1`

用途区分：

- 新 P0 基准：GAT on/off 的直接 paired control；
- 旧 no-cut 基准：纵向历史对照、回滚和算法演化分析；
- 旧 formal P0 promotion：证明 projection/packed-state 之前的性能分布，不能和新数据拼接。

### G0.2 首轮不再等待完整 10/3 promotion

新基准已有 80 个实例、160 个 exact slots 的 strict cold-start 单重复证据，足以开始 shadow
telemetry 和训练数据建设。正式 5/10 十次、20/30 三次重复保留到唯一 GAT 候选冻结后执行，
避免在模型尚未介入前重复消耗大规模算力。

### G0.3 固定消融矩阵

所有 GAT 实验至少包含：

| 模式 | 定价引导 | 分支排序 | cuts |
|---|---:|---:|---|
| B0 | 关闭 | 关闭 | P0 root-only |
| B1 | 开启 | 关闭 | P0 root-only |
| B2 | 关闭 | 开启 | P0 root-only |
| B3 | 开启 | 开启 | P0 root-only |

B0 必须按同一冻结代码重新运行，不能直接拿历史耗时充当 paired control。

## 4. Stage G1：先补 telemetry 和标签契约

在训练模型前，先让当前 P0 求解器稳定输出可复用的事件级数据。

### G1.1 Pricing 事件

每次 RMP pricing call 记录：

- 当前 cover/fleet/cut/branch true dual 摘要；
- active nonzero cut dual 数量、绝对值和 support 摘要；
- branch depth、same/different pair 数量；
- RMP objective、fractional support 和 degeneracy 指标；
- task/task-set/label 候选的产生顺序；
- candidate true reduced cost；
- 是否物理重复、是否已在 column pool、是否可加入；
- 找到首条 addable negative column 的时间；
- harvest 中每条列的 RC、rank 和实际 RMP 采用情况；
- generated/expanded/dominated labels；
- frontier peak、Native RSS 和 pricing wall/CPU；
- exhaustive proof tail 的开始时间、持续时间和结果。

### G1.2 Pricing 标签

不能只用 `true_rc < 0` 作为正标签。正式标签至少分为：

- `true_negative`：真实负 RC；
- `addable_negative`：负 RC 且非重复、可进入 RMP；
- `useful_negative`：加入后实际推动 RMP objective/support；
- `hidden_negative_miss`：基线排序较晚才发现的负列；
- `delayed_negative_debt`：若按 guidance 排序会被延后的负列；
- `proof_tail_risk`：本轮最终 exact search 的时间/labels/frontier 风险；
- `harvest_selected`：候选是否应进入有限 harvest batch。

核心目标是更早找到“可加入并有用”的负列，而不是反复命中重复列。

### G1.3 Branch 事件与标签

每个合法 Ryan–Foster pair 记录：

- pair fractionality 和当前 λ support；
- 两任务的拓扑、资源、时间窗、风险和共现特征；
- strong/probe 后左右 child 的 LP gain；
- 左右 child 的第一次负列时间；
- child pricing CPU、labels、frontier 和 Phase-I 状态；
- child closure/incomplete 状态；
- 两侧 pricing-pressure balance；
- 后续 subtree nodes 和总 wall-clock。

branch target 优先学习总下游代价：

```text
left_child_total_work + right_child_total_work + imbalance_penalty
```

即时 LP gain 仅作为特征和辅助标签，不能独占训练目标。

## 5. Stage G2：数据集构造与防泄漏

### G2.1 数据来源

按优先级采集：

1. 当前 full80 P0 原始运行；
2. 20/30 的慢例和退化例；
3. 相同 RMP/branch context 下的候选 hard pairs；
4. 5/10 快例，用于训练 inference overhead 和 do-no-harm；
5. 后续专门的 shadow capture，不改变 solver。

30 规模重点样本包括当前明显退化或长尾的 instance012、018、019，以及改善显著的
instance002、005、008、009，形成正负对照。

### G2.2 划分规则

- 以 instance/seed family 分组切分，禁止同一实例的相邻 RMP iteration 跨 train/test；
- 20/30 必须分别有完全未见实例 holdout；
- 5/10 保留独立 do-no-harm holdout；
- normalization 只用 training split 拟合；
- checkpoint 必须绑定 split manifest 和 source baseline ID；
- 不允许从最终 objective、未来 child closure 等结果字段泄漏到在线特征。

### G2.3 先验证可学习信号

在上 GAT 前先训练轻量 ranking baseline，例如线性模型或小型 MLP。若其在严格 holdout 上
无法超过 deterministic ordering，则先修标签和特征，不直接用更复杂 GAT 掩盖数据问题。

## 6. Stage G3：模型结构

采用共享图编码器、独立任务头：

```text
shared graph encoder
    ├── pricing_priority_head
    ├── harvest_priority_head
    ├── proof_tail_risk_head
    └── branch_priority_head
```

可选辅助头：

- candidate addability；
- delayed-negative risk；
- Phase-II pricing pressure；
- OOD/confidence。

不同 head 使用独立 loss 和校准，不把定价分数与分支分数压成一个标量。

图特征至少覆盖：

- task、depot/recharge、vehicle/resource 节点；
- directed travel/resource/time-risk 边；
- 当前 true cover dual；
- active nonzero cut dual 的任务 support 摘要；
- branch same/different context；
- RMP fractional λ support；
- pricing 历史和 label-growth telemetry。

## 7. Stage G4：Shadow-only

第一阶段模型只输出排序，不改变 solver：

- 记录基线顺序与 GAT 顺序；
- 计算 top-k useful-negative recall、NDCG、MRR；
- 估计 time-to-first-addable-negative；
- 统计会被延后的 true negative；
- 计算 branch candidate regret；
- 检查 OOD、置信度和推理耗时。

Shadow gate：

- candidate set preservation 100%；
- permanent drop 0；
- stale-context hint acceptance 0；
- checkpoint/schema/hash mismatch fail closed；
- proof-debt accounting 完整；
- 5/10 inference p50 不超过其基准总时间的 2%；
- 20/30 inference p50 不超过单次 pricing wall 的 1%。

## 8. Stage G5：Pricing ordering opt-in

只允许改变：

- task/task-set priority；
- worker/batch dispatch order；
- candidate reconstruction order；
- harvest return order；
- exact label queue 的 tie/order policy，但不能改变 dominance、feasibility 或候选集合。

首轮不允许：

- learned label pruning；
- learned completion bound；
- learned arc deletion；
- GAT no-negative early exit；
- 无限期 delay；
- 用 stabilized/learned dual 签发证书。

OOD、高不确定性、推理超时、NaN、schema/hash mismatch 时立即回退 B0。

Pricing screening gate：

- 20/30 time-to-first-addable-negative p50 至少下降 15%；
- exact proof-tail p50 不上升；
- hidden-negative miss 和 permanent drop 均为 0；
- 5/10 end-to-end mean/p50 不高于 B0 的 105%；
- 全部 exact objective、RC audit 和 certificate binding 与 B0 一致。

## 9. Stage G6：Ryan–Foster 分支排序 opt-in

GAT 只能重排由精确 solver 枚举出的合法 pair。若 GAT 缺失某 pair，该 pair仍保留在候选集；
若 GAT 失效，使用当前 deterministic branch score。

训练和评价同时关注：

- 两 child 的总 pricing CPU；
- max-child tail；
- child workload balance；
- subtree node count；
- subtree closure wall-clock；
- objective/bound progress。

不能只按即时 strong-branch LP gain 晋级。

Branch screening gate：

- 合法候选集合完全不变；
- fallback 可复现；
- 20/30 child pricing CPU 或 subtree wall p50 至少改善 10%；
- node count、mean wall 和长尾实例不得出现系统性退化；
- exact/certificate 门禁全部通过。

## 10. Stage G7：联合消融与正式 promotion

完成 B1、B2 后才运行 B3。若其中一个 head 没有独立收益，不为形式完整性强制放入最终模型。

筛选完成后冻结唯一 checkpoint、feature schema、normalization、OOD policy 和 baseline binding。

正式 paired promotion：

- 5、10：每实例每模式 10 次；
- 20、30：每实例每模式 3 次；
- fresh Python/Native runtime；
- B0/B3 使用 AB/BA；
- strict cold-start；
- no resume、no shared column pool、no cross-slot graph cache。

最终门槛：

- 20、30：
  - GAT p50 ≤ 0.90 × 新 P0 基准 control；
  - GAT mean ≤ control；
  - paired geometric mean ≤ 0.90；
  - paired bootstrap 95% CI 上界 < 1.00；
- 5、10：
  - mean/p50 ≤ 1.05 × control；
  - paired geometric mean ≤ 1.05；
  - CI 上界 < 1.10；
- 所有正式重复：
  - exact；
  - objective 一致；
  - zero redline；
  - zero RC mismatch；
  - zero certificate leak；
  - zero permanent negative drop。

未通过时，新 P0 基准继续作为默认实验 control，GAT 保持 shadow/opt-in。

## 11. 正式编码前的立即执行顺序

1. 校验本次 V2 freeze 的 manifest、`.so`、config 和性能快照；
2. 固定 guidance context-binding 与 telemetry schema；
3. 写 schema/property/fail-closed tests；
4. 从现有 full80 raw artifacts 构建第一版只读 dataset；
5. 对缺失字段运行少量 P0 shadow recapture；
6. 建立 deterministic/MLP ranking baseline；
7. 确认可学习信号和防泄漏审计；
8. 再实现共享 GAT encoder 和 pricing heads；
9. pricing shadow 通过后实现 ordering opt-in；
10. 最后接 branch ranking，完成 B0/B1/B2/B3 消融。

首个代码变更应当是 telemetry/schema/binding，而不是直接写 GAT 网络。这样训练标签、在线
接口和 exactness boundary 会先稳定下来，避免后续模型被错误标签或不可复现上下文反复推倒。
