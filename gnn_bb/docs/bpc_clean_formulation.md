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
sum_{p in C} lambda[p,r] <= |C|-1            for schedule no-good cuts
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

当前实现保留上述证书条件，但把 `bpc/pricing.py` 内部改为增量 reduced-cost 计算：label 扩展时维护访问 bitmask、资源、服务时间和任务 dual 贡献，直接评估 route reduced cost；只有 route 为负 reduced-cost 候选时才构造完整 `RouteColumn` 并用公共公式复核。该优化不改变完整枚举的 route 集合，也不改变 exactness。

## 5. Cuts

当前 clean BPC 包含 schedule pair conflict cuts、schedule no-good cuts、统一 crossing cuts 和 schedule capacity upper-bound cuts。统一 crossing cut 合并了 RCI 与 k-path/resource lower bound，同一个任务子集只保留 RHS 最大的版本。

如果两条 route `p,q` 被 exact schedule checker 证明不能由同一辆车共同排程，则对每辆同质车加入：

```text
lambda[p,r] + lambda[q,r] <= 1
```

该 cut 使用 route signature 判断系数，不依赖 route 对象 id。

如果整数解中，某辆车选择的 route 集合 `C` 经过 exact schedule checker 证明无法按任意顺序完成，则对每辆同质车加入：

```text
sum_{p in C} lambda[p,r] <= |C| - 1
```

这类 cut 只排除原问题不可行组合，因此不破坏 exactness。

Schedule capacity upper-bound cut：

```text
z[i,r] = sum_p a[i,p] lambda[p,r]

sum_{i in S} z[i,r] <= U(S) y[r]          for all r
```

其中 `U(S)` 是一辆真实车辆在完整多 sortie schedule 中最多能服务 `S` 内多少个任务。当前实现用 exact labeling oracle 计算；若 oracle 超过状态上限或不能证明，则不加 cut。

有效性：若 `y[r]=0`，车辆 `r` 不服务任何任务；若 `y[r]=1`，左侧是一辆车在 `S` 中服务的任务数，按 `U(S)` 定义不超过该上界。因此该 cut 不删除任何原问题整数可行解。

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
4. heuristic pricing 和 restricted integer master 只用于找列或找 incumbent；不能用于证明节点完成。
5. node lower bound 只在 full pricing + cut separation 后使用。
6. integer incumbent 必须通过 exact schedule checker。
7. pricing 中断时不能声明节点完成，也不能用该节点 bound 做证明。
8. 时间限制在节点证书完成前触发时，状态必须是 `TIME_LIMIT`。

因此 v1 可能慢，但不是启发式算法。
