# P0V4+V5 Temporal-GAT V2 / Data Epoch D5 当前状态交接

> 交接日期：2026-08-25（Asia/Shanghai）  
> 工作目录：`/home/kai/work/GAT_BPC_moonTerk`  
> 当前实验：`p0v5_temporal_gat_production_v1_round5_20260824`  
> V2 数据定位：`p0v5_temporal_gat_data_epoch_d5_20260824`  
> 当前阶段：`CONTEXT_ELIGIBILITY`，需要从 31/274 幂等续跑  
> 当前进程状态：**没有活动 eligibility parent/child**  
> 三臂状态：**尚未开始，arm outcome 数为 0**  
> Production 状态：仍为 `no_cut + P0V4/P0V5 Exact + literal Q0`  
> GAT deployment / production switch：**均未授权**

---

## 0. 给新对话的第一条指令

新对话应先完整阅读本文和以下两个权威文件，然后立即从第 7 节恢复 eligibility；不要先改 source，不要运行三臂：

1. `plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825_ZH.md`
2. `plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825.freeze.json`
3. `plan/GAT/CODEX_REVIEW_P0V4_V5_TEMPORAL_GAT_PRODUCTION_CURRENT_STATE_20260825_ZH.md`

可直接给新对话发送：

```text
请仔细阅读
plan/GAT/CODEX_HANDOFF_P0V4_V5_TEMPORAL_GAT_V2_D5_CURRENT_STATE_20260825_ZH.md
以及其中列出的 V2 protocol/freeze。按交接从现有 31 个 final eligibility
artifact 幂等恢复 Round 5/Data Epoch D5 eligibility，持续监控到 274/274；
不得删除或重算已有 final，不得提前运行 context freeze、三臂 schedule 或任何
Q0/CONTINUE_QD1/REVERT_Q0 outcome。eligibility 完成后在 V2 hard stop 处生成
D5 capacity/reuse/access/zero-outcome audits，再等待审阅。
```

---

## 1. 一句话结论

V2 failure-aware reuse 协议已经在第一个 D5 三臂 outcome 产生前正式冻结，Round 5 的 corpus、274 个 raw snapshots 和有效 eligibility 将作为可复用 `Data Epoch D5`；但 eligibility 执行进程因承载它的工具会话消失而在 31/274 后停止。现有 31 个结果均已原子写成 final，未留下 `.partial`，所以现在最正确的动作是原命令幂等续跑，而不是重建 corpus、重新 collection、修改 Round 5 config 或启动三臂。

---

## 2. 权威边界与不变的 exact-safe 原则

Temporal-GAT 生产候选只允许影响：

- scale30/50；
- `root_cg`；
- P0V4 exact fallback；
- label proof queue 的 Q0/QD1 comparator 与迁移/返回动作。

以下语义不允许由 GAT 修改：

- P0V5 bidirectional witness prepass；
- route/label legal universe；
- dominance、reduced cost 和 exact bound；
- cut、Ryan–Foster branch 和 stopping condition；
- certificate authority；
- timeout、memory pressure、label drop、non-empty frontier 的 fail-closed 语义。

`TIMEOUT`、`MEMORY_LIMIT`、label drop 或 incomplete frontier 不能形成错误 certificate。GAT 只能指导合法队列工作，不能成为证明者。

V2 只修改失败恢复与证据复用协议，不降低 correctness、sealed independence、portable parity、development、formal acceptance、canary 或 production promotion gate。

---

## 3. V2 protocol revision 已完成的正式冻结

### 3.1 已冻结文件

| Artifact | SHA256 |
|---|---|
| `plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825_ZH.md` | `27eff6ba60516d9ade20d7aca87266115fbc435239df8c9fe00b0a47dad77c7a` |
| `plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825.freeze.json` | `c2a458f13b7657209712cdfb006f30f7afdb1f0bdb273300d78afdf20553dd8e` |

机器冻结件状态为：

```text
FROZEN_BEFORE_FIRST_D5_ARM_OUTCOME
```

它正式批准：

1. 让 Round 5 eligibility 完整结束；
2. eligibility 后先做 D5 capacity/reuse/access audit；
3. 不自动启动数千个三臂任务；
4. 后续 Policy Round 复用 D5 corpus、有效 snapshots 和 eligibility；
5. 多个 Policy Round 可以在严格 partition access ledger 下引用 D5；
6. terminal negative 默认只关闭失败的 policy/evaluation hypothesis，不再无差别推倒 platform 与 Data Epoch。

### 3.2 Round 5 原冻结件没有被静默修改

| Round 5 binding | SHA256 |
|---|---|
| `configs/experiments/p0v5_temporal_gat_production_v1_round5.json` | `7bb5091ded82ddb412a2ecfc186cb2558dfb4bf89e0b8ce48774f85231d1cef5` |
| `runs/p0v5_temporal_gat_production_v1_round5_20260824/config.freeze.json` | `2958c4dafe161c77953696509bf749ce97a9de00e6bf89c4496b0457b21fe609` |
| `runs/p0v5_temporal_gat_production_v1_round5_20260824/source.freeze.json` | `8ee71258c10a59ae9beebcd28e6069af6a030bf46be093bf1f7c15cec6ea645b` |
| `runs/p0v5_temporal_gat_production_v1_round5_20260824/research_contract.freeze.json` | `853d6462f75b668ba556e08a5a492833a764748ec8696d58cda3283b1a587e4f` |
| `data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json` | `24ed33a714c6f459594f8f753a6be7136cfc16c4e120d5d6f65c22a60848b6b1` |

V2 是独立 protocol revision，不是对 Round 5 frozen config 的原地篡改。

---

## 4. Round 5 / D5 已完成的内容

### 4.1 Corpus

已生成并冻结 scale30/50 各 80 个 real-map instance，共 160 个；每尺度 split 为：

| Partition | 每尺度数量 |
|---|---:|
| train | 40 |
| calibration | 12 |
| development_e2e | 12 |
| sealed_final | 16 |

Corpus freeze 报告 `official_or_historical_overlap_count=0`。后续 Policy Round 默认复用这些实例和 split，不重新生成 160 个实例。

### 4.2 Root context collection

train/calibration 的 104 个 collection marker 已完成，形成 274 个 raw root-CG P0V4 fallback snapshots：

| Scale | Partition | collection instances | 有 snapshot 的 instances | raw snapshots |
|---:|---|---:|---:|---:|
| 30 | train | 40 | 33 | 34 |
| 30 | calibration | 12 | 10 | 10 |
| 50 | train | 40 | 39 | 178 |
| 50 | calibration | 12 | 12 | 52 |
| **合计** |  | **104** | **94** | **274** |

这些 snapshots 是 outcome-blind 输入。development 与 sealed-final 未用于 context supervision。

### 4.3 Boundary eligibility 当前现场

2026-08-25 当前核验：

| 项目 | 当前值 |
|---|---:|
| raw snapshots | `274` |
| final eligibility artifacts | `31` |
| remaining | `243` |
| `.partial` artifacts | `0` |
| Q0/CONTINUE/REVERT arm outcomes | `0` |
| `contexts.freeze.json` | 不存在 |
| train schedule | 不存在 |
| model/bundle | 不存在 |
| active eligibility process | 不存在 |

31 个 final artifact 的 `engine_status` 分布：

| `engine_status` | 数量 |
|---|---:|
| `FOUND_NEGATIVE_PARTIAL` | 24 |
| `COMPLETE` | 5 |
| `MEMORY_LIMIT` | 2 |

`runs/p0v5_temporal_gat_production_v1_round5_20260824/state.json` 仍显示：

```json
{
  "current_stage": "CONTEXT_ELIGIBILITY",
  "status": "READY",
  "terminal": false,
  "candidate_trained": false,
  "deployment_authorized": false,
  "production_switch_authorized": false
}
```

注意：该 state 表示持久化实验阶段，不代表 Linux process 仍在运行。以 `ps` 为准，当前没有活动 parent/child。

---

## 5. eligibility 为什么停止，以及为什么可以安全续跑

原 eligibility parent 为：

```text
PID 97836
python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py eligibility ...
```

它运行在先前对话的统一工具执行会话中。工具会话/权限上下文切换后，该 parent 不再存在；它没有自然跑到 274/274。这个事件不是算法 gate failure，也没有产生 terminal decision。

停止前最后新增的 final artifact 是：

```text
runs/p0v5_temporal_gat_production_v1_round5_20260824/
boundary_eligibility/
684179b2afa499bd3575fd9199eb0d3d6efa29d521cd599b659b79f34b832b21.json
```

其关键事实：

```text
scale                  = 50
engine_status          = MEMORY_LIMIT
boundary               = 16384
boundary reached       = true
graph built            = true
model called           = false
labels dropped         = false
processed labels       = 16,950,000
frontier size          = 57,544
wall                   = 2455.790271864 s
native memory cap      = 10.867 GiB
```

`MEMORY_LIMIT` 是合法 fail-closed final status：它可保留为 eligibility/representation/resource evidence，但不能形成 exact certificate，也可能使后续对应三臂 block 无法满足 resource-censor gate。

续跑安全性来自现有 collector 的原子/幂等实现：

- final target 已存在时直接 `continue`：`collect_p0v5_temporal_gat_root_contexts_v1.py:329-333`；
- 发现 `.partial` 时停止并要求 audit：`:150-153`；
- child 成功形成合法 JSON 后才 `os.replace(staging, output)`：`:171-178`。

因此不应删除 31 个 finals；重复执行同一 eligibility 命令会跳过它们，从第一个缺失 target 继续。

---

## 6. 当前禁止事项

在 eligibility 真正完成前，禁止：

1. 修改 `src/`、Native source、既有 temporal-GAT scripts/tests 或 Round 5 执行路径；
2. 修改 Round 5 config/source/corpus/research-contract freeze；
3. rebuild 当前 frozen Native binary；
4. 删除或覆盖已有 31 个 final eligibility artifacts；
5. 忽略或自动删除 `.partial`；
6. 运行旧 `freeze` mode；
7. 创建 `contexts.freeze.json` 或 train trial schedule；
8. 启动任何 Q0 / CONTINUE_QD1 / REVERT_Q0 arm；
9. 训练模型、选 K、校准 threshold；
10. 把 `MEMORY_LIMIT`/incomplete 当作 certificate 或成功 closure；
11. 因单个 Policy Round negative 重建 D5 的 160 个实例和 274 次 eligibility。

允许的动作只有：读取/核验协议，幂等恢复原 eligibility，监控资源和 final artifact 数量，以及在 `plan/GAT/` 补充不进入执行 source inventory 的说明文档。

---

## 7. 新对话的立即执行步骤

### 7.1 先检查没有重复 writer

在项目根目录执行：

```bash
ps -eo pid,ppid,etime,cmd | rg '[c]ollect_p0v5_temporal_gat_root_contexts_v1.py eligibility|[r]eplay_p0v5_qg2_label_state_snapshot.py'
```

当前预期无输出。若发现真实 parent/child，不要再启动第二份；接管并监控现有进程。

### 7.2 原命令幂等恢复

```bash
python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py eligibility \
  --config configs/experiments/p0v5_temporal_gat_production_v1_round5.json \
  --corpus data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round5_20260824
```

应使用可持续轮询的执行 session，不要附加 `--task-limit`，也不要同时启动第二个 host instance。

### 7.3 监控

另一个只读检查可统计 final 数量：

```bash
find runs/p0v5_temporal_gat_production_v1_round5_20260824/boundary_eligibility \
  -maxdepth 1 -type f -name '*.json' | wc -l
```

检查 partial：

```bash
find runs/p0v5_temporal_gat_production_v1_round5_20260824 \
  -type f -name '*.partial' -print
```

每次轮询不应阻塞超过 60 秒。scale50 单 task 冻结上限为 3600 秒，长时间没有新 final 并不自动表示 hang。

若承载进程的工具 session 再次消失：

1. 用 `ps` 确认没有存活 parent/child；
2. 确认 `.partial=0`；
3. 重新执行同一命令；
4. 不删除 finals，不从 corpus/collection 重来。

若存在 `.partial`，停止，不自动删除；记录对应 state hash、进程状态、mtime/size 和 child exit 情况后再做人工 audit。

### 7.4 eligibility 完成判据

只有同时满足以下条件才算 D5 eligibility 完成：

1. collector parent exit code 为 0；
2. final eligibility JSON 为 `274/274`；
3. `.partial=0`；
4. 无活动 parent/child writer；
5. config/corpus/source bindings 无 drift；
6. `state.json.current_stage` 被原 collector 更新为 `CONTEXT_FREEZE`；
7. 没有 label-drop correctness redline 或未审计异常退出。

完成后立即进入 V2 hard stop，不要接着运行旧 `freeze` mode。

---

## 8. eligibility 后的 V2 hard stop

原 V1 流程会从 `freeze` 继续到 train schedule。现在不能这样做。eligibility 完成后必须先生成并审阅：

1. `D5_COMPLETION.audit.json`；
2. `D5_CONTEXT_CAPACITY.audit.json`；
3. `D5_ARTIFACT_REUSE.audit.json`；
4. `D5_PARTITION_ACCESS.ledger.json`；
5. `D5_ZERO_ARM_OUTCOME.audit.json`；
6. `D5_DATA_EPOCH.freeze.json`；
7. `NEXT_ACTION.json`。

这些 artifact 至少要证明：

- 274 个 snapshot 与 eligibility final 一一绑定；
- 每个 final 的 instance/state/config/engine/source hash 合法；
- 每个尺度/partition 的 reached、graph-built、status、resource censor 分布；
- 最早三个 boundary-reaching context 规则下的 instance/context capacity；
- scale30 train 的 distinct determined-instance reserve；
- corpus/snapshot/eligibility 是否可被后续 Policy Round 复用；
- train/calibration/development/sealed 当前 access state；
- D5 尚未产生任何 Q0/CONTINUE/REVERT outcome；
- D5 没有 model、deployment 或 production authority；
- `NEXT_ACTION` 是 `WAIT_FOR_POLICY_ROUND_REVIEW`，而不是自动启动 schedule。

在增加任何会匹配旧 `SOURCE_GLOBS` 的 V2 source 前，先对 D5 的 `source.freeze.json` 中每个冻结 path/hash 做一次只读完整性核验并持久化结果。D5 绑定原 source epoch；后加的 V2 orchestrator 属于新的 Platform/Protocol 层，不能倒写成“eligibility 使用过 V2 source”。

### 8.1 当前尚未实现的 V2 工程件

以下目前只是协议要求，尚无可宣称完成的执行实现：

- D5 finalizer；
- append-only evidence bank/registry；
- partition access ledger writer；
- dependency/reuse verifier；
- failure-class invalidation engine；
- Policy Round initializer；
- `NEXT_ACTION` hard-stop controller；
- 对应 tests。

新对话应在 eligibility 完成并保存原 source-integrity evidence 后实现这些工程件。实现必须使用新 V2 artifact/schema，不得悄悄修改 Round 5 frozen config，也不得让 finalizer 自动调用 arm runner。

---

## 9. D5 封存后如何创建新的 Policy Round

D5 finalization audit PASS 后，才可以初始化例如：

```text
temporal_gat_policy_round_p1_d5_<date>
```

Policy Round 必须显式绑定：

- D5 freeze SHA256；
- action universe：Q0 / CONTINUE_QD1 / REVERT_Q0；
- scale30/50 boundary；
- K candidate/staged-K protocol；
- context selection；
- model architecture、loss、ensemble 和 controls；
- OOD/disagreement policy；
- threshold grid；
- partition access ledger snapshot；
- source/binary/feature/schema hashes；
- failure-class invalidation policy。

Policy Round freeze 仍须发生在该 round 第一个 arm outcome 前。

### 9.1 简化后的分阶段执行

不要一次性生成并启动约 5724 个 train fresh-process task。建议按 V2 frozen staged protocol：

1. **Capacity/reserve gate**：只用 D5 outcome-blind audit 判断是否有足够 distinct train instances；
2. **Staged K screen**：在 train 内预冻结小批次筛除明显不可行 K；
3. **Train arms**：仅对仍存活 K 扩大三臂 blocked repeats；
4. **Train-only representation gate**：比较 GAT、linear、MLP、no-message、shuffled topology、always-continue/revert；
5. **Calibration**：只在冻结的 calibration partition 选 threshold；
6. **Portable/native validation**：parity、migration、ABI、500 differential；
7. **Development E2E**：预冻结分批执行，任一 hard gate failure 即停止该 attempt；
8. **Sealed final**：只对完全冻结、通过 development 的 candidate 揭盲；
9. **Formal acceptance/canary**：全部通过后才生成 immutable production candidate；
10. **Production switch**：最后才允许从 `no_cut` 切换，且保留一键回滚。

一个 Policy Round terminal negative 不自动销毁 D5。根据 failure class 只失效有依赖的 policy/evaluation evidence；未揭示 partition 可在 verifier PASS 后继续复用。若 sealed 已揭示，它只能转为后续 training/development evidence，不能继续充当独立 sealed promotion evidence。

---

## 10. 当前风险判断

### 10.1 scale30 capacity 余量很薄

scale30 train 只有 33 个有 snapshot 的 distinct instances，而原 gate 要求至少 32 个 determined instances，只有 1 个 instance 余量。eligibility 结束后的 capacity audit 是第一个必须面对的真实 gate；不能通过降低已冻结 gate 绕过。

### 10.2 scale50 resource censor 已出现

31 个 eligibility final 中已有 2 个 `MEMORY_LIMIT`。这不破坏 exact-safe 语义，但说明后续 K/arm 任务可能因 resource censor 无法晋升。V2 的价值之一是先用 capacity/resource audit 缩小任务面，避免在已知不可行区域盲跑数千任务。

### 10.3 当前没有 GAT 效果可以报告

Round 5/D5 尚未产生：

- K oracle outcome；
- benefit/adverse/gain label；
- GAT/control checkpoint；
- threshold/activation coverage；
- portable bundle；
- development/sealed speedup；
- production candidate。

因此不能说“GAT 已有效”或“已达到 5% speedup”。当前完成的是 exact-safe infrastructure、frozen corpus、root snapshots 和部分 outcome-blind eligibility。

### 10.4 工作树很大，不能做广域清理

仓库含大量既有实验/用户变更。不要使用 `git reset --hard`、`git checkout --`、批量删除或基于全局 `git status` 误清理。只修改本任务明确授权的文件，并在交接时列出准确路径。

---

## 11. 当前文件索引

### 首要入口

- 本交接：`plan/GAT/CODEX_HANDOFF_P0V4_V5_TEMPORAL_GAT_V2_D5_CURRENT_STATE_20260825_ZH.md`
- V2 协议：`plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825_ZH.md`
- V2 机器冻结：`plan/GAT/P0V4_V5_TEMPORAL_GAT_V2_FAILURE_AWARE_REUSE_PROTOCOL_REVISION_20260825.freeze.json`
- 完整算法/模型/现状审阅：`plan/GAT/CODEX_REVIEW_P0V4_V5_TEMPORAL_GAT_PRODUCTION_CURRENT_STATE_20260825_ZH.md`

### Round 5 / D5

- Config：`configs/experiments/p0v5_temporal_gat_production_v1_round5.json`
- Corpus：`data/p0v5_temporal_gat_production_v1_round5/corpus.freeze.json`
- Run root：`runs/p0v5_temporal_gat_production_v1_round5_20260824`
- State：`runs/p0v5_temporal_gat_production_v1_round5_20260824/state.json`
- Source freeze：`runs/p0v5_temporal_gat_production_v1_round5_20260824/source.freeze.json`
- Raw snapshots：`runs/p0v5_temporal_gat_production_v1_round5_20260824/root_snapshots/`
- Eligibility finals：`runs/p0v5_temporal_gat_production_v1_round5_20260824/boundary_eligibility/`

### 当前执行代码

- Collector：`scripts/collect_p0v5_temporal_gat_root_contexts_v1.py`
- Replay child：`scripts/replay_p0v5_qg2_label_state_snapshot.py`
- Common contracts：`scripts/p0v5_temporal_gat_common.py`

---

## 12. 新对话的有界目标

新对话第一阶段只应完成：

```text
31/274 eligibility
    -> 幂等续跑
    -> 274/274 + partial=0 + writer=0
    -> 原 D5 source/config/corpus/result 完整性核验
    -> 生成七个 D5 V2 audit/freeze/ledger/next-action artifacts
    -> HARD STOP，提交审阅
```

在用户审阅 D5 capacity/reuse audit 和新 Policy Round freeze 之前，不要启动任何三臂 outcome。

---

## 13. 最终交接判断

当前项目没有因 V2 而推倒重来。Round 5 已经生成的 160 个 corpus instances、274 个 raw snapshots 和 31 个 valid final eligibility artifacts都应保留。需要修复的只是执行连续性：恢复剩余 243 个 eligibility replay，并在完成后把 Round 5 正式封存为 Data Epoch D5。

V2 protocol 已经在 arm outcome 为 0 时冻结，满足“先修协议、后看 outcome”的要求；但 V2 registry/ledger/finalizer 仍待实现。新对话不得把“协议已写”误报成“V2 工程已全部实现”，也不得把 eligibility `MEMORY_LIMIT` 误报成 GAT 效果或 exact failure。

最安全、最节省计算的继续路线是：**原命令幂等续跑 eligibility → D5 capacity/reuse hard stop → 冻结一个引用 D5 的新 Policy Round → staged arms**。
