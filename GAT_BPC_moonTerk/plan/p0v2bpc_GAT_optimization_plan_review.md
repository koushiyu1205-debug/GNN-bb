# 基于 P0 V2 的跨规模 GAT 性能优化计划评审意见

**评审日期：** 2026-07-23  
**评审对象：**《基于 P0 V2 的跨规模 GAT 性能优化实施计划》  
**当前基准口径：** `p0v2bpc` / `FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`

---

## 1. 执行摘要

这份计划的核心方向是正确的：它没有让 GAT 参与可行性判断、精确剪枝或证书签发，而是把学习模块严格限制在任务、arc、label queue、harvest 和 Ryan–Foster 候选的**排序层**。只要“排序不改变候选宇宙、不永久删除合法状态、最终证书仍由真实对偶下的穷尽式 Native exact pricing 产生”这一契约得到严格执行，GAT 可以作为 exact BPC 的安全性能增强层。

计划最强的部分包括：

- 以 P0 V2 作为唯一实验 control，而不把它误写成当前 production default；
- 禁止 learned pruning、learned bound、提前 no-negative 和候选删除；
- exact 包与 Torch/GAT 实现隔离；
- 对 50/100 的 timeout、memory kill 和未探索区域使用 censored 语义；
- 将现有 full80 原则上锁定为最终未见测试；
- 采用 shadow、逐层在线消融和正式 cold-start promotion 的晋级路径。

但该方案原样执行仍有几个关键问题：

1. “全部合法 Ryan–Foster pairs”会改变 P0 的候选宇宙，导致 GAT 收益与候选扩展收益混淆；
2. full80 被声明为最终测试，但 scale30 的 012、018 又被用作开发门槛，构成测试泄漏；
3. “candidate/label 集合必须与 P0 完全一致”不是正确的安全不变量，会与排序优化目标冲突；
4. branch 标签公式的方向与文字定义相反，incomplete probe 也不应使用简单固定罚项；
5. 小规模只测单次 forward 延迟，无法覆盖 fresh-runtime 下 Torch 导入、checkpoint 加载和多次推理的真实开销；
6. Guidance binding 不应再造一套与 exact request 平行的 hash 体系；
7. 在新增 GAT static tensor cache 前，应先修复 `LunarIceData` 的浅层不可变和 stale cache 风险。

因此，这份文档适合作为**长期研究路线图**，但不适合原样成为第一轮开发任务。建议第一版只落地：

> **统一 binding + snapshot replay + pricing/harvest ordering + shadow 评估。**

proof queue、branch counterfactual、50/100 survival/OOD 和正式六规模 promotion 应依次展开，而不是同时成为首版阻塞项。

---

## 2. 综合评分

| 维度 | 评分 | 评价 |
|---|---:|---|
| 精确性与证书安全 | 9.5/10 | 安全边界定义非常清楚，方向正确 |
| 总体架构 | 8.5/10 | exact/learning 隔离合理，接口意识较强 |
| 数据与实验设计 | 7.5/10 | 有 censored、shadow、holdout 意识，但存在泄漏和样本量问题 |
| 统计严谨性 | 7/10 | 有 paired、CI、worst-scale，但验证集与多重选择需加强 |
| 首轮工程可执行性 | 6/10 | 一次包含过多基础设施、模型、求解器和实验工作 |
| 长期研究价值 | 8.5/10 | 可以形成有说服力的 exact-safe learning-to-order 框架 |
| 作为下一次提交计划 | 6.5/10 | 需要拆分为多个明确的里程碑 |

---

## 3. 应保留的核心设计

### 3.1 GAT 只改变顺序，不改变数学问题

以下约束应保留为不可突破的红线：

- 不删除合法 arc；
- 不永久删除 label；
- 不改变 feasibility、dominance、completion-bound 的数学条件；
- 不使用 learned lower bound；
- 不由 GAT 宣称 no-negative；
- 不在 branch 阶段省略 `same` 或 `different` child；
- 不改变 RMP、cut coefficient、真实对偶和 reduced-cost 公式；
- 推理超时、OOD、NaN、schema/checkpoint/binding 失配时整包回退 P0；
- 只有 Native exact search 的穷尽状态和现有 certificate gate 能产生正式证书。

这应形成一个可测试的总原则：

```text
Guidance may reorder exact work; it may not remove exact work.
```

### 3.2 exact 包与学习包隔离

在 exact 包中仅放置不依赖 Torch 的 frozen dataclass，是正确的架构方向。建议继续坚持：

- exact 包不得导入 Torch、checkpoint、GAT 或 OOD 实现；
- exact 侧只接受已经验证过的只读排序 hints；
- guidance 关闭时执行路径与 P0 完全相同；
- 学习模块失败不得改变 exact backend 的状态机和返回语义。

### 3.3 50/100 使用 censored 与 shadow 语义

以下设计是正确的：

- hard kill 前未探索区域不能标成 nonnegative；
- `MEMORY_LIMIT` 不是“无负列”标签；
- bounded run 只能提供 observed best RC、first-negative time、frontier/RSS/survival 等部分信息；
- 50/100 在 exact closure 前只能证明排序信号、安全迁移和资源行为；
- 不得将 induced subgraph 标签冒充完整 BPC 性能标签；
- 没有真实 branch tree 时，不伪造 50/100 的 downstream branch 标签。

### 3.4 full80 不参与训练

现有 full80 应排除在以下全部过程之外：

- 有监督训练；
- 自监督预训练；
- normalization 拟合；
- OOD 阈值校准；
- queue policy 选择；
- loss 权重与超参数选择；
- checkpoint 选择；
- early stopping。

只要模型对最终 test graph 做过有梯度的自监督预训练，该评估就不再是严格 inductive holdout。

---

## 4. 必须修改的关键问题

## 4.1 Ryan–Foster 全候选枚举会混淆真实贡献

计划提出：

> 先枚举全部合法 fractional Ryan–Foster pairs，不再使用当前 deterministic top-3 作为候选宇宙。

这不是纯粹的 GAT 排序接入。它本身改变了 P0 的 branch candidate universe，并可能改变：

- 选中的 pair；
- 树形；
- 子节点难度和平衡；
- 树节点数量；
- 总时间和长尾。

如果只比较 B2 与原始 B0，就无法判断收益来自：

1. 扩大候选集合；
2. GAT 排序。

应新增控制组：

| 模式 | 候选宇宙 | 排序 |
|---|---|---|
| B0 | 当前 P0 shortlist/top-3 | 当前 deterministic |
| B0U | 全部合法 pairs | deterministic |
| B2 | 全部合法 pairs | GAT |
| B3 | GAT pricing | GAT branch |

真实的 branch-learning 增益应使用：

```text
B2 vs B0U
```

最终系统级收益仍可以使用：

```text
B2/B3 vs B0
```

但报告必须把“universe expansion”和“learned ranking”分开披露。

更保守的首版方案是：

- 全部合法 pairs 只用于离线 counterfactual 数据采集；
- 在线首版仍只重排当前 shortlist；
- 全候选在线启用留到独立消融通过之后。

---

## 4.2 full80 与 scale30 012/018 门槛存在测试泄漏

计划前面写：

> 现有每规模 20 个 benchmark 全部锁定为最终测试。

后面又要求：

> scale30 既有长尾例 012、018 不得超过 B0 的 1.05 倍。

只要 012、018 被用于：

- queue policy 选择；
- checkpoint 选择；
- 模型淘汰；
- G4–G6 晋级；
- 超参数调整；

它们就已经是开发集，而不是最终未见测试集。

必须二选一：

### 方案 A：将 012、018 明确改为已知长尾回归集

```text
known_tail_regression_suite = {scale30/012, scale30/018}
```

随后补充新的 hidden scale30 test instances，维持最终测试集的独立性。

### 方案 B：保留 full80 全部未见

不得在正式测试前单独查看 012、018；另行生成新的长尾 regression instances 供 G3–G6 使用。

不能同时宣称 full80 完全锁定，又用其中具体实例做研发门槛。

---

## 4.3 “candidate/label 集合与 P0 完全一致”不是正确不变量

计划要求：

- candidate set preservation 100%；
- candidate、arc、label、branch pair 集合排序前后完全一致；
- 全规模候选集合与 P0 一致。

其中，**排序前的合法 action/arc/pair 宇宙**可以要求一致；但最终：

- explored label 集合；
- retained frontier；
- harvested negative columns；
- task-set representatives；

不应要求与 P0 完全一致。

原因是排序会改变到达顺序，而 dominance 和有限 harvest budget 会自然导致：

- 某些 label 更早被支配；
- 某些中间 label 不进入 retained queue；
- 在固定时间或固定 harvest target 下返回不同负列；
- 更早发现 addable/useful negative。

这正是排序优化的目标。若要求最终候选集合完全一致，GAT 的主要作用将被取消。

建议将安全不变量改为：

```text
guidance_filter_count == 0
guidance_arc_drop_count == 0
guidance_label_drop_count == 0
guidance_branch_pair_drop_count == 0
legal_action_universe_hash_before_sort 一致
legal_branch_pair_universe_hash_before_sort 一致
exact objective 一致
exact global minimum / proved threshold 语义一致
certificate blockers == 0
labels_dropped == false
```

harvest 模式应比较：

- equal-time / equal-label-budget addable-negative recall；
- time-to-first-addable-negative；
- best RC trajectory；
- duplicate rate；
- RMP bound gain；
- downstream proof-tail。

而不是要求 harvested column 集合与 P0 相同。

---

## 4.4 Branch 标签的方向写反了

原计划定义：

```text
log1p(left_work + right_work)
+ 0.5 * log1p(max_child_work)
+ 0.25 * normalized_imbalance
+ 2.0 * incomplete_indicator
```

随后又写：

> 分数越高表示预计下游工作越少。

这两者相反。上式越高表示：

- 总工作越多；
- 最难 child 越重；
- 越不平衡；
- 出现 incomplete。

应明确选择一种定义：

```text
branch_cost = 上述公式
选择 branch_cost 最小者
```

或者：

```text
branch_utility = -branch_cost
选择 branch_utility 最大者
```

### incomplete 不应只加固定罚项

bounded probe 未闭合时，只知道：

```text
true_work >= observed_work
```

它是右删失数据，不是“真实工作 = observed + 2”。固定 `2.0 * incomplete_indicator` 可能把最困难的 pair 压缩成一个任意有限成本。

更安全的方法：

- complete probe：使用完整 work；
- incomplete probe：记录 observed lower bound 与 censoring time；
- 用 censored survival/ranking loss；
- 只有 A 的可信上界小于 B 的可信下界时，才形成强 pairwise 排序；
- 其余比较赋较低权重或标记不确定。

---

## 4.5 小规模推理开销不能只测一次 forward

scale5/10 的 P0 总时间很短。即使模型 forward 本身只有几毫秒，fresh-runtime promotion 中还包含：

- `import torch`；
- checkpoint 读取与反序列化；
- normalization/OOD 状态加载；
- graph tensor 构造；
- cache miss；
- 每次 RMP 后的多次 inference；
- hints 绑定验证；
- Python→Native 数据安装；
- allocator 和线程池初始化。

因此必须记录完整开销：

```text
guidance_import_sec
guidance_checkpoint_load_sec
guidance_tensorize_sec
guidance_forward_total_sec
guidance_call_count
guidance_binding_validation_sec
guidance_native_install_sec
guidance_total_wall_sec
guidance_total_wall / baseline_total_wall
```

### 自动回退必须发生在推理前

如果 scale5/10 先加载模型并运行 inference，再决定回退 Q0，开销已经发生，无法防退化。

建议使用：

- 一个共享 checkpoint；
- 一个冻结的 deployment gate；
- 未通过 promotion 的规模在入口直接 bypass guidance；
- bypass 路径不导入 Torch、不加载 checkpoint、不构图。

这仍然满足“一个共享 checkpoint”，但部署策略应允许：

```text
checkpoint_available_but_guidance_bypassed
```

---

## 4.6 Guidance binding 应复用 exact request 的 canonical binding

当前 exact backend 已经拥有：

- instance hash；
- config hash；
- signed true-dual binding；
- branch context hash；
- cut context/hash；
- cut lineage hash；
- live-cut policy hash；
- RMP iteration；
- objective mode；
- cut-state schema；
- separator policy。

不应再独立实现一套相似但不完全相同的 guidance hash 规则。

建议：

```python
GuidanceContextBinding.from_backend_request(request)
```

由一个唯一 canonical serializer 同时生成：

- exact backend binding；
- guidance request binding；
- Native request binding；
- replay snapshot binding。

否则容易因为以下差异产生错误失配或错误接受：

- map 顺序；
- cut 排序；
- float 文本格式；
- `+0.0` 与 `-0.0`；
- JSON serializer 版本；
- 缺失字段默认值。

对于 signed zero，建议区分：

- **数学 binding：** 将 `+0.0` 和 `-0.0` 规范化为 `0.0`；
- **诊断 raw hash：** 可额外保留 IEEE 原始表示。

因为 exact zero-dual projection 在数学上会同时投影 `+0.0` 和 `-0.0`。

---

## 4.7 新增 GAT tensor cache 前必须先修复数据不可变性

`LunarIceData` 虽然是 frozen dataclass，但内部 `tasks`、`arcs`、`reference_solution` 仍是可变容器。若现有 instance/static payload cache 和未来 GAT tensor cache 都以对象 ID 或旧 instance hash 为键，内部原地修改可能造成：

- Python exact 路径读取新数据；
- Native static payload 仍是旧数据；
- GAT graph tensor 仍是旧数据；
- instance hash 仍然不变；
- binding 表面却一致。

因此 G0 应先完成：

1. `LunarIceData` 深度不可变；
2. `tasks`、`arcs` 转为 immutable mapping；
3. canonical instance/content hash 在构造时固定；
4. Native static cache 和 GAT tensor cache 都以该 content hash 为键；
5. 添加 mutation-rejected 回归测试；
6. 禁止任何运行时代码原地修改 instance graph。

---

## 5. 数据与训练设计的修订建议

## 5.1 Validation 数量偏少

每规模 8 个 validation instances，同时承担：

- early stopping；
- checkpoint 选择；
- loss 权重选择；
- queue policy 选择；
- OOD 阈值校准；
- worst-scale 指标；
- 三个训练 seed 的选择；

统计上不够稳定。50/100 仅 4 个 validation instances 更容易被单例支配。

建议至少采取以下措施之一：

- 增加 validation 数；
- 使用 grouped cross-validation；
- 另建 calibration split；
- checkpoint validation 与 OOD calibration 分离；
- 使用 validation bootstrap 下置信界，而不是单点 worst-scale；
- 最终只在独立 test 上做一次不可逆评估。

## 5.2 不建议按连续编号切分 50/100

`001–008 / 009–012 / 013–020` 可能与生成顺序、seed family 或参数块相关。

建议：

- 先按 instance content hash 固定分桶；
- 再按时间窗模式、任务模式、热点类型等分层；
- 保存 split manifest 和 seed-family audit。

## 5.3 六规模最低 15% 权重不适合所有 head

六个规模各至少 15%，最低总和已经达到 90%。更重要的是，不同 head 的可信监督范围不同：

| Head | 建议使用的规模 |
|---|---|
| exact pricing ranking | 5/10/20/30 |
| addability/harvest | 5/10/20/30，加少量 50/100 observed data |
| proof-tail/survival | 5–100 |
| branch ranking | 首轮主要 5–30 |
| OOD/scale consistency | 5–100 |

不应强迫 50/100 的低保真 censored 信号在每个 head 中占 30%。建议按 head 独立设置 scale sampler 和最低权重。

## 5.4 2/4/8 GiB 数据必须把预算作为输入

同一 graph/context 在不同 memory/time budget 下会产生不同的 observed best RC、frontier、RSS 和 censoring。若输入中没有 budget，同一输入会对应冲突标签。

proof-risk/survival head 应显式输入：

```text
log1p(memory_limit_bytes)
log1p(wall_time_budget)
queue_policy_id
exact/harvest mode
```

也可以为固定预算建立条件化 target，但不能忽略 budget。

## 5.5 固定 loss 权重需要梯度诊断

以下 loss 的数值尺度不同：

- listwise ranking；
- BCE；
- survival；
- branch ranking；
- consistency。

在采用固定权重前，应记录：

- 每个 head 的原始 loss 范围；
- encoder/head gradient norm；
- 不同任务间的 gradient cosine similarity；
- 每个规模对共享 encoder 的梯度贡献。

如出现负迁移，可采用：

- capped GradNorm；
- uncertainty weighting；
- PCGrad；
- 分阶段训练；
- 先冻结 encoder，再训练 head。

## 5.6 模型结构不应过早锁死

`3 层 × hidden 64 × 4 heads` 可以作为候选，但不应在验证 MLP/小 GAT 前成为硬约束。

首轮应比较：

- linear；
- 小型 MLP；
- 1 层 32 维 attention；
- 2 层 32 维 2-head；
- 3 层 64 维 4-head。

小规模性能的主要成本可能是 Python/Torch dispatch，而非参数量。若 MLP 已能达到相同排序收益，应优先部署更小模型。

---

## 6. Native queue 与 branch 接入的补充要求

## 6.1 Queue key 建议使用字典序 tuple

不要把 partial RC、heuristic lower-key 和 GAT score 通过随意加权相加，因为不同量纲会使安全行为难以审计。

建议每个 Q policy 定义为明确的 lexicographic key，例如：

```text
Q1 = (partial_rc, -guidance_score, stable_tie_key)
Q2 = (heuristic_completion_key, partial_rc, -guidance_score, stable_tie_key)
```

其中所谓 `completion lower-key` 若不是数学下界，应改名为：

```text
heuristic_completion_priority
```

避免在文档和证书中被误解为可认证 bound。

## 6.2 Stable label ID 的定义需要明确

若 label ID 只是创建序号，改变 expansion 顺序后 ID 也会改变。它只能保证同一策略下确定性，不能保证跨策略稳定。

建议：

- 仅用于运行内 tie-break：命名为 `creation_sequence_id`；
- 需要跨策略 replay 对齐：使用 canonical state/path signature 或稳定 hash。

## 6.3 Pair head 的对称性不能只靠 pair ID

排序后的 pair ID 只能保证索引规范化。模型输入也必须对称，例如：

```text
h_i + h_j
abs(h_i - h_j)
h_i * h_j
global_graph_embedding
pair_fractionality_features
```

不要直接使用有方向的 `[h_i, h_j]` 拼接，否则仍可能出现：

```text
score(i, j) != score(j, i)
```

---

## 7. 消融设计需要细化

当前 B0/B1/B2/B3 将所有 pricing guidance 合并为一个开关，无法识别真实收益来源。

筛选阶段建议使用：

| 模式 | Harvest | Task/Arc | Proof Queue | Branch |
|---|---:|---:|---:|---:|
| P0 | 关 | 关 | Q0 | 关 |
| H | 开 | 关 | Q0 | 关 |
| HA | 开 | 开 | Q0 | 关 |
| HAQ | 开 | 开 | GAT/Q1–Q4 | 关 |
| R | 关 | 关 | Q0 | 开 |
| HAQ+R | 开 | 开 | GAT/Q1–Q4 | 开 |

正式 1040-slot promotion 可以只比较最终 P0 与 combined，避免成本过高；但 G4–G6 必须保留分层归因。

---

## 8. 推荐的实施顺序

## 阶段 A：非 ML 前置基础设施

1. 统一 `p0v2bpc`、model ID、freeze ID、manifest ID；
2. 修复 `LunarIceData` 深度不可变；
3. 建立唯一 canonical binding serializer；
4. 定义 universe-before-sort hash 和 no-filter telemetry；
5. 建立 snapshot replay；
6. 建立 deterministic 与 MLP baseline；
7. 此阶段不改 Native queue，不改在线 branch universe。

## 阶段 B：只做 pricing discovery

首版只启用：

- task priority；
- arc/path-option priority；
- harvest ordering。

proof-risk 和 branch head 只做 shadow prediction。

首轮目标：

- 20/30 time-to-first-addable-negative 明显改善；
- 20/30 end-to-end 有可复现收益；
- 5/10 在 inference 前 bypass；
- 50/100 shadow 无安全或资源回归。

## 阶段 C：接入 exact proof queue policy

在 pricing discovery 独立通过后，再引入 Q1–Q4：

- 先对 scale5 做全量小实例 differential；
- 对 scale10/20 做代表实例；
- 对 scale30 做固定 replay snapshot；
- 验证 exact objective、global minimum、no-negative proof 和 certificate gate 一致；
- 记录每个 policy 的 inference 和 queue-maintenance 开销。

## 阶段 D：branch ranking

1. 建立 `B0U = all-pairs + deterministic`；
2. 单独评估候选 universe 扩展；
3. 再评估 `GAT branch vs B0U`；
4. 50/100 保持 shadow，直到存在足够多真实闭合 fractional branch nodes；
5. root closure 本身不足以证明 branch head 可在线启用。

## 阶段 E：正式 promotion

最终冻结：

- checkpoint；
- normalization；
- graph/feature schema；
- canonical binding schema；
- OOD calibration；
- deployment/bypass gate；
- queue policy；
- Torch、BLAS、HiGHS thread count；
- deterministic inference 设置。

然后运行 fresh-runtime、cold-start、no-resume 的正式 paired promotion。

---

## 9. 建议采用的修订版成功门槛

### 9.1 精确性硬门槛

所有在线规模必须满足：

```text
guidance-induced permanent drop = 0
binding mismatch accepted = 0
NaN/Inf hint accepted = 0
objective mismatch = 0
RC audit mismatch = 0
certificate leak = 0
labels_dropped = false
extra incomplete = 0
legal universe hash before sort 一致
```

### 9.2 小规模门槛

除原有 paired 指标外，增加：

- fresh-runtime guidance 总开销；
- Torch/checkpoint 是否在 bypass 规模被完全跳过；
- guidance call count；
- p90/p99 冷启动开销；
- deployment gate 必须在 inference 前完成。

### 9.3 20/30 门槛

建议保留：

- first-addable-negative p50 改善；
- proof-tail p50 不增加；
- end-to-end p50、mean、geometric mean、p90 门槛；
- zero extra incomplete。

同时增加：

- equal-budget best RC trajectory；
- duplicate negative rate；
- RMP bound gain per pricing second；
- queue policy 单独消融；
- known regression suite 与 hidden test 严格分开。

### 9.4 50/100 门槛

建议继续保持 shadow/bounded 口径：

- observed/addable-negative top-k recall；
- matched-time best RC；
- first-negative survival；
- frontier/RSS p90；
- OOD fallback；
- bounded payload 大小固定有界；
- 不因 incomplete 宣称 exact speedup。

---

## 10. 最终结论

这份计划不是方向错误，而是**范围过大且有四处必须先修正的实验语义问题**：

1. all-pairs branch universe 必须有独立 deterministic control；
2. full80 与 012/018 的开发使用必须解耦；
3. “最终 label/candidate 集合一致”必须改为“无 guidance-induced filtering + exact 结果一致”；
4. branch cost 方向和 incomplete censoring 必须重写。

修订后，它可以成为一份很强的 exact-safe learning-to-order 研究路线图。

第一版最合理的范围是：

> **完成 binding、replay、数据隔离和 pricing/harvest ranking；proof queue 与 branch 先 shadow。**

这样可以最快回答最重要的问题：

> 在不改变 P0 V2 数学问题和证书语义的前提下，GAT 是否能在 scale20/30 上带来真实、可复现、可归因的端到端收益？

只有这个问题得到肯定答案后，才值得继续扩大到 exact proof queue、branch counterfactual 和 50/100 在线启用。
