# 当前主线模型完整报告：B4.3 SPPRC Labeling 与 30-scale 精确求解现状

生成时间：2026-07-12

本文面向初学者，从头解释当前算法为什么这样设计、每一步在做什么、代码改了什么、性能到了哪里、以及真正的问题在哪里。报告中的英文术语都会给出中文含义。

---

## 1. 一句话结论

当前主线已经从早期的“拿成熟列池或 probe 证明一个已知 30-scale 实例”转向更严格的 **cold-start exact benchmark**，也就是每个实例都必须从 `instance_XXX_logical_graph.json` 冷启动，所有 seed（初始列）、pricing（定价找列）、RMP（受限主问题）、final judge（最终定价审判）、branch tree（分支树）、certificate（证书）时间全部计入求解时间。

当前主线模型名：

```text
B4_3_SPPRC_LABELING_V1
```

当前官方目标函数是：

```text
normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion
```

也就是：

- `normalized_cost`：归一化成本。
- `normalized_risk`：归一化风险。
- `normalized_weighted_completion`：归一化加权任务完成时间。
- `makespan`：最晚完成时间，本轮只记录为指标，不进入目标函数。

当前状态：

- 5/10/20 规模已有 B3B/B4.1 回归证据，主线 exact 逻辑没有证书红线问题。
- 30-scale instance001 在 **mature probe**（成熟列池/成熟 source probe）条件下曾闭合，约 550-582 秒。
- 但 strict cold-start（严格冷启动）B4.3 目前还没有在 30-scale instance001 上闭合。
- 最新完成的 30-scale instance001 cold-start 1800 秒 run：没有 `BPC_TREE_OPTIMAL`，状态是 `BPC_INCOMPLETE_PRICING`。
- 这不是因为 direct-DP（直接动态规划）求不出，也不是因为证书乱报，而是因为 root pricing / final judge 还在持续发现 true-dual negative columns（真实对偶负 reduced-cost 列），没有完成 no-negative proof（无负列证明）。

最关键的新进展：

- 我把 RMP（Restricted Master Problem，受限主问题）的 LP（Linear Program，线性规划）求解器从 Python 手写 simplex（单纯形法）接到了 HiGHS。
- 这显著降低了大列池时 RMP 重解成本。
- 30-scale instance001 在 600 秒内的 active columns（活跃列数）从旧线约 6000 多推进到 7378；1800 秒内推进到 8798。
- 但仍没有完成 exact no-negative proof，所以 B4.3 尚未验收。

---

## 2. 术语表

这一节先把后面会出现的英文都解释清楚。

### BPC

`BPC = Branch-Price-and-Cut`，中文可叫“分支-定价-切割算法”。

它是求解大规模整数规划的一类精确算法。

核心思想：

1. `Branch`：分支。遇到分数解时，把问题分成两个或多个子问题。
2. `Price`：定价。不是一次性列出所有路线，而是根据当前对偶价格寻找有价值的新路线/新列。
3. `Cut`：切割。加入额外有效不等式来强化 LP bound（线性松弛下界）。

当前代码严格来说是 **Branch-and-Price framework with diagnostic cuts**：

- 有 branch-and-price 的主问题、定价、证书边界。
- live master cuts（正式进入主问题的切割）目前没有作为主线启用。
- subset-row / fleet 等 cut 仍主要是 diagnostic-only（只诊断，不参与正式证书）。

所以当前不是“完整 live branch-price-and-cut 已成熟版”，而是“BPC 证书框架 + pricing proof-tail 强化主线”。

### Column

`Column` 是“列”，在这里就是一条可选 journey（任务执行方案/路线组合）。

一列通常包含：

- 覆盖哪些 task（任务）。
- 使用多少 sortie（出车/出行段）。
- 成本、风险、完成时间。
- official objective（官方目标函数值）。

主问题不是直接决定每个任务怎么走，而是在许多列里面选择若干列，使所有任务被覆盖。

### RMP

`RMP = Restricted Master Problem`，中文是“受限主问题”。

为什么叫受限？

因为理论上所有可能 journey columns 数量巨大，不能一次性全放进去。RMP 只放当前已经生成的一部分列。

RMP 解出：

- 当前 LP bound（线性松弛下界）。
- task cover duals（任务覆盖对偶变量）。
- fleet dual（车队/路线数限制对偶变量）。

这些 duals（对偶变量）会送给 pricing，用来判断还有没有值得加入的新列。

### Pricing

`Pricing` 是“定价子问题”。

它回答一个问题：

```text
在当前 RMP dual 下，还有没有 reduced cost < 0 的新列？
```

如果有，说明当前 RMP 列池不完整，需要把这些负列加入主问题。

如果没有，并且 pricing 覆盖了完整空间，才能说 root LP 闭合。

### Reduced Cost

`Reduced Cost`，中文是“约化成本”或“检验数”。

对一列 `j`：

```text
reduced_cost_j = column_objective_j - dual_contribution_j
```

在 minimization（最小化）问题里：

- `reduced_cost < 0`：这列有价值，加入 RMP 可能降低目标值。
- `reduced_cost >= 0`：这列不会改善当前 LP。

只有证明所有可能列的 reduced cost 都 `>= -eps`，才能说 no-negative proof 成立。

### True Dual

`True dual` 是“真实 RMP 对偶”。

当前代码很强调：

- worker（工作器/启发式找列器）可以用 smooth dual（平滑对偶）或 relaxed dual（放松对偶）帮助找列。
- 但 official reduced cost（官方约化成本）、final judge（最终审判）、certificate（证书）必须用 current true RMP dual（当前真实 RMP 对偶）。

这是为了避免启发式双变量把证明搞错。

### Final Judge

`Final Judge` 是“最终定价审判器”。

它的职责不是随便找几列，而是：

1. 在当前 true RMP dual 下尝试完整 pricing。
2. 如果找到 true negative column（真实负列），返回负列，RMP 继续迭代。
3. 如果找不到负列，而且覆盖完整 pricing space（定价空间），才允许给 no-negative certificate。

当前 30-scale 的瓶颈就在这里：final judge 仍经常找到大量负列，或者时间不够导致 coverage incomplete（覆盖不完整）。

### Certificate

`Certificate` 是“证书”。

在这里不是文件证书，而是算法意义上的证明：

```text
当前解确实是精确最优。
```

关键证书状态：

- `BPC_TREE_OPTIMAL`：分支定价树已闭合，精确最优。
- `BPC_NODE_LP_CERTIFIED`：某个节点的 LP no-negative proof 已闭合。
- `CERTIFIED_NO_NEGATIVE`：定价证明所有列 reduced cost 都非负。
- `DIAGNOSTIC_PRICING_FRONTIER`：只是诊断前沿，不能当最优证书。
- `FEASIBLE_INCUMBENT_ONLY`：只有可行解，没有最优证明。
- `BPC_INCOMPLETE_PRICING`：定价未完成，不能声称最优。

### Cold Start

`Cold start` 是“冷启动”。

严格定义：

```text
每个实例从 instance JSON 开始，不能读取同实例历史列池，不能读取成熟 probe，不能人工补列。
```

允许：

- 固定通用 seed。
- 同一次 run 内 checkpoint/resume。
- B0/reference incumbent 作为初始上界或 seed。

不允许：

- mature pool（成熟列池）。
- source probe（外部已有探针结果）。
- per-instance override（按实例调参）。
- 手工补列。

这是你指出“提前建好列池等于作弊”之后，B4.2/B4.3 明确收紧的 benchmark 口径。

### SPPRC / ESPPRC

`SPPRC = Shortest Path Problem with Resource Constraints`，中文是“带资源约束最短路问题”。

`ESPPRC = Elementary Shortest Path Problem with Resource Constraints`，中文是“元素不重复的带资源约束最短路问题”。

这里的 pricing 子问题本质上类似：

```text
在有时间窗、能量、风险、任务覆盖、sortie 结构等资源约束下，找 reduced cost 最小的路线/任务集合。
```

`Elementary` 表示任务不能重复访问。

当前 B4.3 的名字叫 SPPRC Labeling，但要注意：

- API 和证书语义已经按 SPPRC/ESPPRC 分层接入。
- 但底层还不是成熟高性能 C++ labeling engine。
- 目前 `SPPRC_ENGINE_SOURCE = internal_resource_label_core`，仍主要依赖内部 Python/compact-pricing 逻辑和 exact final judge。

---

## 3. 目标函数是什么

当前官方目标函数不是原始成本直接相加，而是 per-instance normalized additive objective（按实例归一化的加性目标）。

公式：

```text
minimize
    normalized_operating_cost
  + normalized_risk
  + 0.4 * normalized_weighted_completion_time
```

### 为什么要归一化

因为原始量级差异很大：

- 成本可能是 10^2 到 10^4。
- 风险可能是 10^0 到 10^2。
- 完成时间可能是 10^3 到 10^5。

如果不归一化，那么权重没有真实意义。例如风险权重写 1.0，但风险数值太小，就会被成本和完成时间淹没。

所以现在每个实例会计算 reference：

- `reference_cost`：单任务最低运营成本之和。
- `reference_risk`：单任务最低风险之和。
- `reference_completion`：单任务 earliest feasible completion 的加权完成时间之和。

然后：

```text
normalized_x = raw_x / reference_x
```

这样权重才代表真实 trade-off（权衡）。

### 为什么 makespan 不进入目标函数

`makespan` 是最晚任务完成时间。

如果把 makespan 直接线性化进 RMP，需要引入全局变量 `T`：

```text
completion_time_i <= T
```

这会破坏当前 column-local reduced cost 结构，因为每个 column 的 reduced cost 会受全局 `T` 影响，pricing 不再是局部可分的。

所以当前策略是：

- makespan 只记录为 metric（评估指标）。
- 不进入 official objective。
- 不参与 `BPC_TREE_OPTIMAL` 证书。

这保证 B0、B1、B2、B3、B4/B4.3 的 reduced-cost 公式一致。

---

## 4. 算法从 B0 到 B4.3 的演进

### B0：Direct DP Frozen Oracle

B0 是 direct DP oracle（直接动态规划 oracle）。

作用：

- 给小规模或受控规模实例一个精确参考。
- 用来对比 BPC 的 objective 是否一致。
- 证明当前 objective 与 journey column objective 没有偏差。

B0 的意义不是作为最终大规模求解器，而是作为 correctness oracle（正确性参照）。

### B1：Root BPC Baseline

B1 开始做 root node column generation（根节点列生成）。

核心流程：

1. 生成初始列。
2. 解 RMP。
3. 根据 RMP dual pricing 找负列。
4. 加入负列。
5. 重复直到 no-negative proof 或超时。

B1 的主要问题是：10/20 规模 root closure 已经开始超时。

### B2：Pricing Tail Optimization

B2 聚焦 pricing tail（定价尾部）。

也就是：

```text
前面找负列不难，难的是最后证明“真的没有负列”。
```

B2 做了 worker tail、final judge、addability audit、manual RC audit 等强化，但 20/30 规模仍然有拖尾。

### B3：Branch-and-Price Tree

B3 加入 branch tree（分支树）。

如果 root LP 解是 fractional（分数解），需要分支。当前主要使用 Ryan-Foster branching（Ryan-Foster 分支），即对一对任务要求：

- same journey（必须同一 journey）。
- different journey（必须不同 journey）。

B3B 曾经在 5/10/20 规模形成 accepted exact baseline。

但注意：

- B3B 对 30-scale 的能力不是严格 cold-start 全量能力。
- B3B/B4.1 中的某些 30-scale 证据来自 mature probe，不是从 JSON 冷启动完整算出来。

### B4：Cut/Formulation Diagnostic

B4 尝试 cut 和 compact formulation strengthening（紧化定价模型）。

这里有两类“cut”要分清：

1. master cut（主问题 cut）：进入 RMP，改变主问题约束。例如 subset-row cut。
2. pricing formulation cut（定价模型 cut）：只在 pricing MILP 或 proof model 里加强可行域，例如 endpoint/order、pair adjacency、time-window pruning。

真正 branch-price-and-cut 里通常说的是第一类 master cut。

当前 B4 主线没有把 subset-row/fleet cut 正式 live 化，原因是：

- 一旦 master cut live 化，cut dual 必须进入 reduced-cost 公式。
- column signature 必须包含 cut coefficient hash。
- manual RC、pricing RC、final judge 都要 cut-aware。
- completion-bound pruning、dominance 等也要证明 cut-compatible。

这些还没有完全闭合，所以当前 cut 线多为 diagnostic-only。

### B4.1：True-Dual Proof-Tail Strengthening

B4.1 的重点是 true-dual pricing / final judge / compact proof tail。

核心成果：

- B4V4/V4SZ 等 compact formulation 对 30-scale instance001 的 mature probe 能闭合。
- 有正式 `BPC_TREE_OPTIMAL` mature-probe 证据，约 549-582 秒。
- 但这是从成熟 root-tail source probe 出发，不是严格 cold-start。

这条线的价值是：

- 证明某些 30-scale 结构在当前 formulation 下是可以闭合的。
- 暴露了 proof-tail 的真实形态。
- 但不能直接作为“新实例 30-scale 1800 秒内精确求解”的正式承诺。

### B4.2：Cold-Start Exact Benchmark

B4.2 的重点是 no-cheat cold-start。

规定：

- 从 JSON 开始。
- 禁止历史列池。
- 禁止 mature probe。
- 禁止 per-instance override。
- 所有前处理、seed、pricing、tree、certificate 时间全计入。

B4.2 让 benchmark 口径变严格。

### B4.3：SPPRC Labeling Pricer

B4.3 目标是引入真正的大规模 SPPRC/ESPPRC labeling pricing engine。

目前已实现的是：

- 正式 B4.3 runner。
- SPPRC request/result API。
- worker/exact 两层 pricing 语义。
- no-cheat config/hash/provenance 检查。
- true-dual audit。
- RMP HiGHS fast path。

但底层高性能 labeling engine 还没有真正成熟，因此 B4.3 目前仍未达到 full 30-scale under 1800s 验收。

---

## 5. 当前主线求解流程

下面从一个 30-scale instance JSON 开始，逐步解释当前 B4.3 怎么求解。

### Step 0：读取实例 JSON

输入文件：

```text
data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json
```

代码会读取：

- depot（基地）。
- tasks（任务）。
- path options（路径选项，例如 low_time、low_risk 等）。
- travel time（旅行时间）。
- energy（能耗）。
- risk（风险）。
- service time（服务时间）。
- task time window（任务时间窗）。

重要边界：

即使选择 `low_time` 路径，也必须累计该路径自己的 risk、energy、distance。

即使选择 `low_risk` 路径，也必须累计该路径自己的 time、energy、distance。

也就是说 path profile 只是路径选择偏好或路径类型，不代表其它属性为 0。

### Step 1：计算 objective reference

每个实例会计算归一化 reference：

- cost reference。
- risk reference。
- completion reference。
- makespan reference 只用于报告。

这些 reference 会进入每列的 objective breakdown。

这样每个 journey column 都有：

```text
objective = normalized_cost + normalized_risk + 0.4 * normalized_completion
```

### Step 2：生成初始 seed columns

`seed column` 是初始列。

当前允许的是固定通用 seed，不允许同实例历史列池。

典型 seed：

- singleton columns：单任务列。
- B0/reference feasible incumbent 相关列。
- 固定 portfolio/cluster/task-set seed。
- low-cost/low-risk/low-time 多样化代表。

seed 的作用：

- 让 RMP 初始可行。
- 给上界和初始解。
- 但 seed 不能提供最优证书。

### Step 3：解 RMP

RMP 当前本质上是：

```text
从当前 active columns 中选择列，使每个 task 被覆盖，fleet 使用不超过限制，目标最小。
```

代码中为了拿 dual，实际求的是 RMP 的 dual LP。

以前：

- RMP dual 用 Python 手写 simplex。
- active columns 到几千以后，tableau 很大，stage 时间明显膨胀。

现在：

- `src/lunar_ice_bpc/exact/master/journey_rmp.py` 加入 `_highs_max_leq`。
- 默认 `LUNAR_ICE_RMP_SOLVER=highs`。
- 用 HiGHS 解同一个 LP。
- 如果 HiGHS 不可用或失败，回退到旧 `_simplex_max_leq`。

这个改动不改变数学模型，只改变 LP 求解器。

### Step 4：拿 true RMP dual

RMP 解出来后，得到：

- task cover duals。
- fleet dual。
- cut duals，如果有 cut context。

当前 official certificate 只允许使用这些 true dual。

### Step 5：worker 找负列

`worker` 是找列器。

当前 B4.3 的 worker mode 是：

```text
RELAXED_NG_WORKER
```

中文解释：

- `RELAXED`：放松的。
- `NG`：ng-route，一种允许局部记忆的路径放松技术。
- `WORKER`：只负责找候选列。

worker 可以更激进、更快，但它没有证明能力。

worker 找不到列时，只能返回：

```text
LOCAL_NO_COLUMN_UNCERTIFIED
```

意思是：

```text
本地没找到列，但不能证明全局没有负列。
```

### Step 6：final judge 做 true-dual exact pricing

当前 B4.3 设置：

```text
labeling_final_judge_mode = on
EXACT_FINAL_JUDGE_FIRST = true
```

也就是说 final judge 是主线。

final judge 做：

1. 用当前 true RMP dual。
2. 在 exact/elementary pricing 空间找 negative columns。
3. 找到后返回一批 columns。
4. 所有返回列必须通过 manual RC / pricing RC / addability audit。
5. 如果没找到负列且覆盖完整，才能给 no-negative certificate。

如果超时或覆盖不完整：

```text
INCOMPLETE_LIMIT
```

不能 claim `CERTIFIED_NO_NEGATIVE`。

### Step 7：把负列加入 active pool

找到负列后，加入 active columns。

然后回到 Step 3：

```text
solve RMP -> get dual -> pricing -> add columns -> solve RMP ...
```

这就是 column generation（列生成）循环。

### Step 8：root LP 闭合判断

root node 可以闭合，需要同时满足：

1. RMP optimal。
2. final judge 证明 no negative column。
3. manual reduced cost 与 pricing reduced cost 一致。
4. 没有 certificate leak。
5. branch/cut context 一致。

如果 root LP 解已经 integral（整数），且 no-negative proof 成立，可以直接：

```text
BPC_TREE_OPTIMAL
```

如果 root LP 是 fractional，需要进入 branch tree。

当前 30-scale instance001 的 cold-start B4.3 还没有走到正式 tree closure，因为 root pricing proof 没闭合。

### Step 9：branch tree

如果需要分支：

- 使用 Ryan-Foster branch。
- 子节点继承 branch context。
- 子节点继续用同一个 pricing oracle。
- 每个子节点也必须 true-dual no-negative proof。

当前 B4.3 对 30-scale 的主要瓶颈不是分支树节点太多，而是 root final judge 还没证明无负列。

---

## 6. 当前代码写了什么

### 6.1 B4.3 official runner

文件：

```text
scripts/run_lunar_ice_b4_3_spprc_labeling.py
```

作用：

- 定义正式模型 ID：`B4_3_SPPRC_LABELING_V1`。
- 固定 no-cheat benchmark 规则。
- 固定 `threads=4`。
- 固定 `profile=V4SZ`。
- 固定 `SPPRC_NG_SIZES=(6,10,14,30)`。
- 固定 `row_limit_sec=1800`。
- 禁止 external mature probe。
- 禁止 source probe。
- 禁止 per-instance override。
- 写入 config hash。
- 写入 engine build hash。
- 写入 column provenance。
- 写入 redline 检查。

当前 runner 还把 RMP solver 固定写入 config：

```text
rmp_solver = highs
rmp_highs_threads = 1
```

这样以后报告里能看出是否用了 HiGHS，而不是隐藏优化。

### 6.2 SPPRC pricer facade

文件：

```text
src/lunar_ice_bpc/exact/bpc/pricing/spprc_pricer.py
```

作用：

- 定义 `SpprcPricingRequest`。
- 定义 `SpprcPricingResult`。
- 定义 worker mode 和 exact mode。
- 输出 telemetry，如 label count、dominance pruned、ng size 等。

当前 engine source：

```text
internal_resource_label_core
```

这说明它还不是外部成熟 C++ SPPRC 引擎，而是内部实现/封装。

### 6.3 RMP HiGHS fast path

文件：

```text
src/lunar_ice_bpc/exact/master/journey_rmp.py
```

新增：

```text
_highs_max_leq
```

它求的是：

```text
max c'x
subject to Ax <= b
x >= 0
```

HiGHS 默认解 minimization，所以代码转成：

```text
min -c'x
```

然后把 HiGHS row dual 取负，恢复成原始 RMP primal lambda。

安全边界：

- HiGHS 不可用时回退 Python simplex。
- `LUNAR_ICE_RMP_SOLVER=simplex` 可以强制旧路径。
- `NEGATIVE_RHS`、`NO_CONSTRAINTS` 等旧语义保留。

这个改动很重要，因为 30-scale active columns 到 6000-9000 时，旧 Python tableau simplex 成本很大。

### 6.4 staged resume / checkpoint

相关文件：

```text
scripts/run_lunar_ice_b4_2_cold_exact.py
scripts/run_lunar_ice_compact_pricing_staged_resume.py
scripts/run_lunar_ice_compact_pricing_batch_probe.py
```

作用：

- 把长 pricing tail 分成 stage。
- 每个 stage 写 `probe.json`。
- 如果 subprocess timeout，尽量保住已经写好的 probe。
- stage 时间全部计入 cold-start total。

为什么要 staged：

- 直接一个 1800 秒大 subprocess，如果中途超时，可能丢掉所有列池进度。
- staged checkpoint 可以让同一次 run 内恢复，不算作弊，因为时间累计。

### 6.5 partial timeout negative harvest

相关文件：

```text
src/lunar_ice_bpc/exact/solver/journey_driver.py
src/lunar_ice_bpc/exact/pricing/journey_pricing.py
```

新增逻辑：

- 如果 exact pricing 在 timeout 时已经找到 partial labels 或 partial best columns，可以返回部分负列。
- 但必须标记：

```text
pricing_complete_for_all_task_subsets = False
can_certify_no_negative = False
```

也就是说：

- 可以救回候选列。
- 不能把 timeout 当成 no-negative proof。

### 6.6 tests

相关测试：

```text
tests/test_lunar_ice_labeling_pricer.py
tests/test_lunar_ice_smoke.py
```

新增/覆盖的关键测试：

- worker no-column 不能 certify。
- exact timeout 不能 certify。
- SPPRC worker mode 只是 candidate search。
- RMP HiGHS fast path 与 simplex 在小实例上 objective/reduced-cost invariants 一致。
- B4.3 config hash/no-cheat gate。
- staged timeout/orphan probe recovery。
- partial timeout 可以返回负列但不能发证书。

最近跑过的目标测试：

```text
Ran 6 tests in 0.216s
OK
```

---

## 7. 当前性能结果

### 7.1 B4.1 mature-probe 30-scale 结果

B4.1 有一条重要但不能混入 cold-start benchmark 的结果：

```text
runs/b4_1_true_dual_proof_tail_acceptance_audit_with_tree_closure/
```

其中 Stage D：

```text
B4.1_30_tree_closure_from_probe
variant = V4_root_tail_probe_tree_gate
BPC_TREE_OPTIMAL = 1
mean wall = 549.355622s
```

另一个当前代码 V4SZ 正式 3600 秒 rerun：

```text
runs/b4_1_v4sz_current_code_30_001_3600s_compare550_20260710/
```

结果：

```text
BPC_TREE_OPTIMAL
wall = 581.578981s
final judge = 580.558614s
active columns = 371
vars = 6005
rows = 14725
```

解释：

- 这证明 mature-probe 条件下，30-scale instance001 可以精确闭合。
- 但 mature probe 本身已经把大量求解工作提前做完了。
- 所以它不能回答“给一个新 30-scale JSON，能否 1800 秒内冷启动精确最优”。

### 7.2 B4.3 cold-start 600s HiGHS run

目录：

```text
runs/b4_3_spprc_highs_rmp_30_001_600s_20260712_122300/
```

结果：

| metric | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| bpc_tree_optimal | `False` |
| cold_start_total_sec | `599.560599` |
| root_cg_sec | `588.523344` |
| root_pool_stage_count | `12` |
| root_pool_active_column_count | `7378` |
| selected final-judge columns | `7680` |
| added to master | `7355` |
| manual_rc_fail | `0` |
| pricing_rc_fail | `0` |
| certificate_leak | `0` |

关键 stage：

| stage | elapsed_s | active_cols | added | final_judge_state | best_rc | returned |
|---|---:|---:|---:|---|---:|---:|
| 5 | 46.528036 | 5154 | 1024 | `FOUND_NEGATIVE` | -0.103154072 | 1024 |
| 6 | 78.326612 | 6174 | 1022 | `FOUND_NEGATIVE` | -0.145405750 | 1024 |
| 7 | 110.793013 | 6591 | 419 | `FOUND_NEGATIVE` | -0.127968327 | 512 |
| 8 | 130.397197 | 6982 | 393 | `FOUND_NEGATIVE` | -0.100496127 | 512 |
| 9 | 138.966885 | 7378 | 401 | `FOUND_NEGATIVE` | -0.121907100 | 512 |
| 10 | 15.750184 | 7378 | 0 | `INCOMPLETE_LIMIT` | 0.207501334 | 512 |

解释：

- 600 秒内没有闭合。
- 但列池推进很快，到 7378 active columns。
- redlines 都是 0，说明没有错证书。
- stage 10 出现 positive best RC，但因为时间太短、coverage incomplete，不能升级 certificate。

### 7.3 B4.3 cold-start 1800s HiGHS run

目录：

```text
runs/b4_3_spprc_highs_rmp_30_001_1800s_20260712_123520/
```

结果：

| metric | value |
|---|---:|
| algorithm_status | `BPC_INCOMPLETE_PRICING` |
| certificate_scope | `DIAGNOSTIC_PRICING_FRONTIER` |
| pricing_state | `INCOMPLETE_LIMIT` |
| bpc_tree_optimal | `False` |
| cold_start_total_sec | `1803.386138` |
| root_cg_sec | `1781.701187` |
| root_pool_stage_count | `17` |
| root_pool_active_column_count | `8798` |
| selected final-judge columns | `9472` |
| added to master | `8793` |
| manual_rc_fail | `0` |
| pricing_rc_fail | `0` |
| certificate_leak | `0` |
| fail_reason | `row time limit reached before root pool certificate` |

尾部 stage：

| stage | elapsed_s | active_cols | added | final_judge_state | best_rc | returned | negative_count |
|---|---:|---:|---:|---|---:|---:|---:|
| 10 | 157.016427 | 7857 | 479 | `FOUND_NEGATIVE` | -0.205898333 | 512 | 1832 |
| 11 | 197.292536 | 8258 | 401 | `FOUND_NEGATIVE` | -0.344837913 | 512 | 1441 |
| 12 | 216.330728 | 8435 | 189 | `FOUND_NEGATIVE` | -0.095738360 | 256 | 622 |
| 13 | 287.521223 | 8672 | 243 | `FOUND_NEGATIVE` | -0.122555000 | 256 | 858 |
| 14 | 343.867543 | 8798 | 126 | `FOUND_NEGATIVE` | -0.028697668 | 256 | 541 |
| 15 | 11.408647 | 8798 | 0 | `INCOMPLETE_LIMIT` | None | 0 | 0 |

解释：

- 1800 秒内仍没有 `BPC_TREE_OPTIMAL`。
- stage 14 仍有 541 个 negative columns，说明 true-dual pricing 空间还没耗尽。
- stage 15/16 只是剩余时间太少，不是完整 no-negative proof。
- redlines 全为 0，是正确 fail-closed。

### 7.4 HiGHS 改动带来的性能提升

旧 B4.3 1800 秒左右：

```text
active_column_count ≈ 6913
cold_start_total_sec ≈ 1801.86
```

新 HiGHS 1800 秒：

```text
active_column_count = 8798
cold_start_total_sec = 1803.386
```

这不是闭合，但说明单位时间推进了更多列。

stage 对比也很明显：

| stage | 旧 elapsed_s | 新 HiGHS elapsed_s |
|---|---:|---:|
| 3 | 70.593439 | 15.020826 |
| 4 | 101.459028 | 16.234695 |
| 5 | 176.837798 | 46.517632 |
| 6 | 237.076294 | 78.195165 |
| 8 | 441.028204 | 126.856060 |

结论：

```text
RMP fast path 是有效的，但不是最终瓶颈的全部。
```

RMP 慢的问题被明显缓解后，真正暴露出来的是：

```text
exact final judge / SPPRC proof coverage 仍不够强。
```

### 7.5 当前未完成的 uncapped harvest run

我把当前代码改成：

```text
LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE = disabled
```

也就是高 active columns 时不再把 harvest target 从 1024 降到 512/256。

原因：

- HiGHS 之前，降低 harvest target 是为了少加列，避免 RMP 太慢。
- HiGHS 之后，RMP 成本下降，过低 harvest cap 反而会让 final judge 发现很多负列却只返回少量，拖长 stage 数。

这个 run：

```text
runs/b4_3_spprc_highs_rmp_uncapped_harvest_30_001_1800s_20260712_130940/
```

已按用户要求停止。

停止前进度：

| stage | elapsed_s | active_cols | added | best_rc |
|---|---:|---:|---:|---:|
| 1 | 13.218035 | 1058 | 1024 | -0.170673 |
| 2 | 13.936268 | 2082 | 1024 | -0.149507334 |
| 3 | 15.074867 | 3106 | 1024 | -0.057350079 |
| 4 | 16.175101 | 4130 | 1024 | -0.059658 |
| 5 | 46.308203 | 5154 | 1024 | -0.103154072 |
| 6 | 78.564426 | 6174 | 1022 | -0.145405750 |

因为停止在 stage 7 之前，没有完整性能结论。

---

## 8. 当前为什么还解不出 30-scale cold-start 精确最优

现在的问题不是“有没有可行解”，也不是“B0 不会算”，而是：

```text
BPC 证明链无法在 1800 秒内证明 root pricing 已经没有负列。
```

更具体地说，有几个层次。

### 8.1 还在持续发现真实负列

30-scale 1800 秒 run 中，stage 14 仍然有：

```text
negative_column_count = 541
best_rc = -0.028697668
```

这说明：

- 当前 active pool 还不够完整。
- final judge 仍能找到对当前 dual 有改善的新列。
- 所以 root LP 还没有闭合。

### 8.2 exact proof coverage 不完整

即使某个短 stage 没找到负列，也不能马上证明最优。

必须证明：

```text
完整 pricing space 里都没有 reduced cost < 0 的列。
```

当前 stage 15/16 返回：

```text
INCOMPLETE_LIMIT
```

意思是：

- 时间不够。
- 覆盖不完整。
- 不能 certify。

这是正确行为。

### 8.3 当前 SPPRC engine 还不是成熟高性能 labeling engine

B4.3 名义上是 SPPRC labeling，但底层还不够“工业级”。

成熟 SPPRC/ESPPRC labeling engine 通常需要：

- C++ 或 native 实现。
- 双向 labeling。
- bucket graph。
- ng-route relaxation。
- DSSR。
- 强 dominance。
- label memory pool。
- checkpointable frontier。
- resource-aware lower bounds。

当前代码只是建立了 API 和证书边界，底层还主要是内部 Python/compact pricing/exact final judge。

所以它能保证不乱报，但性能还不够。

### 8.4 mature probe 能闭合不等于 cold-start 能闭合

B4.1 mature probe 只有 371 active columns 就能最终 proof。

但这个 371 列不是从空白 JSON 开始自然获得的，它来自成熟 root-tail source probe。

严格 cold-start 要把这些准备时间全部算进去。

当前 B4.3 cold-start 反而在 1800 秒内生成到 8798 active columns，还没证明闭合。

这说明：

- mature probe 可能已经处在一个非常“好”的 dual/pool 状态。
- cold-start 的列池构造路径仍不够聪明。
- 当前 worker/final judge 加列策略还没有把最关键的列优先找齐。

### 8.5 不是 live cut 能立刻解决的问题

加入 subset-row cut 可能改善 LP bound，但它也会带来新成本：

- cut dual 要进入 pricing reduced cost。
- 每列要记录 cut coefficient。
- dominance 要 cut-compatible。
- final judge 要 cut-aware。
- certificate ledger 要验证 cut context。

如果没有完整审计，live cut 可能让模型更复杂但不一定更快。

当前瓶颈主要是 true-dual pricing proof 和 negative column discovery，而不是 branch tree 过大。

所以 live cut 不是当前最直接的突破口。

---

## 9. 现在是否还是 BPC

答案要分层说。

从框架上说，是 BPC/branch-price 框架：

- 有 RMP。
- 有 column generation。
- 有 true-dual pricing。
- 有 branch context。
- 有 BPC_TREE_OPTIMAL gate。
- 有 no-negative certificate。

但从“成熟 branch-price-and-cut”角度说，还不是完整成熟版本：

- live master cuts 没有正式启用。
- 当前 30-scale 冷启动没有闭合。
- SPPRC labeler 还不是高性能工业级 labeler。
- 许多 B4 cut/formulation 仍是 diagnostic-only。

所以准确说：

```text
当前主线是 exact-safe branch-and-price / BPC certificate framework，
正在把 pricing oracle 升级为 B4.3 SPPRC labeling pricer；
但 B4.3 尚未成为 full 30-scale accepted exact solver。
```

---

## 10. 代码状态与风险

当前工作树有较多未提交改动和大量 run 目录。

主要改动集中在：

- B4.3 runner。
- RMP HiGHS fast path。
- pricing timeout partial harvest。
- staged checkpoint/resume。
- SPPRC facade。
- tests。

主要风险：

### 风险 1：当前 B4.3 还没有全量验收

不能声称：

```text
B4.3 已经能 30-scale 1800 秒精确最优。
```

只能说：

```text
B4.3 no-cheat shell 和证书边界已接入；
HiGHS RMP 显著改善推进速度；
30-scale exact cold-start 仍未闭合。
```

### 风险 2：uncapped harvest 还没完整跑完

当前代码已经把 adaptive cap 关闭，但完整 1800 秒 run 被停止。

所以它是合理方向，但还没有完整性能数据。

### 风险 3：RMP solver 改动需要更大回归

小实例测试已经通过：

- HiGHS 与 simplex objective 一致。
- reduced-cost invariant 一致。

但在全量 5/10/20 上还没用同一 B4.3 config 完整回归。

### 风险 4：SPPRC 名字与底层能力不完全匹配

当前已经有 SPPRC API，但底层不是成熟 C++ SPPRC labeler。

报告或论文里不能写成：

```text
implemented state-of-the-art SPPRC labeling engine
```

只能写：

```text
introduced an SPPRC-style pricing interface and exact-safe certificate boundary;
the current backend remains an internal exact pricing/core implementation.
```

中文：

```text
引入了 SPPRC 风格的定价接口和精确证书边界；
当前后端仍是内部 exact pricing/core 实现，不是成熟高性能 SPPRC 引擎。
```

---

## 11. 下一步建议

### 不建议继续做的事

不建议继续：

- 针对单个 30-scale instance001 手调参数。
- 依赖 mature probe 报性能。
- 手工补列。
- 把局部 `(k,m)` 调优当成全量能力。
- 直接 live subset-row cut，但没有 cut-aware certificate。

这些要么不泛化，要么会污染 benchmark。

### 建议继续做的事

#### 方向 1：真正实现高性能 SPPRC/ESPPRC labeling engine

这是最核心方向。

需要：

- native C++ sidecar 或 extension。
- Python 只做 orchestration、RMP、audit、certificate gate。
- label frontier 可 checkpoint。
- 每个 label 记录：
  - current node。
  - visited task mask。
  - time。
  - energy。
  - risk/resource。
  - sortie state。
  - branch/cut state。
- dominance 要足够强，但必须 exact-safe。

#### 方向 2：worker 与 final judge 分工更清楚

worker：

- 可以 relaxed。
- 可以 ng-route。
- 可以 dual smoothing。
- 可以 aggressive。
- 只能找列。

final judge：

- 必须 exact。
- 必须 true dual。
- 必须 coverage complete。
- 只能它给 certificate。

#### 方向 3：checkpointable proof frontier

当前 stage 的问题是：

- 找列可以 checkpoint。
- 但 exact proof coverage 不能很好 checkpoint。

需要把 final judge 的搜索空间前沿持久化：

```text
frontier state -> saved -> resume -> continue proof
```

否则每个 stage 都在重复证明或重复搜索。

#### 方向 4：更聪明的列选择

当前 final judge 发现很多负列，但返回/加入策略不一定最优。

可以优化：

- 更偏好 new task set。
- 更偏好 support-changing columns。
- 更偏好会改变 RMP basis 的列。
- 减少大量相似列。
- 但所有列必须 true-dual RC audit。

#### 方向 5：全量回归顺序

建议顺序：

1. B4.3 current code 跑 30-scale instance001 1800s，确认 uncapped harvest 结果。
2. 如果仍不闭合，不继续跑 full 30。
3. 优先实现真正 SPPRC labeler / checkpointable exact frontier。
4. instance001 先 `BPC_TREE_OPTIMAL <1800s`。
5. selected 5 个 30-scale。
6. full 30-scale 20/20。
7. 同一 config hash 跑 full 5/10/20。

---

## 12. 当前最终判断

当前模型不是失败在“数学不对”，而是失败在“精确 pricing proof 工程能力不够强”。

已经做对的部分：

- 目标函数归一化。
- makespan 不进 pricing objective。
- true-dual certificate 边界。
- worker 不能 certify。
- final judge fail-closed。
- no-cheat cold-start runner。
- RMP HiGHS fast path。
- partial timeout 不乱发证书。
- redlines 为 0。

还没做成的部分：

- 真正高性能 SPPRC/ESPPRC labeler。
- 30-scale cold-start root no-negative proof。
- full 30-scale 1800 秒 exact closure。
- full 5/10/20 同 config hash 回归。

所以当前最准确的结论是：

```text
B4.3 已经建立了正确的严格 benchmark 和证书框架，
并通过 HiGHS RMP 显著提高了 cold-start 列池推进速度；
但当前底层 pricing/final-judge engine 仍不足以在 1800 秒内闭合 30-scale。

下一步不应继续靠成熟列池、手工调参或局部 probe，
而应实现真正高性能、可 checkpoint 的 exact SPPRC/ESPPRC labeling pricer。
```

