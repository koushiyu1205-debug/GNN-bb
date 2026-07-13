# GAT_BPC_moonTerk Native SPPRC/ESPPRC Backend 执行计划规范

> 本文是给 Codex 的实施规划输入，不是已经完成的实现说明。  
> 目标是让 Codex先基于真实代码制定一份可执行计划，再由后续实现阶段按 gate 推进。

---

## 1. 文档元数据

| 字段 | 值 |
|---|---|
| Repository | `koushiyu1205-debug/GNN-bb` |
| Target directory | `GAT_BPC_moonTerk/` |
| Audited baseline commit | `48552b04c7bfc69ab95c0e2d664cbbe7c2ef206e` |
| Current model | `B4_3_SPPRC_LABELING_V1` |
| Current engine source | `internal_resource_label_core` |
| Primary proposed backend | custom native backend based on `lab-core/rcspp` |
| Optional worker backend | `RoutePricer/PathWyse` |
| Deferred alternative | `BALDES` |
| Planning language | 中文，代码标识保留英文 |
| Planning mode | 只制定计划，不改生产代码 |

实际执行前必须记录：

```bash
git rev-parse HEAD
git status --short
python --version
uname -a
```

如果实际 HEAD 与上述基线不同，计划需列出受影响文件和设计差异。

---

## 2. 任务定义

当前项目已经有一套较强的 exact-safe BPC 外壳：

- RMP 与 true dual；
- manual journey reduced-cost 公式；
- relaxed worker 与 exact final judge 分离；
- Ryan–Foster branch context；
- cut context；
- semantic column signature；
- certificate ledger；
- timeout/incomplete fail-closed；
- cold-start no-cheat runner；
- GAT guidance 与 exact proof boundary 分离。

当前主要缺口不是“没有 BPC 框架”，而是：

```text
SPPRC facade 已存在，
但底层仍主要是 Python/internal compact-pricing 与 exact final judge，
缺少成熟 native label engine 的吞吐、内存管理和完整 frontier 能力。
```

因此任务不是重写整个 solver，而是：

> 在保持现有证明边界和 Python orchestration 的前提下，替换或增强 pricing backend。

---

## 3. 当前真实模型必须被精确表达

### 3.1 Scale 与 benchmark

项目支持：

```python
SCALES = (5, 10, 20, 30, 50, 100)
```

对应 fleet、horizon、shadow cap 和时间限制均按规模变化。计划不能硬编码只支持 30。

### 3.2 每个逻辑有向边有三个 path option

```text
low_time
low_energy
low_risk
```

每个 option 具有独立的：

- travel time；
- energy；
- risk；
- distance；
- shadow exposure；
- path geometry。

native backend 必须保留 parallel-arc 语义，返回稳定 `arc_id`，不能只返回 node sequence 后猜测 `path_type`。

### 3.3 一个 column 是 multi-sortie journey

`JourneyColumn` 不是一条普通 VRPTW route，而是多个顺序 sortie 的组合：

```text
depot -> task sequence -> depot -> recharge
       -> task sequence -> depot -> recharge
       -> ...
```

全局状态：

- 已访问任务集合；
- 当前时间；
- 累计 objective；
- branch/cut state。

每个 sortie 内累积并在 depot return 后重置的状态：

- demand/capacity；
- energy；
- shadow exposure。

回 depot 后：

```text
recharge_time = dock_overhead + sortie_energy / recharge_power
next_sortie_start = return_time + recharge_time
```

但全局 visited 和 time 不重置。

### 3.4 Feasibility

至少包含：

- task time windows；
- `max_tasks_per_trip`；
- capacity；
- sortie energy limit；
- sortie shadow exposure limit；
- overall horizon；
- global task elementarity；
- branch context；
- 后续 live cuts 所需状态。

### 3.5 Official objective

当前 official objective 是按实例 reference 归一化的加性目标：

```text
weight_cost * normalized_operating_cost
+ weight_risk * normalized_risk
+ weight_completion * normalized_weighted_completion_time
```

makespan 只作为 metric，不进入 pricing objective。

weighted completion 必须在任务服务完成时，用当时的动态 completion time 计算。不能把它错误地预先压成固定 arc cost。

### 3.6 Reduced cost

当前 exact reduced cost：

```text
column.objective
- fleet_dual
- sum(task_cover_dual for visited tasks)
- sum(cut_dual * cut_coefficient)
```

native solver 内部可以使用增量 reduced cost，但返回 Python 后必须继续调用现有 manual RC 公式重新复核。

---

## 4. 不可破坏的证明契约

### 4.1 Guidance 永远不是 oracle

GAT、kNN、OOD、dual smoothing 和 heuristic ranking 只能影响：

- queue ordering；
- arc ordering；
- worker candidate selection；
- bounded delay；
- early negative harvesting。

它们不能：

- 永久删除 exact feasible arc；
- 把 true-negative column 永久排除；
- 产生 official lower bound；
- 产生 no-negative certificate；
- 导致 fathom/prune/OPTIMAL。

### 4.2 Worker 与 exact 必须分离

Worker 可使用：

- NG-route；
- stabilized dual；
- label/column cap；
- early stop；
- GAT priority；
- aggressive but audited candidate generation。

Worker 的 no-column 结果必须始终是：

```text
LOCAL_NO_COLUMN_UNCERTIFIED
```

或其他非证书状态。

Exact final judge 必须：

- 使用 current true RMP dual；
- 使用完整 exact elementarity；
- 不使用未经证明安全的 truncation；
- 不以 K columns、timeout、memory limit 或 interrupt 提前结束后发证书；
- 输出明确 native exit status；
- 通过现有 manual RC、branch、cut、reconstruction、coverage 和 certificate audit。

### 4.3 只有完整搜索才可证书

最低条件：

```text
native_status == COMPLETE
and no true-dual negative column
and reconstruction audit passes
and manual RC audit passes
and branch audit passes
and supported cut audit passes
and exact model feature coverage is complete
```

任何一项未知或失败，必须 fail closed。

---

## 5. 推荐架构

### 5.1 保留的外层

以下层原则上保留：

```text
RMP / HiGHS
column pool
pricing-tail orchestration
final judge gate
certificate ledger
semantic signatures
branch/cut contexts
benchmark and no-cheat shell
GAT guidance boundary
```

### 5.2 新增 backend registry

建议结构：

```text
GAT_BPC_moonTerk/
  src/lunar_ice_bpc/exact/bpc/pricing/
    backends/
      __init__.py
      protocol.py
      internal_backend.py
      native_rcspp_backend.py
      routepricer_worker_backend.py      # optional
```

稳定协议应接收：

```python
LunarIceData
JourneyDuals / ReducedCostContext
SpprcPricingRequest
BranchContext
CutContext
seed/support/existing task sets
wall-time and memory budgets
```

返回：

```python
native status
coverage status
columns
global min RC if known
label/extension/dominance telemetry
memory and timing telemetry
feature-support declaration
engine build hash
dependency versions
```

### 5.3 Native C++ 建议目录

具体路径由 Codex 审计后决定，建议之一：

```text
GAT_BPC_moonTerk/native/lunar_spprc/
  CMakeLists.txt
  pyproject.toml or top-level build integration
  include/lunar_spprc/
    model.hpp
    state.hpp
    extension.hpp
    feasibility.hpp
    dominance.hpp
    branch_state.hpp
    cut_state.hpp
    solver.hpp
    result.hpp
  src/
    model.cpp
    solver.cpp
    bindings.cpp
  tests/
```

不要把整个外部项目源码无审计地复制进仓库。优先：

- pinned Git submodule；
- CMake `FetchContent` pinned commit；
- 或明确的最小 fork。

---

## 6. 后端选择的 feasibility spike

在正式编码前必须安排一个小型 spike，并把结论写入 ADR。

### 6.1 `lab-core/rcspp` 必查项

验证：

- C++23 工具链是否可用；
- cyclic graph 是否 exact-safe；
- repeated depot node 是否允许；
- path 可否重复 depot 但不能重复 task；
- parallel arcs 和稳定 arc IDs；
- custom composite state；
- custom cross-resource extension；
- custom feasibility；
- custom dominance；
- exact visited bitset；
- timeout/memory/interrupt 状态；
- `COMPLETE` 是否表示 frontier exhaustion；
- Python binding 如何返回 arc IDs、resources、telemetry；
- 是否必须 fork Python bindings；
- bucket container 与 custom state 是否兼容；
- preprocessor 是否会错误删除 multi-sortie/recharge arcs；
- upper-bound pruning 是否需要关闭。

### 6.2 判定规则

若 public API 能正确表达模型：

```text
使用 pinned lab-core/rcspp + 小型 project extension。
```

若核心算法可用但 binding 不够：

```text
增加项目本地 pybind layer，尽量不 fork solver core。
```

若 custom state、cyclic multi-sortie 或 exact status 无法保证：

```text
选择最小 fork，或在项目 native 目录实现专用 labeler；
不得通过错误简化模型来强行适配。
```

### 6.3 `RoutePricer/PathWyse` spike

只评估 worker：

- 单 sortie ESPPRC candidate；
- multi-path parallel arc 的 graph expansion 成本；
- DSSR/NG worker 的 column throughput；
- 多解返回；
- true-dual Python re-audit；
- GPLv3 影响。

不得把其 no-column 结果直接升级为 certificate。

### 6.4 BALDES spike 的触发条件

只有以下情况才投入深入评估：

- live SRC/rank-1 cuts 已成为主线；
- branch tree 而非 root pricing 成为瓶颈；
- native rcspp 路线被技术证据否决；
- 能明确实现 weighted completion、multi-sortie reset 和 current branch semantics。

---

## 7. Native graph 与 state 设计要求

### 7.1 Graph

推荐保留逻辑节点：

```text
source/depot
task nodes
sink
```

每个 path option 是独立 arc。

必须验证 cyclic depot graph。若底层 labeler不能安全处理重复 depot，可考虑显式 state-machine node，但不得造成不可接受的 `O(n^3)` 图膨胀或破坏 elementarity。

### 7.2 Label state

第一版 exact state 至少包含：

```cpp
current_node
global_time
sortie_task_count
sortie_demand
sortie_energy
sortie_shadow
accumulated_reduced_cost
global_visited_tasks
sortie_count or depot phase
branch obligations/state
```

返回结果还需要 predecessor arc chain。

### 7.3 Extension

任务 arc extension：

1. 加 travel time；
2. 应用 ready time；
3. 检查 due time；
4. 加 service time；
5. 加 arc/task energy；
6. 加 arc/task risk；
7. 加 arc/task shadow；
8. 加 demand；
9. 加 normalized cost/risk；
10. 按动态 completion time 加 weighted-completion objective；
11. 减 task cover dual；
12. 更新 visited 与 branch/cut state。

返回 depot：

1. 加 return travel；
2. 检查 sortie resource feasibility；
3. 加 dock/recharge time；
4. 检查 horizon；
5. reset sortie demand/energy/shadow/task count；
6. 保留 global time/visited/objective/branch state。

从 source 开始时只减一次 fleet dual。

### 7.4 Elementarity

全局 task visited 必须跨 sorties 保留。

若实现 graph expansion 或 path-option node copies，visited key 必须使用逻辑 task ID，而不是物理图 node ID。

### 7.5 Ryan–Foster state

`different_journey(a,b)`：

- 一旦两者都进入当前 journey，label infeasible。

`same_journey(a,b)`：

- partial label 允许只访问一个；
- 到 sink 时必须两者都出现或都不出现；
- dominance key 必须区分尚未履行的 pair obligation；
- 不得在访问第一个任务后立即错误剪枝。

### 7.6 Cuts

分阶段：

1. empty cuts；
2. fleet-lower-bound cut；
3. task-set-only subset-row cuts；
4. 更复杂 cut memory。

Subset-row 系数：

```text
floor(overlap / divisor)
```

不能仅用普通逐 arc coefficient 直接表示。可以在访问 cut task 时按 threshold crossing 增量扣 dual，但必须维护足够的 cut state，并证明 dominance 兼容性。

### 7.7 Dominance

第一版宁可保守，也不能错误。

候选条件示意：

```text
same current logical node
compatible branch/cut/depot phase
visited_A subset_of visited_B
time_A <= time_B
sortie_task_count_A <= sortie_task_count_B
demand_A <= demand_B
energy_A <= energy_B
shadow_A <= shadow_B
reduced_cost_A <= reduced_cost_B
```

需要证明这些条件对未来可扩展集与未来成本均安全。

若 exact dominance 证明未完成，应保留更多 labels，而不是启用可疑剪枝。

---

## 8. Exact 与 worker 两种运行模式

### 8.1 Worker mode

目的：快速找到 addable negative columns。

允许：

- NG-route；
- dual stabilization；
- GAT/heuristic ordering；
- K-column stop；
- time cap；
- label cap；
- aggressive harvesting；
- parallel workers。

强制：

- 每列返回 Python 后用 current true dual 重算；
- worker no-column 永不 certificate；
- 日志必须记录 candidate dual 与 true dual 是否相同。

### 8.2 Exact mode

目的：no-negative proof。

第一版建议：

- forward exact labeling；
- exact visited bitset；
- no label truncation；
- no max-solutions stop；
- no stabilized dual；
- no unsafe preprocessor；
- no unsafe cost upper-bound pruning；
- no unproved bidirectional join；
- current true RMP dual；
- explicit COMPLETE/incomplete status。

待 forward exact 差分验收后，再逐项加入：

- bucket labels；
- exact-safe completion lower bounds；
- preprocessing；
- bidirectional labeling；
- dynamic half-way；
- frontier checkpoint。

每加一项都要有 on/off 一致性测试。

---

## 9. 两阶段 exact pricing

建议保留当前“harvest + proof”思想：

### Pass A：negative harvest

- exact model；
- true dual；
- 可设置 K-column stop；
- 返回多条不同 task-set/signature 的负列；
- 该 pass 自身不能发 no-negative certificate。

### Pass B：proof

- 不设置 K stop；
- 完整搜索；
- 若发现负列，返回并继续 CG；
- 只有 COMPLETE 且无负列时 certificate。

计划必须说明如何避免 Pass B 每轮从零重复做大量工作：

- 可复用静态 graph/model；
- 可复用无 dual 依赖的预处理；
- 可复用内存池；
- dual 相关 bound 必须重新计算或正确 invalidation；
- 长期目标是 checkpointable exact frontier。

---

## 10. 文件级变更计划要求

Codex 的计划必须列出：

### 10.1 预期新增

示例：

```text
src/lunar_ice_bpc/exact/bpc/pricing/backends/protocol.py
src/lunar_ice_bpc/exact/bpc/pricing/backends/internal_backend.py
src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp_backend.py
native/lunar_spprc/...
tests/test_native_spprc_backend.py
tests/test_native_spprc_differential.py
tests/test_native_spprc_fail_closed.py
tests/test_native_spprc_branching.py
tests/test_native_spprc_scale_smoke.py
configs/experiments/native_spprc_shadow.yaml
configs/benchmarks/native_spprc_acceptance.yaml
docs/design/native_spprc_backend.md
```

### 10.2 预期修改

至少审计：

```text
spprc_pricer.py
final_judge.py
pricing_tail_solver.py
run_lunar_ice_b4_3_spprc_labeling.py
相关 config hash/build hash 输出
benchmark/audit/report 代码
```

### 10.3 原则上不修改语义

```text
manual_journey_reduced_cost
JourneyColumn official objective
certificate ledger core rules
GAT proof boundary
cold-start no-cheat definition
```

若确需修改，计划必须单独列出数学原因和差分测试。

---

## 11. 测试策略

### 11.1 单元测试

覆盖：

- task extension；
- wait and time windows；
- service completion objective；
- capacity；
- energy；
- shadow；
- depot recharge/reset；
- multiple sorties；
- repeated-task rejection；
- three path options；
- arc-ID reconstruction；
- objective normalization；
- fleet/task dual application；
- branch state；
- supported cut state；
- dominance positive/negative cases。

### 11.2 Differential tests

对 5-task 全量或大量随机实例，比较 native 与 internal exhaustive oracle：

- global minimum RC；
- negative/no-negative；
- best task set；
- route semantic signature；
- objective；
- completion times；
- resource values；
- branch feasibility；
- cut coefficients。

对 10-task 做固定 acceptance corpus 与随机 corpus。

误差门槛建议：

```text
objective / manual RC absolute error <= 1e-7
```

若内部代码在 6 位小数处 round，计划必须明确 canonical comparison 层。

### 11.3 Metamorphic tests

至少：

- 增大 capacity/energy/shadow cap 不应减少可行列；
- 放宽 due time 不应使原可行路径不可行；
- 所有 task dual 同时增加时，包含更多任务的 reduced cost 按公式变化；
- 切换 path option 只影响对应 arc 的资源和 cost；
- completion bound on/off 在 exact complete 时给出同一 global min RC；
- bucket on/off 在 exact complete 时一致；
- worker ordering 改变不能改变 exact proof。

### 11.4 Fail-closed tests

强制注入：

- timeout；
- interrupt；
- memory limit；
- max solutions；
- label cap；
- max phases；
- unsupported cut；
- unsupported branch feature；
- corrupted reconstruction；
- dual fingerprint mismatch；
- engine build hash mismatch。

所有情况都必须证明：

```text
can_certify_no_negative == False
uses_true_dual_bpc_certificate == False
```

### 11.5 Regression

现有关键测试必须继续通过：

```text
tests/test_lunar_ice_labeling_pricer.py
tests/test_lunar_ice_smoke.py
```

不得通过删除断言来“修复”测试。

---

## 12. Scale 验收矩阵

“在 50/100 可使用”与“50/100 必须在当前时限内 exact optimal”是不同要求。

本文定义：

- 5/10/20：必须 exact closure，并优化性能；
- 30：必须 exact closure，且显著加速；
- 50/100：必须 robust exact-safe operation；exact closure 是 stretch goal，未完整时必须 fail closed。

| Scale | Correctness hard gate | Performance target | Large-scale behavior |
|---:|---|---|---|
| 5 | objective、RC、signature、certificate 与基线一致 | median wall time 至少下降 20% | 全量 differential |
| 10 | exact closure 与基线一致 | median 至少下降 30% | 固定 corpus + 随机 differential |
| 20 | exact closure，不允许证书回归 | median 至少下降 40% 或显著降低 exact-pricing 占比 | 记录 RSS/labels |
| 30 | strict cold-start `BPC_TREE_OPTIMAL` | hard ≤1800s；target ≤900s；stretch ≤600s | 不使用 mature probe/per-instance override |
| 50 | 可启动、可定价、可恢复、true-RC audit 通过、无错误证书 | native worker/pricer 明显优于 Python baseline | timeout/内存后 `INCOMPLETE_LIMIT` 合法 |
| 100 | 同 50，且无不可控内存增长 | label throughput 与 memory telemetry 稳定 | 必须支持 configurable memory/time guard |

若 5/10/20 当前基线本身很快，百分比指标可能受启动时间噪声影响。计划需同时报告：

- pure pricing time；
- graph build time；
- binding overhead；
- RMP time；
- total wall time。

### 12.1 30-scale benchmark 顺序

1. `instance001` shadow correctness；
2. `instance001` cold-start closure；
3. matched-hardware 重复；
4. 再扩展到多实例；
5. 未过 instance001 gate 前，不盲目跑完整 30-scale matrix。

### 12.2 50/100 smoke

至少验证：

- graph construction；
- one worker round；
- one exact bounded run；
- true-dual re-audit；
- state/report serialization；
- timeout；
- memory guard；
- same-run resume；
- no certificate leak。

---

## 13. Benchmark 规则

### 13.1 Baseline

冻结：

```text
commit
config
instance manifest
hardware
thread count
solver/library versions
environment variables
```

基线优先为当前 main 的官方 B4.3 cold-start runner。

### 13.2 Cold-start

禁止：

- 历史同实例列池；
- mature probe；
- source probe；
- 手工列；
- per-instance profile；
- 从以前 run 读取 dual-dependent frontier。

允许：

- 固定通用 seed；
- 同一次 run 的 checkpoint/resume；
- 无 dual 依赖且由当前 instance 重建的静态 cache；
- 所有累计时间计入总时间。

### 13.3 指标

必须输出：

- total wall；
- graph build；
- worker；
- exact harvest；
- exact proof；
- RMP；
- reconstruction/audit；
- peak RSS；
- labels created/extended；
- dominance checks/pruned；
- queue/bucket size；
- negative candidates；
- true-negative audited；
- columns returned/added/duplicate/replacement；
- active pool size；
- best RC；
- native exit status；
- certificate state；
- config/engine/dependency hashes。

### 13.4 重复次数

建议：

- 5/10：至少 3 次；
- 20：至少 2 次；
- 30：先单次长跑，达标后再做重复；
- 50/100：smoke + 至少一次 bounded profile。

---

## 14. 依赖与构建政策

### 14.1 允许安装

Codex 可自行安装缺失工具，例如：

```bash
python -m venv .venv-native-spprc
source .venv-native-spprc/bin/activate
python -m pip install --upgrade pip
python -m pip install cmake ninja scikit-build-core pybind11 pytest numpy highspy
```

外部 engine 应 pin：

```text
repository URL
commit SHA/tag
license
build flags
compiler version
```

### 14.2 许可证

- `lab-core/rcspp`：计划中核验当前许可证与 pinned commit；
- `PathWyse/RoutePricer`：GPLv3，作为依赖前明确分发影响；
- `BALDES`：核验 pinned revision 的许可证和 third-party dependencies。

### 14.3 不允许的下载

不得下载：

- 对应 benchmark instance 的预求列池；
- 已知 optimal route pool；
- mature probe；
- source probe；
- 人工筛选的 per-instance seed；
- 会让 cold-start 失真的求解 artifact。

---

## 15. 性能优化顺序

严格按风险从低到高：

1. Python/C++ boundary 批处理；
2. graph/model reuse；
3. static arc/resource preprocessing；
4. label pool reuse；
5. compact bitset；
6. exact-safe dominance；
7. bucket container；
8. negative batch harvesting；
9. exact-safe lower bounds；
10. parallel worker；
11. exact parallelism；
12. bidirectional join；
13. checkpointable proof frontier；
14. live cut memory。

每一步都要有：

```text
feature flag
on/off differential
performance profile
rollback
certificate compatibility statement
```

---

## 16. 50/100 的内存与恢复

必须规划：

- `max_memory_gb` 或等价 hard limit；
- pressure telemetry；
- exact mode 下不得用丢弃非 dominated labels 的方式继续声称 COMPLETE；
- worker 可截断，但只能 candidate-only；
- stage-level checkpoint；
- 长期 exact frontier serialization；
- graph/static data 与 dual-dependent state 分离；
- cache invalidation key 至少包括 instance、objective、dual、branch、cut、engine build 和关键 config。

若 exact frontier 暂时无法序列化：

- 明确这是风险；
- 50/100 仍可做 bounded exact-safe run；
- 退出状态必须 incomplete；
- 不得把只保存 columns 等同于保存 proof frontier。

---

## 17. 风险与 fallback

### 风险 A：`lab-core/rcspp` 无法精确表达 cyclic multi-sortie

Fallback：

1. 最小 fork 增加 custom composite state；
2. project-native 专用 labeler；
3. BALDES feasibility spike；
4. PathWyse 仅保留 worker。

### 风险 B：visited bitset 导致 label explosion

缓解：

- safe dominance；
- NG worker；
- bucket；
- completion lower bound；
- candidate harvest；
- memory telemetry；
- 先 forward exact 正确性，再 bidirectional。

### 风险 C：weighted completion 使 backward join 困难

缓解：

- 第一版 exact forward-only；
- backward label 必须携带足够的 affine completion information；
- 未完成数学推导前不得启用 bidirectional certificate。

### 风险 D：live subset-row cuts 破坏 dominance

缓解：

- 第一版 empty cuts；
- fleet cut；
- task-set subset-row incremental state；
- unsupported cuts fail closed；
- cut-aware signature 与 audit。

### 风险 E：外部依赖不稳定

缓解：

- pinned commit；
- wrapper boundary；
- internal backend fallback；
- CI build matrix；
- engine build hash；
- dependency lock。

---

## 18. 分阶段实施模板

Codex 输出的计划应把每一阶段写成：

```markdown
### Phase X: 名称

**目标**

**读取/修改文件**

**设计与实现步骤**

**依赖/命令**

**测试**

**Benchmark**

**Exit gate**

**Rollback**

**已知风险**
```

推荐阶段：

1. Repository audit and baseline freeze；
2. Native dependency/toolchain feasibility；
3. Backend protocol extraction；
4. Native model/state/extension；
5. Path reconstruction and true-RC audit；
6. 5-task exact differential；
7. 10/20 exact promotion；
8. 30-scale root integration and profiling；
9. Native worker/negative harvesting；
10. Ryan–Foster branch support；
11. Cut support；
12. 50/100 memory/resume hardening；
13. Bucket/bounds/bidirectional performance；
14. Official acceptance and documentation。

---

## 19. Definition of Done

只有同时满足以下条件，才能称为完成：

### Correctness

- 5/10/20 exact differential 通过；
- 30 strict cold-start exact optimal gate 通过；
- no false negative/no false certificate；
- path reconstruction 与 manual RC 一致；
- branch/cut supported scope 明确；
- unsupported scope fail closed。

### Performance

- 5/10/20 有可复现优化；
- 30 ≤1800 秒，目标 ≤900 秒；
- 50/100 bounded run 稳定；
- peak RSS 和吞吐有 telemetry；
- 性能来自通用算法，不是 per-instance hardcode。

### Engineering

- dependency pinned；
- reproducible build；
- backend fallback；
- config/build hash；
- tests；
- benchmark report；
- rollback path；
- documentation；
- no-cheat audit。

### Proof discipline

- worker no-column 永不 certificate；
- stabilized dual 永不 official proof；
- timeout/memory/interrupt/K-stop 永不 COMPLETE；
- GAT 不改变 exact feasible space；
- official objective 未被静默修改。

---

## 20. Codex 最终计划的输出格式

最终计划文档必须包含：

1. Executive summary；
2. Audited current-state call graph；
3. Architecture decision and rejected alternatives；
4. Mathematical state/resource formulation；
5. File-by-file change map；
6. Phase plan；
7. Dependency installation/build commands；
8. Test matrix；
9. Benchmark matrix；
10. Acceptance gates；
11. Risk/fallback table；
12. Rollback strategy；
13. Estimated critical path，以依赖关系表达，不要只给模糊工期；
14. First implementation milestone；
15. Definition of Done。

计划应回答：

> Codex 下一次进入实现模式时，第一条命令、第一处代码修改、第一组测试和第一个性能 gate 分别是什么？
