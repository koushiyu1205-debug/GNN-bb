# Clean BPC 模型记录

本文档记录根目录 `bpc/` 下 clean Branch-Price-and-Cut 主线的模型状态、实现边界和修改历史。后续每次修改 `bpc/` 主线时，不覆盖已有描述；在“模型记录”中追加新的日期时间小节，并说明本次修改内容、为什么修改、是否影响 exactness。

## 当前主线定位

`bpc/` 是独立于旧 `src/gnn_bb/bp/` 的 clean BPC 实现。旧代码只作为参考，不作为本主线入口。

SCIP 的职责：

- 求解每个节点的 Restricted Master Problem LP；
- 返回 primal solution 和 dual values；
- 处理 LP 数值计算。

`bpc/` 自己负责：

- BPC 搜索树；
- Phase-I / Phase-II RMP 控制；
- exact RCSP pricing；
- schedule no-good cuts；
- branching；
- incumbent 可行性验证；
- lower bound / upper bound / gap 证明逻辑；
- JSONL 日志。

明确不进入当前 clean 主线的内容：

- SCIP 默认 B&B 树；
- outer cut-and-resolve；
- SCIP lazy constraint handler；
- column pool；
- stabilized pricing；
- reduced graph heuristic pricing；
- ng relaxation；
- ML branching；
- pricing time budget 参与证明。

## 模型记录

### 2026-05-11 21:10:14 CST +0800

#### 版本备注

建立 `bpc/` clean BPC 初始模型说明。当前版本优先保证流程规范和 exactness 可审查，不以性能为第一目标。

#### Master Formulation

当前采用 route-vehicle DW master。列是一条资源可行 sortie route：

```text
p = 0 -> i1 -> i2 -> ... -> iq -> 0
```

route 内部满足：

- 任务时间窗；
- 载重上界 `Q`；
- sortie 电量上界 `B_use`；
- 单条 sortie 返回 depot；
- route 内任务不重复。

集合和参数：

```text
I        任务集合
R        车辆集合
P        当前已生成 route 集合
a_ip     route p 是否服务任务 i
c_p      route p 的行驶 + 服务成本
w_p      route p 的车辆工作时间下界
F        固定车辆成本
H        单车总工作时间上界
S_bar    单车最多 sortie 数上界
C        已加入的 schedule no-good cuts
```

变量：

```text
lambda[p,r] >= 0   RMP LP 中车辆 r 是否选择 route p 的松弛变量
0 <= y[r] <= 1     RMP LP 中车辆 r 是否启用的松弛变量
u[i]        >= 0   Phase-I 人工覆盖变量
```

Phase-I RMP：

```text
min sum_i u[i]

sum_r sum_p a_ip lambda[p,r] + u[i] = 1       for all i in I
sum_p a_ip lambda[p,r] <= y[r]                for all i in I, r in R
sum_p lambda[p,r] <= S_bar y[r]               for all r in R
sum_p w_p lambda[p,r] <= H y[r]               for all r in R
y[r+1] <= y[r]
schedule cuts
branching constraints
```

Phase-II RMP：

```text
min sum_r F y[r] + sum_r sum_p c_p lambda[p,r]

sum_r sum_p a_ip lambda[p,r] = 1              for all i in I
sum_p a_ip lambda[p,r] <= y[r]                for all i in I, r in R
sum_p lambda[p,r] <= S_bar y[r]               for all r in R
sum_p w_p lambda[p,r] <= H y[r]               for all r in R
y[r+1] <= y[r]
schedule cuts
branching constraints
```

其中：

```text
w_p = travel_time_p + service_time_p + energy_p / rho
```

`w_p` 是车辆工作时间下界，不包含不同 sortie 之间的等待时间。真实多 sortie 时间顺序由 exact schedule checker 和 no-good cuts 处理。

#### Pricing

pricing 是 exact RCSP。当前版本不使用 heuristic pricing。

设：

```text
pi_i      任务覆盖约束 dual
eta_r     sortie 数约束 dual
beta_r    车辆工作时间约束 dual
gamma_g   schedule cut dual
b_gpr     route-vehicle column 在 cut g 中的系数
```

Phase-II reduced cost：

```text
rc(p,r) = c_p
        - sum_i a_ip pi_i
        - eta_r
        - beta_r w_p
        - sum_g b_gpr gamma_g
```

Phase-I reduced cost：

```text
rc_I(p,r) = 0
          - sum_i a_ip pi_i
          - eta_r
          - beta_r w_p
          - sum_g b_gpr gamma_g
```

节点只有在 exact pricing 使用 true dual 完整结束，并证明不存在负 reduced-cost route 后，才允许使用该节点 lower bound。

#### Cuts

当前只实现 schedule no-good cut。

如果整数解中某辆车选择的 route 集合 `Q` 无法排成真实执行顺序，则加入：

```text
sum_{p in Q} lambda[p,r] <= |Q| - 1
```

当前实现会对所有同质车辆加入同类 cut。该 cut 只排除 exact schedule checker 已证明不可行的 route 组合，因此不改变原问题可行域。

#### Branching

当前 branching 顺序：

1. Ryan-Foster branching；
2. task-vehicle assignment branching；
3. vehicle-use branching。

Ryan-Foster：

```text
same(i,j)=1: route 中必须同时包含 i,j 或同时不包含 i,j
same(i,j)=0: route 中不能同时包含 i,j
```

task-vehicle：

```text
task i on vehicle r
task i off vehicle r
```

vehicle-use：

```text
y[r] = 0
y[r] = 1
```

这些 branching constraints 都能传递到 RMP 和 pricing，且左右子节点覆盖父节点解空间。

#### Exactness 备注

当前版本保持 exactness 的条件：

- RMP 初始可行由 Phase-I 人工变量保证；
- reduced cost 与 RMP dual 一致；
- exact pricing 使用 true dual、branching constraints、cut duals；
- heuristic pricing 不参与证明；
- node lower bound 只在 full pricing 后使用；
- integer incumbent 必须通过 exact schedule checker；
- 若 pricing 中断，不得声明节点完成或使用该节点 bound 证明。

#### 已验证命令

very small smoke test：

```bash
cd /home/kai/work/gnn_bb

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances very_small \
  --time-limit 30 \
  --max-nodes 200 \
  --results-csv results/smoke/bpc_clean_very_small.csv \
  --log-dir results/smoke/logs/bpc_clean \
  --solution-dir results/smoke/solutions/bpc_clean
```

结果：

```text
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
nodes=3
rmp=6
pricing=4
```

20 规模短测：

```bash
cd /home/kai/work/gnn_bb

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 5 \
  --max-nodes 2 \
  --results-csv results/smoke/bpc_clean_medium_5s.csv \
  --log-dir results/smoke/logs/bpc_clean_medium_5s \
  --solution-dir results/smoke/solutions/bpc_clean_medium_5s \
  --quiet
```

结果：

```text
status=NODE_LIMIT
primal=None
dual=490.283693
gap=None
nodes=2
rmp=9
pricing=7
routes=663
cuts=0
```

#### 后续修改记录规则

以后修改 `bpc/` 时，在本节之后追加新条目，格式为：

```text
### YYYY-MM-DD HH:MM:SS TZ +offset

#### 版本备注
说明本次改了什么。

#### 数学/算法变化
说明模型、pricing、cuts、branching 或 proof logic 是否变化。

#### Exactness 影响
说明是否影响精确性，若有风险，写清 fallback 或证明条件。

#### 验证命令与结果
记录至少一个 smoke test。
```

### 2026-05-11 21:19:39 CST +0800

#### 版本备注

本次修复 clean BPC 在 20 规模 `medium` 上过早进入 `BRANCH_FAILED` 的问题：

- `branching.py` 增加对已固定 Ryan-Foster、task-vehicle、vehicle-use 分支的过滤，避免同一路径上重复选择已经被固定的候选。
- 增加 `route_signature` fallback branching，避免 LP 解仍分数但 RF / task-vehicle / vehicle-use 都无法给出候选时直接失败。
- `rmp.py` 支持 `vehicle_use_on/off` 和 `route_signature_on` 约束。
- `tree.py` 的初始 incumbent 从单任务贪心改为 schedule-aware 插入贪心：优先尝试把任务插入已有 route，必要时新开 route，并且仍通过 schedule 可行性检查。

#### 数学/算法变化

主模型仍是 route-vehicle Dantzig-Wolfe master：

- route column 表示一条资源可行 sortie；
- master 决定每辆车选哪些 route；
- exact pricing 仍是完整 RCSP；
- cut 仍是 schedule no-good cut；
- BPC tree 仍由 Python 显式控制，SCIP 只求解 RMP LP。

新增的 `route_signature` fallback 使用二分：

- 左支：禁止某个具体 route signature；
- 右支：要求至少选择一次该 route signature。

这是对当前 route-column master 的有效分支，用于补足分支候选缺口。

#### Exactness 影响

本次修复不引入启发式剪枝，也不允许 heuristic pricing 证明无负 reduced-cost 列。node bound 仍只在 exact pricing 完成后使用。

需要注意：`route_signature_on` 是 fallback 分支，只应在常规 RF / task-vehicle / vehicle-use 候选都不可用时触发。它是有效 disjunction，但不是长期最优的 VRP 分支策略；后续如果要做高性能 BPC，应减少它被频繁触发。

#### 验证命令与结果

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 2 tests in 0.127s
OK
```

20 规模运行命令：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 3600 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium.csv \
  --log-dir results/logs/bpc_clean \
  --solution-dir results/solutions/bpc_clean \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_terminal.log
```

运行观察：

- 初始 schedule-aware greedy incumbent：`743.688845`。
- root LP 完成并进入分支树，root bound 约为 `490.283693`。
- 修复后不再立即出现 `BRANCH_FAILED`。
- 约 132 秒时 open nodes 已超过 700，incumbent 没有改善，global lower bound 仍提升较慢。

当前判断：

- clean BPC 的 exactness 流程比旧实验代码更清楚，但 20 规模性能仍不健康。
- 当前瓶颈不是 root pricing，而是 branching 太弱、incumbent 太差、cut 强度不足。
- 下一步优先级应是：先加强 primal heuristic 得到接近 `526.9` 的真实 schedule incumbent，再做更强 branching；否则 gap 会被弱 UB 长时间拖住。

### 2026-05-11 21:21:08 CST +0800

#### 版本备注

补充一次 20 规模 `medium` 的自然 time-limit 验证，确认修复后的 clean BPC 能正常到时退出并写出 CSV。

#### 数学/算法变化

无模型变化，仅补充验证记录。

#### Exactness 影响

无影响。

#### 验证命令与结果

命令：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 30 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium_30s.csv \
  --log-dir results/logs/bpc_clean_30s \
  --solution-dir results/solutions/bpc_clean_30s \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_30s_terminal.log
```

结果：

```text
status=TIME_LIMIT
primal=743.688845
dual=494.885971
gap=0.334552
time=30.051416s
nodes=149
rmp=308
pricing=181
routes=946
cuts=21
```

评价：

- 修复后不再是结构性失败，程序能正常记录 `TIME_LIMIT`。
- root pricing 正常，root bound 约 `490.283693`。
- 30 秒内 incumbent 没有从 `743.688845` 改善，说明当前 schedule-aware greedy incumbent 仍然太弱。
- 大量节点仍停在 `494.885971` 附近，说明 branching 对 lower bound 推进不足。

### 2026-05-11 21:31:28 CST +0800

#### 版本备注

加强 clean BPC 的 primal heuristic：

- 初始化阶段从单一贪心改为 multi-start construction。
- 加入 route sequence permutation 改良。
- 加入 task relocate 局部搜索。
- 加入整条 route 跨车辆移动，用于减少车辆固定成本。
- 当 RMP 给出整数 route 集合但当前车辆排程不可行时，先尝试把这些 route 重新分配到车辆，若得到真实 schedule 可行解则更新 incumbent，然后仍继续加 schedule cut。

#### 数学/算法变化

主 BPC 数学模型没有变化。新增内容全部属于 primal heuristic：

- 不改变 RMP lower bound；
- 不改变 reduced cost；
- 不改变 exact pricing 证明；
- 不剪枝；
- 只在通过原问题 schedule feasibility 检查后更新 incumbent。

#### Exactness 影响

不破坏 exactness。heuristic 只提供上界，所有 node lower bound 仍然必须在 exact pricing 完成后才能使用。

#### 验证命令与结果

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 2 tests in 0.143s
OK
```

`very_small` smoke：

```text
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
nodes=1
```

20 规模 30 秒对比：

```text
上一版:
  status=TIME_LIMIT
  primal=743.688845
  dual=494.885971
  gap=0.334552
  nodes=149

本版:
  status=TIME_LIMIT
  primal=626.902419
  dual=495.116564
  gap=0.210217
  nodes=85
```

20 规模 120 秒结果：

```text
status=TIME_LIMIT
primal=626.902419
dual=500.885206
gap=0.201016
nodes=673
rmp=1368
pricing=773
routes=1608
cuts=45
```

评价：

- primal heuristic 明显改善 UB：`743.688845 -> 626.902419`。
- 30 秒 gap 明显下降：`33.46% -> 21.02%`。
- 120 秒内 UB 没有继续改善，说明继续堆贪心收益有限。
- 下一步应转向 branching/cuts：减少大量节点停留在 `494.885971 ~ 501` 的平台区间。

### 2026-05-11 21:39:05 CST +0800

#### 版本备注

替换 `route_signature` fallback branching：

- 删除 route-signature on/off fallback。
- 新增 arc-usage branching：
  - 左支 `arc(i,j)=off`：pricing 禁止 route 内部直接使用任务弧 `i -> j`；
  - 右支 `arc(i,j)=on`：RMP 加入 `sum q[i,j,p] lambda[p,r] >= 1`，并把该分支约束 dual 放入 pricing reduced cost。
- 更新 `docs/bpc_clean_formulation.md`，正式声明当前模型是 `route-vehicle BPC with schedule cuts`，不是 `vehicle-schedule BPC`。

#### 数学/算法变化

当前 branching 顺序变为：

```text
Ryan-Foster
task-vehicle assignment
arc-usage
vehicle-use
```

`arc_on` reduced cost 增加分支 dual：

```text
rc[p,r] = ...
        - sum_h q[h,p,r] delta[h]
```

其中 `q[h,p,r]=1` 表示 route `p` 内部包含对应有向任务弧。

#### Exactness 影响

这是正向收紧：

- 删除了较不结构化的 route-signature fallback；
- arc-usage branching 是 VRP route master 中常见的 pricing-compatible 结构分支；
- `arc_on` 的 RMP dual 已进入 exact pricing；
- `arc_off` 直接传递为 pricing 中的 route 过滤规则。

当前仍不是 vehicle-schedule BPC，而是 route-vehicle BPC with schedule cuts。route-vehicle master 是原问题的松弛，schedule cuts 用来排除不可排程的整数 route 组合。只要 schedule cuts valid，且 node bound 只在 exact pricing + cut separation 后使用，仍保持精确性。

#### 验证命令与结果

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 3 tests in 0.139s
OK
```

`very_small` smoke：

```text
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
nodes=1
```

20 规模 30 秒短测：

```text
status=TIME_LIMIT
primal=626.902419
dual=495.116564
gap=0.210217
nodes=86
rmp=188
pricing=117
routes=1150
cuts=6
```

观察：

- 没有再出现 route-signature 分支。
- 30 秒结果与上一版基本一致，没有因为替换 fallback 出现明显回退。
- 目前分支日志中主要仍是 Ryan-Foster、task-vehicle 和 vehicle-use；arc branching 是结构化 fallback，只有前面候选不可用时才触发。

### 2026-05-11 21:46:47 CST +0800

#### 版本备注

新增最优性证明文档：

```text
docs/bpc_clean_optimality_proof.md
```

#### 数学/算法变化

无代码和模型变化，仅补充证明文档。证明文档覆盖：

- route-vehicle master 与原问题的松弛关系；
- schedule no-good cuts 的有效性；
- RMP / full master / pricing 的 LP 最优性关系；
- Phase-I 不可行证明；
- Ryan-Foster、task-vehicle、arc-usage、vehicle-use branching 的覆盖性；
- incumbent 原问题可行性；
- node lower bound 与全局最优性证明；
- time limit 下 UB/LB/gap 的含义。

#### Exactness 影响

无直接影响。该文档明确了当前 clean BPC 要保持 exactness 必须满足的工程条件：

```text
schedule separation 完整；
exact pricing 完整；
branching 完整；
node bound 只在完整定价和切割后使用。
```

#### 验证命令与结果

文档检查：

```bash
cd /home/kai/work/gnn_bb
test -f docs/bpc_clean_optimality_proof.md
```

### 2026-05-12 07:44:59 CST +0800

#### 版本备注

新增 no-ML 3PB branching baseline。这里的 3PB 是论文中的 no-ML branching baseline 思路：先用便宜候选筛选，再做 LP testing，最后对少量候选做更贵的 heuristic testing。当前实现只影响分支候选选择，不参与剪枝、不证明节点最优、不影响 exact pricing。

#### 代码变化

主要修改：

```text
bpc/branching.py
bpc/tree.py
bpc/solver.py
scripts/run_bpc_clean.py
configs/bpc_clean.yaml
```

新增内容：

- `BranchCandidate`：统一描述 Ryan-Foster、task-vehicle、arc-usage、vehicle-use 分支候选。
- `generate_branch_candidates`：为当前 LP 解生成完整候选集。
- 3PB 筛选流程：
  - 第一阶段：用已有 pseudo-cost 和 fractionality 选择候选；
  - 第二阶段：对候选做 restricted child RMP LP testing；
  - 第三阶段：对少量候选做 limited pricing heuristic testing；
  - 最终按测试分数选择分支。
- JSONL 日志新增：
  - `branch_candidates`：记录候选数量、候选类型分布、筛选后的候选；
  - `branch_selection`：记录每个测试候选的 LP score、heuristic score、左右子节点测试结果、最终选择。

#### Exactness 影响

不破坏精确性：

- 3PB 只改变 branching candidate 的选择顺序。
- LP testing 和 heuristic testing 的结果只用于打分，不用于节点剪枝。
- 节点 lower bound 仍然只在完整 exact pricing 和 cut separation 后使用。
- pricing 证明仍使用 true dual、branching constraints 和 cut duals。

#### 配置

当前默认开启：

```yaml
branching_strategy: 3pb
three_pb_pseudocost_candidates: 6
three_pb_fractional_candidates: 6
three_pb_lp_candidates: 3
three_pb_heuristic_candidates: 2
three_pb_heuristic_max_labels: 800
```

#### 验证命令与结果

语法检查：

```bash
cd /home/kai/work/gnn_bb
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py
```

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 3 tests in 3.060s
OK
```

`very_small` smoke：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances very_small \
  --time-limit 30 \
  --config configs/bpc_clean.yaml \
  --results-csv results/smoke/bpc_clean_very_small_3pb.csv \
  --log-dir results/smoke/logs/bpc_clean_3pb \
  --solution-dir results/smoke/solutions/bpc_clean_3pb
```

结果：

```text
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
nodes=1
rmp=4
pricing=3
routes=10
```

20 规模 30 秒短测：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 30 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium_30s_3pb.csv \
  --log-dir results/logs/bpc_clean_30s_3pb \
  --solution-dir results/solutions/bpc_clean_30s_3pb \
  > results/logs/bpc_clean_terminal/medium_30s_3pb_terminal.log 2>&1
```

结果：

```text
status=TIME_LIMIT
primal=626.902419
dual=494.885971
gap=0.210585
nodes=15
rmp=43
pricing=30
routes=905
cuts=3
```

分支日志检查：

```bash
rg -n '"event": "branch_candidates"|"event": "branch_selection"' \
  results/logs/bpc_clean_30s_3pb/medium.jsonl
```

观察：

- 日志已经包含候选类型分布、筛选候选、LP score、heuristic score 和最终选择。
- 3PB 相比简单 branching 会增加测试开销，所以短时节点数下降是预期现象。
- 当前实现是 no-ML 3PB baseline，下一步可以在同一日志结构上采集 2LBB 的 M1/M2 训练数据。

### 2026-05-12 09:06:10 CST +0800

#### 版本备注

将 no-ML 3PB 从简化版改为完整 workflow 版本。上一版第三阶段只对部分 LP top 候选做一次 limited pricing 修正；当前版本对 LP testing 后的 top `theta_tilde` 候选全部做 heuristic CG testing。

#### 代码变化

主要修改：

```text
bpc/tree.py
bpc/node.py
bpc/solver.py
scripts/run_bpc_clean.py
configs/bpc_clean.yaml
```

当前 3PB 流程：

1. Initial screening：
   - 有 pseudocost 的候选按 pseudocost score 取 top `theta_p`；
   - 无 pseudocost 的候选按 fractionality 取 top `theta_f`。
2. LP testing：
   - 对 screened candidates 的左右 child 只解 restricted child RMP LP；
   - 不做 column generation；
   - 用左右 bound improvement 计算 LP score；
   - 取 top `theta_tilde`。
3. Heuristic CG testing：
   - 对 top `theta_tilde` 全部做 limited child CG loop；
   - 每轮解 child RMP、调用 limited pricing、把找到的列加入测试用的局部 column set、再重解 child RMP；
   - 测试用列不加入全局 column pool；
   - 测试结果只用于 branching score，不用于剪枝和证明。

新增 CSV 统计字段：

```text
branch_lp_test_rmp_solves
branch_heuristic_test_rmp_solves
branch_heuristic_test_pricing_calls
branch_lp_candidates_tested
branch_heuristic_candidates_tested
branch_testing_time
```

`branch_selection` 日志新增：

```text
testing_time
left_heuristic_iterations
right_heuristic_iterations
left_heuristic_added_routes
right_heuristic_added_routes
left_heuristic_exhausted
right_heuristic_exhausted
```

#### 配置

当前配置：

```yaml
branching_strategy: 3pb
three_pb_pseudocost_candidates: 6
three_pb_fractional_candidates: 6
three_pb_lp_candidates: 3
three_pb_heuristic_cg_iterations: 3
three_pb_heuristic_routes_per_iter: 50
three_pb_heuristic_max_labels: 800
```

这里没有单独的 `three_pb_heuristic_candidates`，因为完整 3PB 要求 LP top `theta_tilde` 全部进入 heuristic testing。

#### Exactness 影响

不破坏精确性：

- child LP testing 和 heuristic CG testing 都只用于分支排序；
- heuristic testing 中的局部列不会加入全局 RMP；
- node lower bound 仍然只来自主流程完整定价和切割后的 RMP；
- 任何 testing infeasible 都不作为节点不可行证明。

#### 验证命令与结果

语法检查：

```bash
cd /home/kai/work/gnn_bb
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py
```

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 3 tests in 0.167s
OK
```

`very_small` smoke：

```text
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
nodes=1
```

20 规模 30 秒短测：

```text
status=TIME_LIMIT
primal=626.902419
dual=526.902419
gap=0.159514
nodes=17
rmp=39
pricing=25
branch_lp_test_rmp_solves=180
branch_heuristic_test_rmp_solves=76
branch_heuristic_test_pricing_calls=70
branch_testing_time=11.064354
routes=1000
cuts=12
```

观察：

- 完整 3PB 的 30 秒 dual bound 明显高于上一版简化 3PB 的 `494.885971`。
- branch testing 成本已经显式记录，后续可以直接评估 2LBB 是否减少 testing overhead。

### 2026-05-12 09:13:06 CST +0800

#### 版本备注

补充 clean BPC 控制台日志字段说明。控制台日志是给人工观察用的摘要；完整结构化记录在对应的 JSONL 文件中，例如：

```text
results/logs/<RUN_ID>/medium.jsonl
```

JSONL 中的每一行都是一个事件，字段更完整，适合后续脚本统计和训练 2LBB 数据。

#### 控制台日志样例

典型输出：

```text
[clean-BPC    25.10s] node 15 cg=2 phase=phase2 obj=526.902419 artificial=0.0 cols=1000
[clean-BPC    25.74s] node 15 cg=2 phase=phase2 best_rc=0.0 found=0 added=0 exhausted=True
[clean-BPC    27.27s] branch node 15: left=arc(10,19)=off right=arc(10,19)=on
[clean-BPC    27.94s] fathom node 9: reason=phase1_infeasible bound=None
[clean-BPC     6.44s] incumbent node 0: obj=627.942924
```

#### 字段解释

`[clean-BPC 25.10s]`

- 当前 clean BPC 求解器输出。
- `25.10s` 是从本次求解开始到这条日志产生时的累计 wall-clock 时间。

`node`

- 当前正在处理的 BPC 搜索树节点编号。
- 例如 `node 15` 表示正在处理节点 15。
- 同一个节点可能重复出现多次，因为一个节点内部可能经历多轮 RMP / pricing / cut / branch。

`branch node`

- 表示当前节点完成 LP 定价和切割后仍然是 fractional，需要创建左右两个子节点。
- 例如：

```text
branch node 15: left=arc(10,19)=off right=arc(10,19)=on
```

含义是节点 15 被分裂成两个子问题：

- 左子节点加入约束 `arc(10,19)=off`；
- 右子节点加入约束 `arc(10,19)=on`。

`left` / `right`

- 当前 branching candidate 的左右分支约束。
- 常见类型：
  - `RF(i,j)=separate` / `RF(i,j)=same`：Ryan-Foster 分支，要求任务 `i,j` 不在同一路线或必须在同一路线。
  - `task_vehicle(i,k)=off/on`：任务 `i` 是否由车辆 `k` 服务。
  - `arc(i,j)=off/on`：任务弧 `i -> j` 是否允许/强制使用。
  - `vehicle(k)=off/on`：车辆 `k` 是否启用。
- 这些约束都必须能传递到 pricing，不能只是 master 里的临时约束。

`d`

- node depth，搜索树深度。
- `d=0` 是根节点。
- 深度越大，表示沿着分支路径累积了更多 branching constraints。

`lb`

- node lower bound，节点下界。
- 在 clean BPC 中，节点下界只在当前节点完成完整 exact pricing 和 cut separation 后才是可靠的。
- 如果还处于 RMP / pricing 中间阶段，不应把临时 RMP objective 当成最终 node bound。

`open`

- 当前仍未处理的开放节点数量。
- 例如 `open=1279` 表示优先队列里还有 1279 个节点等待处理。
- open 很大说明树还很宽；open 下降可能来自 bound fathoming、infeasibility fathoming 或 integral fathoming。

`cg`

- 当前节点内 column generation 迭代编号。
- `cg=1` 通常是该节点第一次求 RMP。
- 如果 pricing 找到 negative reduced-cost columns 并加入 RMP，就会进入下一轮 `cg=2`、`cg=3`。
- 如果 pricing 找不到负 reduced-cost 列且 exhausted=True，当前阶段的列生成完成。

`phase`

- 当前 RMP 阶段。
- `phase=phase1`：Phase-I 可行性阶段。人工列存在，目标是把 artificial 变量降到 0，证明当前节点 RMP 可行。
- `phase=phase2`：真实目标函数阶段。人工列不再参与目标，RMP objective 对应原问题当前节点的 LP 松弛目标值。
- 如果 `phase1` 完整 pricing 后 artificial 仍大于 0，则当前节点可证明不可行。

`obj`

- 当前 RMP LP 的目标值。
- 在 `phase1` 中，`obj` 是人工变量总惩罚目标，不是原问题成本。
- 在 `phase2` 中，`obj` 是当前 restricted master 的 LP 目标值。
- 注意：只有当当前节点完成 exact pricing 且没有 violated cuts 后，`phase2 obj` 才能作为该节点的有效 lower bound。

`artificial`

- Phase-I 人工变量总量。
- `artificial=0.0` 表示当前节点在已有列和 Phase-I pricing 下已经可行，可以进入 `phase2`。
- 如果 exact Phase-I pricing 完成后 `artificial > 0`，说明该节点不可行，可以 fathom。

`best_rc` / `best_r`

- pricing 找到的最小 reduced cost。
- 日志里字段名是 `best_rc`，你说的 `best_r` 可以理解为同一个字段。
- 对最小化问题：
  - `best_rc < 0`：存在 negative reduced-cost column，应加入 RMP 继续列生成；
  - `best_rc >= 0` 且 `exhausted=True`：pricing 已完整证明没有负 reduced-cost 列；
  - `best_rc` 接近 0：列生成进入尾期，边际改善变小。

`found`

- 本轮 pricing 找到的 negative reduced-cost route 数量。
- 控制台里 `found` 对应 JSONL 的 `negative_routes`。
- 例如 `found=6` 表示 pricing 找到了 6 个候选负 reduced-cost route。

`added`

- 本轮真正加入全局 route pool 的新 route 数量。
- 可能小于 `found`，原因包括：
  - route 已经存在；
  - 达到 `max_routes_per_pricing`；
  - 多个候选签名重复。
- `found>0` 但 `added=0` 一般说明找到的是重复列或已在池中。

`exhausted`

- pricing 是否完整枚举结束。
- `exhausted=True`：pricing 没有被 label limit / time budget 等限制中断，可以用于证明“没有负 reduced-cost 列”。
- `exhausted=False`：pricing 是不完整的，只能说明当前启发式/受限搜索没有继续找到列，不能用于证明节点 LP 最优。
- clean BPC 主流程中，只有 `exhausted=True` 且 `added=0` 才能结束该节点的 column generation 阶段。

`fathom node`

- 当前节点被剪掉，不再生成子节点。
- 常见原因：
  - `reason=bound`：节点 lower bound 已经不优于 incumbent。
  - `reason=bound_before_process`：节点从队列取出前，其继承 lower bound 已经不优于 incumbent。
  - `reason=phase1_infeasible`：Phase-I 证明该节点不可行。
  - `reason=integral`：节点 LP 解是整数解，并且通过原问题可行性检查。
  - `reason=rmp_infeasible` 或类似状态：RMP 自身不可行。

`incumbent node`

- 找到新的原问题可行整数解，并更新全局 upper bound。
- 例如：

```text
incumbent node 0: obj=627.942924
```

含义是节点 0 找到了目标值为 `627.942924` 的可行解。

- clean BPC 中 incumbent 必须通过原问题可行性检查，包括：
  - 每个任务恰好覆盖一次；
  - route 本身满足时间窗、载重、电量；
  - 每辆车 route set 可以排成真实 schedule；
  - sortie 数不超过上界。

`cols`

- 当前全局 route pool 中的 route column 数量。
- RMP 中实际变量数通常是 `cols * vehicle_count` 的子集，因为 branching constraints 会禁用部分 route-vehicle 变量。

`cuts`

- 当前全局 schedule no-good cuts 数量。
- 这些 cut 来自对整数 route-vehicle 解的 schedule 可行性检查。
- cut 增加后，pricing 的 reduced cost 必须加入 cut dual，否则 lower bound 不可靠。

#### 如何判断日志是否健康

根节点或普通节点中，健康行为通常是：

```text
前期：best_rc 明显小于 0，found 和 added 较多，obj / lb 改善明显；
中期：best_rc 靠近 0，found 和 added 减少；
尾期：best_rc >= 0 且 exhausted=True，节点 LP 完整定价结束；
之后：若 fractional 则 branch，若 integral 则校验并更新 incumbent 或加 cut。
```

需要警惕的行为：

```text
best_rc 长期不变；
found 很多但 added 长期为 0；
exhausted=False 却被当作证明；
节点反复加重复 cut；
open 快速膨胀但 dual bound 不动；
incumbent 长期不更新且 primal-dual gap 不降。
```

### 2026-05-12 10:58:19 CST +0800

#### 版本备注

新增保守的 robust Rounded Capacity Inequalities，简称 RCI/RCC，并加入 inactive cut purging 机制。没有加入非鲁棒 cut。

#### 数学形式

对任务子集 \(S\subseteq N\)，标准 capacity cut 是：

```text
x(delta(S)) >= 2 * ceil(d(S) / Q)
```

其中：

```text
d(S) = sum_{i in S} d_i
Q    = 单条 sortie 的载重容量
```

在 route-vehicle master 中，使用 route 投影：

```text
sum_{k in K} sum_{r in Omega} cross(r, S) * lambda_{r,k}
    >= 2 * ceil(d(S) / Q)
```

`cross(r, S)` 是 route `r` 从 depot 出发、访问任务、回 depot 的序列中穿过割集 `delta(S)` 的次数。

例如 route `(1, 2, 3)` 对 `S={1,2}` 的 crossing 是 2；对 `S={1,3}` 的 crossing 是 4。

#### 为什么这是 robust cut

这个 cut 是 arc/edge crossing 形式。它可以写成：

```text
x(delta(S)) = sum route crossing coefficient * lambda
```

pricing 中只需要给 route 加一个固定 crossing coefficient，不需要引入 subset-row 那类 floor/count 状态，也不需要改变 elementarity 结构。因此它属于 robust cut。

之前讨论过的“任务子集 route-count cut”：

```text
sum routes touching S >= ceil(d(S)/Q)
```

它是有效不等式，但不是我这次实现的版本。原因是它的系数是“route 是否触碰 S”的集合指示，不是标准 arc crossing 投影；在 pricing 中需要额外记忆是否已经触碰某个 S。为了保持 pricing 简洁和 robust，本次没有加入这个版本。

#### 有效性证明

任意整数可行解中，服务 \(S\) 中总需求 \(d(S)\) 至少需要：

```text
ceil(d(S) / Q)
```

条 sortie。每条服务 \(S\) 的 sortie 必须至少从 \(S\) 外进入 \(S\) 一次，并从 \(S\) 回到外部一次，因此每条这样的 sortie 至少贡献 2 次 crossing。

所以任意整数可行解都满足：

```text
x(delta(S)) >= 2 * ceil(d(S)/Q)
```

该 cut 不会删除任何原问题整数可行解，只会切掉 LP 松弛中的 fractional 解。

#### 实现范围

当前 separation 很克制：

```yaml
robust_capacity_cuts_enabled: true
robust_capacity_cut_max_depth: 0
robust_capacity_cut_max_subset_size: 5
robust_capacity_cut_max_per_round: 20
robust_capacity_cut_min_violation: 1.0e-5
robust_capacity_cut_max_rounds_per_node: 3
```

含义：

- 只在根节点做 RCI separation；
- 只枚举大小不超过 5 的任务子集；
- 每轮最多加 20 条；
- 每个节点最多 3 轮；
- violation 不明显则不加。

#### Phase-I 可行性处理

RCI 是 `>=` cut。加入 cut 后，当前 restricted column pool 可能暂时没有足够列满足 cut，但 full master 是可行的。因此 Phase-I 中对 cut 也加入人工变量：

```text
<= cut: lhs - artificial <= rhs
>= cut: lhs + artificial >= rhs
```

Phase-I pricing 使用这些 cut 的 true dual。只有完整 pricing 后 artificial 仍大于 0，才能说明节点不可行。

#### Purging 机制

只清洗 RCI，不清洗 schedule no-good cuts。

RCI 会记录 inactive age。若一条 RCI 连续多次满足：

```text
slack > cut_purge_slack
abs(dual) <= cut_purge_dual
```

则从 active cut list 中移除。

当前参数：

```yaml
cut_purge_age: 20
cut_purge_slack: 1.0e-5
cut_purge_dual: 1.0e-8
```

删除 valid cut 不会破坏 exactness，因为它只会放松 RMP；删除后必须重新解 RMP，不能沿用旧 bound。

#### 验证结果

语法检查：

```bash
cd /home/kai/work/gnn_bb
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py tests/test_bpc_clean.py
```

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 4 tests in 0.119s
OK
```

20 规模 30 秒短测：

```text
status=TIME_LIMIT
primal=626.902419
dual=526.902419
gap=0.159514
robust_capacity_cuts_added=0
cuts_purged=0
```

观察：

- 在当前 20 规模实例和根节点小集合 separation 范围内，没有发现 violated robust RCI。
- 这不是错误，而是保守 separation 的结果；没有明显违反就不加 cut。
- 后续如果要继续加强 cut，应优先考虑严格的 k-path / resource lower bound cut，而不是放宽到非鲁棒 route-count cut。

### 2026-05-12 11:07:37 CST +0800

#### 版本备注

新增严格的 k-path/resource lower bound cut。它只在能够给 \(k(S)\) 一个可证明下界时添加，并且仍采用 robust crossing 形式，不加入非鲁棒 subset-row cut。

#### Cut 形式

对任务子集 \(S\subseteq N\)，新 cut 为：

```text
x(delta(S)) >= 2 * k(S)
```

在 route-vehicle master 中写成：

```text
sum_{v in K} sum_{r in Omega} cross(r, S) * lambda_{r,v} >= 2 * k(S)
```

其中 `cross(r, S)` 是 route `r` 的 depot-task-depot 序列穿过 `S` 与 `N\S` 边界的次数。

#### k(S) 的可证明下界

当前实现使用两个严格下界的最大值：

```text
k(S) = max( ceil(d(S) / Q), chi(G_S) )
```

第一项是容量下界：

```text
d(S) = sum_{i in S} d_i
Q    = 单条 sortie route 的容量
```

第二项来自资源不兼容图 \(G_S\)：

```text
V(G_S) = S
(i,j) in E(G_S) 当且仅当任务 i 和 j 不存在任意顺序的同 route 可行 sortie
```

这里的“同 route 可行”使用完整 route feasibility 检查：

```text
depot -> i -> j -> depot
depot -> j -> i -> depot
```

并同时检查时间窗、载重、电量、horizon 和服务时间。

#### chi(G_S) 为什么是 route 数下界

任意一条 feasible route 在 \(S\) 中服务的任务集合，不能包含 \(G_S\) 中的一条边。否则这两个任务必须同时出现在同一条 route 中，但边的定义说明这在任何顺序下都不可行。

因此，每条 route 在 \(S\) 上对应 \(G_S\) 的一个 independent set。

如果整数可行解用 \(q\) 条 route 覆盖 \(S\)，则这 \(q\) 条 route 给 \(G_S\) 的所有顶点提供了一个 \(q\)-coloring。因此：

```text
q >= chi(G_S)
```

同时容量要求给出：

```text
q >= ceil(d(S) / Q)
```

所以：

```text
q >= max(ceil(d(S)/Q), chi(G_S)) = k(S)
```

当前实现对小集合 \(S\) 精确计算 \(\chi(G_S)\)，不是启发式近似。若无法证明更强下界，就不加 cut。

#### crossing cut 的有效性证明

任意服务 \(S\) 中至少一个任务的 route，必须从 \(S\) 外进入 \(S\)，再从 \(S\) 返回外部，因此至少贡献 2 次 crossing。

若服务 \(S\) 至少需要 \(k(S)\) 条 route，则：

```text
x(delta(S)) >= 2 * k(S)
```

这个 cut 不会删除任何原问题整数可行解，只会切掉违反资源下界的 LP fractional 解。

#### 为什么仍然是 robust cut

新 cut 的 route 系数仍然是：

```text
cross(r, S)
```

pricing 中只需要在 route 完成后计算该 crossing coefficient，并把 cut dual 乘以 coefficient 放进 reduced cost：

```text
rc(r,v) = cost(r) - cover_dual - vehicle_dual - time_dual
          - sum_c cut_dual[c] * coeff_c(r,v)
          - branch_dual * branch_coeff(r,v)
```

因此 pricing 不需要记忆“route 是否已经触碰某个 S”或“S 内访问了几个任务”这类额外状态。它不会改变 exact RCSP pricing 的可行域枚举，只改变 reduced cost。

#### 与普通 RCI 的关系

普通 RCI 使用：

```text
k(S) = ceil(d(S) / Q)
```

新 cut 只在：

```text
chi(G_S) > ceil(d(S) / Q)
```

时添加，避免重复添加与 RCI 等价或更弱的 cut。

#### 分离范围和清洗

默认配置：

```yaml
resource_lower_bound_cuts_enabled: true
resource_cut_max_depth: 0
resource_cut_max_subset_size: 6
resource_cut_max_per_round: 20
resource_cut_min_violation: 1.0e-5
resource_cut_max_rounds_per_node: 3
```

含义：

- 只在根节点做 conservative separation；
- 只枚举大小不超过 6 的任务子集；
- 只加入当前 LP 解明显违反的 cut；
- 每轮最多 20 条；
- 每个节点最多 3 轮。

清洗机制复用 robust cut purging：RCI 和 k-path/resource cut 都可以被清洗；schedule no-good cut 不清洗。

#### 验证结果

语法检查：

```bash
cd /home/kai/work/gnn_bb
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py tests/test_bpc_clean.py
```

单元测试：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 5 tests in 3.188s
OK
```

20 规模 30 秒短测：

```text
results/20260512_110634_medium_3pb_resource_cut_30s.csv

status=TIME_LIMIT
primal=626.902419
dual=526.902419
gap=0.159514
robust_capacity_cuts_added=0
resource_lower_bound_cuts_added=0
cuts_purged=0
```

观察：

- 当前 20 规模实例中，根节点小集合范围内构造出的资源不兼容图有 70 条 pair incompatibility edge；
- 但没有发现 violated k-path/resource cut，所以没有强行加 cut；
- 这符合“宁缺毋滥”的原则：没有严格违反就不添加。

### 2026-05-12 11:22:05 CST +0800

#### 版本备注

新增 task-vehicle linking constraint，并修正文档中的 `y[r]` 范围说明。

#### 约束形式

车辆启用变量在代码中一直是 LP relaxation：

```text
0 <= y[r] <= 1
```

这次新增有限 linking row：

```text
sum_{p in Omega} a[i,p] * lambda[p,r] <= y[r]
    for all i in I, r in R
```

含义：

```text
如果任务 i 在车辆 r 上被任何 route 服务，则车辆 r 必须启用。
```

该约束不改变整数可行域。整数情况下，只要某个 `lambda[p,r]=1` 且 `a[i,p]=1`，则必须有 `y[r]=1`。LP 下它强化 fixed vehicle cost 的表达，避免仅靠 `sum_p lambda[p,r] <= S_bar y[r]` 时车辆启用成本被 sortie 上界过度稀释。

#### Reduced Cost 更新

设 task-vehicle linking dual 为 `xi[i,r]`，则 route `p` on vehicle `r` 的 reduced cost 增加对应项：

```text
rc[p,r] = c[p]
        - sum_i a[i,p] pi[i]
        - sum_i a[i,p] xi[i,r]
        - eta[r]
        - beta[r] w[p]
        - sum_g b[g,p,r] gamma[g]
        - sum_h q[h,p,r] delta[h]
```

Phase-I 中 route objective 仍为 0，其余 dual 项保持一致。

#### 实现备注

- `bpc/rmp.py` 新增 `task_vehicle_link[i,r]` 约束；
- `RMPDuals` 新增 `task_vehicle[(i,r)]`；
- dual capture pricer 会读取这组 dual；
- `bpc/pricing.py` 的 exact pricing reduced cost 已加入 `- sum_i xi[i,r]`；
- label priority 也使用该 dual 改善遍历顺序，但证明仍依赖完整 exact pricing。

#### 验证结果

单元测试：

```text
Ran 6 tests in 0.138s
OK
```

20 规模 30 秒短测：

```text
results/20260512_112330_medium_3pb_task_vehicle_link_30s.csv

status=TIME_LIMIT
primal=627.942924
dual=492.686503
gap=0.215396
nodes=9
rmp=27
pricing=18
generated_routes=803
cuts_added=0
root_relaxation=490.283693
```

短测观察：

- 新 linking row 没有提升 root relaxation，仍为 `490.283693`；
- 30 秒内 primal 比上一版差，因为这次分支路径没有及时触发 schedule repair incumbent；
- 这不说明约束无效，但说明它不是当前实例 root bound 的直接瓶颈；
- 是否保留需要看 3600 秒完整对比，尤其是最终 gap、branch tree 规模和 incumbent 更新速度。

### 2026-05-12 11:30:14 CST +0800

#### 版本备注

新增 root LP fractional structure 诊断脚本：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python scripts/diagnose_root_fractional.py \
  --instance medium \
  --config configs/bpc_clean.yaml \
  --subset-max-size 6 \
  --top 12
```

脚本只做根节点 column generation，不进入 branch tree。输出 root LP fractional 结构、branching 候选统计、RCI/k-path cut violation 诊断。

本次输出：

```text
results/root_diagnostics/20260512_113217_medium_root_fractional.json
```

#### Root LP 诊断结果

根节点 full pricing 后：

```text
root objective = 490.283693
route pool size = 730
support route-vehicle variables = 19
fractional route-vehicle variables = 19
fractional Ryan-Foster pairs = 13
fractional arcs = 12
RCI violated count = 0
k-path/resource violated count = 0
```

最后一轮 pricing：

```text
phase = phase2
best_reduced_cost = -0.0
negative_routes = 0
added_routes = 0
exhausted = True
```

说明当前 root LP 已完整定价。

#### 车辆层面的结构

当前 root LP 的车辆启用和资源约束：

```text
vehicle 1: y=0.553143362, sortie_mass=2.245212756, work_mass=132.754407, H*y=132.754407
vehicle 2: y=0.553143362, sortie_mass=2.070255835, work_mass=132.754407, H*y=132.754407
vehicle 3: y=0.553143362, sortie_mass=2.184531409, work_mass=132.754407, H*y=132.754407
```

观察：

- 车辆工作时间约束是紧的；
- sortie count 约束很松；
- `task-vehicle linking` 没有被违反；
- root bound 主要被车辆工作时间下界和 fractional route mixing 支撑，而不是 sortie 数或容量子集 cut。

#### 任务被多辆车 fractional split

典型 split：

```text
task 1 : vehicle 2 = 0.446856638, vehicle 1 = 0.276571681, vehicle 3 = 0.276571681
task 3 : vehicle 3 = 0.553143362, vehicle 1 = 0.223428319, vehicle 2 = 0.223428319
task 7 : vehicle 3 = 0.553143362, vehicle 1 = 0.223428319, vehicle 2 = 0.223428319
task 9 : vehicle 3 = 0.553143362, vehicle 1 = 0.223428319, vehicle 2 = 0.223428319

task 2/4/8/15:
vehicle 2 = 0.553143362
vehicle 3 = 0.248529640
vehicle 1 = 0.198326997
```

这说明 root LP 不是违反某个容量子集，而是在多个车辆和多个 route pattern 之间做 convex mixing。

#### Fractional pair / arc 结构

典型 Ryan-Foster pair：

```text
(1,3)=0.5
(1,7)=0.5
(1,9)=0.5
(1,11)=0.5
(1,13)=0.5
(1,17)=0.5
(3,9)=0.5
(3,18)=0.5
```

典型 arc：

```text
1 -> 9  = 0.5
9 -> 11 = 0.5
11 -> 7 = 0.5
3 -> 7  = 0.5
7 -> 3  = 0.5
7 -> 18 = 0.5
13 -> 1 = 0.5
```

这说明 root fractional structure 更像 branching/route pattern ambiguity，而不是容量 cut violation。

#### 为什么 RCI 不起作用

RCI 检查：

```text
x(delta(S)) >= 2 ceil(d(S)/Q)
```

当前枚举 `|S| <= 6` 后：

```text
violated_count = 0
best_candidate violation = 0.0
```

最紧的例子：

```text
S = {2,4,8,10}
demand = 10
rhs = 4
activity = 4
violation = 0
```

结论：当前 LP 解虽然 fractional，但没有在容量 crossing 意义上少用 route。它已经满足这些容量割。

#### 为什么 k-path/resource cut 不起作用

资源不兼容图：

```text
pair incompatibility edges = 70 / 190
```

且存在很多集合满足：

```text
chi(G_S) > ceil(d(S)/Q)
```

诊断中 `stronger_than_capacity_subset_count = 36916`。

但当前 root LP 对这些更强下界仍然没有 violation：

```text
k_path_resource violated_count = 0
best_candidate violation = 0.0
```

最紧的例子：

```text
S = {5,15,17,19,20}
capacity_bound = 2
chromatic_bound = 5
k_bound = 5
rhs = 10
activity = 10
violation = 0
```

结论：资源不兼容结构存在，但当前 fractional 解在 crossing 视角下已经给足了边界 crossing。k-path/resource cut 不能切掉这种 convex mixing。

#### 当前瓶颈判断

现在瓶颈不是 capacity/resource subset cuts，而是：

```text
route-vehicle master 的 root LP 允许多个 route pattern fractional 混合；
schedule no-good cut 只在整数 route 集无法排程时触发；
当前 fractional 解已经满足 RCI 和 k-path crossing 下界；
branching 需要快速打破 pair/arc/task-vehicle 的 0.5 mixing。
```

因此，继续盲目加容量类 cut 的性价比低。下一步更合理的是：

1. 强化 branching：优先针对 0.5 Ryan-Foster pair 和 arc pattern；
2. 做 root fractional route conflict 诊断，找是否存在能用于 robust cut 的 clique/packing 结构；
3. 如果加 cut，应转向 schedule-aware valid inequalities，而不是继续扩大 RCI/k-path 枚举。

### 2026-05-12 11:50:38 CST +0800

#### 版本备注

新增 schedule capacity upper-bound cut。该 cut 是 schedule-aware valid inequality，用 exact 单车多 sortie schedule oracle 计算上界；若 oracle 无法在安全状态数内证明上界，则不加 cut。

#### Cut 形式

定义：

```text
z[i,r] = sum_{p in Omega} a[i,p] * lambda[p,r]
```

对任务子集 \(S\) 和车辆 \(r\)，加入：

```text
sum_{i in S} z[i,r] <= U(S) * y[r]
```

等价写成 route-vehicle column 形式：

```text
sum_{p in Omega} |p intersect S| * lambda[p,r] - U(S) * y[r] <= 0
```

其中 \(U(S)\) 是一辆真实车辆在完整多 sortie schedule 中最多能服务 \(S\) 内多少个任务。

#### U(S) 的计算

当前实现新增 `bpc/schedule_capacity.py`，使用 exact labeling oracle：

```text
state = (visited_mask, current_node, current_time, load, energy, completed_sorties)
```

状态扩展包括：

```text
1. 在当前 sortie 继续访问一个未访问任务；
2. 回 depot、充电/准备完成，关闭当前 sortie；
3. 从 depot 开启下一条 sortie。
```

所有扩展都检查：

```text
任务时间窗
载重 Q
电量 B_use
车辆 horizon H
sortie 数上界 S_bar
```

dominance 只在相同 `(visited_mask, current_node)` 下使用，并要求：

```text
time 更早
load 不更大
energy 不更大
completed_sorties 不更多
```

因此 dominance 不会删除潜在更优 schedule。

如果状态数超过：

```yaml
schedule_capacity_oracle_max_states: 200000
```

oracle 返回未证明，separation 直接跳过该集合，不加 cut。

#### 有效性证明

对任意整数可行解：

- 若 `y[r]=0`，车辆 `r` 未启用，因此所有 `lambda[p,r]=0`，左侧为 0；
- 若 `y[r]=1`，左侧就是车辆 `r` 在任务集合 `S` 中服务的任务数量；
- 按 \(U(S)\) 的定义，一辆真实车辆最多服务 \(U(S)\) 个 `S` 内任务。

所以：

```text
sum_{i in S} z[i,r] <= U(S) * y[r]
```

对所有整数可行解都成立，不会破坏原问题可行域。

#### Pricing 兼容性

该 cut 的 route coefficient 是：

```text
|p intersect S|
```

`y[r]` 的 coefficient 是：

```text
-U(S)
```

pricing 只需要在 reduced cost 中处理 route coefficient：

```text
rc[p,r] -= cut_dual * |p intersect S|
```

不需要给 RCSP label 增加额外状态，因此它是 pricing-friendly 的 schedule-aware cut。

#### 默认配置

```yaml
schedule_capacity_cuts_enabled: true
schedule_capacity_cut_max_depth: 0
schedule_capacity_cut_max_subset_size: 10
schedule_capacity_cut_max_per_round: 20
schedule_capacity_cut_min_violation: 1.0e-5
schedule_capacity_cut_max_rounds_per_node: 3
schedule_capacity_oracle_max_states: 200000
```

当前只在根节点做保守 separation。候选集合来自当前 LP 中某辆车承担质量最高的任务前缀。

#### 验证结果

单元测试：

```text
Ran 8 tests in 2.784s
OK
```

20 规模 30 秒短测：

```text
results/20260512_114949_medium_3pb_schedule_capacity_30s.csv

status=TIME_LIMIT
primal=627.942924
dual=491.291843
gap=0.217617
schedule_capacity_cuts_added=2
cuts_added=2
root_relaxation=490.283693
```

实际加入的 cut：

```text
vehicle=2
S={1,2,4,5,8,12,13,14,15,16}
U(S)=9
violation=0.340569913
oracle_states=14437

vehicle=1
S={1,2,4,5,8,12,13,14,15,16}
U(S)=9
violation=0.446856637
oracle_states=14437
```

短测观察：

- cut 被成功触发，说明它确实抓到了 root fractional vehicle-task overload；
- 但 30 秒内 root objective 仍为 `490.283693`，说明 RMP 找到了同目标替代 fractional 解；
- 这是正常的，schedule capacity cut 是有效强化，但当前候选集合还不够强；
- 下一步应基于诊断扩展 candidate separation，而不是放弃该 cut。

### 2026-05-12 11:56:34 CST +0800

#### 版本备注

增强 schedule capacity upper-bound cut 的 candidate separation。增强的是候选集合生成，不改变 cut 的有效性判定；每个候选仍必须由 exact schedule oracle 给出 \(U(S)\) 后才会加入。

#### 新增候选来源

原版本只使用每辆车任务承担质量最高的前缀集合。当前版本增加三类候选：

```text
1. high-mass task combinations
   对每辆车取 task-vehicle mass 最高的前若干任务，枚举高分组合。

2. route support union
   从当前 LP support 中取权重较高的 route，把若干 route 的任务并集作为 S。

3. near-y task set
   对当前车辆 r，挑选 z[i,r] 接近 y[r] 的任务集合。
```

这些启发式只决定“试哪些 S”，不决定 cut 是否有效。

#### 精确性说明

候选分离的流程是：

```text
generate candidate S
compute U(S) by exact schedule oracle
if oracle fails or hits state limit: skip S
if LP violates sum_i z[i,r] <= U(S) y[r]: add cut
otherwise skip
```

因此即使候选生成是启发式，也不会破坏 exactness。

#### 新增配置

```yaml
schedule_capacity_candidate_top_tasks: 12
schedule_capacity_candidate_max_combinations: 300
schedule_capacity_route_union_top_routes: 8
schedule_capacity_route_union_max_routes: 4
```

#### 验证结果

语法和单元测试：

```text
Ran 8 tests in 2.898s
OK
```

20 规模 30 秒短测：

```text
results/20260512_115549_medium_3pb_schedule_capacity_sep_30s.csv

status=TIME_LIMIT
primal=627.942924
dual=491.291843
gap=0.217617
schedule_capacity_cuts_added=5
cuts_added=5
root_relaxation=490.283693
```

候选数量：

```text
round 1: vehicle 1 = 341, vehicle 2 = 337, vehicle 3 = 329
round 2: vehicle 1 = 334, vehicle 2 = 353, vehicle 3 = 318
round 3: vehicle 1 = 334, vehicle 2 = 339, vehicle 3 = 318
```

新增 cut 例子：

```text
vehicle=2
S={1,2,4,5,8,12,13,14,15,16}
U(S)=9
violation=0.340569913

vehicle=3
S={2,4,5,8,9,12,14,15,16,18}
U(S)=9
violation=0.43704386
```

短测观察：

- enhanced separation 从 2 条 schedule capacity cut 增加到 5 条；
- root relaxation 仍为 `490.283693`，说明这些 cut 仍未切掉最终 root 最优面；
- 但 node 数从 6 降到 4，branch testing time 从约 10.65s 降到约 7.49s；
- 当前候选增强是安全的，但还没有解决 root bound 弱的问题。

### 2026-05-12 12:00:01 CST +0800

#### 版本备注

补充长时间运行时的终端打印输出，方便 3600 秒实验对比。

#### 新增终端输出

`schedule_capacity_candidates` 现在会打印每轮每辆车的候选数量：

```text
[clean-BPC xx.xx s] node 0 schedule-cap candidates={'1': 341, '2': 337, '3': 329}
```

`cut_added` 改为紧凑格式，重点显示 cut family、节点、加入数量和首条 cut 的关键信息：

```text
[clean-BPC xx.xx s] cut_added family=schedule_capacity node=0 added=2 first(vehicle=2, |S|=10, U=9, viol=0.340569913)
```

`finish` 现在打印总 cut 数和 schedule capacity cut 数：

```text
[clean-BPC xx.xx s] finish status=... primal=... dual=... gap=... cuts=... sched_cap=...
```

脚本最终 summary 现在额外显示：

```text
rci=...
kpath=...
sched_cap=...
cuts_purged=...
branch_test_time=...
```

#### 验证结果

```text
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 8 tests in 0.146s
OK
```

### 2026-05-12 13:56:44 CST +0800

#### 版本备注

新增 long-run ablation 入口，用于判断 20 规模上 3600s gap 改善主要来自：

- `task-vehicle linking`；
- `schedule-capacity cut`；
- 两者叠加；
- 或者只是 branch tree 路径偶然性。

#### 新增可控开关

RMP 现在支持配置：

```yaml
task_vehicle_linking_enabled: true
```

开启时加入有限 linking row：

```text
sum_p a_ip lambda[p,r] <= y[r]      for all task i, vehicle r
```

关闭时不加入该 row，`task_vehicle` dual 字典为空，pricing reduced cost 中对应项自然为 0。这个开关只用于实验消融；默认主线仍开启。

#### 新增 ablation 入口

新增：

```text
configs/bpc_ablation.yaml
scripts/run_bpc_ablation.py
```

默认四个 variant：

```text
no_link_no_schedcap   task_vehicle_linking=false, schedule_capacity=false
link_only             task_vehicle_linking=true,  schedule_capacity=false
schedcap_only         task_vehicle_linking=false, schedule_capacity=true
link_schedcap         task_vehicle_linking=true,  schedule_capacity=true
```

四个 variant 使用同一实例、同一 seed、同一 BPC 参数，只切换这两个组件。每个 variant 完成后立即追加写入 summary CSV，避免长跑中断后丢失已完成结果。

#### 3600s 消融命令

该命令不会覆盖历史日志，因为 `RUN_ID` 带时间戳：

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_link_schedcap_ablation_3600"
mkdir -p results/logs/bpc_ablation_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_ablation.py \
  --config configs/bpc_ablation.yaml \
  --instances medium \
  --time-limit 3600 \
  --run-id "$RUN_ID" \
  2>&1 | tee "results/logs/bpc_ablation_terminal/${RUN_ID}_terminal.log"
```

输出位置：

```text
results/ablation/<RUN_ID>/summary.csv
results/ablation/<RUN_ID>/logs/<variant>/medium.jsonl
results/ablation/<RUN_ID>/solutions/<variant>/solution_medium.json
results/logs/bpc_ablation_terminal/<RUN_ID>_terminal.log
```

#### 精确性说明

这个 ablation 不引入启发式剪枝：

- 关闭 linking row 只会放松 RMP，不会错误删除原问题可行解；
- 开启 linking row 是原问题整数可行解满足的 valid inequality；
- schedule-capacity cut 仍必须由 exact schedule oracle 证明后才加入；
- 每个 variant 的 node bound 仍只在 exact pricing 和 cut separation 完成后使用。

因此四个 variant 都保持 exact BPC 证明流程；区别只在 LP 松弛强度和搜索路径。

### 2026-05-12 14:29:32 CST +0800

#### 版本备注

新增当前完整模型文档：

```text
docs/bpc_current_complete_model.md
```

本次只补文档，不修改算法代码。

#### 文档内容

该文档系统记录当前 clean BPC 主线：

- route-vehicle BPC with schedule cuts 的定位；
- 原问题、route column、RMP Phase-I / Phase-II；
- task-vehicle linking；
- reduced cost；
- exact RCSP pricing；
- schedule no-good cut、RCI、k-path/resource cut、schedule capacity cut；
- 3PB branching baseline；
- incumbent 来源，包括 `route_assignment_repair`；
- 节点处理流程；
- exactness 条件；
- 当前局限和运行命令。

#### 精确性说明

本次没有改变任何求解逻辑、pricing、cuts 或 branching，因此不影响 exactness。

### 2026-05-12 15:34:44 CST +0800

#### 版本备注

补充 `docs/bpc_current_complete_model.md` 中三个实现细节，回应模型审查中容易产生歧义的位置。

#### 澄清内容

1. Route duplicate suppression：
   当前使用 ordered task sequence 作为强 canonical signature，不依赖对象 ID；同一有序任务序列不会绕过 schedule no-good cut。

2. Schedule checker witness：
   当前 checker 可返回 feasible order 和 ready time，但不可行时不返回失败见证；`shrink_infeasible_route_set` 只是贪心 deletion-minimal core，不是全局最小 core 或 IIS 证书。

3. `arc_on` branching row：
   当前代数形式是 `sum_{p,r} q_ij,p lambda_pr >= 1`，不是纯过滤规则；pricing 完整枚举 route 后计算 `q` 并在 reduced cost 中扣除该 row dual。

#### 精确性说明

本次只补文档，不修改代码。新增说明强调：若未来给 pricing 加 label dominance，active `arc_on` usage mask 必须进入 dominance state，否则可能漏列。

### 2026-05-12 16:39:45 CST +0800

#### 版本备注

新增 reduced-cost 一致性审计测试，确保 RMP 中每条影响 `lambda[p,r]` 的 row，其 dual 都进入 pricing。

#### 代码变化

`solve_rmp_lp` 增加只供测试使用的可选参数：

```text
capture_lambda_reduced_costs
```

开启后会从 SCIP 读取已有 `lambda[p,r]` 的 solver reduced cost，并放入 `RMPSolution.lambda_reduced_costs`。正常 BPC 求解默认关闭，不影响主流程。

同时将 RMP 内部的 `lambda` 变量 key 改为当前 `routes` 列表下标，而不是 `RouteColumn.id`。生产流程中的 route id 本来由 `RoutePool` 规范化；这次修改是防御性加固，避免测试或审计工具传入临时 `RouteColumn(id=-1)` 时发生变量覆盖。

新增测试：

```text
tests/test_bpc_clean.py::test_existing_lambda_reduced_cost_matches_solver
```

测试覆盖：

- cover row；
- task-vehicle linking row；
- sortie count row；
- vehicle time row；
- schedule-capacity cut row；
- `arc_on` branching row。

#### 验证结果

```text
python3 -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/run_bpc_ablation.py
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_bpc_clean.py
```

结果：

```text
Ran 10 tests in 0.158s
OK
```

#### 精确性说明

本次没有改变默认求解模型。新增 reduced-cost 导出只在测试显式开启时运行，用来审计 pricing 公式和 SCIP dual/reduced-cost 的一致性。

### 2026-05-12 20:02:24 CST +0800

#### 版本备注

合并 crossing 类 cuts，并新增 sortie-count ordering 对称破除。

#### 代码变化

1. `RoundedCapacityCut` 与 `KPathResourceCut` 统一为 `CrossingCut`：

```text
sum_{p,r} crossing(p,S) lambda[p,r] >= 2 K(S)
K(S)=max(Kcap(S), Kresource(S))
Kcap(S)=ceil(d(S)/Q)
Kresource(S)=chi(G_S)
```

cut manager 使用内部 key：

```text
("crossing_cut", frozenset(S))
```

同一个 `S` 不再同时保留 RCI 和 k-path/resource 两条重叠 cut；如果发现更强 RHS，只保留 RHS 最大的版本。

2. RMP 新增相邻车辆 sortie-count ordering：

```text
sum_p lambda[p,r] - sum_p lambda[p,r+1] >= 0
```

这是同质车辆的静态对称破除。对应 dual 已加入 route pricing reduced cost：

```text
rc -= rho[r,r+1] * coeff
coeff =  1  if route column 属于车辆 r
coeff = -1  if route column 属于车辆 r+1
coeff =  0  otherwise
```

3. reduced-cost consistency test 已覆盖新增 row：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean.CleanBPCTests.test_existing_lambda_reduced_cost_matches_solver
```

#### 验证结果

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```

结果：

```text
Ran 11 tests in 0.161s
OK
```

#### 精确性说明

`CrossingCut` 是 robust cut，pricing 只需要计算 route crossing coefficient，不改变 RCSP 状态空间。sortie-count ordering 是对同质车辆的静态对称破除；它从根节点起就是 RMP 的一部分，之后 branch tree 在该已排序可行域内继续完整划分。新增 ordering row 影响 `lambda[p,r]`，因此其 dual 已进入 pricing，并由 reduced-cost 一致性测试校验。

### 2026-05-13 08:28:15 CST +0800

#### 版本备注

根据 20 规模 3600 秒对比结果，撤回 sortie-count ordering。`link_schedcap` 继续作为当前主线：保留 task-vehicle linking、schedule-capacity cuts、统一 crossing cuts。

#### 撤回原因

上一轮结果显示：

```text
schedcap_only:
primal = 626.902419
dual   = 527.939413
gap    = 15.786%

link_schedcap:
primal = 533.926567
dual   = 527.939413
gap    = 1.1213%
```

`crossing_cuts_added=0`，所以统一 crossing cut 不是性能变化来源。sortie-count ordering 改变了搜索树和 incumbent 发现路径，尤其让 `schedcap_only` 的 primal bound 明显变差。为保持主线稳定，撤回该排序约束。

#### 代码变化

- 删除 RMP 中的相邻车辆 sortie-count ordering row：

```text
sum_p lambda[p,r] - sum_p lambda[p,r+1] >= 0
```

- 删除 `RMPDuals.sortie_order`；
- 删除 pricing reduced cost 中对应 `rho` dual 项；
- reduced-cost consistency test 回到当前实际 RMP row 集合；
- 保留 `y[r+1] <= y[r]` 的车辆启用顺序约束；
- 保留 `CrossingCut` 合并逻辑。

#### 精确性说明

撤回一个 valid symmetry breaker 只会放宽 LP / 搜索空间，不会删除任何原问题可行解，因此不会破坏 exactness。当前每条影响 `lambda[p,r]` 的 RMP row 仍由 reduced-cost consistency test 审计。

#### 验证结果

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```

结果：

```text
Ran 10 tests in 2.930s
OK
```

### 2026-05-13 09:01:21 CST +0800

#### 版本备注

新增 schedule pair conflict cut，减少“route 层面整数、真实 schedule 不可行”时反复添加大 no-good cut 的情况。

#### 代码变化

当 `_validate_integral_or_cut` 发现某辆车的 route set 不可排程时，现在按以下顺序处理：

```text
1. 在该 route set 内寻找双向不可排程的 route pair；
2. 若找到，加入 schedule_pair_conflict cut：
   lambda[p,r] + lambda[q,r] <= 1
3. 若找不到 pair conflict，退回 deletion-minimal schedule_nogood_core cut；
4. 若 core cut 已存在，再退回 full route set no-good；
5. 若仍无法新增 cut，不允许把该节点当作 integral feasible fathom。
```

pair cut 仍复用 `ScheduleNoGoodCut` 的 signature-based coefficient，但使用独立 kind：

```text
schedule_pair_conflict
```

新增统计字段：

```text
schedule_pair_conflict_cuts_added
schedule_nogood_cuts_added
```

终端日志现在会区分：

```text
cut_added family=schedule_pair_conflict ...
cut_added family=schedule_nogood_core ...
```

#### 有效性说明

若 exact schedule checker 证明 `[p,q]` 不可排程，则同一车辆不可能同时执行这两条 route。因此：

```text
lambda[p,r] + lambda[q,r] <= 1
```

不会删除任何原问题整数可行解。该 cut 的 coefficient 使用 canonical route signature，避免同一路径不同对象 id 绕过 cut。

#### 验证结果

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/run_bpc_ablation.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```

结果：

```text
Ran 11 tests in 2.113s
OK
```

### 2026-05-13 10:52:35 CST +0800

#### 版本备注

撤回 `schedule_pair_conflict` cut，保留 `link_schedcap` 主线。

20 规模 3600 秒对比显示，pair conflict cut 虽然是 valid cut，但当前分离方式没有提升 dual bound，反而增加 cut 数、RMP 次数和 branching testing 开销，并使最终 gap 变差。因此它不再作为 clean BPC 主线组件。

#### 当前 schedule infeasible integer assignment 处理顺序

```text
1. exact schedule checker 检查每辆车选中的 route set；
2. 若不可排程，调用 shrink_infeasible_route_set 得到 deletion-minimal core；
3. 加 schedule_nogood_core cut；
4. 若 core cut 已存在，退回 schedule_nogood_full cut；
5. 若仍无法新增 cut，不允许把该节点当作 feasible incumbent 或 integral fathom。
```

#### 代码变化

- 删除 `_add_first_schedule_pair_conflict_cut`；
- 删除 `schedule_pair_conflict_cuts_added` 统计字段；
- 终端和 JSONL finish 输出不再打印 `pair_conflict`；
- 删除 pair conflict 专用单元测试；
- 当前主线仍保留 `task_vehicle_linking` 与 `schedule_capacity_cuts`。

#### 验证结果

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
Ran 10 tests in 2.870s
OK

/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/run_bpc_ablation.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
OK
```
