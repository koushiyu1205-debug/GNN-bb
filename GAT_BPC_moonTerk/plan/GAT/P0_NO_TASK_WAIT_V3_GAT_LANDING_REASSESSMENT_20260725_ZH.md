# P0 No-Task-Wait V3 基准冻结与 GAT 落点复审

日期：2026-07-25

## 1. 当前决策

新的实验主基准已经冻结为：

```text
FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3
```

它采用：

- `no_task_wait_base_departure_shift_v1` 服务时序；
- HiGHS restricted master；
- Native exact SPPRC；
- root-only P0 SRI-3；
- Ryan-Foster same/different branching；
- current true-dual exhaustive pricing certificate。

旧的 `FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2` 降为历史实验基准，
但不删除、不覆盖。Production 默认仍为 `no_cut`，本次没有授权切换
production。

对 GAT 的当前决定是：

```text
唯一首选在线落点 = P0 合法 top-3 Ryan-Foster shortlist 的分支排序
dual-center stabilization = 暂停
Native per-label proof queue GAT 排序 = 暂停
```

这里的“选择 top-3 branch ranking”是下一轮因果验证和训练的数据方向，
不是说已有 GAT 可以部署。所有旧语义下的模型、split hash、oracle 结果均
不能直接晋级到 V3。

## 2. 基准冻结证据

冻结包：

```text
runs/frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725
```

校验结果：

```text
valid = true
source bundle = 162/162
source bundle mismatch = 0
result rows = 80
exact = 80/80
correctness = 80/80
```

正式 full80 单次 cold-start 结果：

| scale | mean | p50 | max |
|---:|---:|---:|---:|
| 5 | 0.441768 s | 0.445990 s | 0.479031 s |
| 10 | 1.461395 s | 0.987978 s | 5.178049 s |
| 20 | 39.820047 s | 17.106476 s | 201.125098 s |
| 30 | 177.357529 s | 77.280779 s | 716.426428 s |

V2 允许 task waiting，V3 禁止 task waiting 并允许统一平移基地出发时刻。
两者是不同数学语义，不能把 V2/V3 时间比写成同问题加速率。

## 3. 新基准的真实时间结构

### 3.1 scale20/30 汇总

| 指标 | scale20 | scale30 | 合计 |
|---|---:|---:|---:|
| cold-start 总时间 | 796.401 s | 3547.151 s | 4343.552 s |
| root CG | 490.603 s | 2219.067 s | 2709.671 s |
| root 占总时间 | 61.60% | 62.56% | 62.38% |
| tree | 297.567 s | 1309.038 s | 1606.605 s |
| tree 占总时间 | 37.36% | 36.90% | 36.99% |
| root pricing rounds | 392 | 666 | 1058 |
| root final-judge wall | 481.924 s | 2156.150 s | 2638.073 s |
| 有分支的实例 | 3/20 | 4/20 | 7/40 |
| 实际分支决策 | 10 | 42 | 52 |
| 可评分 top-3 状态 | 12 | 58 | 70 |
| tree final-judge wall | 194.579 s | 665.155 s | 859.734 s |

root final-judge 占 root CG 的 97.36%。这说明当前 root tail 主要不是
Python、RMP 或 GAT 缺失造成的表面开销，而是 Native exact pricing
产生的实际 proof workload。

### 3.2 两类不同的拖尾

第一类是 root-integral proof tail：

- scale30/013：root 511.846 s，tree 57.081 s，root integral；
- scale30/014：root 285.595 s，tree 96.681 s，root integral；
- scale30/009：root 268.601 s，tree 44.582 s，root integral；
- scale30/012：root 175.356 s，tree 63.269 s，root integral。

这四个实例的 root 时间合计 1241.398 s，占 scale30 全部时间的
35.00%。它们没有分支动作，所以 branch GAT 不可能改善这一部分。

第二类是 branch-induced proof tail：

- scale30/016：总时间 716.426 s；
- root 69.118 s；
- tree 646.256 s；
- 65 个 tree nodes；
- 32 次实际分支决策；
- 48 个出现合法 top-3 shortlist 的 fractional 状态；
- tree final-judge 220.839 s；
- tree Native label queue pushes 2,070,476,080。

这是 branch ranking 最有希望改变的尾部：一次更好的 branch action
可以减少后续节点、后续 RMP 和后续 exact proof 的总量，而不是只在一个
固定 proof workload 内改变访问次序。

## 4. 为什么不把 GAT 放在 proof queue

scale30 full80 的 tree 中记录了 3,868,676,090 次 label queue push。
不论模型多小，都不能按 label 调用 Python/Torch GAT。

即便每个 pricing context 只调用一次 GAT，再把静态优先级交给 Native，
当前仍缺少能够证明净收益的动作：

1. 最昂贵的闭合轮大多是 `EXHAUSTIVE_NO_NEGATIVE`；
2. 无负列时，“先找到好列”不存在，纯重排没有天然提前停止点；
3. 如果不减少扩展、支配后的 retained labels 或安全 completion
   workload，最后仍要完成同一个 proof；
4. 旧的动态 QD1 实验没有得到可冻结的稳定端到端收益；
5. 每个 context 都付模型成本，会重新出现“有效位置稀疏、调用成本密集”
   的问题。

因此 proof queue 可以继续保留 telemetry 和 deterministic research，
但当前不应作为 GAT 首个在线落点。

## 5. 为什么不立即重启 dual-center

旧服务时序下，使用未来 true dual 的强 oracle 已经给过一个重要反例：

- scale20/043 有约 1.09% 小收益；
- scale30/017 虽把 rounds 从 53 降到 35，wall time 却增加 65.91%；
- 合计 oracle/P0 为 1.6327×。

V3 改变了数学语义，因此该数值不能作为 V3 的正式 causal gate。但它仍是
一个很强的负面先验：减少 CG rounds 不等于减少 exact pricing wall。
预测未来中心的 GAT 信息弱于该 oracle，不能在没有新的 V3 oracle
headroom 前直接训练。

新 full80 也显示 root 时间的 97.36% 在 exact final judge。dual-center
只能作为 discovery dual，不能签发 certificate；它是否能降低总 exact
workload 必须由 matched end-to-end V3 反事实验证，不能由 dual L1、
round count 或 best RC 单独推断。

所以 dual-center 不是当前首选落点。若将来重启，它必须是独立研究线，
不能与 branch head 捆绑后用总收益掩盖失败。

## 6. 为什么选择 top-3 branch ranking

### 6.1 它同时对应“引导分支”和一类真实拖尾

GAT 只放在：

```text
exact node LP closure
  -> P0 生成合法 Ryan-Foster shortlist
  -> shortlist 至少有 2 个候选
  -> 对最多 3 个候选评分
  -> 高置信时重排，否则保持 P0 rank-0
  -> 原 exact child creation / pricing / proof
```

它不是对每轮 pricing 付费，而只在 fractional branch state 付费。V3
full80 中：

- scale5：0 次实际分支决策；
- scale10：2 次；
- scale20：10 次；
- scale30：42 次。

因此 scale5 可直接 pre-import bypass；scale10 在证据不足前也应 bypass
或纯 shadow。模型成本集中在 scale20/30 的真实可作用位置。

### 6.2 旧语义下已有动作空间证据

旧 development 数据的 matched exact top-3 oracle 曾得到：

- scale20：pooled oracle 净收益 7.33%；
- scale30：pooled oracle 净收益 1.47%；
- 合计：3.00%，instance-bootstrap 95% CI 为 [0.82%, 7.20%]；
- fixed rank-1 为 1.2229× P0；
- fixed rank-2 为 1.2020× P0。

这证明“候选动作有差异”以及“必须状态相关地选择”，但不能证明 V3 GAT
有效。V3 必须重新绑定 content hash、重新运行 B0 和重新收集反事实。

### 6.3 当前最大的风险是样本集中

scale30 的 42 次实际分支决策中，32 次来自 instance_016，即 76.19%。
58 个可评分状态中，48 个也来自该实例。直接把 full80 节点当训练行会让
一个拖尾实例支配模型，并导致严重测试泄漏。

训练采样必须固定为：

```text
scale -> instance -> canonical branch state -> candidate
```

每实例先限额，再在状态内部比较 top-3；不能按节点行随机切分。

## 7. V3 的训练标签和目标

### 7.1 先收集 state-local one-deviation 反事实

对 development 实例中每个被选中的 canonical branch state `s`：

1. 使用完全相同的 root source 和 canonical path 到达 `s`；
2. 分别选择 P0 top-3 中的 `a0/a1/a2`；
3. 只在 `s` 偏离一次；
4. 后续所有状态恢复 P0；
5. 所有 arm 都跑到 exact closure，或记录合法删失下界；
6. 验证 shortlist universe hash 一致、drop count 为零、objective 和
   certificate 一致。

这样得到的是“这个状态的这个动作造成了什么”，而不是把整棵树的结果
错误归因给沿途所有动作。

### 7.2 主标签不再混合早期四系数 cost

对同一状态、同一预算，定义无量纲主标签：

```text
y(s, a) = log((T_downstream(s, a) + epsilon)
              / (T_downstream(s, a0) + epsilon))
```

其中：

- `a0` 是 P0 rank-0；
- 越小越好；
- `T_downstream` 包含从该状态到 exact closure 的 wall time；
- 正式 gate 额外计入完整 guidance lifecycle cost；
- `epsilon` 只用于数值稳定，固定并写入 label schema。

不再把 node count、label pushes、左右不平衡和 wall time用任意四个系数
混成一个“cost”。这些量改为独立 telemetry / auxiliary heads：

- downstream exact final-judge wall；
- downstream label queue pushes；
- downstream node count；
- peak RSS；
- left/right child censoring state。

主模型选择始终看 matched downstream wall 和最终 end-to-end wall。

### 7.3 损失函数

首选训练形式：

```text
listwise ranking loss over a0/a1/a2
+ abstain-to-P0 loss
+ censored survival loss for incomplete arms
```

规则：

- 只有 paired confidence interval 可比较时才形成强 pairwise 关系；
- 未闭合 arm 只提供 work lower bound 和 censoring，不加固定罚项；
- alternative 相对 P0 的保守净收益下界不大于模型生命周期成本时，
  abstain 标签为真；
- 先训练 linear ranker，再比较 MLP，最后才允许 GAT；
- GAT 必须在同 fold、同样本、同生命周期预算下显著优于 linear/MLP。

### 7.4 GAT 结构

如果 linear/MLP 未达到门槛而图关系确有剩余可学信号，才使用小 GAT：

- task/path-option/column support 的共享图编码器；
- pair head 使用对称输入：

```text
h_i + h_j
abs(h_i - h_j)
h_i * h_j
global/node context
pair fractionality and support context
```

- 输出三个候选的相对 downstream cost 和 abstain confidence；
- 缺失、OOD、低置信或 checkpoint mismatch 时恢复 P0 顺序。

当前不建立 dual-center head，不建立 per-label queue head，也不训练一个
多头模型同时承担三个失败风险。

## 8. 跨规模部署边界

| scale | 当前 V3 机会证据 | 首轮策略 |
|---:|---|---|
| 5 | full80 无分支动作 | pre-import bypass |
| 10 | 仅 1 个实例、2 次动作 | bypass 或 shadow |
| 20 | 3 个实例、10 次动作 | development oracle 通过后训练/验证 |
| 30 | 4 个实例、42 次动作，且有明显 tree tail | 首要验证规模 |
| 50 | 尚无 V3 exact root/tree promotion 证据 | shadow only |
| 100 | 尚无 V3 exact root/tree promotion 证据 | shadow only |

共享 checkpoint 不等于六规模强制启用。`DeploymentEligibilityManifest`
必须逐规模控制，bypass 路径不得导入 Torch、读取 checkpoint 或构图。

## 9. 必须先修复的数据绑定

现有 `p0v2_gat_split_manifest.json` 的 content hash 属于旧服务时序。示例：

```text
scale20 development instance_038
old manifest hash = 02b53ea0ee27b184
V3 current hash   = 11f05b98a0892835
```

因此旧 manifest、static tensor cache、B0 ledger、oracle label 和模型均
不能直接复用。正确顺序是：

1. 保留旧 manifest 为历史证据；
2. 基于 V3 content hash 新建 split manifest V3；
3. 在新 development pool 上重跑同代码 B0；
4. 重新按 V3 难度分层；
5. 重新做 top-3 state-local oracle；
6. 完美策略净收益门槛通过后，才从 linear ranker 开始。

冻结 full80 只能用于本轮基准审计和最终一次评估，不能用于训练、阈值选择
或挑选 GAT 架构。

## 10. 晋级门槛

V3 top-3 branch 方向只有依次满足下列条件才能继续：

1. 新 development split 的 actionable 状态覆盖达到预设 quota；
2. one-deviation perfect oracle 在 scale20 和 scale30 的 pooled net gain
   均为正；
3. worst-scale bootstrap 下界为正，且覆盖 full lifecycle overhead；
4. linear ranker 相对 P0 在 grouped CV 中非退化；
5. MLP/GAT 只有显著优于更小模型才晋级；
6. scale5/10 bypass 经 fresh runtime 验证没有 Torch import；
7. 最终冻结后才运行 full80 一次；
8. exact objective、legal universe、RC audit、certificate 和 incomplete
   redline 全部保持零差异。

若新的 V3 perfect oracle 不通过，就终止 branch GAT；不能再用更复杂网络
掩盖动作空间本身没有收益。
