# P0 V3 GAT Proof-Tail 单次否决落点验证

日期：2026-07-26

## 结论

当前唯一保留的 GAT 落点是：

> root 定价采用确定性的 processed-label work budget；连续两次 bounded harvest
> 都未填满目标后，系统第一次准备进入 `proof_only` 时，只调用一次可弃权模型。
> 模型只能接受 proof，或否决 proof 并再执行一轮合法 bounded harvest。

该落点已经表现出真实但尚未充分的 oracle headroom，值得继续采集同生成域
development 数据；目前仍不授权训练、部署或修改冻结 P0。

scale5/10 应 pre-import bypass，scale20 暂时只做 shadow，scale30 是首个候选启用
规模，scale50/100 在 exact root closure 数据充分前保持 shadow。

## 为什么触发器要先改成 two-strike

原 `adaptive_sparse_harvest_v1` 在一次 sparse harvest 后立即安排 proof。六个 fresh
scale20/30 实例的首次 proof 反事实表明：

- 5 个状态继续 harvest 更快；
- 1 个状态不可区分；
- 没有状态明确支持立即 proof。

这说明原触发器系统性偏早。这类一致性错误应由确定性规则修正，而不是交给 GAT
学习。因此新增 development-only two-strike control：连续两次 sparse harvest
后才安排 proof。默认 strikes 仍为 1，原 P0 行为没有改变。

## two-strike 首次 proof 的 matched 结果

共获得 11 个 exact-safe matched pairs，每个动作重复 3 次并取中位数：

| 规模 | exact pairs | 应继续 harvest | 应直接 proof | 双侧删失 |
|---|---:|---:|---:|---:|
| 20 | 5 | 1 | 4 | 1 |
| 30 | 6 | 2 | 4 | 0 |
| 合计 | 11 | 3 | 8 | 1 |

三次正确否决 proof 的原始 cost-to-closure 收益约为：

- scale20/005：0.265 秒；
- scale30/004：2.183 秒；
- scale30/006：1.111 秒。

按每个 exact state 都发生一次、每次完整模型开销 0.02 秒计费：

- 原始 perfect-oracle gain：3.559 秒；
- 11 次调用总开销：0.220 秒；
- 净 perfect-oracle gain：3.339 秒；
- 平均净收益：0.304 秒/实例；
- one-sided 95% bootstrap mean lower bound：约 0.004 秒；
- two-sided 95% bootstrap mean interval：约 [-0.020, 0.774] 秒。

分规模看：

- scale20 净收益仅 0.165 秒，置信下界仍为负，不支持在线启用；
- scale30 净收益 3.174 秒，是主要 headroom 来源，但 6 个实例仍不足以授权训练。

scale20/008 的完整 two-strike source trajectory 耗尽 600 秒，从首次 proof
snapshot 启动的 harvest counterfactual 也耗尽 600 秒，两者均未 exact closure。
由于 source trajectory 在到达该 snapshot 前已经消耗部分预算，这两侧不构成严格的
同起点 matched 600 秒 pair；该实例只作为合法双删失/OOD 风险记录，不形成强动作标签。

## 为什么 micro-harvest 不能替代 GAT

在 11 个 exact state 上额外运行了 10k/25k/50k processed-label deterministic
micro-harvest。最浅探针耗时约 0.05--0.08 秒，但列数与动作不单调：

- `column_count = 0` 同时包含两个应 harvest 状态和三个应 proof 状态；
- 更深探针仍不能用单阈值无误区分；
- 在本 pilot 上调出的最优单阈值总净收益约 0.67 秒，明显低于 selective
  oracle 的 3.34 秒，并产生错误否决。

因此，单纯使用上轮列数、最佳 RC 或很浅的 Native 搜索不足。剩余可学习信息应来自
当前 true dual 与任务—弧—path-option 图结构的组合，以及 active master support。

## 建议的模型与训练目标

模型每个 root 最多调用一次，动作只有：

```text
accept_proof
veto_once_to_bounded_harvest
```

输入包括：

- task、arc、path-option 图；
- 当前 true RMP task/fleet/cut dual；
- active master task-set support；
- 当前 RMP primal support；
- 两次 sparse harvest 的 processed labels、列数、best RC；
- dual L1/Linf drift、bound delta、round、规模与预算。

监督目标不是局部 Native 调用时间，而是 matched state fork 的 exact
cost-to-closure：

```text
delta = log1p(C_proof) - log1p(C_harvest)
```

建议联合使用：

- 两个 action cost 的 Huber regression；
- 以真实秒数 regret 加权的 pairwise ranking；
- exact-vs-censored 的 survival/ranking loss；
- 高精度 selective-risk loss，错误否决的损失按实际负 regret 加权；
- abstain 时恢复 two-strike deterministic proof。

必须按 linear、MLP、小 GAT 的顺序比较。若 trajectory-only linear/MLP 达到相同
效果，则不部署 GAT。GAT 只有在 grouped held-out 实例上显著提高安全 precision
和净收益时才晋级。

## 继续采集和训练门槛

当前 `training_authorized=false`。建议至少满足以下条件后才从 linear ranker 开始：

1. scale30 至少 30 个 exact matched first-trigger pairs；
2. 至少 8 个高于完整推理开销和 deadband 的 harvest-veto 正例；
3. 所有实例等权，任何单实例的后续 proof states 不得支配训练；
4. perfect selective oracle 的 one-sided 95% mean lower bound 大于 0；
5. 双侧删失率和 RSS p90 单独报告；
6. calibration、full80 和现有 50/100 protected test 保持未读；
7. checkpoint/import/tensorize/forward 总开销按 fresh runtime 计费；
8. linear 先通过 grouped validation，才能尝试 MLP 和 GAT。

为降低采集成本，可把同一 exact trajectory 的所有 proof-candidate snapshots 用于
连续 cost/regret 预训练，但部署门槛仍只看每实例一次的 first-trigger 结果，并在
采样时按 instance 等权。

## Exact-safe 边界

- 不增加、删除或过滤任何合法 route/label/arc；
- GAT 不改变 reduced cost、bound、pruning 或 certificate；
- 任何缺失、OOD、NaN/Inf、binding mismatch 都接受 deterministic proof；
- bounded harvest 只能按 deterministic processed-label budget 截断；
- exact proof 禁止 processed-label truncation；
- incomplete 只保存 observed lower bound 和 censoring budget，不生成 no-negative
  certificate；
- 所有 matched forks 必须重建同一 state、保持 universe safe，并闭合到同一
  6-decimal RMP objective（允许 1.1e-6 量化容差并显式记录 delta）。

## 主要证据

- `runs/p0v3_gat_landing_search_20260726/twostrike_first_proof_combined_exact_labels.json`
- `runs/p0v3_gat_landing_search_20260726/twostrike_first_proof_forks/`
- `runs/p0v3_gat_landing_search_20260726/expansion_twostrike_first_proof_forks/`
- `runs/p0v3_gat_landing_search_20260726/twostrike_first_proof_microharvest/`
- `data/gat_v3_tail_selective_real_map_expansion_20260726_content_manifest.json`

上述产物全部是 development-only，不能用于认证 source solve 或宣称正式加速。

## 2026-07-26 追加验证：该落点未通过

### 触发语义修正

重新核对 snapshot 生命周期后发现，`source_pass_strategy=proof_only` 并不都
代表一次合法模型调用。exact proof 执行后，后续状态也可能继续是
`proof_only`，此时 sparse strike 已清零。真正的单次 pre-call 状态必须同时满足：

```text
source_pass_strategy = proof_only
required_sparse_harvest_strikes = 2
sparse_harvest_strike_count = 2
```

原 15 个 first-proof pairs 中只有 13 个满足该条件；其余 2 个应被排除，而不是
通过放宽特征校验进入训练。13 个真实调用点中有 4 个 median override target，
但结合三次重复的方差，仅 3 个是强正例。

### 双 strike 特征与稠密预训练

首版特征只记录最近一次 sparse harvest，与设计文档要求的“两次轨迹”不一致。
V2 特征已补入：

- penultimate harvest column count / processed labels / best RC；
- 两次 harvest 的 count 与 RC 差；
- current dual 相对 penultimate dual 的 L1/Linf drift；
- current bound 相对 penultimate bound 的变化。

在 18 个同域 development roots 上，从每次真实 bounded harvest 得到 426 个
observed outcome rows，其中 61 个是 sparse。按实例 grouped、等权的 40-epoch
稠密预训练结果表明：

- GAT 的连续 harvest-yield MAE 稳定低于 MLP；
- MLP 的 sparse-AUC 在三随机种子上为约 `0.800/0.859/0.870`；
- GAT 的 sparse-AUC 为约 `0.702/0.835/0.726`；
- GAT 对 first-trigger action 的 proxy AUC 对随机种子不稳定，
  yield-AUC 为 `0.667/0.333/0.194`。

因此图 attention 能学习连续 harvestability，但该代理量与“再 harvest 一轮是否
缩短 exact closure”没有稳定单调关系。

### 冻结 selector 的旧 development 结果

采用：

```text
40 epochs dense pretrain
freeze encoder
120 epochs selective selector
seed = 20260726
```

13 个 grouped held-out first-trigger 的结果为：

| 模型 | true veto | false veto | net gain |
|---|---:|---:|---:|
| linear | 1 | 1 | +0.778 s |
| MLP | 0 | 2 | -0.866 s |
| GAT | 2 | 2 | +0.417 s |

GAT 没有超过 linear，且 50% precision 不满足高置信安全门槛。

### 新同域、标签前冻结的 held-out

新生成 8 个 scale30 real-map 实例，并在读取 action 标签前按 content hash
固定为：

- development 6；
- locked calibration 2。

分区 audit 无 overlap，未使用任何 tail label。6 个 development roots 均
exact-safe：

```text
root wall = 7.028--67.031 s
```

只有 2/6 发生合法 two-strike pre-call：

| 实例 | round | harvest median | proof median | 正确动作 |
|---|---:|---:|---:|---|
| scale30/004 seed203307272 | 15 | 23.175 s | 16.534 s | proof |
| scale30/007 seed203307275 | 18 | 3.527 s | 4.163 s | veto once |

两点的 perfect selector 在计入 `0.02 s/call` 后净收益为 `0.597 s`，但
bootstrap lower bound 仍为 `-0.02 s`。

模型、特征、训练数据、epoch、seed 和判定门槛已在新标签产生前冻结到：

```text
configs/p0v3_proof_tail_gat_validation_protocol_v1.json
```

冻结模型在两个 held-out 调用点上的结果完全一致：

| 模型 | true veto | false veto | missed veto | net gain |
|---|---:|---:|---:|---:|
| linear | 0 | 0 | 1 | -0.040 s |
| MLP | 0 | 0 | 1 | -0.040 s |
| GAT | 0 | 0 | 1 | -0.040 s |

GAT 通过零误否决门槛，但未通过正净收益，也未超过更小模型。因此冻结 gate 的
正式结论是：

```text
PROOF_TAIL_GAT_HELDOUT_GATE_FAILED
```

### 最终处理

该具体落点不接入在线路径，不导出 checkpoint，不实现 Native/NumPy runtime，
不读取 locked calibration，也不修改冻结 P0 V3。

two-strike deterministic control 仍只是 development experiment；本轮没有形成
其相对 P0 的正式 promotion 证据。

若继续搜索 proof-tail GAT，下一候选应改成：

> 在确定性尾部触发后，GAT 只调用一次并产生 task/node potential，随后由
> Native exact label queue 在不删 label、不改 bound/certificate 的前提下使用
> 该 potential 作为字典序 tie-break / secondary ordering。

该方向必须先在 frozen snapshot 上验证 learned-potential oracle 相对 QC0 和 QD1
的 matched exact wall headroom；没有稳定 oracle 上界时直接停止，不再训练新的
稀疏 action classifier。

追加证据：

- `runs/p0v3_gat_landing_search_20260726/harvest_dynamics_rows_realdev18.json`
- `runs/p0v3_gat_landing_search_20260726/proof_tail_transfer_ladder_grouped.json`
- `data/gat_v3_proof_tail_veto_expansion_20260726_content_manifest.json`
- `runs/p0v3_gat_landing_search_20260726/newheldout_twostrike_first_proof_exact_labels.json`
- `runs/p0v3_gat_landing_search_20260726/proof_tail_transfer_frozen_newheldout_evaluation.json`
