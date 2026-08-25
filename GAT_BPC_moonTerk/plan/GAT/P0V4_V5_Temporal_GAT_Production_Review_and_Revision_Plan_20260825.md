# P0V4+V5 Temporal-GAT Production 当前方案审阅与修改建议

> **审阅对象**：`CODEX_REVIEW_P0V4_V5_TEMPORAL_GAT_PRODUCTION_CURRENT_STATE_20260825_ZH.md`  
> **项目**：`GAT_BPC_moonTerk`  
> **当前实验**：`p0v5_temporal_gat_production_v1_round5_20260824`  
> **取证时点**：2026-08-25 15:36:23 CST  
> **文档用途**：用于指导后续算法设计、实验合同调整、代码修改与论文同步；不是 promotion manifest，也不构成 production 授权。  
> **事实边界**：当前 Round 5 仍处于 `CONTEXT_ELIGIBILITY`；GAT 尚未训练、校准、进入 development 或获得部署授权。本文将“当前方案中已经实现和冻结的事实”与“审阅意见和修改建议”明确区分。

---

## 1. 执行摘要

当前 Temporal-GAT 路线中，最值得保留的核心思想是：

> 在同一个 exact pricing request 内，先以 Q0 运行到冻结边界，再将完整 frontier 迁移到 QD1，执行一段真实且计入总 wall 的短 trial，随后仅决定继续 QD1，还是把**当前 frontier**迁回 Q0 comparator。

这比旧的静态 frontier GAT 更接近真实因果机制，也避免了双 prefix counterfactual 的重复成本。当前 exact-safe 外壳、双向迁移、creation-ID conservation、fail-closed、portable inference、数据冻结和 outcome-blind context collection 都具有较高工程质量。

但当前计划存在若干**结构性问题**。这些问题不是通过扩大 GAT、增加特征或继续跑完现有数千个三臂任务就能自然解决的。最关键的四项是：

1. **Calibration 的统计单位不成立**：同一 instance 的多个 context 不能作为独立 Bernoulli 样本；阈值还在同一 calibration outcomes 上选择，现有 95% harm upper 声明存在 post-selection bias。
2. **scale30 与 scale50 被错误地统一成同一种 selector 问题**：历史证据更支持 scale30 使用经过 fresh E2E 验证的 deterministic late-switch QD1，而真正需要选择器的是 scale50。
3. **当前三个输出头与动作效用不一致**：`p_benefit`、`positive_gain`、`p_adverse` 高度冗余，`expected_gain - p_adverse > 0` 没有明确的风险效用解释，且 incomplete 样本处理会产生选择偏差。
4. **模型容量与独立样本量严重不匹配**：仅 fusion trunk 与两个输出头已约 16.3 万参数，尚未计入两个 GAT encoder；而当前独立 train instances 只有 scale30 的 33 个和 scale50 的 39 个。

此外，还存在 K 选择泄漏、绝对 pop budget 不可比、缺少 `STAY_Q0` 动作、reverse migration 的瞬时内存风险、resource censor 归因不清、缺少 addressable-wall/Amdahl gate、context 生命周期分布偏移、GAT 科学结论与生产策略绑定过紧、development/sealed 统计功效不足，以及论文正文与真实 Temporal-GAT 算法已经不一致等问题。

### 建议的总方向

- **Round 5 不应直接作为最终 production promotion round。**
- 让当前 eligibility 完整结束，不中断、不污染冻结合同。
- eligibility 后先生成独立样本容量、addressable wall、migration resource、calibration feasibility 四类审计；在这些审计完成前，不自动启动最多约 5724 个 train trial tasks。
- 将 Round 5 定位为：**temporal trial 基础设施与 action-support pilot**。
- 在新的实验 round 中实施实质性修改：
  - scale30 deterministic QD1；
  - scale50 temporal controller；
  - K-selection、model-training、Calibration-A、Safety-B、development、sealed 相互分离；
  - 以 instance 为统计单位；
  - 预测带不确定性的 signed log wall ratio 与 censor risk；
  - 使用更小的 temporal cell-flow model；
  - 将 solver production track 与 GAT scientific claim track 分开。

---

## 2. 当前方案中正确且应当保留的部分

以下设计是当前路线的基础优势，不建议因为后续修改而破坏。

### 2.1 学习模块不拥有任何证明权限

Temporal-GAT 只允许改变合法 frontier labels 的 comparator；禁止：

- 删除、剪枝或过滤合法 label/route；
- 修改 dominance relation、dominance threshold；
- 修改 reduced cost、negative threshold、route reconstruction；
- 修改 cut、branch、dual、completion bound；
- 修改 exhaustive stopping 或 certificate authority；
- 让 GAT 生成 bound、closure 或 certificate。

这个边界应继续作为所有后续版本的硬约束。

### 2.2 REVERT 的语义定义正确

当前方案明确指出：

> `REVERT_Q0` 恢复的是“当前 frontier 的 Q0 comparator”，不是“从未执行 QD1 trial 的反事实 Q0 轨迹”。

QD1 trial 已经不可逆地改变了 label 到达和 dominance 的时序，因此三臂必须真实测量 `trial + revert` 的净 wall。这个声明必须保留，并应在论文中明确写入。

### 2.3 双向 frontier migration 的 exact-safe 工程设计较强

当前设计包含：

- Q0→QD1 的 size/hash/creation-ID conservation；
- QD1→Q0 的 staging queue、验证后原子 swap；
- duplicate creation-ID 与 binding 检查；
- migration 失败时不留下半空 live queue；
- creation ID 跨迁移保持，新增 label 使用单调序列。

后续需要优化的是资源预留和瞬时内存，而不是放弃原子迁移与 conservation audit。

### 2.4 数据冻结与负结果纪律正确

当前方案具备：

- fresh real-map corpus；
- train/calibration/development/sealed 在 queue outcome 前冻结；
- context selection outcome-blind；
- 旧 Round 3/4 已终止，不通过删除 terminal artifact 续跑；
- 当前 production 仍为 `no_cut`；
- 未产生 GAT 结果前不声称 GAT 有效。

这些原则必须继续保留。

---

## 3. 问题优先级总表

| 编号 | 级别 | 问题 | 不修改的主要后果 |
|---|---|---|---|
| P0-1 | 阻断级 | Calibration 统计单位与阈值后选择偏差 | “95% harm upper ≤ 0.10”缺少有效统计含义 |
| P0-2 | 阻断级 | scale30/scale50 被强行统一成 selector | 可能因缺少 revert 类别而错误否定一个稳定的 deterministic 策略 |
| P0-3 | 阻断级 | 监督目标、censor 与动作效用不一致 | 模型输出内部冲突，风险与收益不可比较，困难样本被系统性排除 |
| P0-4 | 阻断级 | 模型容量远大于独立样本量 | 高概率学习 instance hardness/proxy，而非可迁移 topology effect |
| P0-5 | 阻断级 | 论文算法与真实 Temporal-GAT 不一致 | 方法、监督、动作粒度和 exact-safe 证明均无法与实现对应 |
| P1-1 | 高 | K selection 与 grouped CV 信息复用 | CV 对模型可学性的估计偏乐观 |
| P1-2 | 高 | K 使用绝对 pops | 不同 frontier 下 trial 强度不可比 |
| P1-3 | 高 | 缺少 `STAY_Q0` 动作 | 所有 eligible context 都必须支付 trial 税 |
| P1-4 | 高 | reverse migration 瞬时内存未预留 | 最困难的 scale50 request 可能因回退动作本身触发内存失败 |
| P1-5 | 高 | resource censor 未区分固有困难与动作新增伤害 | 可能错误地用 core solver failure 否定 temporal policy，或反向掩盖动作伤害 |
| P1-6 | 高 | 缺少 addressable-wall/Amdahl gate | 可能在理论上不可能达到 5% E2E 时仍投入大量训练任务 |
| P1-7 | 高 | context 选取范围与 deployment scope 不一致 | 模型在后期 root-CG request 上发生 lifecycle distribution shift |
| P1-8 | 高 | GAT 科学结论与 production 策略绑定 | MLP/确定性策略即使更安全更快，也可能被错误丢弃 |
| P1-9 | 高 | Development/sealed 样本量与 CI 设计不足 | 5% GM 改善和零 harmful 可能只是小样本偶然结果 |
| P2-1 | 中 | OOD 使用 `mean ± 8σ` | veto 过宽，难以识别 late lifecycle 与重尾分布偏移 |
| P2-2 | 中 | topology gate 只要求 BA 下降 0.01 | 可能不到一个独立 instance 的实际差异，不能证明 message passing 有价值 |

---

# 4. P0-1：Calibration 的统计合同不成立

## 4.1 当前合同

当前每尺度有 12 个 calibration instances，每个 instance 最多 3 个 contexts，理论上最多约 36 个 calibration rows。阈值要求：

- 至少 4 个 activated instances；
- activated rows 中 observed adverse = 0；
- 使用

\[
\text{harm\_upper}=1-0.05^{1/n}
\]

计算单侧 95% 上界；
- 要求 `harm_upper <= 0.10`。

零 observed harm 时，约需 29 个 activated rows 才能使该上界降到 10% 以下。

## 4.2 第一层问题：context rows 不是独立样本

同一 instance 中的 1—3 个 root-CG contexts 共享：

- 同一任务空间结构；
- 相似的任务时间窗与资源限制；
- 同一列生成轨迹；
- 高度相关的 dual、frontier 和 solver hardness；
- 相同地图与 instance-level 难度因素。

因此，统计单位应当是 **instance**，而不是 context row。

若按独立 instance 计算：

\[
u_{0.95}(12)=1-0.05^{1/12}\approx0.2209
\]

即使 12 个独立 calibration instances 全部零 harm，也只能支持“95% 上界约为 22.1%”，不能支持“不超过 10%”。

当前 scale30 calibration 中只有 10 个 instances 有 snapshot。即使 10 个全部激活且零 harm：

\[
u_{0.95}(10)=1-0.05^{1/10}\approx0.2589
\]

上界约为 25.9%。

## 4.3 第二层问题：阈值选择产生 post-selection bias

当前 threshold grid 为：

\[
5\times3\times3\times3=135
\]

组候选策略。若在同一批 calibration outcomes 上：

1. 查看 135 组策略的 activation 与 harm；
2. 选择一组零 observed harm 的阈值；
3. 再对这组阈值使用普通零事件二项上界；

则该上界不再对应一个事先固定策略的 95% 覆盖率。阈值是“看过结果以后选出来的”，存在多重选择偏差。

## 4.4 正确修改

将 calibration 拆成两个完全独立的阶段：

| 数据集 | 允许用途 | 禁止用途 |
|---|---|---|
| Calibration-A | Platt calibration、gain calibration、阈值选择、OOD 参数拟合 | 不用于最终安全上界 |
| Safety calibration-B | 在 bundle、K、阈值、OOD 和动作规则全部冻结后，仅验证 activation 与 harm | 不允许重新调阈值、重训、改 gate |

Safety-B 必须按 **instance-level policy outcome** 计数：

> 一个 instance 内，只要任一被模型激活的 context 出现 adverse、timeout、memory censor 或 action-induced failure，该 instance 就记为 harmful。

若仍坚持零 observed harm 下 95% 上界不超过 10%，至少需要 29 个**相互独立且实际被激活的 instances**。

若预期 activation coverage 为 \(c\)，Safety-B 的原始独立实例数至少应满足：

\[
N_{\text{raw}}\ge \left\lceil\frac{29}{c}\right\rceil
\]

例如：

| 预期 activation coverage | Safety-B 最少独立 instances |
|---:|---:|
| 0.80 | 37 |
| 0.70 | 42 |
| 0.60 | 49 |
| 0.50 | 58 |

## 4.5 必须新增的 artifact

```text
calibration_a.freeze.json
threshold_selection.audit.json
safety_calibration_b.freeze.json
safety_policy_binding.json
instance_level_harm.audit.json
```

其中 `safety_policy_binding.json` 必须绑定：

- exact engine hash；
- model/bundle hash；
- selected K；
- threshold；
- OOD envelope；
- disagreement rule；
- action semantics；
- scale/lifecycle scope；
- code/source hash。

Safety-B 开始后，上述内容不得变化。

---

# 5. P0-2：scale30 不应被强行设计为 selector 问题

## 5.1 当前证据实际支持什么

历史 fresh evidence 对两个尺度给出了不同信号：

### scale30

- V3 real-map instance-weighted GM：约 `0.778757`；
- V10R1 fixed QD1 net GM：约 `0.820842`；
- 8/8 determined instances；
- harmful instances = 0；
- probe overhead GM 接近 1。

这更像是：

> scale30 的 late-switch QD1 很可能是一个应当通过独立 E2E 验证的确定性策略，而不是必须学习 continue/revert 的双动作 selector。

### scale50

- fixed QD1 在 16384 boundary 仍约慢 16%；
- oracle GM 约 `0.936561`；
- 存在明显 harmful tail；
- 只有选择性使用 QD1 才可能产生价值。

这才是真正的 selector 问题。

## 5.2 当前 gate 的逻辑倒置

当前 scale30 K gate 还要求：

- continue instances ≥ 24；
- revert/adverse support ≥ 4。

如果 scale30 几乎总应 continue，那么“没有足够 revert/adverse 样本”不是模型失败，而是 selector 没有必要。当前合同反而可能因为缺少负类，否定一个稳定且有价值的 deterministic QD1。

## 5.3 推荐的尺度分治策略

```text
scale30:
    P0V5 -> P0V4 literal Q0
    -> frozen boundary
    -> deterministic QD1
    -> 只做 fresh E2E / formal / no-harm 验证

scale50:
    P0V5 -> P0V4 literal Q0
    -> pre-trial gate
    -> QD1 trial
    -> Temporal controller:
         CONTINUE_QD1
         或 REVERT_Q0
```

两者仍可共用：

- exact-safe trial 外壳；
- migration；
- telemetry；
- manifest/bundle binding；
- production registry；
- fail-closed；
- rollback。

但不需要强行共用一个 GAT encoder，也不需要 scale30 形成双动作支持。

## 5.4 若工程上必须使用统一 bundle

允许 scale30 head 退化为冻结的常量策略：

```text
scale30_head = ALWAYS_CONTINUE_AFTER_BOUNDARY
scale50_head = TEMPORAL_CONTROLLER
```

这比为了“统一模型”而人为制造 scale30 revert 类别更诚实，也更符合已有证据。

---

# 6. P0-3：监督目标、动作规则与 censor 处理需要重构

## 6.1 当前三个输出高度冗余

当前输出：

- `p_benefit`；
- `positive_gain`；
- `p_adverse`。

而三个目标均由同一 wall ratio 变换得到：

\[
r=\frac{T_{\text{continue}}}{T_{\text{revert}}}
\]

- benefit：\(r\le0.98\)；
- adverse：\(r\ge1.05\) 或 continue censor；
- positive gain：\(\max(0,1-r)\)。

独立训练三个 head 会产生内部不一致，例如：

- `p_benefit` 高；
- `p_adverse` 也高；
- `positive_gain` 仍然大。

## 6.2 `expected_gain - p_adverse > 0` 缺少效用解释

`expected_gain` 是时间比例收益，`p_adverse` 是事件概率。直接相减隐含“每次 adverse 的损失幅度等于 100%”，但当前没有定义：

- adverse 的平均损失幅度；
- timeout 与 5% slowdown 是否同权；
- memory censor 的代价；
- closure failure 的代价；
- 是否需要风险厌恶系数。

因此该判定不是严格的 expected utility。

## 6.3 incomplete 样本存在选择偏差

当前“两臂都 incomplete 不进入 supervised loss”。这会把最困难、最可能与 proof tail、内存和安全风险相关的 contexts 系统性排除。

特别是 scale50 已经出现到达 boundary 后处理超过 2088 万 labels 并触发 `MEMORY_LIMIT` 的 request。此类 context 不应被当成普通缺失值。

## 6.4 推荐的主目标

预测带符号的 log wall ratio：

\[
y=\log\frac{T_{\text{continue}}}{T_{\text{revert}}}
\]

解释：

- \(y<0\)：continue 更快；
- \(y>0\)：revert 更快；
- log ratio 对长尾更稳定；
- 相对加速与减速在 log 空间更接近对称；
- 可直接形成风险上界决策。

模型输出建议改为：

1. \(\hat\mu_y\)：log ratio 预测均值；
2. \(\hat\sigma_y\)：预测不确定性；
3. \(p_{\text{censor,continue}}\)：continue 导致 timeout/memory/action-induced censor 的概率；
4. 可选辅助头：processed-label ratio、dominance-check ratio、peak-frontier ratio、peak-RSS ratio。

## 6.5 推荐的动作规则

例如使用保守上分位：

\[
q_{0.90}(y)=\hat\mu_y+z_{0.90}\hat\sigma_y
\]

只有同时满足：

\[
q_{0.90}(y)<\log(0.98)
\]

\[
p_{\text{censor,continue}}\le\tau_c
\]

并且：

- 非 OOD；
- ensemble disagreement 低于阈值；
- migration memory preflight 通过；
- remaining wall 足以摊薄 trial；
- request lifecycle 在授权范围内；

才执行 `CONTINUE_QD1`，否则 `REVERT_Q0`。

这意味着：

> 不是预测“平均上可能更快”就继续，而是预测“在保守风险上界下仍有至少 2% 收益”才继续。

## 6.6 四类 arm outcome 的正确语义

| CONTINUE | REVERT | 监督语义 |
|---|---|---|
| complete | complete | 使用真实 log wall ratio |
| complete | incomplete | continue 明确胜出；revert 为右删失/失败 |
| incomplete | complete | continue adverse；进入 censor/risk 监督 |
| incomplete | incomplete | unsafe/abstain/resource-hard；不作为普通无标签样本 |

若实现复杂度允许，可使用 interval-censored regression；若暂不实现，则至少采用：

- complete-complete：回归 `log ratio`；
- one-arm incomplete：作为硬 action/censor 标签；
- both incomplete：进入 unsafe/OOD/resource-risk 数据集，并禁止 production 激活。

## 6.7 区分 pricing request 语义

至少将以下语义显式输入模型：

```text
COLUMN_HARVEST
NO_NEGATIVE_PROOF
```

因为：

- harvest 的目标是尽快形成 usable negative column；
- proof 的目标是完整结束穷举并建立 no-negative 结论；
- 两者对 queue ordering 的偏好可能相反。

如数据支持，应使用 request-type-specific head 或至少加入显式 interaction feature。

---

# 7. P0-4：当前 GAT 容量与独立样本量不匹配

## 7.1 当前参数规模

当前 temporal fusion 为：

```text
1206 -> 128 -> 64
```

并有两个 scale-specific `64 -> 3` heads。

仅 fusion trunk 与两个 heads 的参数量约为：

\[
1206\times128+128+128\times64+64+2(64\times3+3)
=163142
\]

这还没有计算：

- cell graph adapters；
- label-task graph adapters；
- 两层四头 edge-aware GAT；
- query/key/value；
- edge embeddings；
- LayerNorm；
- attention pooling。

实际总参数量更高。

而当前 raw train snapshot 的独立 instance 数只有：

- scale30：33；
- scale50：39。

同一 instance 的多个 contexts 不能等价为多个独立训练样本。

## 7.2 主要风险

模型很可能学习到：

- instance hardness；
- frontier size；
- root-CG round；
- creation-order proxy；
- memory pressure；
- dual magnitude；
- 某些固定 seed/map pattern；

而不是可迁移的 topology-specific temporal response。

## 7.3 当前 temporal representation 的不足

当前跨时点主要使用：

- 同 cell temporal edge；
- sampled surviving label identity edge；
- survival/churn/counter deltas。

但真正决定 QD1 动力学的往往是：

- label mass 从哪个 depth×RC cell 流向哪个 cell；
- 哪些 labels 被 processed；
- 哪些 labels 被 dominance 删除；
- 新 labels 从哪些 parent cell 生成；
- depth、partial RC 与 terminal status 如何联合迁移。

同 cell temporal edge只能表示“同一个 bucket 前后变化多少”，不能完整表达跨 cell 的流动；最多 256-label sample 又可能漏掉全量 churn。

## 7.4 推荐的 full-mass temporal cell-flow graph

构造一个联合时空图：

```text
64 个 t0 cells
64 个 tK cells
BIRTH source
PROCESSED sink
DOMINATED sink
TERMINAL/NEGATIVE sink（可选）
```

跨时点边包括：

1. surviving creation ID：
   \[
   \text{cell}^{t0}_a\rightarrow\text{cell}^{tK}_b
   \]
2. trial 中新生成 labels：
   \[
   \text{BIRTH}\rightarrow\text{cell}^{tK}_b
   \]
3. trial 中被处理 labels：
   \[
   \text{cell}^{t0}_a\rightarrow\text{PROCESSED}
   \]
4. 被 dominance 删除 labels：
   \[
   \text{cell}^{t0}_a\rightarrow\text{DOMINATED}
   \]
5. terminal/negative events：
   \[
   \text{cell}^{t0}_a\rightarrow\text{TERMINAL}
   \]

边特征可包含：

- label count；
- 占 source-cell mass 的比例；
- 平均 depth shift；
- 平均 partial-RC shift；
- parent-child generation count；
- mean/quantile age；
- dominated ratio；
- terminal/negative count；
- mean true-RC delta。

该表示直接回答：

> QD1 trial 将 frontier 质量从什么区域推向了什么区域，并产生了多少有效扩展、支配删除或终止事件。

## 7.5 label-task micrograph 的建议

label-task graph 可以保留为可选第二分支，但应修改：

- task nodes 使用全部 30/50 个任务，而不是只保留与 sampled labels 相关的任务；
- sampled labels 强制覆盖：
  - best partial-RC；
  - deepest；
  - oldest；
  - recently-created；
  - negative-ancestor；
  - high dominance-degree；
  - high dual-gain；
- creation ID 不直接作为跨 request 数值特征，应转换为相对 age、rank 或分位数；
- 明确区分 label identity、parent-child generation 与 task interaction。

## 7.6 模型规模建议

优先使用：

```text
cell-flow encoder: hidden 16 或 24，1–2 层
label-task encoder: hidden 16，可选
fusion: 128–256 -> 64 -> outputs
```

不建议继续同时拼接：

\[
h_0,h_K,h_K-h_0,|h_K-h_0|
\]

可改为：

\[
h_0,\Delta h,|\Delta h|
\]

或直接在联合时空图上进行 message passing。

如果 scale30 移出 selector，模型只服务 scale50，结构可以进一步缩小。

## 7.7 模型晋升原则

- 若独立 train instances 仍少于约 60—80 个，优先使用 Linear/MLP/小型 cell-flow GNN；
- 只有当 topology controls 显示稳定增量，才扩大 message passing；
- 不要用更多参数补偿 observability 不足。

---

# 8. P1-1：K selection 与 grouped CV 存在信息复用

## 8.1 当前问题

当前 train partition 同时用于：

- K selection；
- 5-fold instance-grouped CV；
- final model fit。

即使 grouped CV 按 instance 划分，某个 outer/held-out fold 的三臂 outcome 已经参与全体 train 上的 K 选择。因此 CV 并不真正独立于超参数选择。

## 8.2 推荐修改

### 方案 A：独立 K/action-support partition

```text
K-selection set
Model-training set
Calibration-A
Safety calibration-B
Development
Sealed
```

K 完全由 K-selection set 冻结；model-training set 只使用选定 K。

### 方案 B：Nested grouped CV

每个 outer fold：

1. 仅用 outer-train folds 选 K；
2. 在 outer-train 上训练；
3. 在 outer-test 上评价；
4. 汇总 outer folds。

考虑工程可审计性，优先推荐方案 A。

---

# 9. P1-2：固定绝对 K 不具有跨 context 可比性

当前 K 候选：

```text
128, 512, 2048 pops
```

但不同 context 的 frontier size 可能差异很大。同样 512 pops 可能对应：

- frontier 的 20%；
- frontier 的 1%；
- frontier 的 0.01%。

因此 `t0 -> tK` 不是统一的动态时间尺度。

## 推荐修改

采用 frontier-normalized trial budget：

\[
K=\operatorname{clip}\left(\alpha |F_{t0}|,K_{\min},K_{\max}\right)
\]

其中 \(\alpha\) grid 应由 eligibility 中 frontier-size 分布的分位数反推，并在 outcome 前冻结，而不是主观指定。

至少向模型输入：

- \(K/|F_{t0}|\)；
- 实际完成 pops / K；
- trial wall / 当前 request 剩余 wall budget；
- new labels / initial frontier size；
- processed labels / initial frontier size；
- migration wall / request wall。

若继续保留绝对 K，也必须将上述归一化量作为核心特征，并分层报告不同 frontier-size 区间下的动作支持。

---

# 10. P1-3：缺少 `STAY_Q0` 动作，trial 税成为必付成本

当前策略空间只有：

```text
执行 QD1 trial 后：
    CONTINUE_QD1
    或 REVERT_Q0
```

无法表达：

> 该 context 根本不值得进入 trial，应保持 Q0。

## 10.1 先保留 taxed-oracle gate

当前 taxed oracle gate 是必要的。若即使知道最佳 continue/revert 动作，支付 trial 成本后仍不能相对 Q0 获得足够收益，就不应训练更复杂模型。

## 10.2 若 taxed oracle 不足，改为两阶段策略

```text
阶段一：廉价 pre-trial gate
    STAY_Q0
    或 ENTER_QD1_TRIAL

阶段二：进入 trial 后
    CONTINUE_QD1
    或 REVERT_Q0
```

pre-trial gate 可先使用确定性规则：

- frontier size 超过最低阈值；
- remaining wall 足以摊薄 K；
- memory headroom 足以预留 reverse migration；
- 尚未形成 usable negative；
- request 属于 proof-tail 或 hard-harvest；
- 当前 root-CG round 在训练支持范围内；
- P0V5 prepass 已显示特定困难信号。

该 gate 只排除明显不值得 trial 的 context，不重复旧静态 GAT“仅凭 t0 直接预测最终 continue/revert”的失败路径。

---

# 11. P1-4：reverse migration 的瞬时内存风险

## 11.1 当前风险

当前 QD1→Q0 使用 staging queue：

1. 从 live QD1 queue 构造完整 staging Q0 queue；
2. 验证 size/hash/duplicate/binding；
3. 通过后 swap；
4. 再清理 QD1 container。

正确性上较强，但可能在大 frontier 上产生明显瞬时额外内存与 allocator fragmentation。scale50 已出现 memory-limit request，因此不能把该风险视为次要工程细节。

## 11.2 推荐修改

进入 QD1 trial 前执行 revert workspace preflight：

\[
\text{estimated\_revert\_bytes}
\le
\text{available\_headroom}-\text{fixed\_reserve}
\]

不满足时：

```text
不进入 trial，保持 Q0
```

实现建议：

- label store 始终只有一份；
- queue container 只存 handle/index，不复制 State；
- 使用可复用 contiguous vector；
- drain 后用 `std::make_heap`，避免逐元素 push 的 \(O(|F|\log |F|)\)；
- Q0→QD1 前预留 reverse buffer capacity；
- 内存预留失败时禁止 trial；
- 不在 trial 后才发现无法 revert。

必须新增 telemetry：

```text
migration_forward_wall
migration_reverse_wall
migration_peak_extra_bytes
frontier_size_at_migration
queue_index_bytes
allocator_failure
revert_workspace_reserved
```

---

# 12. P1-5：resource censor 必须区分固有困难与动作新增伤害

当前 K gate 要求 resource censor = 0，但需要区分：

1. Q0 本身也会 timeout/memory 的固有困难 context；
2. QD1 trial、continue 或 migration 新增的 censor。

建议记录：

```text
baseline_q0_censor
continue_additional_censor
revert_additional_censor
migration_induced_censor
peak_rss_delta_vs_q0
```

K gate 应要求：

- correctness redline = 0；
- **相对 Q0 新增的 resource censor = 0**；
- migration-induced censor = 0；
- action-induced peak RSS ratio 不超过阈值；
- 三臂都 incomplete 的 context 进入 unsafe/resource-hard audit，而不是普通监督样本。

这样既不会用 GAT 掩盖 core exact solver 的边界，也不会让原本就失败的 Q0 context 错误否定所有 K。

---

# 13. P1-6：在大规模三臂前增加 addressable-wall/Amdahl gate

Temporal-GAT 当前只作用于：

- scale30/50；
- root-CG；
- P0V5 已进入 P0V4 fallback；
- 授权的 exact pricing request。

它不作用于：

- P0V5 prepass 本身；
- tree pricing；
- RMP；
- branching；
- cut processing；
- 其他生命周期。

因此必须先回答：

> 当前授权 scope 在完整 BPC wall 中占多少？即使局部 oracle 完美，是否理论上可能达到 formal 要求的 5% E2E 改善？

令：

\[
f=\frac{\text{authorized temporal scope wall}}{\text{total BPC wall}}
\]

局部 taxed-oracle ratio 为 \(r_{\text{local}}\)，则最乐观 E2E ratio 约为：

\[
R_{\text{E2E,min}}=(1-f)+fr_{\text{local}}
=1-f(1-r_{\text{local}})
\]

要达到 5% E2E 改善，必须：

\[
f(1-r_{\text{local}})\ge0.05
\]

示例：

| 局部 oracle 改善 | \(r_{local}\) | 所需最小 addressable wall share \(f\) |
|---:|---:|---:|
| 10% | 0.90 | 50% |
| 20% | 0.80 | 25% |
| 30% | 0.70 | 16.7% |

## 必须新增的审计

```text
addressable_wall.audit.json
```

每个 instance 至少包含：

- total BPC wall；
- root-CG wall；
- P0V4 fallback wall；
- authorized temporal scope wall；
- P0V5 wall；
- tree pricing wall；
- RMP/branch/cut wall；
- local oracle lower bound；
- implied best possible E2E ratio。

若理论下界仍大于 0.95，则当前 scope 不可能达到 formal 5% gate。此时应停止训练，转向：

- 扩大合法 action scope；
- 优化 exact SPPRC proof tail；
- 优化 RMP/tree；
- 或下调论文中对 E2E 的预期，而不是继续调 GAT。

还应单独检查 scale50 未闭合实例究竟失败在：

- root fallback；
- tree pricing；
- memory；
- 其他 proof stage。

若 closure failure 大多不在 temporal scope，要求 GAT 增加 scale50 closure 缺少可实现性基础。

---

# 14. P1-7：context selection 与 deployment scope 不一致

当前训练/校准每个 instance 选择最早到达 boundary 的最多三个 root-CG requests。该规则 outcome-blind，这是优点。

但如果 production 允许模型作用于所有 eligible root-CG fallback requests，则后期 requests 可能出现：

- 更强 dual shift；
- 更大 frontier；
- 更高 memory pressure；
- 更接近 proof tail；
- 不同 cut/column context。

这会形成 lifecycle distribution shift。

## 两种修改方式

### 方案 A：限制 deployment scope

模型只允许作用于每个 instance 最早三个 eligible root-CG requests；后续全部 Q0。

### 方案 B：outcome-blind 分层采样

每个 instance 选择：

- first eligible；
- middle eligible；
- late eligible；

或按 Q0 chronology 的 quantile 选择。选择仍禁止使用 QD1 outcome。

优先建议方案 B，因为其覆盖 production 生命周期更完整。

---

# 15. P1-8：将 production track 与 GAT scientific claim track 分开

当前 representation gate 要求：

- GAT BA 严格优于 Linear/MLP/no-message；
- GAT policy utility 严格更好；
- shuffled topology BA 至少下降 0.01；
- 否则整个 round `TERMINATED_NEGATIVE`。

这对“是否能声称 GAT topology 有价值”是合理的，但不应决定“生产求解器应该部署什么策略”。

## 推荐双轨晋升

| 轨道 | 目标 | 可接受候选 |
|---|---|---|
| Solver production track | 找到最安全、最快、可审计的策略 | deterministic、Linear、MLP、GAT |
| GAT scientific claim track | 证明 message passing/topology 有不可替代的增量价值 | 只能是通过 topology controls 的 GAT |

若最终：

- MLP E2E 快 7%；
- 无 harmful；
- portable/exact audit 全部通过；
- GAT 不优于 MLP；

正确结论应是：

> temporal response 有生产价值，但 topology message passing 没有额外价值；production 部署 MLP，论文不得宣称 GAT 增量。

候选名称必须真实反映模型：

```text
FIXED_QD1_SCALE30_V1
TEMPORAL_QD1_MLP_SCALE50_V1
TEMPORAL_QD1_GAT_SCALE50_V1
```

不能为了论文叙事把最佳简单控制器包装成 GAT。

## topology gate 的修改

`shuffled topology BA 下降 0.01` 太弱。建议使用：

- 多个 topology shuffle seeds；
- instance-level paired policy utility；
- 相对 taxed oracle 的 regret；
- harmful tail；
- cluster bootstrap CI；
- development E2E 增量。

BA 只作为诊断指标，不作为主要科学证据。

---

# 16. P1-9：Development 与 sealed 的统计功效不足

当前每尺度：

- development：12 instances；
- sealed：16 instances；
- 每个 instance 3 repeats。

重复实验可以降低同一 instance 的运行噪声，但独立统计单位仍是 instance。

## 16.1 零 harmful 不能等价为低风险

16 个独立 instances 零 harm 时：

\[
1-0.05^{1/16}\approx0.1707
\]

即 95% 上界仍约 17.1%。因此“sealed 中没有 harmful”只能说明该 sealed sample 内零 harmful，不能支持总体 harm rate 很低。

## 16.2 5% GM 改善需要置信区间

建议使用 instance-level log ratio：

\[
z_i=\log\frac{T_{model,i}}{T_{Q0,i}}
\]

并报告：

- mean/median；
- geometric mean；
- cluster bootstrap 95% CI；
- one-sided upper CI；
- censor-aware performance profile；
- completion count；
- harmful count；
- peak RSS ratio。

推荐 production gate 至少要求：

```text
point-estimate GM <= 0.95
且 one-sided 95% upper CI < 1.00
```

若希望更强，可要求 CI upper ≤ 0.98，但这会显著增加样本需求。

Development/sealed 的独立实例数应由预期方差和最小可检测效应通过 pilot power analysis 决定，而不是只沿用 12/16。

---

# 17. P2：OOD 与 topology diagnostics 的改进

## 17.1 OOD 不应只使用 `mean ± 8σ`

对重尾 solver telemetry，`mean ± 8σ` 可能极宽，且易受少量 extreme instances 影响。

建议 per-scale 使用：

- median/MAD；
- empirical quantile envelope；
- robust Mahalanobis；
- calibration-based conformal nonconformity score；
- lifecycle/root-CG round hard scope；
- frontier-size quantile scope。

OOD 只能作为 abstention veto，不能被解释为安全保证。

## 17.2 topology value 应以 policy-level 结果为主

至少执行：

- no-message；
- edge-feature zeroing；
- topology shuffle，多 seed；
- temporal-edge removal；
- cell-flow removal；
- label-task branch removal；
- counters-only MLP。

比较指标优先级：

1. E2E paired utility；
2. harmful/censor；
3. oracle regret；
4. activation coverage；
5. calibration quality；
6. BA/AUC。

---

# 18. P0-5：论文正文必须与真实 Temporal-GAT 同步重写

当前论文第 4.6 节描述的是：

- GAT 为每个 label 生成局部优先分数；
- 只在相同基地返回状态和相同 partial-RC bucket 内重排；
- 监督来自 accepted negative columns 与 no-negative proof contribution；
- 动作粒度是 label ordering。

当前真实计划是：

- 先使用 Q0 到 boundary；
- 完整 frontier 迁移到 QD1；
- 运行 K 次真实 QD1 pops；
- 使用 t0/tK temporal graph；
- 对整个 pricing request 决定 `CONTINUE_QD1 / REVERT_Q0`；
- 动作粒度是 comparator policy selection。

两者不是小修，而是在以下方面都不同：

| 维度 | 当前论文 | 当前真实计划 |
|---|---|---|
| 动作粒度 | 单 label 局部排序 | 单 pricing request 的 comparator policy |
| 输入 | 静态任务图与 label 状态 | 双时点、多分辨率 temporal response |
| 输出 | label priority score | continue/revert action |
| 监督 | accepted/proof-contribution | counterfactual arm wall/censor |
| exact-safe 论证 | 同 bucket 内重排 | 完整 frontier migration + comparator conservation |
| 适用范围 | 泛化写成穷举定价内部 | root-CG P0V4 fallback 的授权 requests |

## 必须重写的部分

- 摘要中的 GAT 描述；
- 引言中的算法贡献；
- Algorithm 1 的定价流程；
- 第 4.6 节全部内容；
- 原式（27）—（30）；
- exactness 引理中学习接口描述；
- RQ3、RQ4；
- comparison methods；
- 学习数据与激活条件；
- 结果指标；
- 讨论中的适用范围。

最终建议名称：

> **temporal-response-based proof-queue policy selection**

不要继续写成：

> GAT directly prioritizes individual labels.

如果 GAT 最终未超过 MLP/no-message，论文应诚实改为 temporal controller，而不是保留 GAT 作为主贡献。

---

# 19. 推荐的 revised production architecture

```text
P0V5 bidirectional witness/prepass
        |
        v
P0V4 exact fallback with literal Q0
        |
        +---- hard scope / lifecycle gate
        |
        +---- addressable-wall gate
        |
        +---- remaining-wall gate
        |
        +---- reverse-memory reservation gate
        |             |
        |             +-- 失败：保持 Q0
        |
        v
scale30
        |
        +-- frozen boundary 后 deterministic QD1
        |   只在 fresh E2E + formal 证明稳定收益后启用
        |
scale50
        |
        +-- normalized QD1 trial
                |
                +-- full-mass temporal cell-flow graph
                +-- all-task / optional label-task graph
                +-- counters + request semantics
                |
                v
        predict:
            signed log wall ratio
            uncertainty
            continue censor risk
                |
                +-- risk upper bound 通过：CONTINUE_QD1
                |
                +-- 否则：REVERT_Q0
```

可选两阶段扩展：

```text
pre-trial deterministic gate:
    STAY_Q0 / ENTER_TRIAL

post-trial model:
    CONTINUE_QD1 / REVERT_Q0
```

---

# 20. 推荐的数据与实验分区

## 20.1 scale30

scale30 不进入 GAT selector 训练，使用：

```text
deterministic-policy pilot
fresh development
sealed final
formal acceptance
```

重点验证：

- boundary 后 always-continue 的 E2E GM；
- harmful tail；
- resource censor；
- peak RSS；
- formal small-scale 不退化；
- 是否稳定兑现历史收益。

## 20.2 scale50

建议分区：

```text
Eligibility / observability cohort
K-selection / action-support set
Model-training set
Calibration-A
Independent Safety-B
Development E2E
Sealed final
Formal acceptance
```

### 最小容量原则

- K-selection：足够覆盖 continue/revert/strong-benefit，且按独立 instance 计数；
- Model-training：若少于 60—80 个独立 instances，则缩小模型或使用简单控制器；
- Safety-B：按 \(\lceil29/c\rceil\) 公式确定；
- Development/sealed：基于 pilot log-ratio 方差做 power analysis；
- 同一 instance 产生的所有 contexts 必须留在同一 partition。

---

# 21. 推荐的新 gate 顺序

## Gate 0：Exact-safe implementation

- disabled-Q0 differential mismatch = 0；
- migration conservation = PASS；
- fault injection = PASS；
- portable parity = PASS；
- runtime binding fail-closed = PASS。

## Gate 1：Independent capacity

- 按独立 instance，不按 context rows；
- 每个 partition 的有效独立实例数达到要求；
- 不通过则停止，不靠增加同-instance contexts 补数。

## Gate 2：Addressable wall

- 当前 action scope 理论上能够达到目标 E2E；
- closure failure 确实在授权 scope 内具有可改善空间。

## Gate 3：Migration/resource feasibility

- reverse workspace 可预留；
- action-induced resource censor = 0；
- migration overhead 在预算内。

## Gate 4：K/action support

- taxed oracle vs Q0 有足够收益；
- revert tax 通过；
- scale50 continue/revert/strong-benefit 支持满足要求；
- scale30 不再要求双动作支持。

## Gate 5：Observability

先用 counters-only Linear/MLP 判断 t0→tK response 是否可预测。若简单模型都无信号，停止 GAT。

## Gate 6：Topology value

只有 GAT 相对 no-message/MLP/shuffled topology 在 instance-level utility 上有稳定增量，才允许 GAT scientific claim。

## Gate 7：Calibration-A

- calibration；
- threshold selection；
- OOD 参数；
- action rule 全部冻结。

## Gate 8：Safety-B

- 独立 instances；
- policy 完全冻结；
- instance-level harm；
- 不允许回调阈值。

## Gate 9：Development E2E

- point estimate；
- one-sided CI；
- harmful/censor；
- peak RSS；
- completion；
- 相对 deterministic/simple best control。

## Gate 10：Sealed

- 不揭盲修改；
- 完整重复 development gates。

## Gate 11：Formal acceptance

- scale5/10/20/30 不退化；
- scale50 closure 与 exact semantics；
- production track 与 GAT claim track 分开判定。

## Gate 12：Canary/activation/rollback

- immutable candidate；
- canary；
- monitoring；
- `no_cut` 一键 rollback。

---

# 22. Round 5 当前应当怎么处理

## 22.1 立即动作

1. **让当前 274 个 eligibility replay 完整结束。**
2. 不中断当前活动进程；不并发启动三臂；不修改冻结 config、corpus、context 规则或 gate。
3. eligibility 完成后，先生成以下四份 outcome-independent 审计：

```text
independent_sample_capacity.audit.json
addressable_wall.audit.json
migration_resource.audit.json
calibration_feasibility.audit.json
```

## 22.2 在四项审计前不要自动启动大规模三臂

当前 raw train snapshot 上限对应最多约 5724 个 fresh-process train tasks。若：

- calibration 统计合同本身不可成立；
- addressable wall 不足；
- scale30 selector 逻辑错误；
- reverse memory 无法预留；

则直接跑完这些任务只会增加计算成本，不会形成合法 production 证据。

## 22.3 Round 5 的合理定位

Round 5 已完成的内容并未浪费：

- temporal Native modes；
- bidirectional migration；
- conservation audit；
- temporal graph；
- telemetry；
- source/corpus freeze；
- root collection；
- eligibility pipeline。

建议将其正式定位为：

> **Temporal trial infrastructure and action-support pilot**

而不是最终 production promotion round。

## 22.4 哪些修改必须进入新 Round

由于 Round 5 已冻结 architecture、split、threshold、gate 和 source contract，以下实质性修改必须进入新 experiment ID、新 corpus、新 partitions：

- scale30 deterministic / scale50 selector 分离；
- K-selection 独立；
- Calibration-A / Safety-B 分离；
- instance-level harm accounting；
- signed log-ratio + censor target；
- smaller temporal cell-flow model；
- addressable-wall gate；
- migration memory reservation；
- revised development/sealed CI；
- production/scientific dual track；
- manuscript同步。

---

# 23. 建议的代码修改清单

## 23.1 Native pricing core

文件：

```text
native/lunar_spprc/include/lunar_spprc/native_pricer.hpp
native/lunar_spprc/src/native_pricer.cpp
```

修改：

- [ ] 增加 `STAY_Q0`/pre-trial eligibility 状态；
- [ ] 增加 normalized K 或 K/frontier ratio telemetry；
- [ ] 增加 reverse workspace estimation/reservation；
- [ ] 使用 reusable contiguous queue buffer；
- [ ] reverse heap 使用 `make_heap`；
- [ ] 区分 baseline/action-induced resource censor；
- [ ] 暴露 `COLUMN_HARVEST` / `NO_NEGATIVE_PROOF` request semantics；
- [ ] 记录 full-mass cell-flow transition；
- [ ] 记录 processed/dominated/birth/terminal sinks；
- [ ] 记录 migration peak extra bytes；
- [ ] trial 前确认 bundle、schema、memory 与 lifecycle 全部合法。

## 23.2 Pybind telemetry

文件：

```text
native/lunar_spprc/src/pybind_module.cpp
```

修改：

- [ ] 暴露 cell-flow matrix；
- [ ] 暴露 action-induced censor tags；
- [ ] 暴露 migration memory；
- [ ] 暴露 request semantics；
- [ ] 暴露 normalized K metrics；
- [ ] 保持 canonical telemetry hash。

## 23.3 模型定义

文件：

```text
src/lunar_ice_bpc/guidance/temporal_frontier_gat_v1.py
```

建议新建版本，而不是覆盖旧合同：

```text
temporal_frontier_controller_v2.py
```

修改：

- [ ] scale30 移出 selector；
- [ ] cell-flow joint temporal graph；
- [ ] smaller hidden width；
- [ ] 输出 `mu_log_ratio`、`sigma_log_ratio`、`p_continue_censor`；
- [ ] request-type embedding；
- [ ] 可选 label-task branch；
- [ ] 删除冗余 1206 维拼接；
- [ ] 统一 instance-balanced/censor-aware loss。

## 23.4 Runtime

文件：

```text
src/lunar_ice_bpc/guidance/temporal_frontier_gat_runtime_v1.py
```

建议新建：

```text
temporal_frontier_controller_runtime_v2.py
```

修改：

- [ ] risk-upper-bound action rule；
- [ ] scale30 deterministic policy；
- [ ] Safety-B binding；
- [ ] robust OOD；
- [ ] memory preflight；
- [ ] fail-closed action reason telemetry；
- [ ] production/scientific candidate identity 分离。

## 23.5 Dataset builder

文件：

```text
scripts/build_p0v5_temporal_gat_dataset_v1.py
```

修改：

- [ ] instance-level partition/group；
- [ ] complete/incomplete 四状态；
- [ ] interval/right-censor 字段；
- [ ] request semantics；
- [ ] cell-flow edges；
- [ ] 禁止把同-instance contexts 分到不同 split；
- [ ] 标注 baseline vs action-induced censor。

## 23.6 K selection

文件：

```text
scripts/select_p0v5_temporal_gat_trial_k_v1.py
```

修改：

- [ ] 仅使用独立 K-selection partition；
- [ ] 先执行 addressable-wall gate；
- [ ] 按 instance 聚合；
- [ ] 报告 normalized trial intensity；
- [ ] 区分固有 resource-hard 与 action-induced censor；
- [ ] scale30 不再做双动作 K gate；
- [ ] 生成 action-support decision，而非直接进入 GAT。

## 23.7 Training/calibration

文件：

```text
scripts/train_p0v5_temporal_gat_production_v1.py
```

建议新建 v2：

- [ ] Calibration-A 与 Safety-B 分离；
- [ ] threshold selection 与 safety validation 不共用 outcomes；
- [ ] censored loss；
- [ ] nested/independent K；
- [ ] production track 与 GAT claim track 分开；
- [ ] cluster bootstrap；
- [ ] multiple topology shuffle seeds；
- [ ] oracle regret；
- [ ] model size/parameter count audit。

## 23.8 Full BPC / formal acceptance

文件：

```text
scripts/run_p0v5_temporal_gat_full_bpc_v1.py
scripts/run_p0v5_temporal_gat_formal_acceptance_v1.py
```

修改：

- [ ] instance-level paired log-ratio CI；
- [ ] completion/censor-aware summary；
- [ ] addressable wall telemetry；
- [ ] scale30 deterministic arm；
- [ ] scale50 best simple controller arm；
- [ ] GAT incremental arm；
- [ ] separate production decision and scientific-claim decision；
- [ ] harmful upper bound 按独立 instance 报告。

---

# 24. 建议的新 Round 合同草案

```text
experiment_id: p0v5_temporal_controller_production_v2_round6_<date>

production_default: no_cut

scale30_policy:
  boundary: frozen_from_fresh_pilot
  action: deterministic_qd1_continue
  learned_selector: false

scale50_policy:
  pretrial_gate: deterministic
  trial_budget: frontier_normalized
  actions:
    - stay_q0
    - continue_qd1
    - revert_q0

partitions:
  k_selection: independent_instances
  model_train: independent_instances
  calibration_a: independent_instances
  safety_b: independent_instances
  development: independent_instances
  sealed: independent_instances

safety_statistics:
  unit: instance
  threshold_selected_on: calibration_a
  harm_validated_on: safety_b
  target_upper_bound: 0.10
  confidence: 0.95

model_target:
  primary: signed_log_wall_ratio
  uncertainty: enabled
  censor_risk: enabled

promotion_tracks:
  solver_production: best_verified_controller
  gat_scientific_claim: topology_increment_required
```

所有字段必须在任何 queue outcome 前冻结。

---

# 25. 决策树

```text
Eligibility 完成
    |
    +-- 独立 capacity 不足
    |       -> Round 5 terminal/pilot closeout
    |
    +-- capacity 足够
            |
            +-- addressable wall 无法达到 5% E2E
            |       -> 停止当前 scope 的 GAT promotion
            |
            +-- addressable wall 足够
                    |
                    +-- migration/revert resource 不可控
                    |       -> 先修 core，不跑三臂
                    |
                    +-- resource 可控
                            |
                            +-- taxed oracle 无收益
                            |       -> 不训练 controller
                            |
                            +-- taxed oracle 有收益
                                    |
                                    +-- simple temporal controller 无信号
                                    |       -> observability negative
                                    |
                                    +-- simple controller 有信号
                                            |
                                            +-- GAT 不优于 MLP/no-message
                                            |       -> production 可选 MLP
                                            |       -> GAT scientific claim negative
                                            |
                                            +-- GAT 有稳定增量
                                                    -> Calibration-A
                                                    -> Safety-B
                                                    -> Development
                                                    -> Sealed
                                                    -> Formal
                                                    -> Canary/Activation
```

---

# 26. 建议的执行优先级

## 第一优先级：不花额外大规模算力即可完成

1. 完成当前 eligibility；
2. independent capacity audit；
3. addressable-wall audit；
4. calibration feasibility audit；
5. migration resource audit；
6. scale30/scale50 问题分治决策；
7. Round 5 pilot/terminal 定位。

## 第二优先级：新 Round 前完成设计冻结

1. revised action space；
2. K-selection split；
3. Calibration-A/Safety-B；
4. signed log-ratio/censor target；
5. smaller cell-flow architecture；
6. production/scientific dual track；
7. manuscript algorithm rewrite outline。

## 第三优先级：代码与小规模 differential

1. migration memory reservation；
2. new telemetry；
3. model/runtime v2；
4. portable parity；
5. synthetic/fault tests；
6. small pilot power/variance estimate。

## 第四优先级：大规模 fresh experiments

只有前述 gates 全部成立后，才启动：

- K/action-support；
- model training；
- Calibration-A；
- Safety-B；
- development；
- sealed；
- formal acceptance。

---

# 27. 最终结论

当前方案最有价值的部分不是“更大的 GAT”，而是将学习动作重新定义为：

> 在一个 exact-safe pricing request 内，观察真实 QD1 短响应后，对当前 frontier 的 comparator policy 作可撤销选择。

这个问题定义是成立的，exact-safe 外壳和实验冻结也做得较好。但当前 Round 5 的 calibration 统计、尺度统一、监督目标、模型容量和 promotion 证据仍存在结构性缺陷。

因此，最合理的判断是：

1. **保留 Temporal trial 与双向 migration 基础设施；**
2. **让 Round 5 eligibility 完整结束；**
3. **在启动大规模三臂前增加独立样本、addressable wall、migration resource 和 calibration feasibility 审计；**
4. **将 scale30 改为 deterministic QD1 验证，将 Temporal controller 聚焦 scale50；**
5. **将目标改为带不确定性的 signed log wall ratio 与 censor risk；**
6. **缩小模型并使用 full-mass temporal cell-flow representation；**
7. **将 threshold selection 与 safety validation 分离，并以独立 instance 为统计单位；**
8. **将 solver production track 与 GAT scientific claim track 分离；**
9. **在新的 experiment round 中冻结并执行实质性修改；**
10. **同步重写论文中 GAT 的动作粒度、输入、监督、算法流程和 exactness 论证。**

在这些修改完成前，Round 5 更适合作为 **Temporal trial infrastructure and action-support pilot**，不适合作为最终 production promotion round。
