# P0V5 Minimal Interaction-GAT QD1 Selector V6 终止交接

## 1. 最终状态

V6 已按冻结计划完成到 calibration gate，并形成机器可读终止：

```text
FAIL / NO_SAFE_GAT_CALIBRATION_THRESHOLD
development_only = true
deployment_authorized = false
production_switch_authorized = false
```

权威状态文件：

```text
runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817/terminal_decision.json
SHA256 = bebc43d1a636701cbf4cbb946cb128ecb418c0bd069cced2054cc50afef02920
```

这是一条合法 negative chain，不是未完成运行，也不是脚本异常。根据预冻结 stop rule，heldout、Development-E2E 和 formal full100 均不得启动。

## 2. 冻结基线与实际完成内容

V6 保持 action universe 为 `Q0/QD1`，Native engine、Q0/QD1 comparator 和 exact semantics 均未修改。QGR1、QB1 永久 forced-veto；所有训练 checkpoint 都只有一个 QD1 arm 和 benefit/gain/adverse 三个输出。

冻结导入和数据集完成情况：

| 项目 | 结果 |
|---|---:|
| copied literal-Q0 pre-action snapshots | 110 |
| V5 raw matched tasks | 444 |
| collapsed QD1 outcomes | 74 |
| train contexts / instances | 57 / 28 |
| calibration contexts / eligible instances | 17 / 7 |
| trained model/seed checkpoints | 15 |

V5 冻结 evidence 实际含一条 scale50 calibration resource failure：Q0 完成、QD1 三个 block 全部 censor。V6 保留该事实并将其并入 adverse target，没有建立只有一个正样本的独立 resource head。

数据集和训练报告：

```text
runs/p0v5_minimal_interaction_gat_qd1_selector_v6_20260817/
  interaction_gat_qd1_training_dataset.freeze.json
  selector_training_report.json
  selector_training/
```

对应 SHA256：

```text
dataset = dfff59ff297781acfa023eb1709942c25dd57af2e2c4a5713fbafab53e149ee9
training report = ab907a3f996ed8472cb122794fbc792930118e22d09329c73a1c6fbc38168c41
freeze registry = 18914df78df30fcea191884badbad2815e78c74127b84c46056a044d02ffbd58
```

## 3. 为什么失败

三个正式 GAT seed 的总体 OOF macro-instance rank accuracy 分别为：

```text
61635  -> 0.708333
91267  -> 0.601190
170141 -> 0.672619
```

这说明模型并非完全没有排序信号，但冻结 threshold grid 上不存在同时覆盖两个规模的安全激活方案。

只读 threshold 诊断显示：

| Seed | scale30 最佳零风险 GM | scale30 激活实例 | scale50 合格 threshold |
|---:|---:|---:|---:|
| 61635 | 0.974665 | 2 | 0 |
| 91267 | 0.915534 | 3 | 0 |
| 170141 | 0.913625 | 3 | 0 |

scale30 已具备安全 gating 信号；失败完全由 scale50 calibration gate 触发。MLP、Linear、no-message 和 shuffled-topology 在 scale50 同样只能成为诚实的 Q0 no-op control，没有任何 control 证明 scale50 QD1 子集可以被现有输入安全识别。

因此当前证据只支持：

```text
QD1 has useful scale30 and scale50 oracle headroom,
but the frozen pre-action Interaction-GAT inputs do not support
safe scale50 QD1 activation.
```

它不支持 `Interaction-GAT-gated QD1 queue-policy acceleration` 成功声明。

## 4. 验证与 exact-safe 边界

已完成：

- V2/V3/V4/V6 相关 Python 回归：68 passed；终止后 V6 专项复验：9 passed。
- V6 clean-process scale5/10/20 与 scale30/50 tree early bypass：manifest、graph、Torch、model、ranker calls 均为 0，并返回同一个 Q0 request。
- V6 task-ID permutation / graph-pooling invariance。
- Native CTest：2/2 passed；`sizeof(State)==176` 断言保留。
- 冻结 500-case old/new Native exact differential：500 cases、0 redline、old/new digest 一致。
- 15 个 checkpoint hash 互异、独立训练、`candidate_authorized=false`。
- normalization 和 5% OOD envelope 可从 28 个 train instances 精确重建；heldout/E2E 不在 dataset 中。
- terminal writer guard 已验证：后续 dataset writer 返回 `terminal V6 chain forbids artifact writers`。

生产默认仍为：

```text
no_cut + P0V4/P0V5 Exact + Q0
```

## 5. 未启动阶段与禁止操作

以下阶段按计划未启动，也不存在对应 outcome：

- selector-heldout fresh；
- Development-E2E；
- formal full100；
- research candidate manifest；
- production review。

不得进行：

- 在 V6 calibration/heldout 上重新调 threshold、seed、OOD envelope 或 action mask；
- 从 MLP/Linear/no-message/shuffled-topology 生成 runtime candidate；
- 用 scale30 收益掩盖 scale50 无安全激活；
- 在 V6 run root 中补写 heldout/E2E/formal artifact；
- 恢复 QGR1/QB1，或把 V6 改写为 label-GAT 成功；
- 修改 V6 terminal decision 或切换 production default。

## 6. 安全重启边界

若继续研究，必须新建独立证据链，不能续写 V6。合理的新方向只能针对 scale50 可识别性，例如增加 outcome-blind 的 scale50 calibration instances、重新设计只使用 action 前信息的 interaction/context features，或采用显式 uncertainty/conformal abstention；新的 representation、threshold 和 acceptance code 必须在读取新 outcome 前冻结。

QGR1 action-surface trace 合同修复仍属于独立 V6R 研究线，不得再次阻塞或污染 Q0/QD1 selector 的证据链。
