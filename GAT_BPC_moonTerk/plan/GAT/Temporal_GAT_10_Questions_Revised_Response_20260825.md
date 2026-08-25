# P0V4+V5 Temporal-GAT 新 Policy Round：10 个确认问题的最终回复（修订版）

> 用途：直接作为交给 Codex 的决策回复与后续执行约束。  
> 修订说明：本版重点修改问题 1 和问题 10。此前任何“GAT 可以降级为可选项”或“由 Codex同步考虑论文重写”的表述，均以本文件为准予以覆盖。  
> 当前事实边界：Round 5 仍处于 `CONTEXT_ELIGIBILITY`；Temporal-GAT 尚未训练、校准或获得部署权限；production default 仍为 `no_cut`。当前活动进程和已冻结 Round 5 artifact 不得因本回复而中断或事后修改。

---

## 一、最高优先级决策

本项目下一阶段必须同时坚持以下四条原则：

1. **GAT 必须保留，并继续作为论文与算法路线的核心创新点。** Temporal trial、完整 frontier 迁移和 exact-safe 控制外壳是基础机制，但最终科学目标不是只得到任意一个可用分类器，而是验证图消息传递是否能够从真实的 `t0→tK` frontier 动态中提取 simple counters、Linear、MLP 与 no-message pooling 无法替代的信息。
2. **GAT 不得获得任何正确性权限。** 它只能在已授权的 P0V4 exact fallback request 内决定 `CONTINUE_QD1` 或 `REVERT_Q0`，不得改变 dominance、reduced cost、cut、branch、bound、termination 或 certificate authority。
3. **scale30 与 scale50 可以采用不同 policy。** scale30 可采用 deterministic QD1 或 literal Q0；scale50 作为主要选择异质性场景，继续承担 Temporal-GAT selector 的核心验证任务。这一分治不削弱 GAT 的论文地位，反而能避免让近似 always-continue 的 scale30 分布稀释 scale50 的图学习问题。
4. **Codex 暂不处理任何论文重写工作。** 论文的结构、叙事、标题、贡献表达和正文修改全部由用户控制。Codex 只负责代码、实验、模型、数据、审计、冻结合同和客观结果报告。

---

## 二、10 个问题的结论摘要

| 问题 | 最终确认 |
|---|---|
| 1 | **必须保留 GAT，并将其作为论文和算法路线的核心创新；MLP、Linear、no-message 与 shuffled-topology 只能作为 controls，不能替代最终 GAT 方法。** |
| 2 | **同意将 scale30 deterministic policy 与 scale50 Temporal-GAT selector 分开。** |
| 3 | **若 scale30 fresh pilot 不稳定，允许 scale30 保持 literal Q0，不影响 scale50 GAT 研究。** |
| 4 | **5% E2E 改善继续作为 production promotion 的首选硬门槛，但在新 Round 冻结前必须先证明当前作用域理论上可达到该门槛。** |
| 5 | **若继续声称 instance-level 95% harm upper `≤0.10`，必须新增足够多、完全独立的 Safety-B instances。** |
| 6 | **优先复用 D5，并在容量不足时执行 D5 extension；不重新生成整套 corpus，除非实例语义或底层数据发生实质变化。** |
| 7 | **新 Policy Round 先验证 trial 后的 `CONTINUE/REVERT` 两动作；确认 trial 有净价值后，再单独考虑 pre-trial `STAY_Q0`。** |
| 8 | **研究数据覆盖 early/middle/late root-CG 生命周期；production authority 按已验证 strata 分阶段开放。** |
| 9 | **MLP 可以作为独立 control 或单独命名的工程候选，但不能替代本研究最终 GAT 候选，也不能把 MLP 成功写成 GAT 成功。** |
| 10 | **Codex 现在完全不考虑论文重写；只维护技术事实与实验产物，论文同步由用户另行决定。** |

---

# 三、逐项详细回复

## 问题 1：优先追求生产 solver 加速，还是必须保留 GAT？

### 最终确认

**必须保留 GAT。GAT 是论文中的核心算法创新，不再将其视为可以被 MLP、Linear 或 deterministic controller 替代的可选组件。**

这意味着下一轮不是单纯寻找“哪个控制器最快”，而是需要同时完成两类目标：

1. 证明 temporal trial 后的动作选择本身具有可实现的净收益；
2. 证明 GAT 的 topology-aware message passing 对该动作选择具有独立增量价值。

只有第一项通过而第二项失败，最多只能说明 temporal response 或简单控制器有用，不能视为本论文所需的 Temporal-GAT 路线成功。

### GAT 必须满足的科学边界

GAT 的核心不是网络规模，也不是在模型名称中保留 “GAT” 字样，而是必须真实使用图拓扑和消息传递，并通过严格 controls 证明拓扑信息具有贡献。至少保留：

- Linear；
- MLP；
- no-message GAT；
- shuffled-topology GAT；
- always-continue；
- always-revert。

最终 GAT 至少需要在 scale50 上同时满足：

- policy utility 优于最佳 Linear/MLP/no-message control；
- topology shuffle 后性能出现稳定退化；
- 该退化在 instance-level paired utility、harm tail 或 E2E 指标上可重复，而不只表现为极小的 row-level BA 波动；
- exact audit、portable parity、resource gate 和 fail-closed 均通过。

### 对模型设计的允许修改

为了让 GAT 真正可学，可以修改：

- temporal graph 的节点与边定义；
- full-mass cell-flow 表示；
- label-task sample 策略；
- hidden width、层数和 pooling；
- signed log wall-ratio、uncertainty 与 censor-risk heads；
- scale-specific head 或 scale-specific encoder；
- K 的归一化方式；
- calibration 与 Safety-B 设计。

但不得以“模型更简单”为理由将最终方法替换为纯 MLP，也不得把 no-message pooling 重新命名为 GAT。

### 如果 GAT 暂时不如 MLP

若 fresh evidence 显示 MLP 明显优于当前 GAT，应当：

1. 将当前 GAT round 记为 topology hypothesis 未通过；
2. 保留 MLP 结果作为 control 和问题诊断；
3. 分析失败来自数据容量、图构造、跨时点流动缺失、模型过大、K 不合适还是监督目标不一致；
4. 在新的冻结 Round 中改进 GAT，而不是直接把论文核心改成 MLP；
5. 未经用户明确授权，不得自动将 MLP 注册为替代 GAT 的 production candidate。

### 与 scale30/scale50 分治的关系

保留 GAT 不等于两个尺度都必须训练 GAT：

```text
scale30:
    deterministic QD1 pilot
    PASS -> fixed QD1
    FAIL -> literal Q0

scale50:
    Q0 -> QD1 trial
       -> Temporal-GAT
          -> CONTINUE_QD1
          -> REVERT_Q0
```

scale50 历史上同时存在 oracle headroom 和 fixed-QD1 harmful tail，更适合承担 GAT 的选择性验证。scale30 若近似 always-continue，强行训练 selector 反而会弱化论文的机制识别。

### Codex 的执行约束

Codex 必须：

- 保留并强化真正的 GAT topology branch；
- 将 MLP 等模型限定为 controls；
- 单独生成 topology value audit；
- 不以简单控制器通过 production gate 代替 GAT scientific gate；
- 不将一个非图模型写入 `TEMPORAL_GAT` bundle、candidate 名称或实验结论。

---

## 问题 2：是否同意把 scale30 deterministic policy 与 scale50 learned selector 分开？

### 最终确认

**同意。**

建议架构为：

```text
scale30:
    literal Q0 到冻结 boundary
    -> deterministic QD1
    -> 只验证 fresh E2E、harm tail、resource censor 和 formal acceptance

scale50:
    literal Q0 到冻结 boundary
    -> QD1 short trial
    -> 构造 t0/tK temporal graph
    -> Temporal-GAT 决定 CONTINUE 或 REVERT
```

两者可以共享：

- Native temporal trial 外壳；
- complete-frontier migration；
- creation-ID conservation；
- telemetry schema；
- exact-safe audit；
- manifest、registry、canary 和 rollback。

但应分别冻结：

- policy；
- K；
- threshold；
- calibration；
- acceptance gate；
- 是否需要双动作支持。

该分治使 GAT 更聚焦于 scale50 的真实选择问题，并避免 scale30 的多数 continue 样本主导共享 encoder。

---

## 问题 3：若 scale30 fresh pilot 不稳定，是否允许保持 literal Q0？

### 最终确认

**允许，而且不影响 scale50 Temporal-GAT 研究继续。**

若 scale30 出现以下任一情况，应保持 literal Q0：

- deterministic QD1 GM 不稳定；
- 存在明显 harmful instance；
- trial/migration overhead 无法摊薄；
- 新增 timeout 或 memory censor；
- peak RSS 超限；
- formal acceptance 无法通过。

此时应解释为 scale30 的 fresh evidence 不支持切换，而不是 Temporal-GAT 整体失败。scale50 仍可独立验证 action support、observability 和 topology value。

需要注意：如果当前 formal contract 将 scale30 与统一 candidate 绑定，新 Policy Round 必须在产生新 outcome 前明确重冻合同，不能看到结果后再临时删改门槛。

---

## 问题 4：Formal acceptance 的至少 5% E2E 改善是否不可修改？

### 最终确认

**5% 继续作为 production promotion 的首选硬门槛，但不是脱离可实现性的绝对数字。**

在新 Round 冻结前，必须先做 addressable-wall audit。设 Temporal-GAT 实际能影响的 wall 比例为 `f`，局部 taxed-oracle ratio 为 `r`，则最佳可能的 E2E ratio 近似为：

```text
R_E2E_min = (1 - f) + f * r
```

只有当 `R_E2E_min <= 0.95` 时，5% gate 才具有可实现性。

若 oracle 上界本身无法达到 5%，应在新 Round outcome 产生前选择：

- 扩大合法 action scope；
- 降低 graph/trial/migration tax；
- 改善 proof-tail 可控比例；
- 或重新冻结 production gate。

不得在 development 或 sealed 结果揭示后事后修改。

---

## 问题 5：是否坚持 instance-level 95% harm upper `≤0.10`？

### 最终确认

**坚持该正式安全声明时，必须新增独立 Safety-B。**

统计单位应为独立 instance，而不是同一 instance 内的 context rows。一个 Safety-B instance 中只要任一获得 production authority 的 context 发生 adverse，即记为 harmful instance。

零 observed harm 时，要使单侧 95% 上界不超过 0.10，至少需要约 29 个独立、实际激活的 instances。考虑 activation、eligibility 和 resource censor，建议每尺度准备约 45–55 个 fresh Safety-B instances。

数据分区应调整为：

```text
K/action-support set
model-training set
Calibration-A
Safety-B
Development
Sealed final
```

其中：

- Calibration-A 用于 Platt/gain/uncertainty calibration 与 threshold selection；
- Safety-B 在模型、K、阈值和 OOD 全部冻结后，只做安全验证；
- Safety-B 不得参与模型选择、架构修改或阈值调整。

---

## 问题 6：是否优先复用 D5，容量不足时做 D5 extension？

### 最终确认

**是。优先复用 D5，并进行受控 D5 extension，不重新生成整套 corpus。**

建议：

- D5 train：用于已有 action-support 和训练候选；
- D5 calibration：可转为 Calibration-A；
- D5 development/sealed：如果尚未揭示且未参与设计修改，可继续保留；
- D5 extension：补充独立 K-selection、lifecycle coverage 与 Safety-B。

D5 extension 必须：

- 使用新 seed range；
- 保持 generator、map source、objective 与 candidate-path 语义一致；
- 做 content-hash 去重；
- 在任何新 queue outcome 前冻结用途；
- 不按已知 benefit/adverse 结果挑选实例；
- 明确记录与 D5 的 lineage。

只有 map、generator、目标函数、候选路径空间或实例语义发生实质变化时，才需要整套重生成。

---

## 问题 7：是否先验证 `CONTINUE/REVERT`，再增加 `STAY_Q0`？

### 最终确认

**是。第一阶段只学习 trial 后两动作。**

实验仍必须保留三臂：

```text
literal Q0
trial + CONTINUE_QD1
trial + REVERT_Q0
```

但 GAT 的第一阶段动作空间仅为：

```text
CONTINUE_QD1
REVERT_Q0
```

这样先回答：在共同经历真实 QD1 trial 后，`t0→tK` response 是否足以决定继续或迁回。

在开始 GAT 训练前应先通过：

- taxed oracle 对 Q0 有净收益；
- trial+revert tax 可接受；
- 当前 action scope 有足够 addressable wall；
- reverse migration 内存可预留。

只有确认 trial 本身值得支付后，才在后续独立 Round 引入 pre-trial `STAY_Q0/ENTER_TRIAL`。不得在同一 revealed 数据上临时增加第三动作。

---

## 问题 8：production scope 限制最早三个，还是覆盖 early/middle/late？

### 最终确认

**研究数据覆盖 early/middle/late，production 按验证 strata 分阶段授权。**

建议 outcome-blind context selection：

```text
early  = 第一个 eligible root-CG request
middle = eligible chronology 的中位 request
late   = 最后一个 eligible root-CG request
```

如果不足三个，则全部保留。选择不得使用 wall ratio、oracle action、benefit、adverse 或模型分数。

Development、Safety-B 和 sealed 应分别报告 early/middle/late：

- activation coverage；
- wall ratio；
- harmful instance；
- censor；
- inference/OOD；
- peak RSS；
- GAT 相对 controls 的增量。

初期 canary 只打开证据最充分的 strata，未验证生命周期保持 literal Q0。

---

## 问题 9：若 MLP 明显优于 GAT，是否接受 production 部署 MLP？

### 最终确认

**可以将 MLP 作为独立、明确命名的工程候选进行评估，但它不能替代本研究最终 GAT 候选，也不能使本轮被判定为 Temporal-GAT 成功。**

必须严格区分：

```text
TEMPORAL_QD1_GAT_V1
TEMPORAL_QD1_MLP_CONTROL_V1
FIXED_QD1_SCALE30_V1
```

若 MLP 更好：

- GAT topology scientific gate 判定未通过；
- MLP 结果作为 control、可观测性证据和工程参考保留；
- 是否将 MLP 单独进入 production 由用户另行批准；
- Codex 不得自动把 MLP 替换进 GAT candidate；
- 论文的 GAT 核心路线继续在新冻结 Round 中改进，而不是直接改成 MLP 论文。

因此，MLP 的工程价值可以被承认，但不能稀释问题 1 所确定的“必须保留 GAT 核心创新”。

---

## 问题 10：论文何时重写？

### 最终确认

**Codex 现阶段不要考虑论文重写问题。论文修改由用户完全控制。**

Codex 的任务范围只包括：

- Native/Python 实现；
- temporal graph 与 GAT 模型；
- dataset、split 与 freeze；
- K/action-support；
- Calibration-A、Safety-B；
- exact differential 与 portable parity；
- development、sealed、formal、canary；
- audit、manifest、telemetry 与客观结果汇总。

Codex 不得主动：

- 修改或重写论文正文；
- 调整论文标题、摘要、引言或贡献点；
- 生成论文结构修订提纲；
- 根据实验结果自动改变论文叙事；
- 修改 `manuscript_zh_trc.docx` 或其他 manuscript 文件；
- 将“当前算法与论文不一致”作为阻断代码或实验工作的 gate；
- 为可能的 positive/negative result 预写讨论、结论或审稿回复。

### 允许 Codex 保留的唯一论文相关信息

为了工程可追溯，Codex可以在技术审计中记录纯事实，例如：

```text
MANUSCRIPT_SYNC_REQUIRED = true
algorithm_delta = request-level temporal continue/revert selector
```

但只能记录：

- 哪些算法接口发生变化；
- 哪些配置、模型输入、动作空间和证明边界发生变化；
- 对应 commit、artifact 和 hash。

不得把这些事实扩写成论文段落、贡献表述或章节修改建议。论文何时同步、如何重写、采用何种叙事，全部等待用户单独指令。

---

# 四、建议冻结的新 Policy Round 总体合同

```text
核心研究目标:
    必须验证 Temporal-GAT
    GAT topology value 是正式 scientific gate
    simple controllers 仅作为 controls

exact authority:
    GAT 只控制 current-frontier comparator
    不控制 dominance / RC / cut / branch / bound / stop / certificate

scale30:
    fresh deterministic QD1 pilot
    PASS -> fixed QD1
    FAIL -> literal Q0

scale50:
    Q0 -> QD1 trial
    -> Temporal-GAT CONTINUE / REVERT

数据:
    reuse D5
    + D5 extension
    + independent Safety-B

partition:
    K/action-support
    model training
    Calibration-A
    Safety-B
    development
    sealed

context:
    early / middle / late root-CG stratification

第一阶段动作:
    post-trial CONTINUE / REVERT
    暂不增加 learned STAY_Q0

模型结论:
    GAT 必须超过 MLP/no-message/shuffled controls
    MLP 成功不能替代 GAT scientific success

论文:
    Codex 不处理
    用户单独控制正文同步
```

---

# 五、Codex 接下来的执行边界

## 5.1 当前 Round 5

在当前 eligibility 完成前：

- 不得中断活动进程；
- 不得并发启动三臂；
- 不得修改任何 frozen config、gate、split 或 manifest；
- 不得提前生成 queue outcome；
- 不得修改 production registry；
- 不得开始论文相关工作。

## 5.2 Eligibility 完成后先做的审计

在启动大规模三臂前，先生成：

1. `independent_sample_capacity.audit.json`  
   按独立 instance 统计每尺度可用容量，而不是只统计 rows。

2. `addressable_wall.audit.json`  
   估计授权 root fallback scope 占完整 BPC wall 的比例，并计算 taxed-oracle 的理论 E2E 上界。

3. `migration_resource.audit.json`  
   记录 forward/reverse migration wall、额外内存、frontier size、预留空间和 allocator 风险。

4. `calibration_feasibility.audit.json`  
   验证现有 D5 是否足以支持 instance-level harm 声明，并计算 Safety-B extension 规模。

5. `gat_topology_identifiability.audit.json`  
   检查 temporal graph 是否包含可区分的跨 cell mass flow、parent-child response 与 dominance dynamics，而不只包含静态统计。

## 5.3 新 Round 才允许的实质修改

若需要改变：

- split；
- Safety-B；
- model target；
- temporal graph；
- K 定义；
- scale policy；
- threshold；
- production scope；
- acceptance gate；

必须建立新 experiment ID 和新的 pre-outcome freeze，不能在 Round 5 revealed outcome 上回改。

## 5.4 明确禁止

Codex 不得：

- 将 MLP 自动升级为论文最终算法；
- 将 no-message model 命名为 GAT；
- 为了通过 gate 事后放宽 topology control；
- 将 context rows 当作独立 Safety-B instances；
- 用 calibration 同时选择阈值并声称独立 harm guarantee；
- 把 resource censor 从训练数据中简单删除而不保留风险标签；
- 修改或生成任何论文正文。

---

# 六、最终决策

本项目下一阶段的目标不是在 GAT、MLP 与 deterministic policy 中无条件选择最快者，而是：

> 在不改变 exact correctness authority 的前提下，构建并验证一个基于真实 `t0→tK` frontier 响应的 Temporal-GAT，使其对 scale50 的 `CONTINUE_QD1/REVERT_Q0` 决策产生可重复、可审计、超过非图 controls 的增量价值，并最终体现为安全的 solver E2E 改善。

scale30 可以采用 deterministic QD1 或保持 literal Q0；这属于尺度适配，不改变 GAT 作为论文核心创新的要求。若当前 GAT 未超过 MLP，结论应是当前图表示或训练设计仍需改进，而不是将论文核心自动改为 MLP。

论文正文同步不属于 Codex 当前任务。Codex 只需把代码、数据、实验和审计做完整、做可复现，所有论文改写由用户后续单独控制。
