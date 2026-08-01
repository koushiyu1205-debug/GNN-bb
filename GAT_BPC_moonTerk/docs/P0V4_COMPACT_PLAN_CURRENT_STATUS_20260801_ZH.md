# P0V4 精简优化计划当前状态（2026-08-01）

## 1. 当前结论

本计划的三个代码分支均已实现，但实验结论不同：

- Diverse Negative Escape：已实现固定 `E_K=(K,4K)`、合法候选审计、
  P0V4 diversity selector 和 partial-return 的 fail-closed 语义。
- Batch Admission：已实现有序原子批量接口、行为差分测试和分阶段计时。
- One-Deviation GAT：原始 route promotion 与后续 sparse-tail revision
  均已实现并运行真实 pilot，但均未通过预注册进阶门，因此 actionful GAT
  与 GAT 性能声明未获授权；运行时保持 NOOP。

当前最终 Exact 开发候选是 V5/E128：P0V4 的 diverse escape、batch
admission 和 exact proof 路径，加上已经触发的 bidirectional pricing 与
SRI group screen。它不是 production 默认，也没有覆盖冻结 P0V4。

正式验收尚未完成。scale5/10/20/30 已有同一 V5 配置的 full20，当前正
通过严格 acceptance runner 串行执行 scale50/002--020；完成后还必须
单独重跑 scale50/001、汇总门槛并执行 scale100 配对诊断。

## 2. 不变的 Exact 边界

以下路径没有交给 GAT：

- 合法候选宇宙；
- true reduced cost；
- dominance、bound 和 pruning；
- branch/cut coefficient；
- exhaustive no-negative proof；
- certificate 的生成与签发。

Negative escape 或 GAT 动作的 incomplete/partial 返回均没有 certificate
authority。TIMEOUT、MEMORY_LIMIT、FRONTIER_LIMIT、hash/OOD、低置信度和
memory adverse event 都 fail closed。P0V4、P0V3 和 production `no_cut`
仍是独立对象。

## 3. Diverse Negative Escape

### 3.1 已实现

Native/Python/config/result 已覆盖：

- `exact_negative_escape_enabled`；
- `exact_admission_batch_size`；
- `exact_raw_negative_pool_size`；
- `exact_negative_escape_policy_id`；
- `negative_escape_triggered`；
- `raw_unique_negative_count`；
- `selected_diverse_negative_count`；
- `negative_escape_termination_reason`；
- diversity bucket、Jaccard、containment 和 true-RC telemetry；
- `can_certify_no_negative`。

Native 只把唯一、合法、true-negative raw columns 计入 `4K`。达到 raw
上限时返回 `FOUND_NEGATIVE_PARTIAL`，强制
`can_certify_no_negative=false`。若搜索空间先穷尽，则保留 P0V4 的
exact closure。Python 审计后零 addable column 时关闭 escape 并用剩余
预算重跑 exhaustive proof；不足 K 但存在 addable columns 时只添加现有
列，不签发证书。

选择阶段复用冻结的 P0V4 selector，不引入新的加权 diversity 优化器。
其优先级仍为 new task set、support-changing、strong replacement、有限
weak replacement，并保留 Jaccard 0.5、containment 0.8 和 true-RC
tie-break。

### 3.2 固定 K 的证据边界

E64/E128/E256 的 192 行 snapshot replay 已完整结束并通过 fail-closed
审计，但原预注册的 10 个 scale50 end-to-end development oracle 没有
完整结束，因此不能声称“形式化 E_K oracle 已选出 E128”。

当前 `fixed_k_selection.json` 的真实语义是：基于用户指定的
“V5+P0V4”研究假设、小规模 80 例和 3 个 scale50 定向实例，将 E128
固定用于 GAT/最终候选开发；其 manifest 明确记录
`formal_e64_e128_e256_development_oracle_complete=false` 和
`formal_exact_promotion_authorized=false`。正式性能只能由当前全量
acceptance 再决定。

## 4. Batch Admission

`ColumnPool.add_many` 和 `MasterColumnView.admit_many_atomically` 先在
scratch pool/view 中逐项复现 P0V4 决策，然后一次提交。保持：

- column ID 与输入/输出顺序；
- semantic signature；
- duplicate/replacement 决策；
- active set；
- RMP coefficient；
- branch/cut context。

计时拆分为 true-RC audit、diversity selection、pool/view admission、
RMP assembly 和 LP solve。原子 batch differential 已覆盖 500 组可穷举
随机输入；当前相关回归没有发现逐列与批量结果不一致。

## 5. One-Deviation GAT

### 5.1 原始 route-level promotion

实现的动作严格是：

- 显式 NOOP 保持冻结 Exact 顺序；
- 从 rank `K+1` 到 `K+32` 选择一列替换 rank K；
- 每个 root 最多一次；
- 下一轮恢复 Exact 顺序；
- 不改变 Native label ordering、候选合法性、proof 或 certificate。

Opportunity census 得到：

- scale30：125 个 eligible contexts、5 个实例，通过规模内 opportunity
  门；
- scale50：0 个 eligible contexts、0 个实例，未通过门；
- 因而昂贵正式 oracle 未获授权。

额外的 5-context scale30 engineering smoke 没有任何一个达到 5% 强信号，
状态为 `STOP_OR_REVISE_ACTION_DEFINITION`。这是原始 route-promotion
动作失败的结论，不能用后续 sparse-tail 结果覆盖。

### 5.2 Sparse-tail revision

为避免继续扩展 route-promotion 取证，后续只试验 root、一次性的
NOOP/S1/S4 sparse true-dual escape。固定 pilot 在动作前冻结了 11 个
自然上下文，执行 22 个动作：

- 22/22 完成；
- 0 个安全/certificate redline；
- 3/22 个动作产生可执行且局部更快的 partial-negative 返回；
- 这 3 个动作只分布在 2 个上下文；
- 结果无关的实例隔离 calibration split 中正动作数为 0。

Two-head GAT 已按固定数据训练一次，推理 p99 为 1.900451 ms，但 harmful
gate 关闭。其 checkpoint、dataset 和 manifest 均 hash 绑定；
`evaluation_authorized=false`、`deployment_authorized=false`，运行时只能
NOOP。

`terminal_decision.json` 将两次失败分支共同绑定为
`STOPPED_BY_PREDECLARED_GATES`。该结论只授权“one-deviation 机制和安全壳
已实现并按门槛停止”，不授权“GAT 有性能收益”。

## 6. 当前运行证据

### 6.1 已完成

同一 V5/E128 配置：

| scale | exact | mean wall (s) | max wall (s) |
|---:|---:|---:|---:|
| 5 | 20/20 | 0.457576 | 0.514521 |
| 10 | 20/20 | 1.194223 | 3.259176 |
| 20 | 20/20 | 19.651638 | 97.118287 |
| 30 | 20/20 | 81.036313 | 262.852607 |

三个 scale50 定向实例也 exact：005 为 991.586073 秒，006 为
250.840685 秒，010 为 1682.661645 秒。它们证明候选可运行，但不能替代
20 例门槛。

早期 bidirectional V2 的 scale50 full20 为 11/20，V3 的前 10 例为
7/10。两者算法配置与当前 V5 不同，只能作为历史诊断。

### 6.2 正在执行

正式输出根：

`runs/p0v4_final_acceptance_v2_20260801/`

当前阶段：

`exact-scale50-heldout`，即 scale50/002--020，单进程、每例最多 3600
秒。结束后单独运行 `exact-scale50-001`。

严格 prepare 状态为 `EXACT_READY_GAT_STOPPED_BY_GATE`。它绑定：

- selected Exact config；
- Native modules；
- Exact/guidance/native 源码；
- acceptance runner；
- one-deviation terminal decision；
- paper ablation configs。

运行期间不得修改上述 binding 内文件，否则 launch manifest 会把证据
标成不可用。

## 7. 当前测试

- P0V4 compact-plan 定向回归：76/76；
- Native backend 与原 route-admission 回归：75/75，28 subtests；
- Native CTest：2/2；
- `git diff --check`：当前新增/修改验收文件通过。

这些测试证明已覆盖的接口和不变量，不替代 scale50/100 性能实验。

## 8. 尚未完成的正式门槛

- 当前 V5 scale50 full20 尚未结束，不能声称 14/20；
- held-out scale50/002--020 尚未证明 13/19；
- scale5/10/20/30 相对冻结控制的正式 paired geometric mean 和合并 5%
  加速门尚未在新 acceptance capsule 中汇总；
- scale100/001--005 的 P0V4/最终 Exact 配对诊断尚未执行；
- 最终独立 freeze 尚未创建；
- GAT 增量 5% 门不适用，因为 actionful GAT 已按预注册门槛停止，任何
  文档都不得把 shadow model 当作正式 GAT 候选。

只有 Exact 的全部正式 evidence、launch binding、redline 和性能门通过
后，才能冻结 Exact-only 最终候选。若任一门失败，应保留 P0V4 与当前
候选为独立实验对象，不切换 production 默认。
