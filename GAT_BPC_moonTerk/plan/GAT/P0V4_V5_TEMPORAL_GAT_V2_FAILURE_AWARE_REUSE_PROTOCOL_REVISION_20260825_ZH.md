# P0V4+V5 Temporal-GAT V2 Failure-aware Reuse Protocol Revision

> 状态：`PROTOCOL_REVISION_APPROVED_BEFORE_FIRST_D5_ARM_OUTCOME`  
> 批准日期：2026-08-25  
> 适用目标：完成 P0V4+V5 统一 Temporal-GAT Production 优化计划  
> 被修订规则：任何 terminal negative 后无差别重建全部 corpus/calibration/development/sealed  
> 保留规则：exact/correctness、sealed independence、outcome-before-freeze 禁令、fail-closed 和 production promotion gates  
> 当前活动任务：Round 5 eligibility 必须自然结束，不得为 V2 中断  
> 当前数据定位：Round 5 将封存为 `Data Epoch D5`

---

## 1. 修订决定

从本协议生效起：

> `TERMINATED_NEGATIVE` 关闭一个冻结的 policy/evaluation hypothesis，但不再自动删除或统计性否定与失败原因无关的 platform、corpus、snapshot、eligibility 和未揭示 partition。

新流程必须根据失败类型计算最小合法 invalidation scope，只重做失效层及其下游。所有复用必须由 content hash、source binding、partition access ledger 和机器可读 reuse decision 证明，不能依靠口头记忆。

本修订不是降低 gate。它减少的是重复生成、重复重放和无差别 restart，不减少：

- exact differential；
- migration conservation；
- route reduced-cost audit；
- certificate semantics；
- Q0/CONTINUE/REVERT direct wall evidence；
- grouped split；
- simple/no-message/shuffled controls；
- calibration、development、sealed 和 formal promotion gates；
- OOD/disagreement fail-closed；
- canary 和 `no_cut` rollback。

---

## 2. 生效边界

### 2.1 Round 5/D5 当前运行不变

正在运行的命令继续使用原冻结代码和配置：

```text
scripts/collect_p0v5_temporal_gat_root_contexts_v1.py eligibility
configs/experiments/p0v5_temporal_gat_production_v1_round5.json
data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json
runs/p0v5_temporal_gat_production_v1_round5_20260824
```

在 eligibility parent 退出前禁止：

- 修改它或后续 child 会 import/execute 的既有 Python/Native source；
- 重建 Native binary；
- 修改 Round 5 config/source/corpus/research-contract freeze；
- 中断当前 child；
- 并发启动任何三臂 task；
- 生成任何 queue-arm outcome。

允许：

- 在 `plan/GAT/` 写本协议和审阅文档；
- 只读监控 process、memory、completed eligibility artifacts；
- 在活动 run 外设计 V2 schema，但不能让新 source 进入 D5 执行路径。

### 2.2 D5 eligibility 完成后的强制停点

eligibility parent 正常退出后，流程不得自动进入 train trials。必须先生成并审核：

1. `D5_COMPLETION.audit.json`；
2. `D5_CONTEXT_CAPACITY.audit.json`；
3. `D5_ARTIFACT_REUSE.audit.json`；
4. `D5_PARTITION_ACCESS.ledger.json`；
5. `D5_ZERO_ARM_OUTCOME.audit.json`；
6. `D5_DATA_EPOCH.freeze.json`；
7. `NEXT_ACTION.json`。

上述 artifact 必须证明：

- 274 个 raw snapshots 的 eligibility 任务均已形成 final artifact，或明确列出 fail-closed final status；
- 不存在 `.partial` writer；
- corpus/snapshot/eligibility/config/source hashes 完整；
- 没有 Q0/CONTINUE/REVERT arm outcome；
- train/calibration/development/sealed 的 access state 可判定；
- eligible instance/context capacity 可供 Policy Round 设计；
- D5 本身不拥有 deployment/production authority。

在这些 audit PASS 前，V2 Policy Round 不得创建 schedule。

---

## 3. 四层实验对象

### 3.1 Platform Epoch

Platform Epoch 绑定会影响 exact/runtime 语义的实现：

- exact engine source；
- Native binary 和 test binary；
- `State` ABI；
- Q0/QD1 comparator；
- graph/feature/telemetry schema；
- bidirectional、dominance、cut/branch/RC/certificate path；
- migration implementation；
- pybind/runtime binding；
- source inventory 和 build info。

建议 ID：

```text
temporal_gat_platform_epoch_e1_<date>
```

只要这些 hashes 不变，platform-level correctness evidence可以复用；一旦 correctness-affecting source/binary/schema 变化，必须新建 Platform Epoch。

### 3.2 Data Epoch

Data Epoch 绑定 outcome-blind 数据材料：

- corpus instances 和 partition assignment；
- generation seed/hash/protected-history audit；
- root collection snapshots；
- boundary eligibility results；
- context eligibility/capacity；
- partition access ledger。

Round 5 被重新定位为：

```text
Data Epoch D5
```

D5 可以被多个后续 Policy Round 引用，但自身不训练 model、不产生 production candidate。

### 3.3 Policy Round

Policy Round 绑定会直接决定 queue action 或模型：

- action universe；
- boundary；
- K candidates/staged-K protocol；
- context selection；
- model architecture；
- optimizer/loss/ensemble；
- controls；
- OOD policy；
- threshold grid；
- K/model/calibration gates。

建议 ID：

```text
temporal_gat_policy_round_p1_d5_<date>
```

一个 Policy Round terminal 不自动使 D5 terminal。

### 3.4 Evaluation Attempt

Evaluation Attempt 绑定：

- calibration outcomes/threshold selection；
- development E2E schedule/outcomes；
- sealed-final schedule/outcomes；
- formal acceptance；
- candidate/canary/promotion evidence。

同一 Policy Round 可以有多个合法 Evaluation Attempt，但只能复用尚未被 outcome 揭示的 partition；任何已揭示 partition 不得继续作为该 lineage 的独立 promotion evidence。

---

## 4. Artifact authority 与 evidence bank

### 4.1 Append-only evidence bank

V2 必须建立 append-only registry：

```text
runs/p0v5_temporal_gat_evidence_bank_v2/registry.json
```

每条 artifact record 至少包含：

```json
{
  "artifact_id": "...",
  "artifact_kind": "...",
  "path": "...",
  "sha256": "...",
  "platform_epoch_id": "...",
  "data_epoch_id": "...",
  "policy_round_id": null,
  "partition": "train",
  "evidence_role": "TRAINING_ONLY",
  "outcome_created": false,
  "promotion_eligible": false,
  "invalidated_by": [],
  "source_bindings": {}
}
```

不得覆盖或删除旧 terminal、outcome 或 audit。旧 evidence 可以从 promotion role 降级为 training/mechanism audit，但物理 artifact 保留。

### 4.2 Evidence roles

合法 role：

- `OUTCOME_BLIND_INPUT`；
- `PLATFORM_CORRECTNESS`；
- `TRAINING_ONLY`；
- `CALIBRATION_ONLY`；
- `DEVELOPMENT_ONLY`；
- `SEALED_PROMOTION_CANDIDATE`；
- `FORMAL_ACCEPTANCE`；
- `CANARY_ONLY`；
- `HISTORICAL_DIAGNOSTIC`；
- `INVALIDATED`。

一个 artifact 可以从更严格 role 单向降级为 training/historical，不能从已揭示 training/development 重新升级为 sealed/formal。

### 4.3 Authority order

发生冲突时：

1. immutable machine terminal/reuse/access decision；
2. bound raw fresh-process outcomes；
3. independent audit；
4. evidence-bank registry；
5. generated status Markdown；
6. handoff/design prose；
7. 对话记忆。

---

## 5. Partition access ledger

### 5.1 Access states

每个 instance/partition 必须有唯一、单调的 access state：

```text
FROZEN_UNOPENED
OUTCOME_BLIND_PRECHECKED
OUTCOME_SCHEDULED
OUTCOME_CREATED_UNINSPECTED
OUTCOME_REVEALED
BURNED_FOR_PROMOTION
REASSIGNED_TRAINING_ONLY
INVALIDATED
```

状态只能沿更少独立性的方向变化，不能回退。

### 5.2 什么算 outcome revealed

满足任一条件即视为 revealed：

- queue arm/full-BPC task 已产生 final outcome file；
- aggregate/audit 读取了 outcome；
- operator/model/script 查看或用于决策；
- outcome file 存在但无法证明未访问；
- access ledger 不完整或存在歧义。

如果只有 instance content、hash、root snapshot 或 literal-Q0 eligibility，而没有 arm/E2E outcome，不算 policy outcome revealed。

### 5.3 未揭示 partition 的复用

只要 ledger 证明：

- 没有 outcome schedule/task/result；
- 没有 aggregate/audit/policy decision 读取；
- source/corpus hash 一致；
- 该 partition 没有被前一轮用于调参；

则 calibration、development 或 sealed partition 可以跨 Policy Round 保持封存，无需因 train/capacity/K failure 重生。

### 5.4 已揭示 partition 的降级

- calibration failure：旧 calibration 可转入 `TRAINING_ONLY`；
- development failure：旧 development 可转入 `TRAINING_ONLY` 或 `HISTORICAL_DIAGNOSTIC`；
- sealed failure：旧 sealed 永久 `BURNED_FOR_PROMOTION`，可在新 lineage 中作为 train/historical；
- formal failure：official outcomes 不得用于反复调参；默认关闭该 promotion lineage。

---

## 6. Failure-aware invalidation matrix

| Failure class | Platform | D5 corpus/snapshots/eligibility | Train outcomes | Calibration | Development | Sealed | Required action |
|---|---|---|---|---|---|---|---|
| `PLATFORM_CORRECTNESS_REDLINE` | invalidate affected epoch | audit impact | invalidate bound outcomes | invalidate bound outcomes | invalidate | invalidate | 新 Platform Epoch |
| `ABI_OR_MIGRATION_MISMATCH` | invalidate | raw corpus可留，eligibility视影响重跑 | invalidate | invalidate | invalidate | invalidate | 修复并全量 affected differential |
| `SOURCE_OR_BINARY_DRIFT` | new epoch | 按 dependency graph 判断 | 按绑定判断 | 按绑定判断 | 按绑定判断 | 按绑定判断 | 禁止无审计复用 |
| `CORPUS_HASH_OR_LEAKAGE` | reuse | invalidate affected partition | affected only | affected only | affected only | affected only | 只重建受污染数据 |
| `ELIGIBILITY_CAPACITY_PRE_OUTCOME` | reuse | reuse all valid D5 artifacts | none | unopened reuse | unopened reuse | unopened reuse | 启用预冻结 reserve/补 train pool |
| `NO_PASSING_K` | reuse | reuse | retain mechanism/training evidence | unopened reuse | unopened reuse | unopened reuse | 新 Policy Round/action hypothesis |
| `GAT_REPRESENTATION_GATE_FAIL` | reuse | reuse | reuse | 已产生则降级 train；未产生则保持封存 | unopened reuse | unopened reuse | 新 representation round |
| `CALIBRATION_NO_SAFE_THRESHOLD` | reuse | reuse | reuse | revealed，降级 train | unopened reuse | unopened reuse | 新 calibration attempt/round |
| `DEVELOPMENT_GATE_FAIL` | reuse | reuse | reuse | 新模型时刷新 | revealed，降级 train | unopened reuse | 新 development + 必要 calibration |
| `SEALED_FINAL_FAIL` | reuse | reuse | reuse | refresh | refresh | burned，必须 fresh | 新完整 evaluation attempt |
| `FORMAL_ACCEPTANCE_FAIL` | reuse only for research | reuse only for research | retain diagnostic | no retuning against official | no retuning against official | burned/diagnostic | 默认关闭 lineage或新增外部 holdout |
| `CANARY_OPERATIONAL_FAIL` | dependency-based | reuse | reuse | reuse | reuse | reuse | 修复 operational issue 后新 canary；不得改模型阈值 |

任一 reuse 必须由 verifier 输出 `PASS`，表格本身不构成授权。

---

## 7. D5 Data Epoch 封存合同

### 7.1 D5 可复用输入

预期纳入 D5：

- Round 5 corpus manifest；
- 160 个 instance file hashes；
- protected-history cache/audit；
- 104 个 collection markers；
- 274 个 raw snapshots；
- 完整 boundary eligibility finals；
- source/config/native/reference bindings；
- context capacity audit；
- zero-arm-outcome audit。

### 7.2 D5 不包含的内容

D5 不包含：

- K selection；
- Q0/CONTINUE/REVERT outcomes；
- model dataset/checkpoint；
- calibration/threshold；
- development/sealed/formal outcome；
- candidate/bundle authority；
- production switch。

### 7.3 D5 freeze 不等于 Round 5 success

D5 freeze 只证明数据材料完整、可追溯、可由后续 Policy Round 引用。即使 eligible train capacity `<32`，D5 仍可作为 evidence bank 中的数据 epoch；后续只需通过预冻结 reserve/补充 train pool形成 D5 extension，而不是重建全部 160 instances。

---

## 8. V2 Policy Round 初始化合同

每个 Policy Round 初始化时必须读取：

- Platform Epoch freeze；
- D5 Data Epoch freeze；
- evidence-bank registry；
- partition access ledger；
- parent terminal/reuse decision（若有）；
- frozen policy config。

初始化器必须生成：

```text
policy_round.freeze.json
reuse_decision.freeze.json
partition_selection.freeze.json
next_action.json
state.json
```

并证明：

- 所有被复用 artifact hash 一致；
- dependency/engine/schema compatible；
- context selection 不读取 queue outcomes；
- 所有 evaluation partition 的 access state 合法；
- 首个 arm outcome 尚不存在；
- config/K/staged protocol/architecture/gates 已冻结。

---

## 9. Staged execution 原则

具体数量必须在 D5 capacity audit 后、首个 arm outcome 前由 Policy Round config 冻结。本协议只冻结以下原则。

### 9.1 Capacity reserve

未来 Data Epoch/extension 应支持：

- `train_primary`；
- `train_reserve`；
- `calibration_primary`；
- `calibration_reserve`；
- 预冻结的 hash order 和启用条件；
- 只在 primary eligibility 不足时 lazy 执行 reserve；
- reserve selection 只能读取 outcome-blind eligibility。

### 9.2 K staged screen

Policy Round 可以使用预冻结的 staged-K：

1. sentinel safety/mechanism screen；
2. correctness/resource redline 立即淘汰；
3. 预冻结 futility/diversity/revert-tax 条件；
4. 只有存活 K 进入完整三重复和最终 K gate；
5. 最终 gate 不得低于原计划。

不得在看到 sentinel outcome 后临时改变 stage size、阈值或幸存规则。

### 9.3 Train-only representation gate

推荐顺序改为：

```text
train three-arm
-> K selection
-> train-only grouped OOF GAT/controls/topology gate
-> PASS 后才执行 calibration three-arm
```

如果 representation gate失败，未运行 calibration/development/sealed 保持封存。

### 9.4 Staged development

可以预冻结 development sentinel：

- 先执行小规模 Q0+MODEL correctness/futility screen；
- 无 redline且未触发预定义 futility 才执行完整四臂三重复；
- 最终 development gate 完全不变；
- sentinel 属于 development，一旦产生 outcome 就按 revealed 记账。

---

## 10. Audit 复用规则

### 10.1 可按 Platform Epoch 复用

当 source/native/schema/hash 完全一致时，可复用：

- ABI/build-info audit；
- migration unit/fault-injection suite；
- disabled-Q0 exact differential；
- deterministic graph/telemetry hash audit；
- implementation-only graph overhead基线。

### 10.2 必须按 bundle/policy 重跑

- Python/C++ portable output/action parity；
- OOD/disagreement action audit；
- inference p99；
- model/controller E2E；
- bundle/source/manifest binding；
- development/sealed/formal/canary。

### 10.3 Dependency verifier

任何“hash看起来一样”的人工判断都不够。reuse verifier 必须根据显式 dependency graph 输出：

```text
REUSE_PASS
REUSE_FAIL_SOURCE_DRIFT
REUSE_FAIL_BINARY_DRIFT
REUSE_FAIL_SCHEMA_DRIFT
REUSE_FAIL_PARTITION_REVEALED
REUSE_FAIL_OUTCOME_PRESENT
REUSE_FAIL_DEPENDENCY_UNKNOWN
```

未知依赖一律 fail closed。

---

## 11. Terminal decision V2 schema

每个 terminal 必须额外写：

```json
{
  "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_terminal.v2",
  "status": "TERMINATED_NEGATIVE",
  "failure_class": "...",
  "failed_layer": "POLICY_ROUND",
  "invalidated_layers": ["POLICY_ROUND"],
  "revealed_partitions": ["train"],
  "reusable_artifact_ids": ["..."],
  "invalidated_artifact_ids": [],
  "required_fresh_partitions": [],
  "promotion_evidence_retained": [],
  "next_allowed_actions": ["CREATE_NEW_POLICY_ROUND_FROM_D5"],
  "production_switch_authorized": false,
  "deployment_authorized": false
}
```

terminal decision 是 immutable closeout，不是删除命令。

---

## 12. Persistent state 与记忆独立性

V2 必须使后续执行不依赖对话历史。每个 active object 至少提供：

- `state.json`：当前 state machine stage；
- `next_action.json`：唯一合法下一步、前置条件和命令模板；
- `artifact_registry.json`：输入/输出 hash；
- `partition_access_ledger.json`：数据独立性；
- `reuse_decision.json`：复用依据；
- `status.md`：由机器文件生成，只供人读。

`next_action.json` 至少包含：

```json
{
  "stage": "D5_CAPACITY_AUDIT",
  "ready": false,
  "blocking_conditions": ["ELIGIBILITY_PARENT_RUNNING"],
  "required_inputs": [],
  "expected_outputs": [],
  "command": [],
  "must_not_run": ["ANY_ARM_TASK"]
}
```

执行器必须幂等：

- final artifact存在且hash匹配则跳过；
- `.partial` 只可由原 writer恢复/清理；
- conflicting artifact立即终止；
- terminal object拒绝继续同一 Policy Round；
- Data Epoch terminal与Policy Round terminal分开。

---

## 13. 当前批准的执行序列

```text
1. 等待 Round5 eligibility 自然结束
2. 验证 parent/child 全部退出
3. 验证 274 final eligibility / 0 partial
4. 验证 0 arm outcome
5. 生成 D5 completion/capacity/reuse/access audits
6. 冻结 D5 Data Epoch
7. 修改/新增 V2 source、tests、schemas
8. 创建新 Platform Epoch（如 source inventory变化）
9. 创建引用 D5 的 Policy Round
10. 冻结 staged-K/representation/calibration protocol
11. 再次验证 0 arm outcome
12. 才允许启动首个三臂 task
```

任何自动 orchestrator 都必须在步骤 5 设置 hard stop，不能从 eligibility 自动落入三臂。

---

## 14. 本协议不直接决定的事项

以下参数要等 D5 capacity audit 后，由新 Policy Round 在 outcome 前冻结：

- train primary/reserve 的实际 instance 数；
- sentinel instance 数；
- sentinel repeat 数；
- K survival/futility阈值；
- 是否保留全部三个 K 到 full gate；
- train-only representation minimum rows；
- development sentinel 数；
- 新 Policy Round ID/seed；
- Data Epoch extension 是否必要。

这些参数不能依据任何三臂 outcome临时决定。

---

## 15. Promotion 边界保持不变

V2 只改变研究执行和 artifact reuse，不改变最终 production promotion：

- GAT 仍只改变 queue ordering；
- P0V5 prepass、dominance、RC、cut、branch、stopping、certificate authority 不变；
- development 与 sealed 必须独立通过；
- formal acceptance contract 保持权威；
- source/binary/bundle audit必须通过；
- candidate先进入独立 registry 的 `AWAITING_CANARY`；
- canary PASS 后才可 activate；
- `no_cut` 始终保留为 rollback。

---

## 16. 审阅结论

本修订把“严格实验”与“重复劳动”分开：

- correctness错误仍会使受影响证据全部失效；
- outcome泄漏仍会烧毁相应 evaluation partition；
- 已经揭盲的 sealed/formal不能循环使用；
- 但 capacity、K、representation 等局部 negative 不再触发全平台、全语料和未揭示 heldout 的无差别重建。

Round 5 的计算不会被丢弃。它将作为 D5 数据 epoch，后续 Policy Round 通过严格 hash/access/reuse ledger 引用。这样完整计划由机器状态和证据图驱动，不再依赖 Codex 或人工记住数周执行历史。

