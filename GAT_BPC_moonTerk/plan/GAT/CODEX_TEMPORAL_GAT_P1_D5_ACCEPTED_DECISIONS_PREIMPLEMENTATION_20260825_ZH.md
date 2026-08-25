# Temporal-GAT P1/D5 已接受决策与预实现合同

> 状态：`FORMAL_DECISIONS_INTEGRATED_PROPOSALS_NOT_FROZEN`
>
> 日期：2026-08-25（Asia/Shanghai）
>
> 适用范围：D5 完成后的新 Temporal-GAT Policy Round 设计
>
> 决策来源：`Temporal_GAT_10_Questions_Revised_Response_20260825.md`
>
> 追加正式授权：`P0V4_V5_Temporal_GAT_Additional_5_Questions_Formal_Response_20260825.md`
>
> 机器可读草案：`CODEX_TEMPORAL_GAT_P1_D5_ACCEPTED_DECISIONS_PREIMPLEMENTATION_20260825.draft.json`
>
> 本文不是 `policy_round.freeze.json`，不授权 queue-arm outcome、训练、deployment 或 production switch。

---

## 1. 本次修改的结论

Codex 接受并纳入后续设计的决定是：

1. GAT 保留为正式 scientific hypothesis；Linear、MLP、no-message、shuffled-topology 和 deterministic policy 是 controls，不能被重命名为 GAT success。
2. GAT 仍只拥有合法 proof queue comparator 的选择权限，没有 dominance、reduced cost、cut、branch、bound、stopping 或 certificate authority。
3. scale30 与 scale50 分治：scale30 进入独立 deterministic QD1 pilot；scale50 承担 post-trial `CONTINUE_QD1/REVERT_Q0` Temporal-GAT selector 验证。
4. 第一阶段不增加 learned `STAY_Q0`；先证明强制支付 trial tax 后仍存在相对 literal Q0 的净价值。
5. D5 优先复用；容量、生命周期覆盖或 Safety-B 不足时建立受控 D5 extension，不无差别重建 160-instance corpus。
6. threshold selection 与独立 safety validation 分离；正式 harm 声明按 instance-level policy outcome 计算。
7. 研究材料覆盖 early/middle/late root-CG 生命周期，production authority 只对已独立验证的 strata 分阶段开放。
8. production utility gate 与 GAT topology scientific gate 分开报告；MLP 结果不能自动进入 GAT candidate。
9. Codex 当前不修改、生成或规划论文正文，只保留接口、artifact、hash 和 `MANUSCRIPT_SYNC_REQUIRED` 等技术事实。

这些修改只进入新的预实现合同；Round 5 frozen config、source、corpus、split、gate 和现有 final artifacts 均不改写。

---

## 2. 当前 D5 边界

本文创建时的只读现场是：

| 项目 | 值 |
|---|---:|
| raw snapshots | `274` |
| eligibility finals | `31` |
| remaining | `243` |
| `.partial` | `0` |
| active eligibility parent/child | `0` |
| Q0/CONTINUE/REVERT outcomes | `0` |
| model/bundle/schedule | 不存在 |

因此：

- D5 目前只有 outcome-blind corpus、snapshots 和部分 eligibility；
- D5 没有“已有 action-support outcome”；
- 当前 `31/274` 不允许推断 K、trial value、GAT observability、topology value 或 E2E speedup；
- eligibility 完成前不得修改它会 import/execute 的 frozen Python/Native source，也不得重建 frozen binary。

---

## 3. 新 Policy Round 的算法合同

### 3.1 不变的 exact-safe authority

允许变化的只有：

- 已授权 scale/lifecycle 的完整 current frontier comparator；
- Q0→QD1 migration；
- 冻结的真实 QD1 short trial；
- trial 后 `CONTINUE_QD1` 或 atomic `REVERT_Q0`。

任何 learned component 均不得：

- 删除、过滤或剪枝合法 label/route；
- 改变 dominance、reduced cost、completion bound 或 route reconstruction；
- 改变 cut、Ryan–Foster branch、dual 或 exact stopping；
- 生成 closure、bound 或 certificate；
- 把 `TIMEOUT`、`MEMORY_LIMIT`、label drop 或 incomplete frontier 解释为 no-negative proof。

### 3.2 scale30 track

候选流程：

```text
literal Q0 -> frozen boundary -> deterministic QD1
```

它是待验证候选，不是已授权 policy。必须使用 fresh paired E2E evidence 检查：

- GM 与置信区间；
- harmful tail；
- action-induced timeout/memory censor；
- peak RSS 与 migration tax；
- formal acceptance compatibility。

任一 hard gate 失败时，scale30 保持 literal Q0；该结论不自动终止 scale50 GAT scientific hypothesis。

### 3.3 scale50 track

第一阶段动作保持：

```text
literal Q0 control
trial + CONTINUE_QD1
trial + REVERT_Q0
```

GAT 只在共同经历真实 trial 后选择 `CONTINUE_QD1/REVERT_Q0`。只有同时证明以下条件，才允许进入 GAT training：

1. authorized scope 具有足够 addressable wall；
2. taxed oracle 相对 literal Q0 有预冻结标准下的净收益；
3. trial+revert tax 可接受；
4. reverse migration workspace 可安全预留；
5. action-induced resource censor 为 0；
6. 独立 instance action support 足够。

`STAY_Q0/ENTER_TRIAL` 只能在后续独立 Policy Round 中考虑，不能在查看本轮两动作 outcomes 后临时加入。

---

## 4. 数据、partition 与复用合同

### 4.1 D5 的合法用途

D5 可提供：

- frozen instance corpus 与原 split lineage；
- outcome-blind root snapshots；
- 完成后的 eligibility/capacity/resource evidence；
- 新 Policy Round 的候选 train/action-support 输入。

D5 当前不提供：

- 已测 action support；
- selected K；
- model target/checkpoint；
- calibration threshold；
- Safety-B、development、sealed 或 formal outcome。

### 4.2 新 Policy Round partition

新 round 必须在首个 queue outcome 前冻结：

```text
K/action-support
model-training
Calibration-A
Safety-B
development
sealed-final
```

同一 instance 的所有 contexts 必须留在同一 partition。K selection、model selection、Calibration-A、Safety-B、development 和 sealed 不得复用同一 revealed policy outcome 充当独立证据。

### 4.3 D5 extension

只有 capacity/access audit 证明现有 D5 不足时才建立 extension。extension 必须：

- 使用 outcome-blind seed/hash order；
- 保持 generator、map source、objective 和 instance semantics compatible；
- 对 official/historical/D5 content hash 去重；
- 在任何 queue outcome 前冻结用途和 partition；
- 明确绑定 parent D5 freeze 与 lineage；
- 不按已知 benefit/adverse/model score 选择实例。

若 generator、map source、objective、candidate path universe 或 instance semantics 实质改变，则不能称为简单 D5 extension，必须新建 Data Epoch。

---

## 5. Safety-B 与统计合同

正式安全声明的统计单位是 independent instance。一个 instance 内，只要任一获得目标 policy authority 的 context 出现预定义 adverse 或 action-induced censor，该 instance 即记为 harmful。

零 observed harmful 时，单侧置信上界使用预冻结的 exact binomial 合同。若仍要求 95% upper `<=0.10`，至少需要 29 个实际 activated、相互独立的 Safety-B instances。

Safety-B raw capacity 不能现在硬编码为 `45–55`。其规模必须由以下量在 outcome 前计算并冻结：

```text
N_raw >= ceil(29 / conservative_activation_lower_bound)
```

并额外计入：

- eligibility loss；
- resource censor；
- lifecycle-stratum coverage；
- 预冻结 reserve；
- 按 scale/policy 分开声明还是联合声明。

`Calibration-A` 可以选择 calibration、threshold、OOD 和 action rule；`Safety-B` 只能验证完全冻结的 policy，不得反向调参。

scale30 与 scale50 必须分别给出 harm contract，不得 pooling：

- scale30 比较 `FIXED_QD1_SCALE30` 与 literal Q0；deterministic policy 对授权 population 全激活，performance harm 暂定义为 instance-level collapsed E2E ratio `>=1.05`；
- scale50 的正式主口径比较完整 `TEMPORAL_GAT_POLICY` 与 literal Q0，并另报 activated-subset risk、coverage、false-continue/false-revert 和 conditional censor；
- 两个尺度的 correctness、route true-RC、certificate、label-drop、migration conservation 和 action-induced resource redline 均要求为 0；
- evidence 不足必须输出 `INSUFFICIENT_EVIDENCE`，不得用 context rows 补齐 independent instance 数。

具体字段进入两份独立 proposal；用户确认前不写入任何 immutable round freeze。

---

## 6. Lifecycle stratification 的实际约束

目标 selection 是 outcome-blind early/middle/late eligible chronology，但不能假设 D5 已有完整覆盖。

当前 raw snapshot census 显示：

| Scale | train+calibration instances with snapshot | raw snapshots | instances with >=3 snapshots |
|---:|---:|---:|---:|
| 30 | `43` | `44` | `0` |
| 50 | `51` | `230` | `36` |

因此：

- scale30 的现有 D5 无法在多数 instance 内形成 early/middle/late 三段；这可能是实际 fallback 生命周期只有一个可观测 request，也可能需要 extension audit，不能靠复制 context 补齐；
- scale50 可以对有足够 eligible snapshots 的 instance 采用 chronology quantile；不足三个时全部保留并记录 coverage class；
- `middle` 应定义为 eligible chronology 的预冻结中位 index，`late` 是最后一个已完整、outcome-blind 捕获的 eligible request；
- 如果 collection time/memory cap 使“最后一个已捕获”不等于“实例生命周期最后一个”，必须标记 `RIGHT_CENSORED_LIFECYCLE`，不能冒充 true late；
- production authority 只能覆盖 Safety-B/development/sealed 中得到独立支持的 strata，其他 strata fail closed 到 literal Q0。

---

## 7. GAT scientific gate

GAT 必须真实使用 topology/message passing，并至少与以下 controls 同数据、同 split、同预算比较：

- Linear；
- MLP/counters-only；
- no-message；
- shuffled topology，多 frozen seeds；
- always-continue；
- always-revert。

scientific gate 应以 instance-level paired policy evidence 为主：

1. relative taxed-oracle regret；
2. paired policy utility/E2E；
3. harmful/action-induced censor；
4. topology shuffle/no-message 的稳定退化；
5. activation coverage；
6. BA/AUC 仅作诊断。

“稳定退化”的定量阈值、置信区间、shuffle seed 数和多重比较规则尚未冻结，必须在任何 model/control outcome 前进入新 Policy Round contract。

正式回复授权的默认 proposal 起点为：

- primary solver effect：GAT 相对最佳 simple/no-message control 的 paired policy wall ratio 点估计 `<=0.98`，且 paired 95% CI 的不利边界严格 `<1.00`；
- cluster unit：independent instance；同-instance contexts 不独立 bootstrap；
- bootstrap：默认 `10,000` 次，seed 与 censor 处理在 outcome 前冻结；
- topology shuffle：至少 10 个独立、预冻结 seeds，与 3 个 model ensemble seeds 分开管理；
- primary comparisons：GAT vs best Linear/MLP、GAT vs no-message、GAT vs shuffled-topology distribution；
- multiplicity：Holm-Bonferroni family-wise error control，`alpha=0.05`；
- BA/AUROC/Brier/ECE 只作 secondary/diagnostic，不能单独形成 topology PASS。

这些值目前仍是 `proposal`；只有用户对正式 topology contract 再次确认后才可冻结。

MLP 优于 GAT时：

- 当前 GAT topology hypothesis 记为未通过；
- MLP 只保留为明确命名的 control/工程证据；
- 不自动注册为 GAT candidate 或 production candidate；
- 是否另开 MLP production lineage 只能由用户明确授权。

---

## 8. Eligibility 后的五类 pre-outcome audit

### 8.1 Independent capacity

按 scale、partition、instance、eligible context 和 lifecycle coverage 报告，不用同-instance rows 补独立样本数。

### 8.2 Addressable wall

在 queue-arm outcome 为 0 时，只允许输出：

- literal-Q0 baseline 中 authorized scope wall share；
- scope completeness/censor；
- 在预声明 local-ratio scenarios 下的 Amdahl E2E ceiling。

真实 `taxed_oracle_ratio` 必须来自后续冻结的 force-on trial outcomes，不能在 outcome-independent audit 中声称已测得。

### 8.3 Migration resource

第一版先区分：

- 当前 telemetry 已能证明的 migration wall/memory；
- 缺失字段；
- reverse workspace reservation 的保守上界；
- 需要新 Platform Epoch 才能验证的 allocator/peak-extra-byte 项。

缺失证据必须输出 `NOT_EVALUABLE`/blocking reason，不能填默认 PASS。

### 8.4 Calibration feasibility

计算 Calibration-A、Safety-B 和 reserve 的独立 instance 需求，报告 activation assumption sensitivity，不预先把 `45–55` 当作正式容量。

### 8.5 Topology identifiability

这是 outcome-blind representation/telemetry sufficiency audit，不是 GAT value PASS。它只能检查：

- 是否存在 full-mass transition 的可构造字段；
- birth/processed/dominated/terminal flow 是否可追溯；
- parent-child 与 cross-cell movement 是否观测完整；
- 缺失是否需要新 schema/Platform Epoch。

是否有 topology predictive value 只能由后续 frozen controls 和 fresh outcomes 决定。

---

## 9. 允许的执行顺序

```text
Round 5 eligibility 31/274
    -> 幂等完成 274/274
    -> D5 completion/capacity/reuse/access/zero-outcome hard stop
    -> freeze D5 Data Epoch
    -> 生成五类 pre-outcome audit
    -> 决定是否需要 D5 extension
    -> 设计并测试新的 Platform Epoch（若 source/schema/memory telemetry 改变）
    -> 冻结新 Policy Round、partition、controls、统计阈值和 staged schedule
    -> 再确认 zero arm outcome
    -> 小规模 staged force-on/action-support
    -> simple observability controls
    -> 仅在前置 gate PASS 后训练 GAT
    -> Calibration-A
    -> Safety-B
    -> development
    -> sealed
    -> formal/canary
```

在新 Policy Round freeze 前，`5% E2E` 仍是首选 production gate。若 outcome-blind scope audit 表明该目标理论不可实现，只能由用户在首个新 outcome 前选择扩大合法 scope或重新冻结 gate；Codex 不自动降低。

当前 post-trial Temporal-GAT topology hypothesis 最多允许 3 个正式 outcome-bearing rounds：

1. `T1`：当前 temporal multi-resolution baseline；
2. `T2`：仅允许一个由 T1 root-cause audit 支持的 representation repair；
3. `T3`：唯一剩余 hypothesis 的最终确认。

连续 2 轮未超过 controls 时强制暂停并生成 `topology_two_round_negative_root_cause.audit.md`；没有明确、可证伪的新 topology hypothesis 时不得启动 T3。连续 3 轮失败时，当前 graph/action/label topology hypothesis 必须 `TERMINATED_NEGATIVE`，不能在同一数据语义上继续调宽度、层数、dropout、seed 或 threshold。

每轮只允许 1 个主 GAT hypothesis、3 个预冻结 model seeds、固定 5-fold instance-grouped CV、至少 10 个 shuffle seeds，以及最多 2 个有明确机制差异且纳入 multiplicity correction 的 architecture candidates。实际 job/CPU/GPU cap 必须在对应 round outcome 前冻结。

---

## 10. 当前禁止修改

在 D5 eligibility 完成并保存 source/config/corpus integrity evidence 前，不修改：

- Round 5 config、source freeze、research contract 或 corpus freeze；
- eligibility collector/replay child 及其 import/Native execution path；
- frozen Native binary；
- 现有 31 个 eligibility finals；
- current production registry；
- 任何 manuscript/论文文件。

本文只落地用户已确认的设计决策，不构成上述修改授权。

---

## 11. 五个追加问题的正式处置

1. `RESOLVED`：scale30 deterministic policy 与 scale50 GAT 分别给出 harm guarantee。
2. `AUTHORIZED_TO_PROPOSE`：Codex 起草 topology effect/CI/shuffle/multiplicity 默认合同；用户确认前不得冻结。
3. `RESOLVED`：当前 topology hypothesis 最多 3 个 outcome-bearing rounds，2 轮失败强制复盘，3 轮失败终止。
4. `RESOLVED`：若 5% ceiling 不可达，优先在首个 outcome 前重新审定新 Policy Round gate；scope expansion 只允许独立新 round。
5. `AUTHORIZED_TO_EXECUTE`：完成 writer、binding、artifact 和 zero-outcome preflight 后，立即幂等恢复 eligibility 至 `274/274`；完成后 hard stop，不自动 context freeze 或三臂。

仍需用户后续确认的只有 topology gate proposal 的最终阈值/统计合同，以及由 audit 推导出的 Safety-B raw capacity、addressable-wall gate 和每轮实际计算 job/time cap。
