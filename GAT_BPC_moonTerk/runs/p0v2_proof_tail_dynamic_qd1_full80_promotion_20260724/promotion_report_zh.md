# P0 V2 动态 QD1 full80 正式验证报告

日期：2026-07-24  
候选：`scale30_branch_or_cut_qd1_else_q0`  
控制：`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2` / Q0  
结论：`NOT_PROMOTED`

## 1. 验证范围

正式验证使用受保护的 full80：

- scale5/10/20/30 各 20 个实例；
- 每个实例 Q0 与候选各一次 fresh cold-start；
- AB/BA 交替，共 160 个 slot；
- solver resume、development 和 calibration 均未进入正式行；
- 运行前冻结 136 个 source/native 文件的 runtime bundle；
- manifest、实例、配置、held-out selection evidence 和 runtime bundle
  在运行期间持续验哈希。

## 2. Correctness 与安全

160/160 slot 均满足：

```text
algorithm_status = BPC_OPTIMAL
certificate_scope = BPC_TREE_OPTIMAL
true-dual certificate ledger valid = true
objective/global lower bound paired equal = true
extra incomplete = 0
safety failure = 0
labels_dropped = false
guidance-induced permanent drop = 0
binding mismatch accepted = 0
legal universe hash mismatch = 0
nonfinite hint accepted = 0
```

候选中的 QD1 telemetry observation：

```text
scale5  = 0
scale10 = 0
scale20 = 0
scale30 = 292
```

因此三个非目标规模确实保持 Q0，未出现 QD1 跨规模泄漏。

## 3. 四规模性能

| scale | geomean 候选/Q0 | p50 候选/Q0 | mean-wall 候选/Q0 | 结论 |
|---:|---:|---:|---:|---|
| 5 | 0.99451 | 0.99988 | 0.99372 | 通过非退化 gate |
| 10 | 1.00157 | 1.00795 | 1.00378 | 通过非退化 gate |
| 20 | 1.00749 | 1.00205 | 1.00741 | 通过非退化 gate |
| 30 | 0.97962 | 0.99743 | 0.94566 | 未通过 promotion gate |

scale30 的 arithmetic mean 改善约 5.43%，但主要由少数重尾实例贡献；
逐实例稳健收益不足：

```text
bootstrap log-ratio UCB95 = +0.012857 > 0
worst candidate/Q0 ratio = 1.080284
```

失败的预冻结 scale30 gate：

- geomean 要求不高于 `0.95`，实际 `0.979624`；
- bootstrap log-ratio UCB95 要求不高于 `0`，实际 `+0.012857`；
- worst ratio 要求不高于 `1.02`，实际 `1.080284`。

## 4. 收益和退化结构

scale30 有 13/20 个实例 wall 改善，但结果不是均匀改善。

最明显收益：

| instance | Q0 | 动态 QD1 | ratio |
|---:|---:|---:|---:|
| 012 | 1545.6043 s | 1122.4712 s | 0.72623 |
| 001 | 149.1188 s | 119.5165 s | 0.80149 |
| 014 | 1694.3076 s | 1657.2126 s | 0.97811 |

其中 instance001 没有观测到 QD1，约 19.85% 差异不能归因于 QD1，
反映单重复端到端 wall 仍存在顺序/运行噪声。可归因的主要重尾收益是
instance012。

明显退化：

| instance | Q0 | 动态 QD1 | ratio | QD1 observations |
|---:|---:|---:|---:|---:|
| 003 | 143.0944 s | 151.1618 s | 1.05638 | 8 |
| 005 | 219.4589 s | 237.0779 s | 1.08028 | 6 |
| 008 | 359.1888 s | 387.2341 s | 1.07808 | 6 |

具有 QD1 observation 的 15 个实例：

```text
geomean ratio = 0.98660
aggregate wall ratio = 0.94182
median ratio = 0.99508
worst ratio = 1.08028
```

这说明 aggregate wall 的确因重尾下降，但典型实例只改善约 1.34%，
且存在 5%–8% 的可重复风险。`branch_context || cut_context` 不是足够
精确的调用条件。

## 5. 决策

- 不创建新的 baseline freeze；
- 不修改 `runs/native_bpc_baseline_registry.json`；
- active experiment baseline 继续为
  `FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`；
- production default 继续为 `no_cut`；
- 动态 QD1 保持实验候选，不进入默认模型。

本次打开后，原 full80 已成为消耗完毕的最终测试，只能作为不可变的
失败证据，不能再用于特征、阈值、调用规则或模型选择。

下一轮如果继续 proof-tail，应在新的 development/calibration 实例上
预测“当前 exact request 使用 QD1 的净 wall regret”，而不是按实例
规模、是否存在 branch/cut 或总拖尾长度直接启用。新数据必须覆盖类似
“少数重尾大收益”和“普通 branch/cut request 退化”的结构，但不能用
full80 的 instance ID、request 轨迹或 outcome 反向挑选。若
deterministic request gate 无法在新开发数据上隔离退化，再考虑 linear
selector，不应直接使用 GAT；再次正式 promotion 需要新生成并冻结一套
未见测试集。
