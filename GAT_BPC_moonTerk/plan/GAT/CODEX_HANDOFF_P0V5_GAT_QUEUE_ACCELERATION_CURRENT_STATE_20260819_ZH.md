# P0V5 GAT Queue Acceleration 当前状态与根因交接

> 日期：2026-08-19
>
> 范围：P0V5 proof-queue ordering、Context/Frontier Interaction-GAT、QD1/QB1/QGR1 研究链
>
> 当前 production default：`no_cut + P0V4/P0V5 Exact + literal Q0`
>
> 当前部署状态：无 GAT candidate 获得 deployment 或 production-switch 授权

## 1. 先读结论

当前不是“代码还没写完”或“实验尚未跑完”，而是多条独立证据链已经把问题收敛到以下结论：

1. **scale30 的 QD1 加速信号真实且稳定。**
   - 旧 real-map 三重复矩阵和新的 Native late-switch diagnostic 都支持 QD1；
   - 在 V10R1 的 4096-pop late-switch 中，8/8 实例受益，fixed QPD1 net GM 为
     `0.820842`，没有 harmful instance；
   - scale30 当前首先是“验证并兑现确定性 QD1 收益”的问题，不是“必须让 GAT
     证明自己必要”的问题。

2. **scale50 存在 QD1 的选择性 oracle headroom，但收益稀疏、伤害很重。**
   - V10R1 在 16384 boundary 的 oracle GM 为 `0.936561`；
   - 固定 QPD1 GM 却为 `1.160861`；
   - 8 个实例中只有 1 个 strong-benefit instance，另有 3 个 harmful instances，
     其中两个 ratio 约为 `1.70941` 和 `3.03615`；
   - 因此 scale50 不是没有机会，而是现有正例支持不足以训练可安全激活的 GAT。

3. **早期 scale50 QB1 的亮眼结果确实存在，但没有复现。**
   - 早期 V3 fresh heldout 中，GAT 在两个 scale50 context 选择 QB1，scale50 net GM
     为 `0.642134`；
   - 后来的 real-map 三重复矩阵中，scale50 QB1 的 27 个 determined contexts 全部
     harmful，0 个 beneficial，best ratio 也只有 `1.055891`，instance-weighted GM
     为 `1.483042`；
   - 所以当前 veto QB1 是由更广、更严格的 fresh evidence 支持的，不能仅凭早期两个
     context 将其复活。

4. **目前连续负结果的根因不是“GAT 层数不够”，而是 action support、可观测性和净开销。**
   - scale30 动作几乎普遍有效，GAT 没有必要性；
   - scale50 动作结果高度异质，切换前的静态图不能稳定预测切换后的 label/dominance
     动力学；
   - 通过两个辅助请求显式观察 counterfactual 虽然保留了 oracle headroom，但固定
     prefix 成本对快速 context 过高；
   - exact-safe、heldout 和 control gates 正确地阻止了把偶然收益包装成 GAT 成功。

当前所有相关运行均已 terminal；截至本交接核对时，没有 V7/V8/V9/V10 Native 实验
进程仍在运行。

## 2. 不可改变的 exact-safe 边界

所有后续研究必须继续遵守：

- GAT 只能选择 queue policy，或改变合法 label 的弹出顺序；
- 不得删除 label、route 或 arm candidate；
- 不得修改 dominance、completion bound、reduced cost、branch/cut、negative threshold、
  exhaustive stopping 或 certificate 条件；
- candidate harvest 不能替代 exhaustive/no-negative proof；
- timeout、memory-limit、label drop 或 frontier 未穷尽不能签发 exact closure；
- scale5/10/20 和未授权 lifecycle 必须 fail-closed 为 literal Q0；
- 当前 `State` ABI 继续保持 `sizeof(State)==176`；
- production default 和历史 baseline registry 不得因 development diagnostic 被改写。

## 3. 当前证据的权威顺序

发生冲突时按以下顺序读取：

1. 对应 run root 的机器可读 `terminal_decision.json`；
2. fresh blocked-process raw tasks 和 collapsed matched outcomes；
3. 独立 verification/audit report；
4. closeout/handoff；
5. implementation plan、训练曲线和旧 diagnostic prose。

设计计划、脚本存在、surrogate accuracy 或旧单次 outcome 均不能覆盖后来的 terminal 和
fresh wall evidence。

## 4. 各研究链实际完成情况

| 研究链 | 机器结论 | 实际说明 |
|---|---|---|
| QG2 TinyGAT | `TERMINATED_NEGATIVE` | scale30 force-on 0/3 beneficial，paired GM `1.296944`；label-GAT 路线停止 |
| V3 old selector | development-only | scale50 两个 QB1 selected contexts 曾有强收益，但未形成独立、可复现的 current-engine arm authorization |
| V3 real-map matrix | `FAIL / RESOURCE_CENSOR_UNDETERMINED` | 已完成 558/639 raw tasks；触发双删失 stop，但已完成部分足以显示 QB1 广泛退化 |
| V4 | `FAIL / INSUFFICIENT_FRESH_ROOT_COVERAGE` | coverage 失败；QB1 forced-veto |
| V5 | `FAIL / QGR1_TRACE_MANDATORY_WITNESS_INCOMPLETE` | QD1 evidence 可用；QGR1 trace contract 不完整，未形成 label-GAT candidate |
| V6 | `FAIL / NO_SAFE_GAT_CALIBRATION_THRESHOLD` | pre-action Interaction-GAT 无安全 threshold；未进入 heldout/E2E/formal |
| V7R3 | `FAIL / SCALE50_BENEFIT_HARM_NOT_SEPARABLE` | 4096-pop frontier 特征对 scale50 benefit/harm 不可安全分离 |
| V9R0 | `FAIL / BASE_LABEL_FRONTIER_NOT_IDENTIFIABLE` | 256-label graph 改善 rank，但 benefit classification 和近邻冲突仍不过门 |
| V9R1 | `FAIL / MULTIRES_FRONTIER_NOT_IDENTIFIABLE` | 64-cell + 256-label 仍未优于 simple/topology controls |
| V10R1 | `FAIL / SCALE50_LATE_SWITCH_SUPPORT_GATE_FAILED` | scale30 通过；scale50 16384 有 oracle，但仅 1 个 strong-benefit instance |
| V8R1 | `FAIL / COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE` | 正确计时后 warm p99 通过，但逐 context 2% prefix 成本门失败；OOF 未启动 |

这些都是合法 negative chain，不是需要从中断位置继续跑的 partial runs。

## 5. 当前最可靠的 queue-arm 证据

### 5.1 scale30 QD1

V3 real-map 已完成部分按冻结三重复 collapse 规则重新核对：

| 指标 | 数值 |
|---|---:|
| determined contexts | 28 |
| determined instances | 18 |
| context benefit `<=0.98` | 26 |
| context harm `>=1.05` | 2 |
| instance-weighted GM | `0.778757` |

V10R1 的独立 late-switch diagnostic：

| 指标 | 数值 |
|---|---:|
| boundary | 4096 |
| determined instances | 8/8 |
| fixed QPD1 net GM | `0.820842` |
| net oracle GM | `0.820842` |
| QPD1 winners | 8 |
| strong-benefit instances | 8 |
| harmful instances | 0 |
| probe overhead GM | `1.003691` |

两个不同数据链都支持同一方向：scale30 的 deeper-first QD1 ordering 是当前最有把握的
queue acceleration arm。但这些仍不是 formal full20/full100 promotion evidence。

### 5.2 scale50 QD1

V3 real-map 已完成部分：

| 指标 | 数值 |
|---|---:|
| determined contexts | 27 |
| determined instances | 11 |
| context benefit `<=0.98` | 14 |
| context harm `>=1.05` | 12 |
| instance-weighted GM | `0.975576` |

这说明 scale50 的 QD1 不是完全无效，而是高度 selective。V10R1 进一步测试同一正式请求
中的不同 late-switch boundary：

| Boundary | Determined | Fixed QPD1 GM | Oracle GM | Winners | Strong benefit | Harm |
|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 7/8 | `1.262341` | `0.987423` | 4 | 0 | 3 |
| 8192 | 7/8 | `1.260554` | `0.982355` | 3 | 1 | 3 |
| 16384 | 8/8 | `1.160861` | `0.936561` | 4 | 1 | 3 |

16384 是唯一通过 `oracle GM <=0.95` 的 boundary，但强收益主要来自：

```text
instance 23cc0c6fee9f1fa0: ratio 0.654282
```

其余三个 winner 约为 `0.95970 / 0.97031 / 0.97158`。与此同时，harmful tail 包含
`1.70941` 和 `3.03615`。当前证据不足以把这一个强正例拆分为 train/calibration/heldout
并证明泛化。

### 5.3 scale50 QB1：为什么历史记忆与当前 veto 不冲突

早期 V3 fresh selector report 的确记录：

```text
scale50 contexts = 12
GAT activated QB1 = 2
beneficial = 2
harmful = 0
net GM = 0.642134
```

这说明“QB1 在某些 context 上可能极快”，但不能推出“QB1 在 scale50 普遍有效”。后来
V3 real-map 矩阵的已完成部分按同一 context 内三重复中位数、实例内折叠、实例等权重算：

| 指标 | 数值 |
|---|---:|
| determined contexts | 27 |
| determined instances | 11 |
| beneficial `<=0.98` | 0 |
| harmful `>=1.05` | 27 |
| best ratio | `1.055891` |
| instance-weighted GM | `1.483042` |

早期结果只覆盖被旧 selector 激活的极少数 context，训练来源也属于旧 outcome chain；后来的
更广 real-map matrix 没有复现。因此 QB1 当前只能作为历史机制线索，不能进入 runtime
action universe。若未来要重新审计，必须另建 outcome-blind、current-engine、fresh
reproducibility chain，不能导入旧 V3 selector threshold 或 outcome。

### 5.4 QGR1/label-GAT

QG2 TinyGAT force-on 已负，QGR1 又因 mandatory witness/parent-chain trace contract 不完整
而未完成可靠训练。到目前为止没有 fresh wall 证据支持 QGR1 加入正式 selector。继续修补
label-GAT 会再次阻塞已经证明有效的 scale30 QD1 主线，因此当前保持 veto。

## 6. 为什么多次 GAT 都是负结果

### 6.1 首先是 action support，不是 model capacity

GAT selector 只能利用“已有动作在某些 context 真正更快”的事实，不能创造 queue arm 的
收益。

- scale30 QD1 几乎普遍有效，selector 的学习问题退化为“多数时候都选 QD1”；
- scale50 QD1 的少量收益与严重伤害并存，strong positive 数量太少；
- QB1/QGR1 没有 current-evidence authorization。

因此继续增加 hidden dimension、attention heads、seed 或 pooling，并不能补足缺失的强正例。

### 6.2 queue ordering 的 wall 影响是后验动力学

QD1/QB1 不改变合法 label 集，但会改变 label 到达 dominance buckets 的顺序，从而改变：

- frontier 增长和 churn；
- extended/dominated label 数；
- dominance candidate checks 和 dominance wall；
- terminal/negative route 到达时间；
- exhaustive proof tail 的工作分布。

同一个 pre-action graph 或 4096-pop frontier 可以很相似，切换后的动力学却完全相反。坏的
scale50 context 会出现 label/frontier 膨胀，wall 放大到 `1.7–3.0x`；好的 context 则可能
提前释放完整 proof，达到约 `0.65x`。这种结果不是单一静态图上的平滑分类函数。

### 6.3 现有 observability 不足

V7R3 的 scale50 grouped-OOF 结果：

| 指标 | 数值 |
|---|---:|
| GAT benefit balanced accuracy | `0.609091` |
| GAT rank accuracy | `0.525000` |
| best control benefit BA | `0.654545` |
| 相似图对的相反 benefit 标签比例 | `0.647059` |

V9R0 的 256-label graph 提高了 rank，但仍未通过安全分类门；V9R1 将完整 64-cell mass 与
256-label sample 联合后，scale50 GAT instance benefit BA 仍只有 `0.654545`，best simple
control 为 `0.709091`，GAT rank 为 `0.625`，没有稳定 topology advantage。

这表明问题不只是节点采样太少。单时点图描述“frontier 现在有什么”，却没有描述“切换
QD1 后 frontier 将如何响应”。

### 6.4 显式 counterfactual 的固定成本过高

V8/V8R1 用两个 telemetry-only 请求分别运行 Q0/QD1 prefix，再启动独立 formal exact
request。V8 原计时合同有误，不能作为最终成本权威；V8R1 重新 fresh 采集并用 Native
endpoint elapsed wall 修正。

V8R1 正确结果：

| B | paired prefix p99 | 超过 QPF0 2% 的 contexts | 最坏比例 | taxed oracle s30 | taxed oracle s50 |
|---:|---:|---:|---:|---:|---:|
| 128 | `119.234 ms` | 5 | `11.822%` | `0.844668` | `0.952201` |
| 512 | `137.553 ms` | 5 | `13.851%` | `0.848260` | `0.952550` |
| 2048 | `174.287 ms` | 6 | `17.848%` | `0.856056` | `0.953544` |

warm p99 和 taxed oracle 都通过，唯一失败的是逐 context 2% overhead gate。五个失败
context 全部是快速 scale30 context：QPF0 只有约 `0.389–1.614 s`，重复执行两次 4096-pop
prefix 的固定税无法摊薄。

因此 V8R1 证明的是：

> “两个独立 4096-pop auxiliary requests + 每 context 2% 净开销门”这一 runtime 合同不可用。

它**没有**证明 counterfactual feature 本身不可分，也没有完成 GAT/MLP/Linear/no-message/
shuffled-topology 的 OOF。不得把 V8R1 写成“GAT accuracy 再次失败”。

### 6.5 严格 gates 正在阻止假阳性

此前负结果还来自 coverage、resource censor、trace completeness、simple-control advantage、
topology contribution 和 heldout-safe activation 等不同 gate。这些 gate 并不是妨碍成功，
而是在阻止：

- 用一个强收益实例掩盖严重 harmful tail；
- 用旧 synthetic/single-run outcome 训练并授权；
- 用 scale30 收益平均掉 scale50 失败；
- 用 MLP/Linear 的收益宣称 GAT message passing 成功；
- 用 processed-label、首次负列或 surrogate accuracy 代替真实 solver wall；
- 把 incomplete pricing 当成 exact certificate。

## 7. 当前没有完成或没有授权的内容

截至 2026-08-19：

- 没有通过 calibration 的 current Interaction-GAT candidate；
- 没有 V8R1 OOF checkpoints、portable candidate bundle 或 runtime manifest；
- V10R1 没有训练 temporal GAT；
- V8R1/V9R1/V10R1 均未读取或生成新的 selector-heldout、Development-E2E 或 formal
  full100 outcome；
- scale30 QD1 尚未完成独立 development-E2E/formal promotion；
- scale50 QD1 没有安全 selector；
- QB1、QGR1、label-GAT 仍被 veto；
- production default、no-cut baseline 和 exact certificate path 均未改变。

## 8. 后续禁止事项

不得：

1. 在 V7R3/V9/V10/V8R1 旧 corpus 上继续换 seed、hidden size、pooling 或 threshold；
2. 放宽 V10R1 的 strong-benefit gate，把唯一强正例当成足够训练支持；
3. 按 V10R1 outcome 继续补选相似实例进入同一 train split；
4. 用早期 V3 的两个 QB1 context 覆盖后来的 27-context negative matrix；
5. 把 V8R1 terminal 解读为已经完成 GAT observability 测试；
6. 用简单模型获胜包装成 GAT acceleration；
7. 让 scale30 的确定性 QD1 收益掩盖 scale50 失败；
8. 在正式 outcome 后修改 boundary、trial budget、OOD、threshold 或 action mask；
9. 修改 Q0 comparator、dominance、bound、RC、certificate 或 production default 来制造性能收益。

## 9. 推荐的下一步

建议拆成两条互不掩盖的研究线。

### 9.1 线 A：兑现 scale30 的确定性 QD1 收益

新建独立 development-only chain，只研究：

```text
scale30 root-CG V5 fallback
literal Q0 until 4096 pops
in-place switch to QD1
```

先做新的 outcome-blind development-E2E，再做 scale5/10/20 bypass 和 formal scale30。
这条线可以声明 `late-switch QD1 queue acceleration`，不能声明 GAT acceleration。

这样可以先保存已经出现两次的 scale30 实际收益，不再让 scale50 GAT 研究阻塞它。

### 9.2 线 B：scale50 同请求内“可撤销 QD1 短试运行”

scale50 的根因是切换后的动态响应不可见。下一次若坚持使用 GAT，建议不再启动两个辅助
pricing requests，而在同一个正式 exact request 内：

```text
Q0 until 16384
→ switch QD1 for a fixed small number K of pops
→ observe actual frontier/dominance/label-growth deltas
→ GAT chooses CONTINUE_QD1 or MIGRATE_BACK_TO_Q0
```

要求：

- Q0↔QD1 迁移均保留全部 label 和 creation IDs；
- K、观测特征、abort/revert contract 必须在 wall outcome 前冻结；
- 模型只能在真实 QD1 短试运行后决定继续或撤回；
- 不重启 pricing，不重复执行前 16384 个 Q0 pops；
- 试运行成本计入 net wall；
- 任一迁移完整性错误为 correctness redline；
- 首先运行 force-on oracle pilot，oracle 不通过时禁止训练 GAT。

建议先用至少 24 个全新、outcome-blind scale50 instances 做固定 pilot，比较：

```text
Q0
QD1-at-16384-and-continue
QD1-at-16384-for-K-then-revert-Q0
```

pilot 首先回答两个问题：

1. bounded QD1 trial 能否把 `1.7–3.0x` harmful tail 压回可接受范围；
2. trial response 是否能在多个独立实例上保留并识别 strong-benefit signal。

只有 strong-benefit 支持分布到多个实例、revert arm 本身 exact-safe 且 net oracle 有足够
headroom，才训练 temporal/response GAT。否则应停止 scale50 queue-selector GAT，转向新的
deterministic queue arm 或 Native dominance/data-structure 优化。

### 9.3 QB1 的唯一合法重开方式

如果明确要求核验早期 QB1 记忆，只能另开一个很小的 current-engine reproducibility audit：

- 全新、outcome-blind scale50 instances；
- 一个自然 root context/instance；
- Q0/QB1 三重复；
- 预冻结 minimum support 和 harmful-tail gate；
- 不训练 selector，不导入早期 threshold；
- 失败后继续永久 veto。

鉴于现有 27/27 harmful 证据，这不是推荐主线。

## 10. 关键证据路径

### 当前根因与 latest terminals

- `runs/p0v5_frontier_observability_root_cause_v7r3_20260818/terminal_decision.json`
- `runs/p0v5_multires_frontier_observability_v9r1_20260818/terminal_decision.json`
- `runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818/terminal_decision.json`
- `runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818/corrected_oracle.decision.json`
- `runs/p0v5_counterfactual_prefix_gat_qd1_selector_v8r1_20260818/terminal_decision.json`
- `runs/p0v5_counterfactual_prefix_gat_qd1_selector_v8r1_20260818/representation_development.report.json`

### QB1/QD1 历史和 real-map evidence

- `runs/p0v5_qg2_v3_gat_first_20260806/arm_selector_fresh_heldout_v1/report.json`
- `runs/p0v5_interaction_gat_queue_selector_v3_20260814/matched_qd1_qb1_execution.freeze.json`
- `runs/p0v5_interaction_gat_queue_selector_v3_20260814/matched_qd1_qb1_execution.freeze_raw/`
- `runs/p0v5_interaction_gat_queue_selector_v3_20260814/terminal_decision.json`

### 推荐先读的 closeouts

- `plan/GAT/CODEX_HANDOFF_P0V5_QG2_TINYGAT_CLOSEOUT_20260807_ZH.md`
- `plan/GAT/P0V5_MINIMAL_INTERACTION_GAT_QD1_SELECTOR_V6_CLOSEOUT_20260817_ZH.md`
- `plan/GAT/P0V5_BASE_LABEL_FRONTIER_V9R0_CLOSEOUT_20260818_ZH.md`
- `plan/GAT/P0V5_TEMPORAL_FRONTIER_LATE_SWITCH_V10R1_CLOSEOUT_20260818_ZH.md`
- `plan/GAT/P0V5_COUNTERFACTUAL_PREFIX_V8R1_CLOSEOUT_20260818_ZH.md`

## 11. 一句话交接

目前最可信的工程结论是：**scale30 应先独立验证并兑现 QD1 late-switch；scale50 仍有
选择性 QD1 oracle，但切换前图不可安全分辨、双 prefix 又太贵，下一步只有在同一 exact
request 内进行可撤销的短 QD1 试运行，并先通过 fresh force-on oracle，才值得再次训练
真正的 message-passing GAT。**
