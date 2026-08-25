# P0V4+V5 Temporal-GAT：新增 5 个问题的正式确认与下一步授权

> 适用对象：Codex / 当前实验执行者  
> 当前实验：`p0v5_temporal_gat_production_v1_round5_20260824`  
> 决策性质：pre-outcome 设计确认与 eligibility 恢复授权  
> 论文事项：不在本文件讨论范围内，Codex 暂不处理论文重写、结构调整或叙事设计

---

## 一、事实边界与执行前提

本回复以当前冻结方案和已有审阅记录为依据。现阶段应继续保持以下事实边界：

- production default 仍为 `no_cut`；
- Round 5 GAT 尚未训练、未校准、未进入 development，也未获得部署权限；
- 当前阶段仍属于 `CONTEXT_ELIGIBILITY`；
- 尚未产生 Round 5 的 Q0、`CONTINUE_QD1`、`REVERT_Q0` 三臂 outcome；
- 在 eligibility 完成、context freeze 和 schedule freeze 之前，不得启动三臂实验；
- GAT 仍是本研究必须保留并重点验证的核心创新，MLP、Linear、no-message 和 shuffled-topology 仅作为必要 controls，不能替代最终 GAT 科学结论。

原审阅稿在 2026-08-25 15:36:23 CST 的快照中记录为 `30/274` 个 eligibility artifacts 已完成，且当时仍存在活动 writer。现在报告“没有 eligibility writer、剩余 243 个”，说明运行状态已经变化。因此恢复前必须重新进行文件系统计数和进程检查，不能直接把 `243` 写死为待执行任务数。

---

## 二、五个问题的结论摘要

| 问题 | 正式确认 |
|---|---|
| 1 | **同意。** scale30 deterministic policy 与 scale50 GAT 必须分别建立 harm guarantee，不得合并统计。 |
| 2 | **授权。** Codex 可在任何 topology outcome 产生前提出正式默认合同；合同必须包含 effect size、CI、shuffle seed 数和多重比较规则，但在我确认前不得冻结或据此启动 topology promotion。 |
| 3 | **需要预设。** Temporal-GAT topology 路线设置最多 3 个正式 outcome-bearing rounds；连续失败触发强制复盘和停止条件，禁止无限调参。 |
| 4 | **优先重新审定 promotion gate。** 若 addressable-wall 证明 5% 理论不可达，应先在首个 outcome 前重新审定新 Policy Round 的 gate；只有存在明确且可审计的相邻 exact-safe wall 时，才另开 scope-expansion round。 |
| 5 | **授权立即恢复。** 在确认没有现存 writer、冻结绑定无漂移并完成幂等 preflight 后，立即按原冻结命令恢复所有缺失 eligibility，单 writer 串行运行并监控至 `274/274`；完成后不得自动进入 context freeze 或三臂。 |

---

# 三、逐项详细回复

## 问题 1：是否分别对 scale30 deterministic policy 和 scale50 GAT 给出 harm guarantee？

### 正式确认：同意，而且必须分开

scale30 与 scale50 的动作机制、适用范围和风险来源不同，不能把两个尺度的 harm 样本合并后给出一个总体安全声明。

- scale30 的候选是固定的 deterministic late-switch QD1 policy，风险主要来自固定切换本身、迁移成本和实例间长尾；
- scale50 的候选是 trial 后由 GAT 在 `CONTINUE_QD1` 与 `REVERT_Q0` 之间作选择，风险还包括选择错误、OOD、ensemble disagreement、activation coverage 和条件性 harmful tail；
- 将两个尺度合并会让 scale30 的稳定样本稀释 scale50 的选择风险，也会让 scale50 的困难样本错误否定 scale30 的确定性策略。

因此应冻结两个独立 safety contracts。

### 1.1 scale30 deterministic policy 的 harm contract

#### 比较对象

```text
FIXED_QD1_SCALE30
vs.
literal Q0
```

#### 统计单位

以**独立 instance**为统计单位，不以同一 instance 内的多个 pricing requests 或 contexts 作为独立 Bernoulli 样本。

#### 硬性 redlines

以下任何一项发生一次，均视为该策略未通过 safety gate：

- correctness mismatch；
- route true-RC reconstruction failure；
- certificate semantics mismatch；
- label drop；
- 相对于 Q0 新增的 timeout 或 memory censor；
- migration conservation、creation-ID、frontier hash 或 binding failure；
- 非法进入未授权 lifecycle 或 scale。

#### 性能 harm 定义

建议将 instance-level collapsed E2E ratio 定义为：

\[
R_i^{30}=\frac{T_i(\text{FIXED\_QD1})}{T_i(\text{Q0})}.
\]

若：

\[
R_i^{30}\ge 1.05,
\]

则该 instance 记为 performance-harmful。

同时必须报告：

- instance-weighted geometric mean；
- median；
- p90/p95；
- worst ratio；
- exact closure 数；
- timeout/memory censor 数；
- migration wall 和 peak extra memory。

#### 正式安全声明

scale30 的 safety guarantee 应独立建立。若仍采用：

```text
instance-level one-sided 95% harm upper <= 0.10
```

则必须在独立 Safety-B 中达到足够的 independent instances。零 observed harm 情况下，至少需要 29 个独立有效 instances 才可能满足该上界。

由于 deterministic policy 对所有授权 scale30 instances 生效，因此这里不存在通过低 activation coverage 规避风险统计的问题。

### 1.2 scale50 GAT policy 的 harm contract

scale50 至少需要区分两层风险。

#### 第一层：总体 production policy harm

比较：

```text
TEMPORAL_GAT_POLICY
vs.
literal Q0
```

这里包括：

- Q0 boundary 前缀；
- QD1 trial；
- GAT inference；
- continue 或 reverse migration；
- fail-closed；
- 完整 request 和完整 BPC 的全部税负。

总体 policy 的 instance-level harm 是正式 production safety 的主口径。

#### 第二层：activated decision harm

只对实际调用 GAT 且通过 OOD、confidence、disagreement 和 resource preflight 的 activated instances，单独统计：

- continue 错选导致的 harmful tail；
- revert 税；
- activation coverage；
- false-continue 与 false-revert；
- continue/revert 分层的 wall ratio；
- activated subset 的 exact closure 和 resource censor。

#### 安全声明规则

- 总体 policy harm 必须给出 instance-level 95% 单侧上界；
- activated subset 必须报告 exact upper bound；
- 只有 activated independent instances 的数量足以支持时，才可以声称 activated harm upper `<=0.10`；
- 若 activation 数不足，应如实报告实际上界，不能用 context rows 或多个 requests 伪造独立样本量；
- scale30 与 scale50 的 harm 结果不得 pooling；
- hard correctness/resource redline 仍然要求为 0。

### 1.3 对 Codex 的具体要求

请在 pre-outcome 阶段提出并冻结两份独立文件草案：

```text
scale30_deterministic_harm_contract.proposal.json
scale50_temporal_gat_harm_contract.proposal.json
```

两份合同必须分别说明：

- policy；
- comparator；
-统计单位；
- harm event；
- censor event；
- CI 方法；
- required independent sample count；
- PASS/FAIL 规则；
- insufficient-evidence 状态。

在我确认之前，不得把草案写入现有 Round 5 的 immutable freeze，也不得根据任何已揭示 outcome 调整定义。

---

## 问题 2：是否授权提出 GAT topology gate 的正式默认合同？

### 正式确认：授权提出，但必须在 pre-outcome 阶段完成，并由我最终确认后才能冻结

Codex 可以立即起草正式默认合同，但该授权不等于允许其自行确定最终阈值或直接启动 topology promotion。

合同必须在以下信息仍未揭示时形成：

- train 三臂 wall ratio；
- selected K；
- benefit/adverse label；
- GAT 与 controls 的 CV 结果；
- development 和 sealed 结果。

### 2.1 topology gate 的主要科学问题

合同必须检验：

> 在相同 temporal response、相同训练数据、相同 action space 和相同评估实例上，显式图消息传递是否提供了 Linear、MLP、no-message pooling 和随机拓扑无法替代的增量价值。

不能只证明“GAT 能分类”，也不能只证明 BA 比某个弱 baseline 高 0.01。

### 2.2 必须包含的 controls

至少保留：

- Linear；
- MLP；
- no-message GAT；
- shuffled-topology GAT；
- deterministic always-continue；
- deterministic always-revert；
- literal Q0；
- taxed oracle，仅作为上界而不是可部署 control。

### 2.3 默认 effect-size 原则

Codex提出的合同必须同时包含 solver-relevant effect 和 representation effect。

#### 主要 effect：policy utility

建议正式默认合同至少要求：

- GAT 相对最佳 simple/no-message control 的 paired policy wall ratio 点估计 `<=0.98`，即至少 2% 的增量改善；
- 相应 paired 95% CI 的不利边界必须严格优于 1.00；
- GAT 不得以增加 harmful instances、resource censor 或显著降低 coverage 为代价获得平均收益。

若 Codex认为 2% 不适合，应在提案中给出：

- addressable-wall 推导；
- measurement noise；
- repeat variance；
- 最小具有 solver 意义的 effect；
- 统计 power。

不能仅凭经验任意选择一个更小阈值。

#### 次要 effect：representation/topology

BA、AUROC、Brier score、ECE 等可以保留，但只能作为辅助指标。建议：

- GAT 相对 no-message 和 shuffled topology 的 benefit BA 差异不低于一个预先固定的最小 effect；
- 该 effect 不应继续沿用缺乏统计意义的单点 `0.01` 作为唯一 gate；
- topology shuffle 必须同时导致 policy utility 或 paired regret 的可测退化，而不只是分类指标轻微波动。

### 2.4 CI 规则

合同至少应规定：

- 所有主要 utility 统计以 instance 为 cluster；
- 对 paired log wall ratio 使用 cluster bootstrap 或等价的 instance-level paired CI；
- 主结论使用 95% CI；
- 同一 instance 的多个 contexts 不得作为独立重采样单位；
- incomplete/censored outcomes 的处理规则必须预先冻结；
- CI 计算代码、seed 和重采样次数必须固定并可复现。

建议 bootstrap 次数不低于 `10,000`，但最终值由 Codex在合同草案中结合运行成本和数值稳定性说明。

### 2.5 shuffle seed 数

建议正式默认合同至少使用：

```text
>=10 个独立、预先冻结的 topology-shuffle seeds
```

要求：

- shuffle seed 在 outcome 前固定；
- 不得挑选最有利或最不利的 shuffle；
- 每个 shuffle 必须保持 node/edge feature marginal 和任务规模不变，仅破坏预先声明的 topology relationship；
- 报告全部 shuffle 的 utility/BA 分布，而不是只报告均值；
- 三个 model ensemble seeds 与 topology-shuffle seeds 必须区分管理。

若计算资源允许，Codex可以提出 20 个 seeds；少于 10 个需要专门说明统计与计算理由。

### 2.6 多重比较规则

主要比较建议至少包括：

1. GAT vs. best Linear/MLP control；
2. GAT vs. no-message GAT；
3. GAT vs. shuffled-topology distribution。

对预先声明的 primary hypotheses，建议使用：

```text
Holm-Bonferroni family-wise error control, alpha = 0.05
```

要求：

- primary 和 secondary hypotheses 在 outcome 前划分；
- 不得在看到结果后把失败的 primary 降为 secondary；
- 不得通过增加大量弱 controls 后只挑最有利比较；
- 所有 exploratory metrics 必须明确标记为 exploratory，不进入正式 topology PASS。

### 2.7 授权边界

Codex下一步可生成：

```text
temporal_gat_topology_gate_default_contract.proposal.md
temporal_gat_topology_gate_default_contract.proposal.json
```

但在我明确确认前：

- 不得写入 Round 5 immutable contract；
- 不得据此训练或筛选 topology；
- 不得修改现有 source/corpus/config freeze；
- 不得读取 future topology outcomes 后再回填合同。

---

## 问题 3：是否需要预设 topology round 上限和计算预算？

### 正式确认：需要，避免无限调参与选择性报告

由于 GAT 必须作为论文核心创新保留，本项目可以允许有控制地改进 GAT，但不能允许在同一数据上无限尝试网络结构，直到偶然超过 controls。

### 3.1 建议的 round 上限

对当前 **post-trial Temporal-GAT topology hypothesis**，最多允许：

```text
3 个正式 outcome-bearing topology rounds
```

建议定义为：

#### Topology Round T1：当前正式基线

- 使用当前 temporal multi-resolution graph；
- 使用冻结的 controls；
- 主要验证 temporal response 是否可观察，以及 topology 是否首次超过 controls。

#### Topology Round T2：一次有因果依据的 representation repair

仅当 T1 失败且诊断能够明确指出表示缺陷时允许，例如：

- 缺少 full-mass cross-cell temporal flow；
- sampled label graph 未覆盖关键 parent-child 转移；
- task topology 与 label topology 融合不充分；
- scale/lifecycle context 未进入 message passing。

T2 不允许只是扩大 hidden width、增加层数或进行无边界 hyperparameter search。

#### Topology Round T3：最终确认轮

- 对唯一剩余、预先声明的 GAT hypothesis 进行最终验证；
- 使用 fresh 或严格隔离的 validation/safety evidence；
- 不再允许在 T3 之后对同一 target、同一 action 和同一数据语义继续结构调参。

### 3.2 连续失败后的处理

#### 连续 2 轮未超过 controls

必须暂停 topology promotion，生成：

```text
topology_two_round_negative_root_cause.audit.md
```

至少回答：

- action support 是否真实存在；
- temporal response 是否可观察；
- controls 是否已吸收全部有效 counters；
- topology 信息是否在图构造中被破坏或丢失；
- 失败来自低 power、标签噪声、trial K、图表示还是 GAT 本身；
- 是否仍有一个明确、可证伪的新 topology hypothesis。

没有明确新假设时，不得启动第三轮。

#### 连续 3 轮未超过 controls

应正式终止当前 topology hypothesis：

```text
CURRENT_TEMPORAL_TOPOLOGY_HYPOTHESIS_TERMINATED_NEGATIVE
```

这意味着：

- 当前 graph/action/label 组合不能支持 GAT 正向结论；
- 不允许继续在同一 corpus 上调层数、宽度、dropout、seed 或阈值；
- 不允许把 MLP 结果包装成 GAT 成功；
- 若仍要保留 GAT 核心路线，必须提出一个新的、机制上不同的图问题定义，并在新 outcome 前建立新 round、新 split、新合同。

### 3.3 计算预算原则

每个 topology round 应预先冻结：

- GAT architecture family 数；
- model seeds；
- shuffle seeds；
- grouped CV folds；
- controls；
- maximum training runs；
- maximum hyperparameter candidates；
- early stopping 规则；
- total CPU/GPU time or job count cap。

建议默认限制：

```text
每轮只允许 1 个主 GAT hypothesis
3 个预冻结 model seeds
>=10 个 topology-shuffle seeds
固定 5-fold instance-grouped CV
不超过 2 个有明确机制差异的 architecture candidates
```

如果同时比较两个 architecture candidates，应将其纳入多重比较校正，且不能在看到 development 后选择其中一个进入 sealed。

### 3.4 与 GAT 核心创新要求的关系

保留 GAT 为核心创新，不等于预设 GAT 一定成功。正确的纪律是：

- 给 GAT 足够但有限的验证预算；
- 每次修改都必须对应明确的 topology hypothesis；
- 连续失败后停止同一假设的无限优化；
- 只有超过 controls、通过安全与 E2E gate 后，才形成正向 GAT 结论。

---

## 问题 4：若 addressable-wall 证明 5% 理论不可达，应先扩大 scope 还是重新审定 gate？

### 正式确认：优先在首个 outcome 前重新审定新 Policy Round 的 promotion gate

我的优先顺序是：

```text
第一步：重新审定 promotion gate 的可实现性
第二步：评估是否存在值得单独开新 round 的 exact-safe scope expansion
第三步：不得在当前冻结 Round 5 中原地扩 scope 或事后放宽 gate
```

### 4.1 为什么不优先直接扩大 exact-safe scope

扩大 scope 会改变：

- lifecycle distribution；
- request hardness；
- graph/context schema；
- trial tax；
- memory 风险；
- safety population；
- GAT action authority；
- formal exact differential 范围。

例如将当前 root-CG 扩展到 tree pricing，不是简单增加若干样本，而是新的算法授权和新的安全合同。若为追求 5% 而直接扩大 scope，可能用更高的 exact-safe 风险换取更多可控 wall。

### 4.2 addressable-wall audit 应先回答什么

至少按 scale 和 lifecycle 计算：

\[
f=\frac{\text{当前授权 temporal scope wall}}{\text{完整 BPC wall}},
\]

并估计 taxed oracle 局部比率 \(r_{oracle}\)。最乐观的 E2E 下界为：

\[
R_{E2E,min}=(1-f)+f r_{oracle}.
\]

如果：

\[
R_{E2E,min}>0.95,
\]

则当前 action scope 在理论上无法达到 5% E2E 改善。此时继续用 5% 作为当前 scope 的 promotion gate，会把一个不可实现的系统上限错误归因于模型失败。

### 4.3 决策规则

#### 情形 A：5% 理论可达

- 保留现有 5% promotion gate；
- 不扩大 scope；
- 先验证当前最小 exact-safe action 是否能够兑现收益。

#### 情形 B：5% 理论不可达，但存在明确相邻 wall

只有同时满足以下条件，才建议另开 scope-expansion round：

- 相邻 scope 占有足够 wall；
- action 仍然只改变 comparator/order；
- 不修改 dominance、RC、bound、certificate 和 stopping semantics；
- 可以建立独立 differential、migration、resource 和 harm contract；
- 有足够 fresh data 覆盖新 lifecycle；
- 扩 scope 后的理论 E2E ceiling 能实质超过 5%。

这必须是新的 experiment ID、config、source freeze、corpus/split 和 acceptance contract，不能修改当前 Round 5。

#### 情形 C：5% 理论不可达，也不存在低风险 scope expansion

应在首个 outcome 前重新审定新 Policy Round 的 production promotion gate，并把以下目标分开：

- GAT topology scientific gate；
- exact-safe policy utility gate；
- production-worthiness gate；
- formal whole-solver acceptance gate。

新 gate 应由 addressable-wall ceiling、trial tax、repeat variance 和运维成本共同决定，而不是事后根据模型结果降低。

### 4.4 当前倾向

因此我的明确倾向是：

> **先重新审定 promotion gate 的理论可实现性；只有存在清晰、有限且可审计的 exact-safe 扩展对象时，再另开 scope-expansion round。**

Round 5 已冻结的 gate 不在当前 run 中修改。任何 gate 或 scope 变化都进入新的 pre-outcome Policy Round。

---

## 问题 5：是否授权立即恢复剩余 eligibility 并监控至 274/274？

### 正式确认：授权立即执行，但必须满足幂等恢复与单 writer 条件

这是下一步唯一可以立即执行的运行任务。授权范围仅限于：

```text
恢复并完成当前 Round 5 的 boundary eligibility replay
```

不包括：

- context freeze；
- train schedule freeze；
- 三臂任务；
- K selection；
- dataset/training；
- calibration；
- development 或 sealed；
- 修改任何 frozen contract；
- production activation。

### 5.1 先重新核对剩余数量

不能直接把 `243` 硬编码为剩余任务数。

原审阅稿快照是：

```text
completed eligibility files = 30/274
```

若现在确实已经完成 31 个，则剩余才是：

```text
274 - 31 = 243
```

因此恢复前必须基于当前 run root 重新计算：

- valid completed artifacts；
- missing artifacts；
- duplicate artifacts；
- partial/corrupt artifacts；
- currently running state hashes；
- marker 与 eligibility output 的一一对应。

最终待运行集合应定义为：

```text
all 274 frozen snapshot IDs
minus
all currently valid completed eligibility IDs
```

### 5.2 启动前 preflight

Codex必须先完成以下检查。

#### A. writer/process exclusivity

- 检查是否存在当前 experiment ID 对应的 parent writer；
- 检查是否存在遗留 child native replay；
- 检查 lock/pid/heartbeat；
- 检查是否有另一个 shell、tmux、service 或 scheduler 正在写同一 run root。

规则：

```text
若发现现存 writer：不得启动第二个 writer，只监控现存进程。
若确认没有 writer：才允许恢复。
```

#### B. immutable binding

必须重新核对：

- experiment ID；
- config path/hash；
- corpus manifest path/hash；
- source freeze；
- exact config；
- native build/hash；
- run root；
- 274 个 raw snapshot inventory；
- arm outcome count 仍为 0；
- model-called count 仍为 0；
- 尚未生成 context freeze 和 train outcome artifacts。

任何 hash drift 都必须停止，不允许“修复后继续原 round”。

#### C. output integrity

- 完成文件必须可解析且 schema 完整；
- 已完成 artifact 不得覆盖；
- partial/corrupt 文件应先保留诊断副本，再按原 state hash 幂等重跑；
- 不得删除已存在的合法 resource-censor row；
- 同一 state hash 只能形成一个 canonical completed artifact。

### 5.3 恢复命令

使用**原冻结命令**和原 runner，不重新拼接一个可能不同的 CLI。优先从以下位置恢复准确命令：

- 原 parent process command line；
- run state/command manifest；
- frozen orchestration log；
- 脚本 `--help` 与当前 config 的正式字段。

核心入口应仍为：

```text
scripts/collect_p0v5_temporal_gat_root_contexts_v1.py eligibility
```

但实际参数必须以原冻结记录为准，不能根据本回复猜测或增删 flags。

### 5.4 运行约束

恢复后必须保持：

- 单 host；
- 单 parent writer；
- 同一时刻最多一个 active eligibility child；
- fresh process 语义不变；
- 原 memory cap 和 reserve 不变；
- 不并发启动 freeze、三臂或其他高内存任务；
- 不调用 GAT；
- 不运行 QD1 trial；
- 不修改 boundary；
- 不修改 eligibility graph schema。

### 5.5 持续监控字段

至少每完成一个 artifact，或按固定 heartbeat 周期，记录：

```text
valid_completed / 274
missing_count
duplicate_count
partial_or_corrupt_count
current_state_hash
current_scale
current_child_pid
current_wall
current_rss
MemAvailable
boundary_reached_count
graph_built_count
model_called_count
label_drop_count
FOUND_NEGATIVE_PARTIAL count
COMPLETE count
MEMORY_LIMIT count
other_fail_closed_status counts
arm_outcome_artifact_count
binding_hash_status
```

### 5.6 哪些情况可以继续，哪些必须停止

#### 允许记录后继续

单个 eligibility request 出现以下原 exact-safe 状态时，可以形成合法 eligibility/resource audit 后继续下一个：

- `FOUND_NEGATIVE_PARTIAL`；
- `COMPLETE`；
- `MEMORY_LIMIT`；
- 其他已声明的 fail-closed incomplete 状态。

前提是：

- boundary/graph/telemetry artifact 合法；
- 没有 label drop；
- 没有错误 certificate；
- 没有 binding drift。

#### 必须立即停止并报告

- 发现第二个 writer；
- source/config/corpus/native hash 漂移；
- `model_called > 0`；
- 出现任何三臂 outcome artifact；
- label drop；
- duplicate canonical state hash；
- eligibility artifact 被非幂等覆盖；
- partial writer 无法恢复；
- memory reserve 低于原冻结安全线且继续运行可能污染宿主机；
- output schema 或 graph hash 不可复现；
- unexpected certificate/closure semantics；
- run root 与 frozen experiment ID 不一致。

### 5.7 达到 274/274 后的动作

完成后只允许：

1. 停止 eligibility writer；
2. 再次确认没有 active child；
3. 生成只读完成审计，例如：

```text
eligibility_completion.audit.json
eligibility_completion.audit.md
```

4. 报告：
   - `274/274` canonical artifacts；
   - per-scale/per-partition valid instance/context capacity；
   - status 分布；
   - resource-censor rows；
   - label drop = 0；
   - model called = 0；
   - arm outcome = 0；
   - binding drift = 0；
   - missing/duplicate/partial = 0；
5. 等待下一步确认。

明确禁止在完成后自动执行：

```text
freeze contexts
freeze train schedule
start three-arm trials
```

因为 eligibility 完成后还需要先进行：

- independent sample capacity audit；
- addressable-wall audit；
- migration resource audit；
- calibration feasibility audit；
- 对新 Policy Round 合同的最终确认。

---

# 四、对 Codex 的立即执行指令

## 现在可以立即做

1. 对当前 run root 做只读进程与 artifact preflight；
2. 重新计算当前真实 completed/missing 数量；
3. 若确认没有 writer，按原冻结命令幂等恢复 eligibility；
4. 单 writer 串行运行至 `274/274`；
5. 持续记录 heartbeat 和 resource/status audit；
6. 完成后生成 eligibility completion audit 并停止；
7. 同时可以在不读取 outcome 的前提下起草：
   - 两尺度独立 harm contract proposal；
   - topology gate default contract proposal；
   - topology round/compute budget proposal。

## 现在不得做

- 不得启动 Q0/CONTINUE/REVERT 三臂；
- 不得冻结 context 或 train schedule；
- 不得修改 Round 5 gate；
- 不得扩大 lifecycle/action scope；
- 不得训练 GAT 或 controls；
- 不得生成 threshold、bundle 或 candidate；
- 不得触碰 production registry；
- 不得处理论文重写问题；
- 不得根据任何意外暴露的 outcome 回填合同。

---

# 五、最终决策

本轮新增决定可概括为：

```text
scale30 safety:
    独立 deterministic harm guarantee

scale50 safety:
    独立 GAT overall-policy guarantee
    + activated-subset risk audit

GAT topology:
    授权 pre-outcome 正式合同提案
    solver utility 为主，BA 为辅
    >=10 frozen shuffle seeds
    95% instance-level paired CI
    Holm-Bonferroni 控制 primary comparisons

Topology budget:
    最多 3 个正式 outcome-bearing rounds
    2 轮失败强制复盘
    3 轮失败终止当前 topology hypothesis

5% addressable-wall:
    先审定 gate 可实现性
    scope expansion 只能另开新 round

Eligibility:
    立即授权幂等恢复
    先确认无 writer并重新计数
    单 writer运行至274/274
    完成后只审计，不自动进入三臂
```

**问题 5 的授权立即生效，但严格以“无现存 writer、冻结绑定一致、幂等单 writer恢复”为前提。**
