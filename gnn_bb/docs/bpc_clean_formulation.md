# Clean Route-Vehicle Branch-Price-and-Cut with Schedule Cuts 数学说明

本文档对应根目录 `bpc/` 下的新主线。目标是先实现一个规范、可审查、保持 exactness 的 BPC，而不是最快版本。

## 0. 当前模型定位

当前 `bpc/` 实现是：

```text
route-vehicle BPC with schedule cuts
```

它不是：

```text
vehicle-schedule BPC
```

区别是：

- route-vehicle master 的列是一条单独 sortie route；
- vehicle-schedule master 的列是一辆车一天内完整、已排序的多 sortie schedule。

当前 route-vehicle master 本身是原问题的松弛：它准确表达任务覆盖、车辆 sortie 数、车辆工作时间下界、单条 route 的时间窗/载重/电量，但不直接枚举同一辆车多条 sortie 的真实先后顺序。

因此，当前算法用 schedule feasibility checker 和 schedule no-good cuts 修补这个松弛：

- 对 LP / integer RMP 给出的 route-vehicle 解，检查每辆车选中的 route 集合是否能排成真实时间顺序；
- 如果整数解不可排程，就加入 valid no-good cut 排除该不可行 route 集合；
- 如果整数解可排程，才作为原问题 incumbent；
- restricted integer master 只在当前 route pool 上寻找 primal incumbent；它可以加入临时排程 no-good 排除不可排程整数候选，也可以把已证明不可排程的 core 回流成正式 schedule no-good cut，但不参与节点 lower bound 证明。

只要所有 schedule cuts 都 valid，且 node bound 只在 exact pricing + cut separation 后使用，该框架仍保持精确性。它的代价是 cut 可能很多，LP relaxation 可能比 vehicle-schedule master 弱。

## 1. 原问题与 DW master

原问题是带时间窗、载重、电量和车辆总工作时间限制的多车辆多 sortie 路径问题。每个任务必须被服务一次；同一辆车可以执行多条 sortie，但这些 sortie 最终必须能排成真实时间顺序。

DW 分解采用 route-vehicle master。一个 route column `p` 表示一条资源可行 sortie：

```text
0 -> i1 -> i2 -> ... -> iq -> 0
```

route 内部满足：

- 任务时间窗；
- 载重 `Q`；
- sortie 电量 `B_use`；
- 单条 sortie horizon；
- 任务不重复。

master 变量：

```text
lambda[p,r] >= 0   车辆 r 是否选择 route p 的 LP 松弛变量
0 <= y[r] <= 1     车辆 r 是否启用的 LP 松弛变量
u[i]        >= 0   Phase-I 人工覆盖变量
```

整数解中 `lambda` 和 `y` 必须为 0/1。clean BPC 显式管理分支树，因此 RMP 中解 LP 松弛。

## 2. Phase-I RMP

Phase-I 用来保证每个节点 RMP 初始可行：

```text
min sum_i u[i]

sum_r sum_p a[i,p] lambda[p,r] + u[i] = 1    for all i
sum_p a[i,p] lambda[p,r] <= y[r]             for all i,r
sum_p lambda[p,r] <= S_bar y[r]              for all r
sum_p w[p] lambda[p,r] <= H y[r]             for all r
y[r+1] <= y[r]
schedule cuts
branching filters
```

如果 Phase-I exact pricing 完整结束后仍有 `sum_i u[i] > 0`，该节点才可判定不可行。

## 3. Phase-II RMP

Phase-II 使用真实目标：

```text
min sum_r F y[r] + sum_r sum_p c[p] lambda[p,r]
```

约束：

```text
sum_r sum_p a[i,p] lambda[p,r] = 1           for all i
sum_p a[i,p] lambda[p,r] <= y[r]             for all i,r
sum_p lambda[p,r] <= S_bar y[r]              for all r
sum_p w[p] lambda[p,r] <= H y[r]             for all r
y[r+1] <= y[r]
sum_{p in C} lambda[p,r] <= (|C|-1)y[r]      for schedule no-good cuts
```

其中 `w[p]` 是 route 的车辆工作时间下界：

```text
w[p] = travel_time[p] + service_time[p] + energy[p] / rho
```

等待时间不放进 master，避免 route-vehicle master 误删真实可排程解。真实时间顺序由 schedule checker 和 no-good cuts 保证。

## 4. Reduced Cost

设：

- `pi[i]` 是任务覆盖约束 dual；
- `eta[r]` 是 sortie 数约束 dual；
- `beta[r]` 是车辆工作时间约束 dual；
- `xi[i,r]` 是 task-vehicle linking 约束 dual；
- `gamma[g]` 是 schedule cut dual；
- `b[g,p,r]` 是 route-vehicle column 在 cut `g` 中的系数。
- `delta[h]` 是 pricing-compatible branching 约束 dual；
- `q[h,p,r]` 是 column 在 branching 约束 `h` 中的系数。

Phase-II reduced cost：

```text
rc[p,r] = c[p]
        - sum_i a[i,p] pi[i]
        - sum_i a[i,p] xi[i,r]
        - eta[r]
        - beta[r] w[p]
        - sum_g b[g,p,r] gamma[g]
        - sum_h q[h,p,r] delta[h]
```

Phase-I reduced cost 使用 route objective `0`：

```text
rc_I[p,r] = 0
          - sum_i a[i,p] pi[i]
          - sum_i a[i,p] xi[i,r]
          - eta[r]
          - beta[r] w[p]
          - sum_g b[g,p,r] gamma[g]
          - sum_h q[h,p,r] delta[h]
```

只有 exact pricing 在 true dual 下完整结束，且不存在负 reduced-cost route，当前节点 LP 才被认证。

当前实现保留上述证书条件，但把 `bpc/pricing.py` 内部改为增量 reduced-cost 计算：label 扩展时维护访问 bitmask、资源、服务时间、任务 dual 贡献、active crossing cut 计数和 active `arc_on` 使用 mask，直接评估 route reduced cost；只有 route 为负 reduced-cost 候选时才构造完整 `RouteColumn` 并用公共公式复核。

安全 dominance 只在状态足够完整时启用：

- dominance key 包含 `visited_mask`、当前任务、active crossing cut 计数、active `arc_on` 使用 mask 和 active signature prefix mask；
- dominance 比较到达时间、载重、能耗和前缀 reduced-cost score；
- schedule capacity cut 只依赖任务集合和车辆，因此由 `visited_mask` 覆盖；
- active crossing cut 由 prefix crossing 计数和相同当前任务覆盖；
- active `arc_on` row 由 `arc_on_mask` 覆盖；
- schedule pair conflict / no-good / core no-good / full no-good 这类顺序签名 cut 由 `signature_prefix_mask` 覆盖，两个 label 对后续可能命中的 active route signatures 完全一致时才比较。

因此该优化不会把顺序签名相关的负 reduced-cost route 错误剪掉。bounded-label heuristic pricing 和 branch-node heuristic boost 仍只能找列；只有 `exhausted=True` 的完整枚举才能证明没有负 reduced-cost route。

## 5. Cuts

当前 clean BPC 包含 schedule pair conflict cuts、schedule clique conflict cuts、route-set schedule packing cuts、schedule no-good cuts、统一 crossing cuts、subset-row cuts、limited-memory rank-1 cuts 和 schedule capacity conflict fallback。代码中保留了 LP 层 schedule capacity separator 和 schedule subset cost lower-bound cuts，但 2026-05-21 `bench_20_02/03` 诊断显示这些 LP oracle separator 没有产生有效 cut，默认关闭。统一 crossing cut 合并了 RCI 与 k-path/resource lower bound，同一个任务子集只保留 RHS 最大的版本。

如果整数解中，某辆车选择的 route 集合 `C` 经过 exact schedule checker 证明无法按任意顺序完成，则对每辆同质车加入：

```text
sum_{p in C} lambda[p,r] <= (|C| - 1)y[r]
```

这类 cut 只排除原问题不可行组合，因此不破坏 exactness。

当前实现先检查不可排程 witness 中是否存在双向不可排程 route pair。若 `p->q` 与 `q->p` 都不可行，则加入更小的 pair cut：

```text
lambda[p,r] + lambda[q,r] <= y[r]
```

由于同一辆车上两条 sortie 必须存在一个先后顺序，且更晚开始不会修复时间窗/电量/horizon 违反，这个 pair cut 是安全的。

在 fractional LP 解上，当前实现还会受控分离 schedule incompatibility cut。对某辆车 `r`，若 LP 支撑中的多条 route 两两满足双向不可排程，则这些 route 构成一个 incompatibility clique `K`。同一辆真实车辆最多只能选择 clique 中一条 route，因此可加入：

```text
sum_{p in K} lambda[p,r] <= y[r]
```

当 `|K|=2` 时就是 pair cut；当 `|K|>=3` 时记为 `schedule_clique_conflict`。该 cut 只使用 exact schedule transition check 证明 pairwise incompatibility，候选 clique 的搜索方式只是分离启发式，不参与有效性证明。为控制列定价状态膨胀，默认只在浅层节点、每个节点少量轮次、每轮少量 violated cut 中启用。

更一般地，当前实现还支持 route-set schedule packing cut。给定同一车辆的一组 route：

```text
C = {p_1, ..., p_m}
```

用 exact schedule DP 计算：

```text
U(C) = 一辆真实车辆最多能从 C 中排程多少条 route
```

若当前 LP 违反：

```text
sum_{p in C} lambda[p,r] <= U(C)y[r]
```

则加入 `schedule_route_set_packing` cut。这个 cut 同时覆盖 pair、clique 和 no-good 的高阶推广：

- pair conflict 是 `|C|=2, U(C)=1`；
- clique conflict 是 `|C|>=3, U(C)=1`；
- 不可排程整数 no-good 是 `U(C) <= |C|-1` 的整数解特例。

有效性：`U(C)` 由 exact DP 在真实 route ready time、horizon 和 sortie 数限制下计算。整数解中若 `y[r]=0` 则车辆不能选择 route；若 `y[r]=1` 则同一辆车最多只能从 `C` 中选择 `U(C)` 条 route。因此 `sum lambda <= U(C)y[r]` 不删除任何原问题整数可行解。若 DP 状态数超过上限或无法完成证明，则不加 cut。候选 `C` 的生成可以是启发式，但 cut 的 RHS 必须来自 exact oracle。

RIM 回流和整数解校验只会把不可排程 route set 中严格强于普通 no-good 的情形提升为 route-set packing conflict cut，即要求 `U(C)<|C|-1`。这里的 `C` 优先取原始不可排程整数解中的 full route set；pair、schedule-capacity 和 no-good fallback 再使用 deletion-minimal core。原因是 deletion-minimal core 通常只会给出 `U(C)=|C|-1`，与普通 no-good 同强度。若 route-set 上界不能加强，当前实现继续尝试 schedule-capacity conflict cut：从不可排程 route 集合中提取任务集合 `S`，若 exact schedule oracle 证明一辆车最多只能服务其中 `U(S)<|S|` 个任务，则加入：

```text
sum_{i in S} z[i,r] <= U(S) y[r]          for all r
```

只有无法证明这类任务集合上界时，才退回 route-signature no-good cut。

Schedule capacity upper-bound cut：

```text
z[i,r] = sum_p a[i,p] lambda[p,r]

sum_{i in S} z[i,r] <= U(S) y[r]          for all r
```

其中 `U(S)` 是一辆真实车辆在完整多 sortie schedule 中最多能服务 `S` 内多少个任务。当前实现用 exact labeling oracle 计算；若 oracle 超过状态上限或不能证明，则不加 cut。

有效性：若 `y[r]=0`，车辆 `r` 不服务任何任务；若 `y[r]=1`，左侧是一辆车在 `S` 中服务的任务数，按 `U(S)` 定义不超过该上界。因此该 cut 不删除任何原问题整数可行解。

Subset-row cut：

```text
sum_{p,r} floor(|p∩S| / k) lambda[p,r] <= floor(|S| / k)
```

其中 `k>=2`。这是标准 VRP set-partitioning 有效不等式。整数解中，任务集合 `S` 内每个任务恰好被一条 route 覆盖，因此所有 route 对 `S` 的覆盖计数按 `floor(count/k)` 聚合后，不可能超过 `floor(|S|/k)`。该 cut 不依赖 schedule oracle，但能加强 route master 的基础 LP 下界。

Limited-memory rank-1 cut：

```text
sum_{p,r} floor((sum_{i in S} m_i a_ip) / d) lambda[p,r]
    <= floor((sum_{i in S} m_i) / d)
```

其中 `d>=3`，`m_i` 是正整数且 `m_i<d`。这是 set-partitioning cover 等式的 rank-1 Chvatal-Gomory cut。当前实现把非均匀 multiplier pattern 限制在小 memory 任务上生成，所以称为 limited-memory 第一版；memory 只限制候选生成，不影响有效性。pricing 中 route 系数精确计算为 `floor(weight(route∩S)/d)`。

Schedule subset cost lower-bound cut 当前是实验项，默认关闭：

```text
z[i,r] = sum_p a[i,p] lambda[p,r]

sum_p c[p] lambda[p,r]
  - L(S) sum_{i in S} z[i,r]
  + L(S)(|S|-1)y[r] >= 0
```

其中 `L(S)` 是一辆车真实多 sortie schedule 完整服务任务集 `S` 的变量成本下界。当前实现用 `exact_schedule_subset_cost()` 在小规模 `S` 上精确求最小成本；若 oracle 状态超限、未完成或证明 `S` 单车不可行，则不加该成本 cut。

有效性：整数解中若 `y[r]=0`，车辆 `r` 没有 route，左侧为 0；若 `y[r]=1` 且车辆没有完整服务 `S`，则 `sum_{i in S}z[i,r] <= |S|-1`，在 route 成本非负时左侧非负；若车辆完整服务 `S`，则该车辆所有 route 构成一个真实 schedule，其变量成本至少为 `L(S)`，左侧仍非负。因此该 cut 不删除任何原问题可行整数解。

pricing 处理：`subset_row` 的 route 系数是 `floor(|p∩S|/k)`；`limited_memory_rank1` 的 route 系数是 `floor((sum_i m_i a_ip)/d)`；若实验性 `schedule_subset_cost_lb` 打开，其 route 系数是 `c[p]-L(S)|p∩S|`。这些系数都进入 true-dual reduced cost。由于成本型 cut 系数包含 `c[p]`，当其 dual 非零时，第一版 exact pricing 暂停 dominance，以免旧 label score 剪掉潜在负 reduced-cost route。

## 6. Branching

主 branching rule 是 Ryan-Foster：

- `same(i,j)=1`：任务 `i,j` 必须在同一 route 中，pricing 禁止只含其中一个任务的 route；
- `same(i,j)=0`：任务 `i,j` 必须不在同一 route 中，pricing 禁止同时含两个任务的 route。

fallback 是 task-vehicle assignment：

- `task i on vehicle r`：pricing 禁止其他车辆生成含 `i` 的 route；
- `task i off vehicle r`：pricing 禁止车辆 `r` 生成含 `i` 的 route。

然后是 arc-usage branching：

- `arc(i,j)=0`：pricing 禁止生成 route 内部直接使用有向任务弧 `i -> j` 的 route；
- `arc(i,j)=1`：RMP 加入 `sum_{p,r} q[i,j,p] lambda[p,r] >= 1`，pricing 的 reduced cost 使用该分支约束 dual。

最后是 vehicle-use branching：

- `vehicle r off`：pricing 禁止车辆 `r` 生成任何 route，RMP 固定 `y[r]=0`；
- `vehicle r on`：RMP 固定 `y[r]=1`。

当前不再使用 route-signature branching 作为 fallback。route-signature branching 虽然可作为列层面的有效分支，但不够结构化，且不利于后续做标准 VRP branching / 2LBB。

上述分支都是 pricing-compatible 的结构分支，或直接作用在 RMP 的车辆启用变量上。

## 7. Exactness 条件

clean BPC 的证明流程依赖以下条件：

1. RMP 初始可行由 Phase-I 人工列保证。
2. reduced cost 公式使用 RMP 的真实 dual。
3. exact pricing 使用 true dual、branching constraints、cut duals。
4. heuristic pricing、branch-node heuristic boost 和 restricted integer master 只用于找列或找 incumbent；不能用于证明节点完成，除非对应 pricing 调用本身 `exhausted=True`。
5. node lower bound 只在 full pricing + cut separation 后使用。
6. integer incumbent 必须通过 exact schedule checker。
7. pricing 中断时不能声明节点完成，也不能用该节点 bound 做证明。
8. 时间限制在节点证书完成前触发时，状态必须是 `TIME_LIMIT`。

因此 v1 可能慢，但不是启发式算法。
