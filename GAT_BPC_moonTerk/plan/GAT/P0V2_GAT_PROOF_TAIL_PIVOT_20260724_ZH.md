# P0 V2 GAT：转向 proof-tail 的首轮实现与实测

日期：2026-07-24

## 结论

route-admission 方向继续保持冻结，当前重点转为 true-dual exact pricing
的 proof tail。但首轮结果不支持“让 GAT 给每个 label 打分”，而支持：

1. Native 内只保留少量、严格不剪枝的确定性队列策略；
2. 在每个 exact pricing context 开始前最多做一次图级预测；
3. 学习器只选择队列策略或回退 QC0，不直接进入 label 热循环；
4. 训练标签必须来自同一数学 binding 下的 matched fresh-process
   policy trajectories；
5. 未证明净收益的规模在导入 Torch 前 bypass。

当前代码仍以 Q0 为生产默认。固定动作集只保留 QC0、QD1：

- QC0 是缓存 key 后的工程 control；
- QD1 是目前唯一在部分 scale30 proof-tail context 上显示 wall 收益的
  候选；
- QB1 只保留为历史反例和离线诊断，不再进入 selector 动作集，因为它
  虽然减少 labels，却显著增加 dominance wall 和总耗时。

两种保留动作均尚未 promotion。

## 实现

新增的 exact-only queue policy：

- `Q0`：原始 terminal-first、partial-RC 队列；
- `QC0`：与 Q0 相同的数学优先级，但在 label 入堆时缓存 key，并以
  `creation_sequence_id` 确定性打破完全相同的 key；
- `QD1`：terminal-first，然后优先更深的 `visited_count`，再按
  guidance、partial RC 和创建顺序；
- `QB1`：terminal-first，然后按
  `partial_rc - remaining_positive_task_dual` 的乐观完成 key。

所有新策略只改变 `next_label` 的弹出顺序，不改变：

- label 的生成与合法性；
- dominance 判定；
- completion-bound 或 subset-dominance 的开关和语义；
- negative threshold；
- exhaustive/frontier-empty/certificate 条件。

`BackendPricingRequest` 现显式携带 `proof_queue_policy_id`。非 Q0
策略只允许用于 `exact_proof` 请求，Native payload、host IPC 和
telemetry 均保留该字段。

`scripts/replay_p0v2_gat_proof_tail_snapshot.py` 支持：

- complete exact snapshot 作为已有 control；
- 只复用 snapshot 的 dual/branch/cut 数学上下文，并重新建立 fresh
  exact control；
- completion bound、subset dominance 和 queue policy 的正交组合；
- fresh-process wall、Native wall、extension/dominance、labels 和
  certificate 语义记录。

## 首轮证据

### 1. 现有 completion bound 不构成有效方向

冻结 scale30/007 最终 no-negative context：

| 配置 | Native wall | extended labels | bound evaluated | bound pruned |
|---|---:|---:|---:|---:|
| bound off | 26.612 s | 80,315,611 | 0 | 0 |
| bound on | 26.300 s | 80,315,611 | 5,476,581 | 0 |

它评估了约 548 万次但一次也未剪枝。该差异只能视为运行噪声，
不能把现有 bound promotion。

### 2. QB1 表明“标签数减少”不是正确训练目标

同一 scale30 no-negative context：

| 策略 | Native wall | extended labels | dominance checks |
|---|---:|---:|---:|
| Q0 | 26.035 s | 80,315,611 | 26,926,831 |
| QB1 cached | 36.983 s | 69,219,237 | 28,400,403 |

QB1 少扩展 13.8% labels，却慢 42.1%。原因是它改变了到达
dominance buckets 的状态分布，使 dominance wall 从 19.625 秒升至
30.774 秒。因此不得用 `extended_labels`、`first terminal` 或
`best RC discovery` 单独代替端到端 proof cost。

### 3. QD1 的收益只出现在部分 proof-tail context

scale30/007 的三个独立数学 context：

| context | exact 结果 | QC0 Native | QD1 Native | QD1/QC0 |
|---|---|---:|---:|---:|
| 51 negative columns | global min `-0.016870284` | 23.673 s | 23.369 s | 0.987 |
| 83 negative columns | global min `-0.015997` | 24.720 s | 24.618 s | 0.996 |
| no negative | proof `< -1e-6` 不存在 | 25.720 s | 23.742 s | 0.923 |

三个 context 的 exact 结果、column count 和 certificate 语义均一致。
QD1 在有负列 context 上几乎没有收益，在真正 no-negative tail
上出现较明显收益。

对同一个 no-negative binding 做三次 matched 重复，QD1/QC0 Native
wall 比值为：

```text
0.923, 0.990, 0.969
```

几何均值为 `0.961`。这些重复只能估计运行噪声，不能当作三个独立
训练样本。

### 4. scale20 明确反对全规模启用 QD1

冻结 scale20/043 final-judge 数学 context，保持该规模当前
`subset_dominance=off`：

| 策略 | Native wall | fresh-process wall | extended labels |
|---|---:|---:|---:|
| QC0 | 0.253 s | 0.389 s | 3,299,585 |
| QD1 | 0.291 s | 0.429 s | 3,401,496 |

QD1 的 Native wall 退化 14.8%，fresh wall 退化 10.2%。这也说明：

- scale 不能被一个共享“总平均收益”淹没；
- 小规模不应为一次 GAT forward、Torch import 或策略切换付固定成本；
- pre-import bypass 是部署合同的一部分，而不是事后补丁。

### 5. 40 个独立 development context 的 quota 结果

最终 quota 使用 40 个互异 development 实例：

- scale20 20 个；
- scale30 20 个；
- 每个 context 做 3 次 QC0/QD1 matched fresh-process 重复；
- 共 120 个有效 pair，0 rejected pair；
- split、content hash、数学 binding 和配置 hash 均冻结；
- 每个 context 先取重复中位数，禁止把重复数当作独立样本数。

采集过程中识别并修复了一个重要偏差：旧 exact snapshot 只能作为
`mathematical_context`，不能因旧运行恰好完成就直接充当 control，
否则会形成 survivor bias。修订后的 v2 quota 对所有选中 context
都重新运行 fresh QC0/QD1 两臂。

按 context 中位数汇总：

| scale | context | QD1 更优 | 固定动作 | selected/QC0 |
|---:|---:|---:|---|---:|
| 20 | 20 | 4 | QC0 | 1.0000 |
| 30 | 20 | 13 | QD1 | 0.9741 |

scale30 的 QC0 总 wall 为 `81.1593 s`，QD1 加每 context `1 ms`
生命周期成本后为 `79.0556 s`，总计改善约 2.59%；bootstrap 平均
saving 的 95% 下界为 `+0.01380 s/context`。但最差 scale30 context
仍退化 `0.11780 s`，所以“scale30 一律 QD1”只通过了 development
均值检查，不能据此直接 promotion。

完美 context oracle 在 scale30 相对 QC0 的总 wall 比值为
`0.97174`，但相对固定 QD1 规则的额外总收益仅约 `0.18954 s/20
contexts`，即约 0.23%。这点 headroom 很难覆盖 linear/MLP/GAT
完整生命周期成本。因此当前不训练 selector，更不训练 GAT；先验证
无 Torch 的静态规则是否能在 matched end-to-end BPC 中产生收益。

### 6. 无 Torch 静态规则的端到端诊断

已实现实验入口 `scale30_qd1_else_q0`：

- 只在 official-objective 的 `exact_proof` 请求上把 scale30 设为
  QD1；
- scale5/10/20/50/100 在导入 Torch、读取 checkpoint、构图前直接
  保持 Q0；
- phase-one、harvest 和显式指定策略不受覆盖；
- selector ID 和实际策略进入 config hash 与 telemetry；
- 环境变量由 acceptance runner 显式设置，避免 ambient env 泄漏。

首批 matched end-to-end 结果：

| instance | Q0 | 静态规则 | 比值 | 解释 |
|---|---:|---:|---:|---|
| scale20/043 | 3.2596 s | 2.9200 s | 0.8958 | 两臂实际均为 Q0，只验证 bypass；单次差异是噪声 |
| scale30/017 | 97.7984 s | 97.8968 s | 1.0010 | QD1 基本持平、略慢 |
| scale30/015 | 154.8652 s | 137.8051 s | 0.8898 | QD1 快约 11.0%，但该例由 development outcome 定向选择，只是诊断 |

三组均为 `BPC_OPTIMAL`、最终 objective 一致、0 duplicate、0
redline。scale30/015 的 harvest/trajectory 可以因排序而不同，这不
违反 no-filter 和 exact-safe 合同；但定向选择结果不能作为
promotion 证据。

### 7. 明显拖尾实例的 3600 秒 matched 检查

选取 development scale30/058（历史 P0 300 秒预算未闭合）进行
Q0/QD1 串行 matched end-to-end 检查。两臂各自拥有完整 3600 秒
row budget，外层保护为 3720 秒；先运行 Q0，再运行 QD1，避免资源
竞争。该实例同样属于根据历史拖尾和 development 标签选出的定向
诊断，不进入 promotion 统计。

结果：

| 指标 | Q0 | QD1 | QD1 相对 Q0 |
|---|---:|---:|---:|
| end-to-end wall | 2094.5084 s | 1977.5748 s | `0.94417×`，快 5.58% |
| root CG wall | 181.4909 s | 179.3771 s | 快 1.16% |
| tree/proof-tail wall | 1911.9607 s | 1797.1438 s | `0.93995×`，快 6.01% |
| 21 个 final-judge Native wall 合计 | 620.8128 s | 520.8436 s | 快 16.10% |
| extended labels | 2,439,037,407 | 2,504,103,370 | 多 2.67% |
| dominance checks | 1,005,465,186 | 1,053,305,056 | 多 4.76% |
| dominance wall | 451.1590 s | 370.6735 s | 少 17.84% |
| extension wall | 596.1871 s | 512.8853 s | 少 13.97% |
| process-tree peak RSS | 4,316,254,208 B | 4,646,424,576 B | 高 7.65% |

两臂均为 `BPC_OPTIMAL`，具有相同的：

- objective/global LB/global UB：`1.392905`；
- 21 个 evaluated nodes、20 个 branches、0 incomplete node；
- 根阶段 53 个 pricing rounds、3109 added columns；
- `BPC_TREE_OPTIMAL` certificate 和有效 true-dual ledger。

安全审计均满足：

```text
row_budget_exhausted = false
outer_timeout = false
duplicate_negative_count = 0
labels_dropped = false
guidance_induced_permanent_drop = 0
binding_mismatch_accepted = 0
legal_universe_hash_mismatch = 0
nonfinite_hint_accepted = 0
certificate/RC redlines = 0
```

候选 artifacts 中 exact proof 调用全部记录为 QD1，对照全部为 Q0，
未发现候选静默 fallback。两臂 candidate-negative 总数分别为 5007
和 5033，最终全局列数分别为 5034 和 5060；这是排序引起的合法轨迹
差异，不是 guidance 过滤。

这个结果支持继续验证固定 QD1，但也给出两个重要限制：

1. 收益不是来自“少扩展 labels”。QD1 反而扩展更多 labels、执行更多
   dominance checks，却显著降低 dominance/extension wall；训练目标
   必须继续使用 matched wall/regret。
2. QD1 peak RSS 高约 7.65%。虽然本次远低于 10 GB limit，但内存必须
   作为大规模 proof-risk gate，不能只看时间。

由于 scale30/058 是按历史拖尾定向选择、且当前只有一次串行 pair，
它证明“明显拖尾上存在可观优化空间”，但不证明稳定泛化或
promotion。下一步应对预先冻结、非 outcome-selected 的 scale30
sentinel 做 matched 重复；在此之前仍不需要引入 linear/MLP/GAT。

## 修订后的训练目标

proof-tail 首轮不训练 per-label ranker，而训练 context-level
cost-sensitive policy selector。

对同一数学 context `i` 和 exact-safe policy `q`，至少做 matched
fresh runs，只有以下条件全部一致才形成可用标签：

```text
instance/content hash
true mathematical dual hash
branch/full-cut/projected-cut context
objective mode and negative epsilon
completion/subset-dominance configuration
memory and wall budget
exact global-min or no-negative result
frontier_empty = true
labels_dropped = false
```

以 QC0 为工程 control。训练 cost 使用直接 wall，而不是标签数量：

```text
c_iq = log((median_native_wall_iq + inference_cost_iq)
           / median_native_wall_i,QC0)
```

若出现 memory pressure、timeout 或 incomplete，则该策略是带删失的
下界成本，不得填入固定罚值，也不得与完成样本形成虚假的强标签。

模型输出各 policy 的概率 `p(q|x)`，主损失为期望配对 regret：

```text
L_policy = sum_i w_i sum_q p(q|x_i) * c_iq
```

可再加入温度 softmin 的 listwise imitation，但模型选择始终依据
真实 paired wall。scale 权重先等权，context 内重复先取稳健中位数，
禁止一个 80M-label context 按 label 数量重复采样。

部署决策采用保守 gate：

```text
仅当 predicted upper confidence bound
    (policy wall + full guidance lifecycle cost - QC0 wall)
< -promotion_margin
时选择非 QC0；否则 QC0 或 pre-import bypass。
```

第一模型仍从 linear selector 开始。只有 linear 在 grouped validation
上不能区分 scale20 退化 context 与 scale30 no-negative tail，才晋级
MLP/GAT。

## 下一步 gate

在任何学习训练前，先收集：

- 至少 20 个独立 scale20 exact contexts；
- 至少 20 个独立 scale30 exact contexts；
- 每个 context 至少 QC0、QD1 两个 matched fresh arms；
- tail/no-tail、negative/no-negative、subset on/off 分层；
- 重复运行只用于估计噪声，不增加独立样本数。

先检查 deterministic oracle：

```text
oracle policy = argmin_q median_native_wall_iq
oracle net benefit = QC0 wall - oracle wall - selector lifecycle cost
```

40-context quota 已表明：静态 scale gate 足以避免 scale20 的已知
退化，而 context selector 相对静态规则只剩约 0.23% 的完美策略
headroom。因此当前 training gate 判定为不训练 linear/MLP/GAT。

下一道门槛不是“再增加模型容量”，而是：

1. 无 Torch 静态规则在非定向 matched end-to-end scale30 样本上
   必须有可重复净收益；
2. 明显拖尾实例必须显示更好的 closure/survival，而不只是短
   snapshot wall 变快；
3. worst-context 退化必须被保守 bypass 或预算 gate 控制；
4. 所有 exact、安全和生命周期开销门槛继续通过。

若静态规则在这些门槛下仍无收益，就停止 proof-queue learning，
转向 dominance 数据结构或更强的 proof-safe completion bound。

## 8. Request-dynamic held-out gate

在固定 QD1 batch1 只得到“tail 有收益、普通实例中性”后，将规则收窄为：

```text
scale30
and official exact proof
and (branch context active or cut context active)
    -> QD1
else
    -> Q0
```

该规则在新的、预先冻结且未使用 QC0/QD1 outcome 选取的 development
batch2 上完成 6 对 matched end-to-end：

```text
paired geomean ratio = 0.915510
paired median ratio = 0.996375
bootstrap log-ratio UCB95 = -0.000481
worst ratio = 1.002462
tail-stratum geomean ratio = 0.769043
extra incomplete = 0
safety failure = 0
promotion_passed = true
```

两个 held-out tail 分别改善 24.14% 和 22.04%。因此该规则获得进入
protected full80 的资格，但 batch2 结果本身不授权 baseline freeze。

## 9. Protected full80 正式验证

正式 full80 使用 5/10/20/30 各 20 个受保护实例，每实例 Q0 与候选
各一次 fresh cold-start，共 160 slots。运行前冻结 136 个
source/native 文件；每个 slot 前复核 manifest、selection evidence、
配置、实例和 runtime bundle hash。development/calibration 未进入
正式行，solver resume 关闭。

160/160 slots 均为 `BPC_OPTIMAL`，paired objective/global lower bound
一致，true-dual certificate ledger 有效，0 extra incomplete、0
safety failure。候选 QD1 telemetry observations 为：

```text
scale5/10/20 = 0
scale30 = 292
```

四规模性能：

| scale | geomean | p50 | mean-wall | scale gate |
|---:|---:|---:|---:|---|
| 5 | 0.99451 | 0.99988 | 0.99372 | pass |
| 10 | 1.00157 | 1.00795 | 1.00378 | pass |
| 20 | 1.00749 | 1.00205 | 1.00741 | pass |
| 30 | 0.97962 | 0.99743 | 0.94566 | fail |

scale30 arithmetic mean 快约 5.43%，但 geomean 只快约 2.04%；
bootstrap log-ratio UCB95 为 `+0.012857`，worst ratio 为 `1.080284`。
因此预冻结的 geomean、bootstrap UCB 和 worst 三项 gate 失败。

主要收益集中在 instance012：

```text
Q0 = 1545.6043 s
dynamic QD1 = 1122.4712 s
ratio = 0.72623
```

明显退化出现在：

```text
instance003 ratio = 1.05638
instance005 ratio = 1.08028
instance008 ratio = 1.07808
```

具有 QD1 observation 的 15 个实例 aggregate wall ratio 为 0.94182，
但 geomean 为 0.98660、worst 为 1.08028。这证明 QD1 能降低少数
重尾的总墙钟，但 `branch || cut` 规则无法可靠隔离受益 request。

## 10. 最终决策

本候选正式状态为 `NOT_PROMOTED`：

- 不创建新的 baseline freeze；
- 不修改 baseline registry；
- active experiment baseline 继续为
  `FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`；
- production default 继续为 `no_cut`。

full80 证据位于：

```text
runs/p0v2_proof_tail_dynamic_qd1_full80_promotion_20260724/
```

本次打开后，原 full80 已消耗完毕，只能保留为不可变失败证据，不得再
用于特征、阈值、规则或模型选择。下一步不能继续扩大静态 QD1 覆盖，
也不应直接训练 GAT。应在新的 development/calibration 实例上采集
request-level frontier、dominance、branch depth、cut count、RMP round
和历史 proof-wall 特征，构造能够保守 abstain 到 Q0 的 request gate；
不得用 full80 的 instance ID、request 轨迹或 outcome 反向挑选新样本。

只有 deterministic/linear selector 能在新开发数据和新 held-out 上
隔离退化后，才有资格继续；下一次正式 promotion 必须重新生成并冻结
一套未见测试集，不能再次使用本轮 full80。
