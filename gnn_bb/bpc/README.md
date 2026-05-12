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
y[r]        >= 0   RMP LP 中车辆 r 是否启用的松弛变量
u[i]        >= 0   Phase-I 人工覆盖变量
```

Phase-I RMP：

```text
min sum_i u[i]

sum_r sum_p a_ip lambda[p,r] + u[i] = 1       for all i in I
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
