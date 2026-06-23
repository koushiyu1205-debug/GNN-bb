# BPC_future：Proof Tail、分支决策与学习模型接入位置分析

## 总判断

你现在最值得改的，不是继续堆一个更复杂的 completion bound，而是把定价器从“**扫完才有证书**”改成“**随时返回一个可验证的全局 reduced-cost 下界**”。

这会同时影响三个问题：

1. proof tail 不再只有 `CERTIFIED_NO_NEGATIVE` 一条出路；
2. 分支评价可以使用“子节点安全下界提升 / 证明成本”，而不是 child width；
3. 学习模型可以优化调度和顺序，但不碰证书本身。

---

# 1. Proof tail 应该怎么做

## 1.1 当前终止条件过强

你现在的 Journey RMP 明确规定：只有 pricing 证明不存在负 reduced-cost journey，节点下界才是 official。主问题包含 task-cover 等式和 fleet-limit 行，每个 journey 列代表一台 rover 的完整多-sortie 日程。

这当然精确，但不必要地要求每个节点都得到**完整 LP 最优性证书**。在 branch-and-bound 中，很多时候只需要一个足够强、严格有效的节点下界来 fathom，并不需要证明当前 RMP 已经等于 full master LP。

你目前的实测已经说明“继续增加扫描预算”不是主要答案：多条 Stage-4 日志中，completion retry 消耗大量时间、没有产生负列，却仍无法证明 no-negative；单实例把 final judge 从 45 秒加到 90 秒也没有闭合。

## 1.2 最关键的结构性改动：允许“修正后的节点下界”

当前 reduced cost 是：

\[
\bar c_j
=
c_j-\mu-\sum_i\pi_i a_{ij}-\sum_k\gamma_kq_{kj},
\]

其中：

- \(\pi_i\)：task-cover dual；
- \(\mu\)：fleet-limit dual；
- \(\gamma_k\)：cut dual；
- 每个 journey 在 fleet-limit 行上的系数都是 1。

假设 exact pricing 虽然没有扫完，但能够严格证明：

\[
\bar c_j \ge \underline r
\]

对所有尚未探索的可行 journey 都成立。

令：

\[
\delta=\max(0,-\underline r).
\]

把 fleet dual 从 \(\mu\) 改成：

\[
\mu'=\mu-\delta.
\]

那么所有列的新 reduced cost 都满足：

\[
\bar c'_j=\bar c_j+\delta\ge0.
\]

因此这是 full master 的一个严格可行 dual。若当前节点最多允许 \(R_N\) 个 journey，则得到官方安全下界：

\[
\boxed{
LB_N=z_{\mathrm{RMP}}-R_N\delta
}
\]

这里的 \(R_N\) 可以直接使用当前 `active_fleet_limit`，必要时再和 task-cover 推出的上界取最小值。

这意味着：

- `\underline r ≥ 0`：退化为普通 no-negative certificate；
- `\underline r < 0`：仍然可以得到安全但较弱的 official lower bound；
- 只要 \(LB_N\ge UB-\varepsilon\)，该节点就可以直接 fathom；
- 不需要把整个 pricing universe 扫空。

这是当前 proof-tail 架构里最重要的缺失部分。

建议把状态从现在的二元语义：

```text
lower_bound_exact = true / false
```

改成：

```text
bound_kind =
    FULL_LP_CERTIFICATE
    PRICING_CORRECTED_DUAL_BOUND
    HEURISTIC_RMP_ONLY

pricing_global_rc_lb
dual_repair_delta
official_node_lb
```

`PRICING_CORRECTED_DUAL_BOUND` 虽然不是 full-LP 精确值，但它是严格有效的 branch-and-bound 下界。

## 1.3 Pricing 应变成 anytime lower-bound oracle

要支持上述公式，pricing 不能只返回：

```text
negative journeys
exhausted
reason
```

还必须返回：

```text
global_unresolved_rc_lower_bound
```

最自然的实现是 best-bound / A* 型 label search。每个开放状态 \(s\) 保存：

\[
f(s)=g(s)+h(s),
\]

其中：

- \(g(s)\)：当前 partial journey 的真实 reduced cost；
- \(h(s)\)：任意可行 completion 的乐观下界。

无论什么时候停止：

\[
\underline r=\min_{s\in OPEN}f(s)
\]

就是所有尚未探索 journey 的全局 reduced-cost 下界。

需要同时覆盖：

- OPEN heap 中的 labels；
- 尚未生成完的 sortie / profile shard；
- 未展开的 start-time / path-option 分支；
- 并行 worker 的所有 shard lower bound。

任何一部分没有下界时，不能假装完整；应退回一个更弱但始终有效的 trivial bound，而不是直接返回 `None`。

因此 pricing 的标准返回对象应该接近：

```text
negative_journeys
best_complete_rc
global_remaining_rc_lb
search_exhausted
bound_valid
frontier_state_count
```

这样 exact pricing 就成为一个**anytime proof procedure**：时间越长，下界通常越高，但不需要等到 frontier 为空才对 B&B 有价值。

## 1.4 哪一种 completion bound 最适合 Journey 结构

Journey pricing 并不是一般的任意路径问题。每个 sortie：

1. 从 depot 出发；
2. 服务一组任务；
3. 回 depot；
4. 充电完成；
5. 再开始下一 sortie。

因此它天然适合拆成两层。

### 第一层：单 sortie profile

每个 profile 保存：

```text
task_mask
ordered_tasks
start_time
end_time_including_recharge
static_cost
resource_vector
path-option signature
branch compatibility signature
cut coefficient vector
```

### 第二层：journey assembly

在 sortie profiles 上做：

```text
时间兼容
task mask 不相交
sortie 数量限制
Ryan-Foster branch compatibility
```

本质上是带 task-mask 的加权 interval / set-packing DP，而不是必须每次从物理弧层重新生成整个 journey。

建议的 exact final-judge 栈如下。

### 1. 廉价静态 feasibility bound

包括：

- 时间窗；
- 最小能耗；
- 容量；
- 剩余 sortie 数；
- 不可达任务。

### 2. Two-cycle / unique-route / assignment 型 dual-aware bound

这类 bound 维度较低、查询便宜，适合保留。成功证书日志中 two-cycle 已阻止大量扩展，说明它具有实际价值。

### 3. 反向 completion envelope

从 depot-return 状态向后构建：

\[
H[\text{remaining mask},\text{time region},\text{sorties left}]
\]

前向 label 直接查询反向 envelope。因为 sortie 之间都回 depot，这比一般 VRP 的双向 joining 更干净。

### 4. 必要时才启用 exact meet-in-the-middle

20 个任务的 bit mask 只有 \(2^{20}\) 个。时间和资源维度仍会放大状态数，但使用紧凑数组、bitset 和编译实现，比每轮在 Python dict 中递归重建更有希望。

不建议把当前 RPCE 或 AMCB 原样升级成默认 final judge。现有实测中：

- RPCE 把预算耗在 Pareto front 构造，最后因 deadline 关闭；
- AMCB 很快打满状态预算，查询很少且没有实际剪枝。

AMCB 把 cover dual 固化进对象和 reduced-cost cache，因此其数值缓存本质上依赖当前 dual。

## 1.5 哪些状态可以复用

| 内容 | 跨 dual | 跨 B&B 节点 | 跨 branch |
|---|---:|---:|---:|
| 物理 path options、travel/resource metrics | 可以 | 可以 | 可以 |
| 单 sortie 可行性、起止时间、task mask | 可以 | 可以 | 可以 |
| 同一 master-coefficient vector 下的 static cost/resource dominance | 可以 | 可以 | 可以 |
| journey/partial-state 的 cut coefficient vector | 可以 | 可以 | 可以 |
| reduced cost、negative 状态 | 不可以 | 不可以 | 不可以 |
| dual-based task ordering、heap priority | 不可以 | 不可以 | 不可以 |
| 不同 task mask 间的 reduced-cost dominance | 通常不可以 | 通常不可以 | 通常不可以 |
| branch-filtered transition/profile list | 同一 branch 可缓存 | 同一 branch 可缓存 | 换 branch 要重新过滤 |
| completion DP 的拓扑 | 可以 | 可以 | 可用放松版复用 |
| completion DP 的数值 | 通常不可以 | 通常不可以 | 通常不可以 |

最安全的跨 dual dominance 条件不是“task set 相似”，而是：

```text
相同 master coefficient vector
相同 branch automaton state
不劣的时间/资源
不高的 static cost
```

只要两个 label 的 task incidence、cut coefficients 和 branch signature 相同，dual 部分会完全抵消，这类 dominance 才是真正 dual-invariant。

你已经遇到过一个典型反例：20-task certificate retry 中的 task-set superset pruning 理论上 exact-safe，但 task-filter 本身耗时非常高；关闭后同实例从长时间未证降到十余秒内最优。

所以原则是：

> 一个理论上更强的 dominance，如果检查成本超过它减少的扩展成本，就是 proof-tail 的负优化。

### 对现有 completion-bound 的结论

不是完全推倒重来：

- 保留现有 profile、two-cycle、unique-route、resource feasibility；
- 保留 exact-safe dominance；
- 删除或隔离昂贵的 cross-mask / superset 热路径；
- 重写“终止与证书契约”为 anytime frontier lower bound；
- 增加 fleet-dual repair 下界；
- final judge 内核最终最好迁到紧凑数组和编译实现。

---

# 2. 什么分支决策真正减少整棵树的证明时间

## 2.1 Branch score 的目标不应是 child width

真正目标应是：

\[
\boxed{
J(p)=t_{\mathrm{probe}}(p)
+\sum_{b\in\{\text{same},\text{separate}\}}
P(\text{child }b\text{ remains open})
\widehat T_{\mathrm{proof}}(s_{p,b})
}
\]

选择 \(J(p)\) 最小的 Ryan-Foster pair。

这里的 \(\widehat T_{\mathrm{proof}}\) 不是节点 LP 大小，也不是当前池列数，而是预测该 child 从当前状态到以下任一事件所需的总 CPU：

```text
fathom
得到有效节点下界
完成 full pricing closure
```

Strong branching 通常能明显减小搜索树，但其 probe 自身很贵，而且局部 bound gain 并不保证全局最优树，因此应采用 limited / reliability strong branching，而不是每个候选完整求两个 child。

## 2.2 指标的重要性排序

### 第一层：安全下界和 fathom 能力

最重要的是：

```text
child corrected official LB
child bound gain per CPU second
一个 child 是否立即 fathom
两个 child 是否都取得稳定下界提升
```

尤其可以使用第 1 问中的 repaired-dual bound。这样 branch probe 不必完整 pricing，也能得到可比较的安全 child bound。

传统 strong-branching 的 product / min score仍可使用：

\[
S_{\mathrm{bound}}
=
\sqrt{
(\Delta LB_{\mathrm{same}}+\epsilon)
(\Delta LB_{\mathrm{sep}}+\epsilon)
},
\]

但必须除以 probe CPU，并加入未闭合尾部成本。

### 第二层：预计 proof-tail 工作量

包括：

```text
pricing frontier 的最小 f 值与 0 的距离
未决 frontier/shard 数
预计 exact label expansions
completion-bound prune ratio
completion helper build cost
negative pricing event rate
CB retry probability
```

这比 child width 更接近真正的 proof cost。

### 第三层：active basis 和 dual 变化

应区分：

- branch 是否触碰 active LP support；
- branch 是否真的改变 basis；
- 是否只删除 inactive pool columns；
- child dual 与 parent dual 的距离；
- basis turnover、dual oscillation；
- branch 后第一个 pricing batch 是否产生 active replacement / new task set。

`active-support touch` 是很好的中间特征，但不是最终标签。它可能改变 LP，也可能导致几十轮新负列。

### 第四层：结构宽度

可以保留：

```text
pool_same_allowed
pool_separate_allowed
max child width
balance gap
reachable task-mask count
```

但只能当廉价 proxy。

现有探针已经证明 child width 不够：pool width 即使被逐层压小，负列链也可能只是转移到更深节点。现有 branch-impact 数据中还有大量 inactive-only 和未被完整处理的 child，存在明显的右删失和选择偏差。

## 2.3 GAT branch-impact 应该学习什么

目前这些标签：

```text
y_tail_improved
y_completion_bound_tail
y_early_branch_continues
y_negative_chain_continues
y_active_touch
y_inactive_only
```

适合作为诊断辅助，但不足以作为最终 branch objective。

更合适的监督信号是同一 parent snapshot 下的 counterfactual strong-branch probe。

### 数据构造方式

1. 固定 parent 的：
   - RMP pool；
   - cuts；
   - dual；
   - incumbent；
   - caches；
   - branch history。

2. 对 top-\(K\) pair 分别建立 same / separate child。

3. 每个 child 使用相同的：
   - CPU 或 expansion budget；
   - pricing mode；
   - worker 数；
   - deterministic seed。

4. 记录：
   - repaired official LB；
   - bound gain；
   - active basis 是否改变；
   - true-negative 次数；
   - exact label expansions；
   - frontier lower-bound margin；
   - CB retry 次数；
   - probe CPU。

候选 pair 的标签应是一个排序回归目标，例如：

\[
Y(p)
=
-\Big[
t_{\mathrm{probe}}
+\widehat T_{\mathrm{same}}
+\widehat T_{\mathrm{separate}}
\Big].
\]

或者使用 pairwise regret：

\[
\operatorname{regret}(p)=J(p)-\min_qJ(q).
\]

对于 probe 时限内没有闭合的 child，不应标成失败 0，而应作为 right-censored 样本，用 survival / ranking loss 处理。

### 建议的 branch-impact 主 heads

```text
predicted_child_safe_bound_gain
predicted_child_fathom_probability
predicted_child_proof_cpu
predicted_child_exact_state_expansions
predicted_child_negative_rounds
predicted_child_cb_retries
predicted_child_active_basis_change
```

`pool width`、`active touch`、`dual stability` 都作为输入特征，不作为最终优化目标。

---

# 3. 学习模型插在哪里才有因果 wall-time ROI

## 3.1 当前阶段的优先顺序

### 第一优先：true-RC 验证后的 batch admission 与加入顺序

这是最适合当前 GAT 的位置。

模型不决定一条列“是否合法”，而是在已经验证：

```text
true reduced cost < -eps
```

之后决定：

```text
现在加入
本轮稍后加入
放入 delay queue
和哪些列组成 batch
```

任何 true-negative journey 都不能永久丢弃；在 certificate 前必须有确定性 fallback 重新释放。

这是 exact-safe 的，而且直接对应当前问题：GAT 能找到很多 true-negative，但大量是 `changed_inactive_only`，扩张了 pool 却不改变 active support，因而没有 wall-time ROI。

Column selection 本身就是序列决策：本轮加入什么会改变下一轮 dual 和后续列的价值。因此应该学习 trajectory-level action，而不是独立候选分类。

### 第二优先：pricing mode switch 与 completion-bound 触发

模型可以控制：

```text
继续 heuristic/profile worker
进入 true-dual exact worker
进入 final judge
提前 branch
```

但不能控制 certificate 是否成立。

`completion-bound trigger` 的正例不应是“触发后没有找到负列”，而应是：

```text
现在触发 CB，
在预算 B 内得到 certificate 或有效 fathom bound，
且比继续 worker 的对照组更省总 CPU。
```

否则模型很容易学会“尾段看起来像 CB”，却把大量时间耗在一次失败 final judge 上。

必须有 deterministic fallback，例如：

```text
预测继续 worker
    -> 连续 K 轮无 active progress
    -> 强制 exact judge

预测进入 CB
    -> helper build budget 超限
    -> 立即退回 simpler exact bound
```

### 第三优先：branch candidate 与 child ordering

潜力很大，但当前数据还不足。

应先构建：

- counterfactual child probes；
- 删失标签；
- tree-level proof cost。

之后再接入 branch ranking。否则模型只是学习当前 fractionality / width 规则的历史偏差。

### 第四优先：exact judge 内部搜索顺序

GAT 可以决定：

```text
先展开哪个 label
先检查哪个 task
先 materialize 哪个 profile
先处理哪个 shard
```

但只能改搜索顺序，不能：

- 删除状态；
- 宣布 dominance；
- 永久忽略 true-negative；
- 生成 no-negative certificate。

现阶段学习型 dominance 只适合作为 ordering hint，不能作为 production pruning rule。

## 3.2 什么才是正确的正例标签

核心原则：

> 标签必须是“在相同 solver state 下采取该动作，实际减少了多少后续证明 CPU”，而不是“该候选看起来像好候选”。

设状态 \(s\)、动作 \(a\)，构造同状态对照：

\[
Y(s,a)
=
T_{\mathrm{baseline}}(s,H)
-
T_a(s,H),
\]

其中 \(H\) 不是固定 CG 一轮，而是直到下一个有意义事件：

```text
下一次 official node bound
节点 fathom
进入 branch
完成 certificate
或固定 CPU horizon
```

计算时间必须包含：

- 模型推理；
- RMP 重求；
- pricing；
- materialization；
- completion helper 构造；
- certificate；
- cache 开销。

### Batch admission 标签

正例应表示：

```text
加入该 batch 后：
time-to-next-official-bound 下降
后续 RMP solve 数下降
后续 exact pricing states 下降
active basis 发生有益改变
CB retry 数下降
```

推荐主回归标签：

\[
\Delta \text{CPU-to-proof-event}
\]

辅助标签：

```text
Δ exact pricing calls
Δ label expansions
Δ RMP solves
Δ active basis support
Δ proof-gap AUC
```

### 弱负列 delay 标签

做同状态对照：

```text
A：现在加入
B：延迟 K 轮或直到 active-progress stall
```

正例是 delay 后总 CPU 更小，同时没有增加最终 proof gap、timeout 或 certificate 次数。

不要把 rough RC 很负当正例。rough RC 可以很负，但 true-RC materialization 后接近 0，并且同类 mask 会反复出现；这类样本正应该成为 delay / low-priority 的训练负例。

### Completion-bound 触发标签

正例：

```text
certificate_within_budget = 1
且
net_cpu_saved > 0
```

负例：

```text
INCOMPLETE_LIMIT
helper 构造耗尽预算
无负列、无下界提升
```

### Branch 标签

使用两 child 的总 proof cost，而不是只观察被优先处理的 child：

\[
Y_{\mathrm{branch}}
=
-
\left(
T_{\mathrm{same}}
+
T_{\mathrm{separate}}
\right).
\]

超时 child 使用删失数据，不直接填一个大常数或 0。

## 3.3 Stage 3 应该用什么指标，才能预测 Stage 4

不要再把下面这些作为主要通过标准：

```text
candidate recall
F1
exact-safe hit overlap
pair repaired count
active-touch accuracy
```

它们最多是安全性和表示能力检查。

真正的 Stage-3 → Stage-4 gate 应是：

1. **同状态 counterfactual policy regret**
   \[
   J(a_{\mathrm{model}})-\min_a J(a)
   \]

2. **paired closed-loop wall time**  
   同一实例、seed、初始 pool、solver 参数做模型开 / 关 A/B。

3. **timeout rate**

4. **p90 / p95 proof time**

5. **总 exact pricing expansions**

6. **总 completion-bound retry CPU**

7. **time to first official bound / final certificate**

8. **所有运行保持完全相同最优值与 certificate 来源**

只有这些指标改善，才能说明模型具有 Stage-4 因果 ROI。

---

# 建议的实际实施顺序

1. 给 exact pricing 增加 `global_remaining_rc_lb`，先不改 GAT。
2. 基于 fleet dual 实现 `z_RMP - R·δ` 的 official corrected bound。
3. 将 final judge 改成 best-bound / A* frontier，支持中断时返回严格下界。
4. 把 profile、resource feasibility、master coefficient vectors 做成 dual-independent 缓存；dual 变化时只重新评分。
5. 对当前 superset / cross-mask dominance 继续做成本审计，默认只保留便宜且高 prune-per-CPU 的规则。
6. 用 true-RC verified batch admission 做第一处在线学习接入。
7. 建立同 parent snapshot 的 limited strong-branch counterfactual 数据。
8. 最后才让 branch-impact GAT 参与候选排序。

---

# 一句话总结

> Proof tail 应从“反复扫到空”改成“持续提高 pricing frontier 下界，并随时把它转换成 official node bound”；branch 模型应学习“两边子树的总证明成本”；GAT 最先应该优化 true-RC 列的批量加入和 pricing 模式调度，而不是学习谁看起来像负列或谁让 child pool 更小。
