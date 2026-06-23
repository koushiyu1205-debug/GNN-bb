# BPC_future：`global_remaining_rc_lb`、\(R_N\)、未探索区域覆盖与 Branch Counterfactual Probe 设计

以下结论基于当前 `BPC_future` 的 Journey RMP、pricing result、completion-bound 日志和分支数据结构。

当前代码中 `JourneyPricingResult` 只有 `best_reduced_cost`、`exhausted` 等字段，尚未定义可供 B&B 使用的全局未决 reduced-cost 下界；同时 `CERTIFIED_NO_NEGATIVE` 还被硬性绑定到 `exhausted=True`。

---

# 1. `global_remaining_rc_lb` 的最小可落地版本

## 1.1 结论

**不需要第一步就把 final judge 全部重写成 A\*。**

最小风险方案是：

> 在现有 direct-label completion-bound retry 内增加一个独立的“frontier certificate ledger”，继续沿用当前搜索顺序，但同时维护所有未探索区域的合法下界。

A\* 是一种提高搜索效率的排序方式，不是产生全局下界的必要条件。只要未探索空间被若干互不遗漏的 region 覆盖，并且每个 region 都有 admissible lower bound，那么：

\[
\underline r
=
\min_{q\in\mathcal F} LB(q)
\]

就是未探索列的全局 reduced-cost 下界，无论实际按 DFS、best-first、启发式 priority 还是 streaming 顺序展开。

当前 final judge 已经存在：

- direct-label heap pop；
- partial completion bound；
- bound-state 统计；
- two-cycle、unique-route 等 helper；
- physical catalog resume 状态。

成功日志中能看到 `direct_label_profile_partial_heap_pops`、`lb_state_count`、`lb_pruned_labels` 和大量 bound checks，说明现有路径已经具备大部分基础组件。

但**不能直接把当前的 `lb_min_value` 当成 `global_remaining_rc_lb`**。它目前是 completion-bound 状态值的聚合统计，并没有证明它覆盖：

- heap 中所有未展开 label；
- 尚未生成的 profile；
- resume heap；
- start/path-option lazy branch；
- worker shard；
- 已发现但未加入 RMP 的完整候选。

报告中的 `lb_min_value`、`lb_state_count` 和 `lb_negative_state_count` 只是统计字段，没有对应的 coverage-complete 契约。

## 1.2 建议的数据接口

在 `JourneyPricingResult` 增加：

```python
global_remaining_rc_lb: float | None = None
global_remaining_rc_lb_valid: bool = False
global_remaining_rc_lb_coverage_complete: bool = False

frontier_region_count: int = 0
frontier_unsupported_region_count: int = 0
pending_complete_min_rc: float | None = None

pricing_proof_kind: str = ""
# NONE
# EXHAUSTIVE_NO_NEGATIVE
# FRONTIER_BOUND_NO_NEGATIVE
# FRONTIER_BOUND_INCOMPLETE
```

并将目前混合在一起的语义拆开：

```python
search_exhausted: bool
pricing_certified: bool
```

因为未来可能出现：

```text
search_exhausted = false
global_remaining_rc_lb >= -eps
pricing_certified = true
```

也就是说，搜索没有逐项枚举完，但 lower bound 已经证明所有未展开区域不可能包含负列。

当前 `_infer_journey_pricing_state()` 要求 `exhausted=True` 才能认证，因此这部分必须同步解耦。

## 1.3 Frontier ledger 的最小实现

每个未决 region 放一个 token：

```python
@dataclass
class FrontierBoundToken:
    token_id: int
    lower_bound: float
    region_kind: str
    active: bool = True
```

维护一个独立的最小堆：

```python
frontier_bound_heap: list[tuple[float, int]]
```

注意，它应与当前搜索 priority heap 分开。当前搜索 priority 可能加入：

- future dual weight；
- cut dual weight；
- diversity；
- best-first 启发项。

这些 priority 不一定是数学下界，因此不能拿搜索 heap 的第一个 key 直接做证书。

展开一个 region 时必须采用原子替换：

```text
父 region token 仍保持 active
→ 生成全部子 region
→ 将全部子 token 注册到 ledger
→ 最后才注销父 token
```

否则在父 token 被删除、子 token 尚未全部建立的瞬间会出现 coverage hole。

中断时：

```python
global_remaining_rc_lb = min(
    minimum_active_frontier_token_lb,
    minimum_pending_complete_candidate_rc,
    minimum_active_worker_shard_lb,
)
```

首版建议只在以下条件全部满足时让 driver 使用它：

```text
pricing kind = exact_completion_bound_retry
global_certificate_capable = true
没有返回 true-negative journey
没有未记录的 negative candidate
frontier_unsupported_region_count = 0
coverage_complete = true
```

这能把改动限定在当前最可信的 final-judge 路径，不污染普通 profile/streaming worker。

现有设计本身也明确把 profile/streaming 定义为 worker，将 direct-label completion bound 定义为后段 true-dual judge。

## 1.4 推荐的实施阶段

### V0：只输出，不用于剪枝

记录：

```text
global_remaining_rc_lb
coverage_complete
unsupported_region_count
```

在 5-task 可穷举实例上比较：

\[
\underline r_{\text{reported}}
\le
r^*_{\text{true remaining}}
\]

### V1：只产生 corrected node bound

即使：

\[
\underline r<0
\]

也允许计算安全节点下界，但暂不称作 LP closure。

### V2：当 \(\underline r\ge-\epsilon\) 时产生 bound certificate

这时不需要 literal exhaustive scan。

### V3：再考虑把搜索顺序改为 A\*

A\* 主要为了更快提高 frontier minimum，不是 V0/V1 正确性的前提。

---

# 2. \(R_N\) 应该精确取什么

## 2.1 \(R_N\) 的正确含义

这里的 \(R_N\) 不是：

- 当前 RMP 中非零列的数量；
- incumbent 使用的车辆数；
- “已经使用车辆数”减去总车辆数；
- 当前 column pool 的 journey 数。

它必须是节点完整 master 中：

\[
\sum_j x_j
\]

的一个 exact-safe 上界。

当前 Journey RMP 有显式约束：

\[
\sum_j x_j \le \texttt{active\_fleet\_limit},
\]

而每个 journey 的 fleet-row 系数都是 1。

当前 reduced cost 也是：

\[
\bar c_j
=
c_j-\mu-\sum_i\pi_i a_{ij}
-\sum_k\gamma_kq_{kj},
\]

即每个 journey 只减一次 fleet dual。

因此首版最稳妥的取值是：

\[
\boxed{
R_N
=
\min\{
\texttt{rmp\_fleet\_limit\_used},
|T|
\}
}
\]

其中 `rmp_fleet_limit_used` 必须是**产生当前 dual 的那次 RMP solve 实际使用的 RHS**。

## 2.2 为什么还能和任务数取最小值

每个 journey 至少包含一个任务。`make_journey()` 会拒绝空 journey，并把其所有 trip 的 task set 合并成非空 `JourneyColumn.task_set`。

task-cover 等式给出：

\[
\sum_j a_{ij}x_j=1,\quad i\in T.
\]

把所有任务行相加：

\[
\sum_j |S_j|x_j=|T|.
\]

因为每个 journey 有：

\[
|S_j|\ge1,
\]

所以：

\[
\sum_jx_j\le |T|.
\]

这是对 LP 分数解也成立的，不只是整数解。

## 2.3 Branch node 是否已有更紧的 fleet 上界

从当前节点结构看，`JourneyNode` 只保存：

```text
lower_bound
id
depth
branch_constraints
lower_bound_exact
priority_width
```

没有 node-specific fleet limit 字段。

因此建议在 node solve result 或 node metadata 中显式保存：

```python
rmp_fleet_limit_used: int
journey_cardinality_upper_bound: int
journey_cardinality_bound_source: str
```

不要在之后根据最新 incumbent 或全局变量反推当时的 RHS。

## 2.4 Same-vehicle branch 可以进一步收紧

如果 Ryan-Foster `same_vehicle(i,j)` 在完整 journey universe 中严格保证：

```text
包含 i 的 journey 必须同时包含 j
包含 j 的 journey 必须同时包含 i
```

那么可以把所有 same-vehicle 约束构成并查集。设 resulting equivalence components 数量为 \(C_N\)，则：

\[
\sum_jx_j\le C_N.
\]

于是可以使用：

\[
R_N
=
\min\{
\texttt{fleet limit},
|T|,
C_N
\}.
\]

但这不建议在第一版直接启用。当前通用 `partial_sequence_allowed()` 对 `separate_vehicle` 做了过滤，却没有在该函数中处理 `same_vehicle`；same 约束很可能在 Journey 的其他环节闭合。

因此启用 \(C_N\) 前必须测试：

```text
任意可行完整 journey
对于每个 same component：
要么完全不包含该 component
要么包含该 component 的全部任务
```

`separate_vehicle` 只禁止某些任务共同出现，通常不会降低“最大 journey 数”，所以它对 \(R_N\) 不提供明显收紧。

## 2.5 Existing columns 不会“消耗” \(R_N\)

当前节点不是构造式 partial schedule，没有把若干 journey 固定为 1 后再分配剩余车辆。

因此不能写：

```text
R_N = fleet_limit - 已选 journey 数
```

RMP 中的所有 `x_j` 都还在共同重新优化。

## 2.6 Corrected bound 公式

若 pricing 给出：

\[
\bar c_j\ge \underline r
\]

对所有未覆盖列成立，令：

\[
\delta=\max(0,-\underline r).
\]

则按照当前 reduced-cost 符号约定，将 fleet dual 下调 \(\delta\) 后：

\[
\bar c'_j=\bar c_j+\delta\ge0.
\]

得到：

\[
\boxed{
LB_N^{\mathrm{corr}}
=
z_{\mathrm{RMP}}
-
R_N\delta
}
\]

实现时应加入数值安全量：

```python
safe_rc_lb = global_remaining_rc_lb - rc_bound_safety_eps
delta = max(0.0, -safe_rc_lb)

corrected_lb = (
    rmp_objective
    - journey_cardinality_upper_bound * delta
    - node_bound_safety_eps
)
```

同时把 proof artifact 写入日志：

```text
dual_hash
cut_hash
branch_constraint_hash
rmp_fleet_limit_used
R_N
global_remaining_rc_lb
dual_repair_delta
corrected_node_lb
```

---

# 3. 当前所有未探索区域能不能都给出 bound

## 3.1 结论

**理论上可以，但当前代码未必已经对所有路径具备可直接导出的数值 bound。**

当前 result 已经显式记录：

```text
label_physical_catalog_exhausted
label_resume_heap
label_resume_profiles
label_resume_exhausted
```

说明 physical-profile generation 和 resume 区域确实可能处于未完成状态。

sharded final judge 也只记录：

```text
shards_total
shards_certified
shards_incomplete
shards_negative_found
```

尚未记录每个 incomplete shard 的剩余 reduced-cost 下界。

所以第一版不能只对 OPEN labels 取 min，然后宣称全局覆盖。

## 3.2 各类区域的处理方法

### OPEN direct labels

可以使用：

\[
g(s)+h(s),
\]

其中：

- \(g(s)\)：partial journey 的真实累计 reduced cost；
- \(h(s)\)：当前 completion helper 给出的安全 continuation bound。

这是最容易接入的部分。

### 尚未生成的 profile shard

不需要先生成所有 profile。

给每个 shard 保留一个父 region bound，例如：

```text
first-task shard
first-sortie-mask shard
task-order prefix shard
```

在 shard 全部 materialize 之前，其父 token 始终留在 ledger 中。

### Start-time 分支

可以放松：

- task waiting；
- time-window coupling；
- recharge occupation；
- 精确 start placement。

使用所有 start placement 中的乐观最小成本。放松可行性只会让 bound 更低，因此 exact-safe。

### Path-option 分支

对每条逻辑弧使用：

```text
minimum option cost
minimum option energy
minimum option travel time
```

忽略不同弧之间的物理耦合，得到乐观 bound。

### Worker shard

coordinator 在 dispatch 前保留：

```text
shard_root_lb
```

worker 运行后可以汇报更紧的：

```text
worker_frontier_lb
```

在 worker 完整返回之前，旧的 shard root token 不能被删除。

### 已经发现但尚未加入 RMP 的完整候选

这类候选必须进入：

```text
pending_complete_min_rc
```

否则可能出现：

```text
未探索 frontier 全都 >= 0
但 delay queue 里还藏着 rc < 0 的完整列
```

此时不能产生证书或 corrected bound。

## 3.3 如果某块没有 lower bound，返回什么

第一版建议严格 fail closed：

```text
global_remaining_rc_lb = None
global_remaining_rc_lb_valid = false
unsupported_region_count > 0
```

数学上等价于：

\[
\underline r=-\infty.
\]

不要为了“始终有数值”而生成未经证明的 finite bound。

第二阶段可以增加全局 trivial finite bound。

设：

- \(C_{\min}\)：任意非空 journey 的静态成本下界；
- \(\pi_i\)：cover dual；
- \(\mu\)：fleet dual；
- cut \(k\) 的系数范围为 \([l_k,u_k]\)。

则一个保守 root bound 是：

\[
L_0
=
C_{\min}
-\mu
-\sum_i\max(\pi_i,0)
-\sum_k
\max\{\gamma_kl_k,\gamma_ku_k\}.
\]

解释：

- 假设 journey 可以收集所有正 cover dual，是最乐观情况；
- 对每个 cut，扣除其最大可能 dual reward；
- 忽略 branch、时间、容量和能量约束，只会放松问题；
- 若无法证明 \(C_{\min}\) 或 cut coefficient 范围，继续返回 \(-\infty\)。

更实用的 partial-state trivial bound 是：

\[
LB(s)
=
g(s)
+LB_{\mathrm{return}}(s)
-\sum_{\ell=1}^{m(s)}
\pi^+_{(\ell)}
-\text{cutRewardUB}(s),
\]

其中 \(m(s)\) 是 remaining sorties 和 max-tasks-per-trip 所允许的最大新增任务数，只扣除剩余任务中最大的 \(m(s)\) 个正 dual。

## 3.4 太松会不会没有意义

会。

但需要区分两个目标：

1. **覆盖正确性**：每个 region 都有安全 bound；
2. **fathom ROI**：bound 足够接近 0。

V0 的意义主要是建立完整证书链和统计：

```text
coverage rate
unsupported region count
global rc lb
corrected node gap
```

之后再根据日志判断真正拖松 bound 的区域：

```text
ungenerated profile
path options
start placement
cut reward
remaining task dual
worker shard
```

逐个收紧，而不是一开始重写整个 final judge。

---

# 4. Branch counterfactual probe 的预算怎么设

## 4.1 结论

**固定 expansion 数应作为主预算，wall time 只作为保护上限。**

因为：

- Python 调度、cache 命中、机器负载会让“5 秒”对应的搜索工作量差异很大；
- 模型需要可比较标签；
- 最终部署仍然关心 wall time，因此应同时记录 CPU。

当前 branch-impact 数据中，许多 child 未处理或仅观察到局部尾段，存在明显删失和行为策略偏差。

## 4.2 推荐的两级 probe

### Stage A：所有候选的廉价 probe

每个 parent 取：

```text
K = 6
```

组成：

```text
当前规则 top 4
+
随机/结构多样候选 2
```

每个 candidate 两个 child，预算：

```text
1 次 child RMP solve
1 次 exact-safe pricing pass
10k–25k label expansions
wall cap 0.5–1.0s
```

估算总成本：

```text
6 candidates × 2 children × 0.5–1s
= 6–12s / parent
```

### Stage B：少数候选深 probe

从 Stage A 选 top 2，预算：

```text
75k–150k expansions
最多 2–3 个 CG round
wall cap 2–3s / child
```

总成本约：

```text
2 × 2 × 2–3s
= 8–12s / parent
```

因此普通离线 parent 总成本约：

```text
14–24s
```

### Gold tranche

只对约 10%–20% 的 parent 做：

```text
top 2 + 1 个随机候选
5s / child
```

用于获得更长 horizon 的删失/闭合标签。

**不建议对全部 top-K 都跑 5 秒。**

例如：

```text
K=8
8 × 2 × 5s = 80s / parent
```

训练成本很高，而且很多 child 仍不会闭合。

## 4.3 每个 cutoff 都记录轨迹

不要只保存 probe 结束时一个数。建议在：

```text
2k
5k
10k
25k
50k
100k expansions
```

记录：

```text
corrected child LB
global_remaining_rc_lb
frontier size
negative columns found
active-support-changing columns
RMP objective
dual distance from parent
```

这样可以训练 anytime progress，而不是只学习某个任意预算终点。

## 4.4 主标签

对 child \(b\)：

\[
\Delta LB_b(B)
=
LB_{b,\mathrm{corr}}(B)
-
LB_{\mathrm{parent},\mathrm{corr}}.
\]

记录：

```text
safe_bound_gain
fathomed_within_budget
certificate_within_budget
pricing_expansions
pricing_cpu
negative_pricing_events
completion_bound_retries
active_basis_changed
```

对 candidate pair \(p\)，不要只用 child-width 或只看一个 child。

至少要保留两个方向的独立 heads：

```text
same_child_safe_bound_gain
separate_child_safe_bound_gain

same_child_proof_work
separate_child_proof_work

same_child_fathom_probability
separate_child_fathom_probability
```

初期可以用一个 robust hand-crafted score 排序：

\[
S_B(p)
=
\log(\Delta_s+\epsilon)
+
\log(\Delta_d+\epsilon)
-\lambda\log(1+W_s+W_d)
+\kappa(F_s+F_d),
\]

其中：

- \(\Delta_s,\Delta_d\)：两个 child 的 corrected bound gain；
- \(W_s,W_d\)：expansion / CPU work；
- \(F_s,F_d\)：是否 fathom。

最终目标仍应是：

\[
J(p)
=
t_{\mathrm{probe}}(p)
+
\widehat T_{\mathrm{proof}}(s_{\mathrm{same}})
+
\widehat T_{\mathrm{proof}}(s_{\mathrm{separate}}),
\]

选择预测总 proof cost 最小的 pair。

## 4.5 未闭合 child 怎么打标签

不能写：

```text
timeout -> y = 0
```

应记录：

```text
censored = true
observed_time = budget
last_corrected_lb
last_frontier_lb
last_frontier_size
last_expansion_count
```

训练方式可以是：

- survival loss；
- censored regression；
- pairwise ranking；
- 同预算 dominance 标签。

例如候选 A 在同预算下满足：

```text
两个 child 的 corrected LB 都不低于 B
总 expansion 不高于 B
至少一个指标严格更好
```

则 A 可以作为 B 的确定 pairwise winner。否则标记为 uncertain，不强制生成错误顺序。

## 4.6 Reliability strong branching

维护两个方向的历史统计：

```text
same direction:
    bound_gain / fractional_infeasibility
    proof_work
    fathom frequency

separate direction:
    bound_gain / fractional_infeasibility
    proof_work
    fathom frequency
```

同一 task pair 在同实例不同节点重复出现时，可以积累 pair pseudo-cost。

跨实例时则使用特征 bucket 或模型不确定性：

```text
depth bucket
same_mass bucket
active-support-touch
family
task scale
dual-stability bucket
```

建议：

```text
可靠样本数 < 3–5
或模型不确定性高
    -> 执行 probe

可靠样本数充分
且预测置信度高
    -> 使用 GAT / pseudo-cost 排序
```

## 4.7 防止 counterfactual 数据被 cache 顺序污染

所有候选必须从同一个 parent snapshot 开始：

```text
相同 RMP pool
相同 cuts
相同 incumbent
相同 parent dual
相同 branch history
相同随机种子
```

缓存规则：

- dual-independent physical/profile cache 可以统一预热、只读共享；
- dual-dependent frontier、priority、reduced-cost cache 必须每个 child 独立；
- 一个候选 probe 发现的列不能进入下一个候选的 pool；
- 候选运行顺序要随机化，检查 order effect。

否则后运行的 candidate 会因为前面 probe 已经预热 cache 而看起来更快，标签不再具有因果意义。

---

# 推荐的落地顺序

1. 给 `JourneyPricingResult` 增加 frontier-bound 和 coverage 字段。
2. 只在 direct-label completion-bound retry 内实现 certificate ledger。
3. V0 只日志输出，在 5-task 穷举上验证下界正确性。
4. Driver 增加 corrected node bound，但不改变 `OPTIMAL` 判定。
5. 首版使用：
   \[
   R_N=\min(\texttt{rmp fleet limit},|T|).
   \]
6. 将 `lower_bound_exact` 拆为：
   ```text
   lower_bound_valid
   full_lp_closed
   lower_bound_kind
   ```
7. 建立 fixed-expansion limited strong-branch probes。
8. same-component 的更紧 \(R_N\) 和 A\* 重排放到第二阶段。

---

# 核心结论

> 先给现有 final judge 加一层完整的 frontier-bound ledger，不必先重写 A\*；\(R_N\) 首版严格取当前 RMP fleet RHS 与任务数的最小值；无法覆盖的区域必须 fail closed 或由统一 root relaxation 兜底；branch probe 用固定 expansion 的两级预算，并把未闭合 child 当作删失样本，而不是失败样本。
