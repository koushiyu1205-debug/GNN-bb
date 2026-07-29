# P0 V3 GAT Proof-Queue Arc Potential 落点验证与关闭

日期：2026-07-26

## 1. 最终结论

本轮验证的具体落点是：

> 在确定性 proof-tail trigger 之后，一次性生成 task/arc potentials，
> 作为 Native exact label queue 的次级排序依据；不做过滤、剪枝、界估计
> 或证书判断。

该落点最终 **不进入 GAT 训练和在线部署**。

原因不是标签仍然稀疏。新的 Native dominance trace 已经能让每个 exact
状态生成大量 arc-level 监督，grouped out-of-fold linear ranker 也能明显
预测离线 target。真正失败的是：

1. 当 guidance 获得全局队列控制权时，近似预测误差会被组合搜索放大，
   出现 `7.7x--12.2x` 的真实减速；
2. 当 guidance 被限制为真正的局部次级键时，灾难性退化消失，但连使用
   同状态未来信息的 dominance oracle 都不能稳定超过 QD1；
3. 因而更复杂的 GAT 只能提高离线拟合能力，不能补回已经被安全局部化
   消除的端到端 headroom。

当前保留的 `QG1` 仅是 development-only 诊断路径，不在 production
selector 中，不导出 checkpoint，也不允许用于 promotion。

## 2. 首先发现的接线问题

Native `State` 原本已经累积 `guidance_score`，queue comparator 也能读取
该值，但 Python backend 同时存在两道 exact-proof 关闭条件：

- exact 请求不会附加 environment guidance；
- Native payload 在 exact mode 下把 task/arc guidance 视为 ineffective。

因此此前的 task/arc hint 并未真正进入 exact proof queue。

本轮增加显式 `QG1` diagnostic policy 后，只有 `QG1 + exact_proof`
可以安装经过 canonical binding 校验的有限 task/arc potentials。其他
exact policy 仍然 fail closed。所有路径继续记录：

- 相同 legal task universe hash；
- 相同 legal arc universe hash；
- guidance filter/drop 均为零；
- labels dropped 为 false；
- exact global minimum 或 no-negative threshold 一致。

## 3. 第一阶段：负列 task oracle 是错误目标

首个困难状态为：

`lunar_ice_sp50_030_007_seed202907271`，
state hash 前缀 `e458c2c5bb61c693`。

最初用完成后的 negative routes 构造 future-leaked task potential：

| policy | fresh-process wall |
|---|---:|
| QC0 | median `9.880 s` |
| QD1 | median `7.697 s` |
| aggressive QG1 + best-route oracle | median `6.992 s` |

该结果证明“改变队列顺序确实可以改变 proof 成本”，但它没有证明可学习：

- 监督优化的是尽快发现负列，不是尽快耗尽 exact frontier；
- 15 个冻结 scale20/30 状态中，negative-route reciprocal-rank oracle
  对固定最优 control 大多退化；
- 其中一个 no-negative 状态根本没有负列，无法生成这种标签。

因此没有使用该 target 训练模型。

对应证据：

- `runs/p0v3_gat_landing_search_20260726/proof_queue_potential_oracle_pilot/`
- `runs/p0v3_gat_landing_search_20260726/proof_queue_potential_oracle_gate_v1/`

## 4. 第二阶段：构造 proof-specific dominance supervision

为避免再次把 discovery 当成 proof，Native 增加了 development-only
聚合 trace。对每个 task 和 arc 记录：

```text
incoming_evaluated
incoming_rejected
existing_dominator_wins
accepted_removed_existing
removed_as_existing
```

trace 只在环境变量
`LUNAR_ICE_PROOF_QUEUE_POTENTIAL_TRACE=1` 时启用。它不改变合法动作、
reduced cost、dominance 判定或 certificate，只给训练数据提供“哪些较早
生成的 label 随后支配了更多 label”的结果信号。

验证过三种 target：

- `dominance_wins_log`；
- `dominance_net_log`；
- `dominance_leverage`。

task-only potential 太粗；arc-level
`reverse( log1p(wins) - log1p(rejected) )` 在 aggressive queue 上最好。

15 个冻结状态的 aggressive oracle 结果为：

| 指标 | 结果 |
|---|---:|
| 状态数 | 15 |
| 相对 `min(QC0,QD1)` 获胜 | 11/15 |
| paired geometric mean ratio | `0.9663` |
| bootstrap 95% interval | `[0.9443, 0.9897]` |
| scale30 获胜 | 7/8 |
| scale30 median ratio | `0.9370` |
| scale30 geometric mean ratio | `0.9511` |
| scale20 geometric mean ratio | `0.9840` |

所有 exact、安全和 universe audit 均通过。scale20 的绝对 wall 太短，
即使 oracle 小幅受益也不足以覆盖 fresh-runtime inference，因此后续已
明确设为 pre-import bypass。

主要证据：

`runs/p0v3_gat_landing_search_20260726/proof_queue_arc_dominance_oracle_gate_v2_summary.json`

## 5. 第三阶段：无泄漏 linear realizability

线性模型输入只使用 exact call 前可见信息：

- 静态 task/node 特征；
- 静态 arc/path-option 特征；
- 当前 true cover/fleet dual；
- 当前 dual 的 request-local rank/normalization；
- 当前 scale、round、active-column count；
- 过去一轮已有的 proof/harvest telemetry。

不输入：

- 当前状态完成后的 routes；
- dominance trace；
- 当前 arm wall；
- future RMP；
- target 状态的 oracle potential。

split 以 `instance_content_hash` 为组，执行五折 out-of-fold 预测；每个
fold 的 feature normalization 和 ridge alpha 只在 training states 上拟合。

离线结果看似很好：

| scale | mean Spearman | mean top-target recall | random recall |
|---|---:|---:|---:|
| 20 | `0.4113` | `0.8193` | `0.1856` |
| 30 | `0.3872` | `0.8138` | `0.1841` |

证据：

`runs/p0v3_gat_landing_search_20260726/proof_queue_arc_linear_cv_v1_summary.json`

这一步说明 dominance target 不是完全不可预测，也说明“标签稀疏”已经
不是本落点的主要阻塞。

## 6. 第四阶段：aggressive queue 的真实失败

当 key 为：

```text
(can_terminate, -guidance_score, partial_rc, creation_sequence_id)
```

时，任意非零 score 差异都会压过 partial RC。两个最先运行的 scale30
OOF 状态立即出现：

| state | QC0 | QD1 | OOF linear QG1 |
|---|---:|---:|---:|
| `20087c...` | `0.398--0.415 s` | `0.484--0.490 s` | `3.184--3.200 s` |
| `dd6ea1...` | `1.177--1.187 s` | `1.155--1.319 s` | `14.516 s` |

即使离线 rank correlation 较好，小量 top-order 错误也会让错误前缀产生
大量 descendants，随后造成 frontier 和 dominance checks 膨胀。因此
在第二个状态后主动中止全量评估。

证据：

`runs/p0v3_gat_landing_search_20260726/proof_queue_arc_linear_oof_exact_v1/`

## 7. 第五阶段：真正次级化之后没有足够 headroom

为避免模型压过确定性骨架，最终 `QG1` 改为：

```text
(
  can_terminate first,
  -visited_count,
  floor(partial_rc / bucket_width),
  -guidance_score,
  partial_rc,
  creation_sequence_id
)
```

含义是：

- QD1 deeper-first 不变；
- guidance 只在同深度、同 partial-RC 粗桶内重排；
- score 缺失或全零时严格退化为 QD1；
- bucket width 是单一、显式、绑定进实验 config 的 normalized-cost
  参数，不再混合早期四系数成本。

在最明显拖尾状态 `e458c2...` 上，从同一 QD1 完成 trace 构造
future-leaked arc dominance oracle：

| arm | fresh-process wall | processed labels | dominance checks |
|---|---:|---:|---:|
| QD1 trace | `7.639 s` | 775460 | 493908762 |
| QG1, width `1e-4` | `7.705 s` | 775460 | 493907226 |
| QG1, width `3e-4` | `7.644 s` | 775460 | 493894233 |
| QG1, width `1e-3` | `7.698 s` | 775460 | 493867547 |
| QG1, same-depth unrestricted | `7.652 s` | 777367 | 482474013 |

即使 oracle 知道同状态未来 dominance 结果，也没有带来 wall 收益。

再检查三个 scale30 状态：

| 约束 | median ratio vs QD1 | geometric mean | wins |
|---|---:|---:|---:|
| width `1e-3` | `1.0107` | `1.0031` | 1/4 |
| same-depth unrestricted | `0.9925` | `0.9891` | 2/4 |

约 1% 的 oracle geometric-mean headroom 还未扣除 `0.02 s` 推理开销，
且最拖尾状态没有收益，远不足以允许训练或部署。

证据：

`runs/p0v3_gat_landing_search_20260726/proof_queue_qd1_arc_oracle_pilot/`

## 8. 为什么不继续训练 MLP/GAT

模型阶梯的正确晋级顺序是：

```text
oracle action headroom
  -> no-leak linear realizability
  -> linear exact replay
  -> MLP
  -> small GAT
```

本轮已经得到两个互补反例：

1. 强控制时 linear/GAT 的近似误差会造成数量级退化；
2. 安全局部控制时 perfect dominance oracle 都没有足够净收益。

因此更复杂网络没有可以恢复的系统 headroom。继续训练只会增加参数、
Torch import、tensorization 和 forward 成本，并提高 false-positive 风险。

## 9. 对后续 GAT 落点的约束

Native label queue 方向到此关闭。后续候选必须同时满足：

1. intervention 发生次数低，最好每个 node/instance 一次；
2. 模型误差不会被数百万 label descendants 放大；
3. perfect oracle 在 matched exact end-to-end 上先通过；
4. 监督来自真实 action cost，而不是 proxy correlation；
5. score 缺失、OOD 或低置信时在导入 Torch 前 bypass；
6. 5/10 默认 bypass；20 只有独立 gate 通过才启用；50/100 继续 shadow。

这意味着后续若继续 GAT，只应回到“低频、可弃权、动作集合很小”的位置，
而不是再次深入 Native label hot loop。

## 10. 与 branch top-3 现状合并后的总判断

当前 target-domain branch top-3 扩展 gate 已记录：

```text
decision_reason_code =
TARGET_CAP_REACHED_WITH_INSUFFICIENT_EVALUABLE_GOLD

target_instance_cap_reached = true
target_sample_threshold_reached = false
target_headroom_passed = false
terminate_target_direction = true
linear_training_authorized = false
gat_training_authorized = false
```

证据：

`runs/p0v3_branch_real_map_headroom_20260726/target_headroom_gate_expanded.json`

因此把本报告与已有 gate 合并后，当前不是“queue GAT 失败，所以立刻改回
branch GAT”，而是：

```text
route-admission             STOP
dual-center stabilization   STOP
dynamic QC0/QD1 selector    STOP
single proof-tail veto      STOP
Native label-queue GAT      STOP
target-domain branch top-3  STOP at current sampling cap
```

截至 2026-07-26，当前 P0 V3 上 **没有已经通过 action-headroom、
no-leak realizability 和 held-out exact replay 三层门槛的 GAT 落点**。

下一步若不改变求解器的可干预结构，继续换网络或换 loss 没有依据。更合理的
研发顺序是先做 deterministic Native proof-tail engineering，形成一个
低频、可回退、具有稳定反事实差异的新动作；只有该动作的 perfect oracle
先通过，才重新开启 linear/MLP/GAT 阶梯。
