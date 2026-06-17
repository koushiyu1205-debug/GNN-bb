# GAT 加速 BPC_future 的目标模式优化计划

日期：2026-06-15

## 1. Executive Summary

目标模式定义为：

```text
Learning-guided discovery, exact-certified closure
```

含义是：GAT/CBF/kNN/OOD 只负责让 column generation 更聪明，帮助 pricing 优先搜索更可能改善 RMP trajectory 的列族、序列、transition、arc-option 和候选 batch；对已经 true-RC verified 的候选负列，只做 `HIGH_PRIORITY` / `DELAY_QUEUE` admission scheduling。最终 optimality proof 仍然必须由当前 branch/cut/dual 下的 exact pricing / final judge 对完整配置宇宙执行 no-negative closure。

这份计划不是 production 启用方案，也不是代码实现说明。它是后续持续优化目标的分阶段路线图。第一阶段只允许 offline / audit-only 结构设计和数据改造；任何 solver 在线效果都必须先 shadow，再 opt-in，再通过 5/10 no-regression、20-task ROI 和 certificate safety gate。

核心原则：

- GAT 可以改变搜索顺序，不能改变 official pricing universe。
- GAT 可以延迟 true-RC negative，不能永久丢弃 true-RC negative。
- `DELAY_QUEUE` 是有限延迟队列，不是 reject，不参与 no-negative certificate。
- final certificate 只来自 exact pricing exhaustive no-negative result。
- 如果 exact pricing hit time、sequence、path-option 或 timed-evaluation limit，节点仍必须 incomplete。

## 2. Current State From Code And Reports

### 2.1 Exact BPC / Journey Master

当前 `BPC_future` 对固定配置宇宙 exact：fixed logical graph、fixed path options、fixed discrete start-time candidates、当前 branch/cut/pricing config。`bpc_future_model_design.md` 明确说明如果 pricing 触发任何预算 limit，节点只能 incomplete，不能证明 optimality。

`JourneyColumn` 表示一辆 rover 在 planning horizon 内的一组 timed trips / sorties。`JourneyPool` 只管理当前 RMP column pool，不定义 proof universe。`JourneyRMP` 的官方 LP lower bound 依赖当前 journey pool 和 pricing closure；`manual_journey_reduced_cost()` 的语义是：

```text
rc(j) = cost(j)
      - fleet_limit_dual
      - sum task_cover_duals
      - sum cut_dual * cut_coefficient(j)
```

该公式是所有 true-RC check 的唯一口径。GAT 不能替代它。

`journey_pricing.py` 当前状态机包括：

```text
FOUND_NEGATIVE
LOCAL_NO_COLUMN_UNCERTIFIED
CERTIFIED_NO_NEGATIVE
INCOMPLETE_LIMIT
DUPLICATE_ONLY
```

只有 exhausted、global_certificate_capable、status=OPTIMAL 且 reason 合法的 no-negative result 才能成为 `CERTIFIED_NO_NEGATIVE`。worker-local no-column、audit no-column、GAT/OOD no-column 都不能升级为 certificate。

### 2.2 Current GAT / Learning Stack

现有 `FutureGraphBuilder` 将 Moon Trek logical graph 转成 PyG graph，保留 directed pair edges 和 flattened path-option list。`OptionEncoder` 对每个 directed pair 的 path options 做 attention 和物理指标 pooling；`HierarchicalOptionGAT` 用 GATv2Conv 编码 logical graph；`ContextAwareColumnSelector` 将 candidate task membership、candidate features、context features 与 task embedding 拼接，输出 `skip/add/abstain` logits。

现有 selector 已经在代码注释中声明：它不是 pricing oracle，不能参与 official lower bound、certificate 或 branch decision；true-RC negative 未被优先加入时必须进入 delay queue。

当前结构的问题是：

- candidate 表示主要依赖 `candidate_task_membership` mean pooling，丢失 task order。
- 对 selected arc options、start/end time、multi-trip timing、energy slack、time-window slack 表示不足。
- 输出更接近 candidate classification，不能充分表达 batch 加入后对 RMP objective、dual、basis、tail retry 的影响。
- CBF/GAT 报告显示 embedding 有信号，但 `production_ready=false`。
- 当前 v36 worker ROI 训练集和 kNN/OOD 壳仍不足以直接 production，尤其 calibrated shell false-safe 非零，zero-FP shell 没有接受 batch。

### 2.3 CBF / Residual Trajectory Evidence

`rmp_residual_cbf_control_direction_zh.md` 将当前瓶颈定义为 state-dependent switching feedback system：

```text
x_t = (theta_t, B_t, z_t)
u_t = admitted true-RC negative column batch
x_{t+1} = F_sigma(x_t, u_t)
```

当前优化对象不应是单列 `p -> good/bad`，而应是：

```text
(x_t, U_t) -> predicted_delta_V
(x_t, U_t) -> predicted_barrier_slack
(x_t, U_t) -> P(stable trajectory transition)
```

CBF gate 的合法含义是 ordering / scheduling constraint，不是 hard filtering。unsafe 只能表示 delay。

### 2.4 Latest Readiness / A/B Evidence

2026-06-14 GAT+CBF kNN/OOD readiness 报告显示：

- trajectory dataset 行数足够进入第一版训练；
- checkpoint 有 horizon CBF target 和 exactness contract；
- capture validation 有小样本 high-priority 信号；
- production blockers 仍包括 no 5/10 no-regression BPC A/B、no 20-task wall-time ROI A/B、no online opt-in integration。

2026-06-14 real smoke 显示 target-priority worker 在一个 20-task Apollo sector-wave 实例上能改善 incumbent，但仍是 `TIME_LIMIT`，`dual_bound=None`，没有 certificate。

2026-06-15 same-run batch impact audit 显示 capture-only 5/10 official result 一致，offline gate 有 zero delay false positive，但 20-task baseline/capture 仍全是 `TIME_LIMIT`。该报告也明确：有效样本必须来自 same-context intervention，不能从 `rc < 0` 或跨上下文样本直接贴 trajectory label。

## 3. Exactness Boundary

以下边界必须作为所有阶段的硬约束。

1. Journey-column RMP 保持不变。
   `JourneyColumn` 仍表示一辆 rover 的 feasible multi-sortie schedule；task cover、fleet limit、pricing-compatible cuts 和 branch rows 的数学语义保持不变。

2. Official lower bound 来源保持不变。
   official RMP lower bound 只能来自当前 exact RMP LP，并且只有在 exact pricing closure 后才可用于节点证明。

3. Exact pricing / final judge 是唯一 certificate source。
   GAT、CBF、kNN、OOD、worker、shadow replay、delay queue 都不能证明 no negative reduced-cost journey。

4. Reduced cost 公式保持不变。
   所有进入 RMP 的列必须用真实 RMP duals 和 `manual_journey_reduced_cost()` 语义验证 true reduced cost。

5. Branch / cut exactness 保持不变。
   `same_vehicle`、`separate_vehicle`、`task_vehicle_on`、`task_vehicle_off` 约束必须继续参与 pricing compatibility；pricing-compatible cuts 的 coefficient 必须继续进入 reduced-cost 公式。

6. 配置宇宙保持不变。
   GAT 不能偷偷扩大或缩小 `Omega_cfg(node)`。如果 GAT 只优先搜索一部分区域，exact fallback 必须最终覆盖完整 configured universe。

7. Limit 语义保持不变。
   pricing hit time、sequence、path-option、DP state、timed-evaluation 或 deadline limit 时，节点不能 certificate，只能 incomplete。

## 4. Fixed Components

后续优化中固定为 exact proof core 的组件：

- `BPC_future/core/journey.py`
  `JourneyColumn`、`JourneyPool`、`make_journey()` 的语义固定。

- `BPC_future/master/journey_rmp.py`
  `solve_journey_rmp()`、`JourneyDuals`、`manual_journey_reduced_cost()` 的 proof 语义固定。

- `BPC_future/core/branching.py`
  pricing-compatible branch constraints 固定。

- `BPC_future/core/cuts.py`
  pricing-compatible cuts 和 cut coefficient 固定。

- `BPC_future/pricing/journey_pricing.py`
  exact pricing 状态机、global certificate capability、completion-bound exact-safe semantics 固定。

- `BPC_future/solver/journey_driver.py`
  official branch-price-and-cut driver 的 certificate 判定固定。

- `BPC_future/configs/*`
  official benchmark 默认配置不能因为本计划直接启用新 GAT gate / worker。

## 5. Forbidden Changes

以下行为禁止进入实现：

1. 禁止把 GAT 当 pricing oracle。
2. 禁止让 GAT 产生 certificate、official lower bound、no-negative conclusion。
3. 禁止 GAT 永久丢弃 true-RC negative `JourneyColumn`。
4. 禁止把 `DELAY_QUEUE` 当作 reject。
5. 禁止 delay queue 参与 no-negative certificate。
6. 禁止为了清空 delay queue 而扩展 exact proof budget。
7. 禁止在 certificate mode 下使用 GAT hard pruning。
8. 禁止将 GAT/OOD/kNN worker 默认启用到 official benchmark。
9. 禁止 5/10 规模因为 GAT 改动产生任何 official result regression。
10. 禁止用 post-addition future features 作为 online training features。
11. 禁止 random-row split 伪造验证效果；主要结论必须使用 instance-level、family-level 或 context-level holdout。
12. 禁止把 `rc < 0` 直接当成高质量列标签。
13. 禁止跨 dual、cuts、branch、pool context 混合样本并贴 causal label。
14. 禁止为追求速度破坏 exact fallback / final judge。

## 6. Target Mode: Learning-guided Discovery, Exact-certified Closure

Target Mode 的在线流程应为：

1. RMP solve 得到当前 `x_t`：
   objective、true duals、active support、pool stats、branch constraints、cut signature、tail counters。

2. Pricing workers 产生候选区域或候选列：
   GAT 可以建议 first-task、transition、arc-option、residual-family priority，让 search 先访问高 ROI 区域。

3. 所有候选列进入 RMP 前必须 true-RC verified：
   使用当前 RMP true duals、branch/cut context 和 `manual_journey_reduced_cost()` 语义。

4. GAT+CBF/kNN/OOD admission scheduling：

```text
if rc(p) >= 0:
    decision = REJECT_NONNEGATIVE_ONLY
elif safe_and_in_distribution(p or batch):
    decision = HIGH_PRIORITY
else:
    decision = DELAY_QUEUE
```

5. `HIGH_PRIORITY` 先加入或先返回给 RMP。
   `DELAY_QUEUE` 保留并有限延迟，后续必须 under current true duals reprice 或 re-expose。

6. Certificate candidate / final proof:
   - reprice delay queue under current true duals；
   - any currently negative delayed column must be added or re-exposed；
   - disable GAT hard filtering；
   - run exact pricing over full `Omega_cfg(node)`；
   - only exhausted + no negative can create `CERTIFIED_NO_NEGATIVE`。

Target Mode 允许 GAT 提速，但不允许 GAT 改变 proof semantics。

## 7. Stage 1: Model Structure Optimization

### 目标

把当前 column-level / candidate-level GAT 升级为 trajectory / batch-impact oriented GAT。阶段 1 只做 offline / audit-only 模型结构设计、原型和数据接口，不接 production solver。

### 当前问题

- `candidate_task_membership` mean pooling 太粗，无法表达 ordered tasks。
- 对 `JourneyColumn.signature` 中的 sortie order、arc-option sequence、start time、multi-trip timing 表示不足。
- 对 energy slack、time-window slack、return/recharge occupancy、branch/cut context 表示不足。
- 当前输出更接近 candidate classifier，缺少 batch-level delta_V、barrier slack、tail retry 预测。
- 当前 GAT embedding 有信号，但所有 readiness 报告仍是 `production_ready=false`。

### 应该修改的组件

保留并复用：

- `FutureGraphBuilder`
- `HierarchicalOptionGAT`
- `OptionEncoder`
- path-option attention
- GATv2Conv message passing

新增或重构：

- `JourneyCandidateEncoder`
  编码 ordered tasks、selected arc options、start/end time、trip count、energy slack、time slack、time-window slack、support overlap、replacement/new-task-set indicator。

- `BatchImpactEncoder`
  聚合一批 `JourneyColumn` 或 candidate journeys，输出 batch embedding；需要支持 best-RC、diverse、support-repair、replacement-heavy 等 batch type。

- `RMPContextEncoder`
  编码当前 RMP state：dual movement、active support、basis turnover proxy、column pool stats、replacement ratio、support-changing ratio、tail retry counters、branch depth、cut signature、family signature。

- Multi-head impact predictor：
  - `P(high_priority)`
  - `predicted_delta_V`
  - `predicted_barrier_slack`
  - `P(tail_improved)`
  - `P(bad_mode_switch)`

### 不允许修改/不允许启用的组件

- 不修改 `manual_journey_reduced_cost()` 语义。
- 不修改 `CERTIFIED_NO_NEGATIVE` 判定。
- 不启用 online GAT gate。
- 不启用 production worker。
- 不修改 benchmark 默认配置。
- 不允许模型输出直接影响 branch/cut/RMP lower bound。

### 建议新增文件

- `BPC_future/learning/journey_candidate_encoder.py`
- `BPC_future/learning/batch_impact_model.py`
- `BPC_future/learning/rmp_context_encoder.py`
- `BPC_future/scripts/build_gat_batch_impact_dataset.py`
- `BPC_future/scripts/train_gat_batch_impact.py`
- `BPC_future/tests/test_gat_batch_impact_model.py`

### 建议修改文件

- `BPC_future/learning/column_selector.py`
  只补充 scheduler decision helper 或兼容包装，不改变现有 exact-safe 语义。

- `BPC_future/learning/graph_builder.py`
  只在必要时补充 metadata，不改变 graph tensor schema 的 checkpoint 兼容性，除非 bump version。

- `BPC_future/scripts/build_gat_trajectory_cbf_dataset.py`
  扩展为 batch-level labels 或抽出共享 feature builder。

### 输入/输出 artifact

输入：

- logical graph JSON
- current RMP/capture event
- candidate batch payload
- current context features

输出：

- model architecture spec
- offline checkpoint with `production_ready=false`
- schema versioned manifest
- offline report explaining which heads are training-only and which may become future scheduler inputs

### 验收标准

- checkpoint contract 明确：
  `pricing_oracle=false`、`certificate_source=false`、`official_bound_effect=false`。
- 模型可以读取 ordered journey/batch/context features。
- multi-head 输出维度和 finite-check 测试通过。
- 所有新增训练/推理脚本 `runs_bpc_or_pricing=false`。
- 不产生任何 solver result change。

### 失败风险

- batch encoder 过拟合小样本。
- order/arc-option 表示太复杂导致数据稀疏。
- context features 混入 post-addition leakage。
- batch-level label 广播到单列后语义污染。

### 进入下一阶段的 gate

- 数据 schema review 通过。
- 单元测试覆盖 exact-safe scheduler names。
- 至少一个 toy/offline dataset 能完整训练和导出 diagnostic checkpoint。
- 无任何 benchmark/config/default behavior change。

## 8. Stage 2: Data Collection

### 目标

收集 same-context intervention 数据，而不是只收 `rc < 0` 数据。

样本定义：

```text
sample = (G, x_t, U_t, y_t)
```

其中：

- `G` = logical graph / path-option graph；
- `x_t` = 当前 RMP 状态；
- `U_t` = candidate `JourneyColumn` batch；
- `y_t` = 加入 `U_t` 后 H-step RMP trajectory 变化。

### 当前问题

错误标签来源包括：

- `rc < 0` 直接当 high-quality label；
- replacement negative column 自动当 positive；
- active support changed 自动当 positive；
- final coarse wall-time ROI 反推单个 batch；
- 不同 dual/cuts/branch/pool context 混合贴 trajectory label；
- same-run candidate 出现但没有 causal target intervention。

### 应该修改的组件

- 扩展 capture / replay / audit-only 采集脚本，记录 same context 下的 intervention。
- 在 `journey_driver.py` 只增加 opt-in shadow/audit logging，不改变 solver decision。
- 在 worker A/B runbook 中固定 target materialization worker，避免 worker search ROI 与 GAT ranking ROI 混合。

### 不允许修改/不允许启用的组件

- 不改变 official solver path。
- 不启用 production worker。
- 不影响 official lower bound。
- 不延长 certificate proof budget。
- 不把 audit replay 的 no-column 结果写入 certificate path。

### 建议新增文件

- `BPC_future/scripts/build_gat_same_context_intervention_dataset.py`
- `BPC_future/scripts/audit_gat_batch_impact_intervention.py`
- `BPC_future/scripts/build_gat_batch_intervention_runbook.py`
- `BPC_future/tests/test_gat_same_context_intervention_dataset.py`

### 建议修改文件

- `BPC_future/solver/journey_driver.py`
  增加 audit-only context snapshots 和 candidate batch shadow decisions，默认 off。

- `BPC_future/scripts/build_gat_same_run_batch_impact_dataset.py`
  扩展为 same-context causal intervention rows。

- `BPC_future/scripts/analyze_gat_fixed_worker_post_injection.py`
  输出 H-step labels 和 strict trajectory labels。

### 输入/输出 artifact

必须采集字段：

- `context_hash`
- `node_id`, `depth`, `cg_iter`
- RMP objective
- cover duals summary
- fleet dual
- cut duals summary
- `dual_l1_delta`, `dual_linf_delta`
- active support hash
- active task sets
- column pool size
- replacement ratio
- support-changing ratio
- `certificate_flat_rounds`
- `certificate_no_column_rounds`
- `final_judge_retry_count`
- `hidden_negative_count`
- `pricing_tail_retry_count`
- branch constraints
- cut set signature
- family / instance / terrain / task_count

候选 batch 类型至少包括：

- best-RC batch
- diverse batch
- support-repair batch
- active-support-overlap batch
- new-task-set batch
- replacement-heavy batch
- random true-RC negative batch
- current GAT high-priority candidate batch
- noop / control batch

标签至少包括：

- `label_high_priority`
- `horizon_delta_V`
- `horizon_barrier_slack`
- `label_tail_improved`
- `label_bad_mode_switch`
- `objective_progress`
- `dual_stability_improved`
- `support_changed_good`
- `final_judge_retry_delta`
- `hidden_negative_delta`

### 验收标准

- 每条 positive label 都有 same-context target intervention evidence。
- 每条 negative label 都区分 true-RC negative without impact 与 nonnegative reject。
- `official_bound_effect=false`。
- `certificate_effect=false`。
- 5/10 capture-only official result 完全一致。
- 数据 manifest 记录 context、family、instance split 信息。

### 失败风险

- 有效 positive 样本稀疏。
- 单实例 Apollo/Tranq 偏置过重。
- context hash 不稳定导致 causal match 失败。
- H-step label 被 final coarse ROI 污染。

### 进入下一阶段的 gate

- 至少覆盖 task20 的 random-wave、sector-wave、greedy-anchor。
- positive/negative 都有多个 instance、family、region。
- same-context causal match rate 达到可用阈值，例如 `>= 90%`。
- audit-only capture 对 5/10 official result 无影响。

## 9. Stage 3: Training

### 训练阶段硬合同

Stage 3 训练不允许解释成“先训练一个分类器，再事后看 ROI / precision”。从第一版训练开始，模型就必须按未来 admission scheduler 验收，默认状态是：

```text
stage4_candidate_ready = false
training_objective_not_satisfied = true
```

只有当同一组 frozen threshold / OOD / fallback rule 在 holdout artifact 中同时证明精准率、回报率、安全性和有效覆盖全部过线，才允许把 checkpoint 升级为 Stage 4 candidate。

训练主目标固定为：

```text
primary_objective = precision_constrained_roi_maximization
```

这里的 `precision_constrained_roi_maximization` 必须按硬约束理解，不是
“分类训练 + 事后 ROI 报告”。训练阶段的目标函数、threshold search、
checkpoint selection 和最终报告必须共同执行同一套 admission policy 验收：

```text
hard_training_goal:
  first, reject unsafe / low-precision admission
  second, reject non-profitable or baseline-losing admission
  third, reject zero-coverage safe shells
  only then optimize expected trajectory utility / loss tie-breakers
```

也就是说，训练阶段的合格 checkpoint 必须同时证明：

- `HIGH_PRIORITY` 的 precision / safe precision 过线，并且 CI lower bound 过线；
- accepted batch ROI 过线，并且 ROI lower bound 高于 random / best-RC / old-GAT baseline；
- false HIGH_PRIORITY on delay、accepted bad-mode、false-safe union rate 都在硬上限内；
- accepted coverage 非零且有加速意义，不能只输出一个 zero-FP empty shell；
- family / context holdout 不出现 precision 或 ROI 坍塌；
- 使用的 threshold / OOD / fallback rule 已冻结，Stage 4 shadow 不得重新调阈值。

任一条不满足，checkpoint 的结论必须是：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
training_objective_not_satisfied = true
```

不能用更低 validation loss、更高 F1、更高 recall、更好 AUC 或更漂亮 embedding
图来抵消 ROI / precision / safety / coverage 的失败。

这不是训练结束后的 summary 指标，而是训练阶段本身的目标函数和 checkpoint 选择合同。任何实现如果先按 `validation_loss`、F1、AUC、recall 或 `rc < 0` 命中率选模型，再把 ROI / precision 作为后处理报告，都必须判定为：

```text
training_contract_incomplete = true
stage4_candidate_ready = false
```

其中含义必须写死：

- precision / safe precision 是入场约束，不是可用 ROI 抵消的软指标；
- accepted batch ROI 是主优化目标，不是训练完成后的附带报告；
- coverage 是实用性下限，zero-FP 但 accepted batch count 为 0 不能通过；
- false HIGH_PRIORITY on delay / low-ROI batch 是硬错误，惩罚权重大于漏放一个 high-ROI batch；
- validation loss、F1、AUC、recall、embedding separation 只能作为 surrogate / diagnostic / tie-breaker。

训练阶段必须在四个位置同时使用 ROI 和 precision，缺一不可：

- loss / surrogate：必须显式惩罚 low-ROI、delay-labeled、bad-mode batch 被打成 `HIGH_PRIORITY`，并用同 context pairwise/ranking 信号推动 high-ROI batch 分数高于 low-ROI batch；
- threshold frontier：每个 epoch / checkpoint 都要扫 frozen threshold 候选，先过滤 precision、safe precision、false-safe、accepted-count、ROI-CI 和 baseline margin，再在可行集合里最大化 accepted ROI；
- checkpoint selection：`best_epoch` 只能从通过 ROI / precision / safety / coverage / holdout gate 的 checkpoint 中选择，loss/F1/recall 只能在可行 checkpoint 之间做 tie-breaker；
- artifact schema：每个 checkpoint 和 threshold 必须输出 machine-checkable 的 ROI、precision、CI lower bound、baseline comparison、coverage、OOD/fallback rule 和 reject reason。

因此 Stage 3 的训练代码不允许出现“模型训练目标是 classification，ROI / precision 只在 evaluator 里算”的结构。训练脚本、threshold search、checkpoint selector 和 report writer 必须共享同一个 deployment-facing gate；否则该 checkpoint 只能叫 diagnostic checkpoint。

训练 artifact 缺少任一硬字段时，结论必须是失败，而不是“暂时无法判断”：

```text
training_objective
checkpoint_selection_policy
selected_thresholds
selected_threshold_reason
high_priority_precision
high_priority_precision_ci_low
safe_precision
safe_precision_ci_low
accepted_batch_count
accepted_batch_rate
accepted_batch_roi
accepted_batch_roi_ci_low
accepted_batch_roi_over_random_baseline
accepted_batch_roi_over_best_rc_baseline
accepted_batch_roi_over_old_gat_baseline
accepted_batch_roi_over_baseline_ci_low
false_high_priority_on_delay
accepted_bad_mode_count
max_accepted_bad_mode_count
false_safe_rate_union
family_context_holdout_precision_roi_coverage
rejected_checkpoint_reasons
```

因此 `best_epoch` 不能来自 `min(validation_loss)`。合法选择只能是：

```text
feasible = checkpoints passing precision / safety / ROI / ROI-CI / baseline / coverage / holdout gates

if feasible is empty:
    selected_checkpoint = null
    stage4_candidate_ready = false
else:
    selected_checkpoint = argmax(feasible, accepted_batch_roi_ci_low, accepted_batch_roi_over_baseline_ci_low, trajectory_utility)
```

### 目标

训练 GAT 学 “candidate batch 加入后是否改善 RMP trajectory”，而不是学 `rc < 0`、best-RC、active-support proxy 或普通二分类边界。

训练阶段的硬目标不是把 validation loss、F1 或 recall 做高，而是训练出一个保守但有真实回报的 admission policy。这里的“真实回报”必须在训练 / validation / holdout artifact 中可量化，至少包括 admission 精准率、accepted batch ROI、tail-risk 抑制和 family/context 泛化。

训练目标必须从一开始就显式考虑回报率和精准率。也就是说，训练脚本的 primary objective 不能是普通分类 loss，也不能是 `rc < 0` 命中率；它必须是带硬约束的 `precision-constrained ROI maximization`。loss、F1、AUC、recall 只能作为 surrogate / diagnostic，不能决定 checkpoint 是否合格。

这条必须写硬：Stage 3 的主目标就是 `precision-constrained ROI maximization`。训练脚本可以用 loss、ranking loss、calibration loss 做 surrogate，但 checkpoint 是否合格必须先看 precision / ROI / safety / coverage gate。没有通过这些 gate 的模型，即使 validation loss 最低、F1 最高、recall 最高，也只能叫 diagnostic checkpoint，不能叫 Stage 4 candidate。

更进一步，ROI / precision 不能只在训练结束后被动报告；它们必须进入训练阶段的四个位置：

- training objective：false HIGH_PRIORITY on low-ROI / delay-labeled batch 必须被硬惩罚，且惩罚权重大于漏放一个 high-ROI batch；
- threshold search：只允许在 precision / safe-precision / false-safe / accepted-count 先过线的阈值集合里最大化 ROI；
- checkpoint selection：`best_epoch` 只能从 ROI / precision / CI / coverage gate 全部过线的 checkpoint 中选；
- artifact schema：每个 checkpoint 和每组 threshold 都必须输出 machine-checkable 的 ROI、precision、CI lower bound、baseline comparison 和 reject reason。

如果训练代码缺少上述任一环节，结论必须是 `training_contract_incomplete=true`，不能用“后处理评估里 ROI 看起来不错”来替代训练阶段硬目标。

训练阶段不允许把 precision 和 ROI 当成可以互相抵消的指标。`high recall + low precision`、`high precision + low ROI`、`positive ROI point estimate + ROI lower bound failed`、`zero false positive + zero accepted coverage` 都是失败，不是不同偏好的模型。

本节按下面的训练合同执行，不能在报告里降级成“分类效果还可以”：

```text
Stage 3 默认状态 = no_candidate

只有同时满足：
  precision gate
  precision confidence lower-bound gate
  accepted ROI gate
  accepted ROI-over-baseline confidence gate
  nonzero useful coverage gate
  kNN/OOD false-safe gate
  family/context holdout gate

才允许输出：
  stage4_candidate_ready = true

否则必须输出：
  stage4_candidate_ready = false
  training_objective_not_satisfied = true
  rejected_checkpoint_reasons = [...]
```

训练脚本的主验收顺序也必须固定：先安全和精准率，再 ROI 和 ROI lower bound，再 coverage，再 utility / tail proxy，最后才允许比较 loss/F1/recall。任何报告如果把 validation loss、F1、recall 放在 ROI / precision gate 前面，结论都只能算 diagnostic。

因此 training artifact 必须能回答：

- 模型放进 `HIGH_PRIORITY` 的 true-RC negative batch，precision 是否足够高；
- 这些 accepted batch 的 ROI 是否显著高于 random / best-RC / old-GAT baseline；
- ROI 和 precision 的 confidence lower bound 是否过线；
- accepted coverage 是否非零且有实际加速意义；
- family/context holdout 上是否没有 precision 或 ROI 坍塌。

如果训练产物只证明“分类指标好”，但不能证明以上五点，结论必须是 `training_objective_not_satisfied`。

Stage 3 的完成定义必须改成 deployment-facing：

```text
训练完成 != 生成一个 checkpoint
训练完成 == 找到一组冻结 threshold / OOD / fallback rule，
            在 holdout 上同时证明 high-priority precision、safe precision、
            accepted batch ROI、accepted coverage、false-safe control 全部达标。
```

如果当前数据或模型只能做到“高 recall 但 precision 低”、“zero-FP 但 accepted batch count = 0”或“precision 高但 ROI 不高于 baseline selection”，训练阶段结论必须是 `stage4_candidate_ready=false`。

更具体地说，训练阶段必须回答两个 deployment 问题：

- GAT 设成 HIGH_PRIORITY 的 batch，真的大概率改善 RMP trajectory 吗？
- GAT 放行的 batch，相比 random / best-RC / old-GAT selection，有稳定的 accepted ROI 吗？

如果这两个问题没有被 holdout artifact 正面证明，训练阶段就没有完成。

```text
在 true-RC negative batch 集合内，
HIGH_PRIORITY 必须高精准、高回报；
DELAY_QUEUE 必须拦住可能拖尾的负列；
accepted batch 不能为 0；
false HIGH_PRIORITY 必须被强惩罚。
```

更硬地说，Stage 3 不是普通分类训练，而是一个带硬约束的 admission policy 训练问题：

```text
maximize    expected_trajectory_utility
            + accepted_batch_roi
            + tail_retry_reduction_proxy

subject to  high_priority_precision >= hard_threshold
            high_priority_precision_ci_low >= hard_threshold_ci_low
            safe_precision >= hard_threshold
            safe_precision_ci_low >= hard_threshold_ci_low
            false_high_priority_on_delay <= hard_limit
            accepted_bad_mode_count <= hard_limit
            false_safe_rate_union <= hard_limit
            accepted_batch_count > 0
            accepted_batch_rate >= useful_coverage_floor
            accepted_batch_roi > baseline_selection_roi
            accepted_batch_roi_ci_low > baseline_selection_roi
            family/context holdout 不出现不可解释的 precision 或 ROI 坍塌
```

任何 checkpoint 只要 precision / safety / ROI / coverage / confidence lower bound 其中之一失败，就只能标记为 diagnostic，不允许被称为 Stage 4 candidate。loss、F1、recall、AUC、embedding 可分性都不能抵消这些失败。阈值也不能事后挑好看的：报告中的 precision / ROI 必须使用将来 admission scheduler 实际会用的同一组 threshold、OOD rule 和 fallback rule。

因此训练目标必须同时优化，并在训练脚本输出中逐项验收：

- high-priority precision / safe precision；
- precision confidence lower bound；
- accepted batch ROI；
- accepted batch ROI over random / best-RC / old-GAT baseline, including confidence lower bound；
- expected trajectory utility；
- false high-priority on delay；
- accepted bad-mode count；
- false-safe rate under kNN/OOD；
- nonzero accepted coverage；
- family/context holdout stability。

其中 precision 和 ROI 不是事后报告项，而必须进入 training objective、threshold search、checkpoint selection 和 reject reason。也就是说，训练脚本不能先按 validation loss 选 best checkpoint 再报告 ROI；必须先筛掉 ROI、precision 或 confidence lower bound 不达标的 checkpoint，再在剩余候选中比较 trajectory utility 和 loss。

训练脚本的 checkpoint 选择必须等价于以下策略：

```text
feasible = checkpoints passing precision / safety / ROI / coverage / CI gates

if feasible is empty:
    selected_checkpoint = null
    stage4_candidate_ready = false
    training_objective_not_satisfied = true
else:
    selected_checkpoint = argmax(
        accepted_batch_roi_ci_low,
        accepted_batch_roi_over_baseline,
        expected_trajectory_utility,
        tail_retry_reduction_proxy,
        validation_loss_tiebreaker
    )
```

`best_loss_epoch`、`best_f1_epoch`、`best_recall_epoch` 只有在它们也通过上述 feasible gate 时才允许被选中。否则报告必须写明它们被拒绝的 ROI / precision 原因。

Recall 只能作为次级指标。一个模型即使 add recall 很高，如果 high-priority precision 或 accepted batch ROI 不达标，也不得进入 Stage 4。相反，zero-FP 但 accepted batch count 为 0 的模型也不合格，因为它只是安全空壳，没有 column generation 加速价值。

训练阶段必须把以下条件当成 checkpoint / Stage 4 的一票否决项，而不是软指标：

| 类别 | 硬目标 | 不满足时的结论 |
| --- | --- | --- |
| 精准率 | validation `high_priority_precision >= 0.85` 只够 diagnostic，Stage 4 candidate 必须 `>= 0.90`，且 `high_priority_precision_ci_low >= 0.85` | 不能作为 admission checkpoint |
| 安全放行 | validation `safe_precision >= 0.85` 只够 diagnostic，Stage 4 candidate 必须 `>= 0.90` 且 `safe_precision_ci_low >= 0.85`；进入 opt-in 前目标 `safe_precision >= 0.95` 或有 family fallback | 不能进入 online shadow / opt-in |
| 错放 delay | `false_high_priority_on_delay <= 1%`，超过 `2%` 直接失败 | 必须提高 threshold 或 family-specific delay |
| false-safe | `false_safe_rate_union <= 1% ~ 2%` | kNN/OOD shell 不合格，不能 Stage 4 |
| 回报率 | `accepted_batch_roi >= max(0.65, baseline_roi + 0.20)`，且 bootstrap / confidence lower bound 必须高于 random / best-RC / old-GAT baseline | 高 F1 / 高 recall 不能抵消 |
| 有效覆盖 | `accepted_batch_count > 0` 且 `accepted_batch_rate` 不得低到没有加速意义 | zero-FP 但不放行只能作为安全上界 |
| 轨迹收益 | `expected_trajectory_utility > 0`，family/context holdout 上不得为负 | 不能宣称改善 RMP trajectory |
| 阈值一致性 | 训练选择、报告、Stage 4 shadow 必须使用同一套 threshold / OOD / fallback rule | 事后调阈值的结果不算有效 |
| 泛化 | instance / family / context holdout 都必须报告 precision、ROI、coverage | random-row split 结果不算主结论 |
| 数值稳定 | 非有限 loss/gradient skipped update rate 必须低于硬阈值，例如 `<= 2%` | checkpoint 只能诊断，不能进入 Stage 4 |

checkpoint selection 顺序必须固定为：

```text
1. 先过滤：precision / safety / ROI / coverage / stability / holdout 全部达标；
2. 再排序：expected trajectory utility、accepted batch ROI、tail retry reduction proxy、validation loss；
3. 只把通过 gate 的 checkpoint 标成 Stage 4 candidate；
4. 未通过的 checkpoint 必须列出 reject reasons；
5. 如果没有 checkpoint 通过 gate，结论必须是 `stage4_candidate_ready=false`，不能降低阈值凑候选。
```

训练报告必须显式给出 `selected_checkpoint_reason`、`selected_threshold_reason` 和 `rejected_checkpoint_reasons`。如果最终 checkpoint 是因为“最安全”而被选中，但 ROI 未达标，报告必须写 `stage4_candidate_ready=false`；不能把它包装成 conservative production candidate。

### 当前问题

- 现有模型容易学习 candidate classification 或 RC proxy。
- delay / non-improving 样本偏少。
- random-row split 会夸大泛化能力。
- false high-priority 的代价高于 false delay。
- 只优化 F1 会把“多放行”误当成好模型，导致 harmful negative batch 进入 HIGH_PRIORITY。
- zero-FP 壳如果 accepted count = 0，也不是可用模型；它只有安全性，没有加速回报。
- training summary 必须报告 ROI / precision / coverage 三者的 tradeoff，不能只报告 classification metrics。
- 只按 validation loss 选 checkpoint 会把 admission 目标变软；Stage 3 必须用 deployment-facing constrained selection。

### 应该修改的组件

- 新增 batch-impact training script。
- 使用 instance-level、family-level、context-level holdout。
- 增加 calibration 和 conservative threshold selection。
- 将 kNN/OOD shell 作为上线前必经验证，而不是 optional report。
- 在训练脚本中把 deployment metrics 作为 checkpoint selection 的一部分，而不是只按 validation loss / F1 选 checkpoint。
- 增加 utility-weighted threshold search：只有满足 precision / false-safe / accepted-count 下限的阈值，才比较 expected ROI。
- 增加 ROI-aware checkpoint gate：checkpoint 必须同时跑 random / best-RC / old-GAT baseline comparison，不高于 baseline 的 checkpoint 直接 reject。
- 增加 precision-first calibration：先保证 high-priority precision / safe precision，再在可行阈值集合中最大化 accepted ROI 和 trajectory utility。
- 增加 threshold-grid artifact：每个 checkpoint 必须输出所有候选 threshold 的 precision、ROI、coverage、false-safe、reject reason，最终只能从通过硬 gate 的 threshold 中选择。
- 增加 confidence-aware ROI / precision report：样本不足时不能只报 point estimate，必须报告 bootstrap / Wilson lower bound；lower bound 不过线按失败处理。
- 增加 hard reject reason taxonomy：至少区分 `precision_below_gate`、`precision_ci_below_gate`、`roi_below_baseline`、`roi_ci_below_baseline`、`zero_accepted_coverage`、`false_safe_too_high`、`holdout_family_collapse`。

### 不允许修改/不允许启用的组件

- 不接 online solver。
- 不启用 production gate。
- 不用模型输出替代 true-RC。
- 不用模型输出替代 final judge。

### 建议新增文件

- `BPC_future/scripts/train_gat_batch_impact.py`
- `BPC_future/scripts/audit_gat_batch_impact_knn_ood.py`
- `BPC_future/scripts/evaluate_gat_batch_impact_holdout.py`
- `BPC_future/tests/test_gat_batch_impact_training.py`
- `BPC_future/tests/test_gat_batch_impact_knn_ood.py`

### 建议修改文件

- `BPC_future/learning/column_selector.py`
  保留旧 class ids，同时新增 batch scheduler decision mapping。

- `BPC_future/scripts/train_gat_worker_roi.py`
  可抽出 loss helpers，避免重复实现 focal / pairwise / hard-negative logic。

### 输入/输出 artifact

训练任务：

- binary / multiclass:
  `HIGH_PRIORITY` vs `DELAY_QUEUE` among true-RC negative batches。

- regression:
  `predicted_delta_V`、`predicted_barrier_slack`。

- auxiliary:
  `tail_improved`、`bad_mode_switch`、`objective_progress`、`support_changed_good`。

训练阶段必须显式输出 deployment-facing metrics：

- `high_priority_precision`
- `high_priority_precision_ci_low`
- `safe_precision`
- `safe_precision_ci_low`
- `accepted_batch_count`
- `accepted_batch_rate`
- `accepted_batch_roi`
- `accepted_batch_roi_over_random_baseline`
- `accepted_batch_roi_over_best_rc_baseline`
- `accepted_batch_roi_over_old_gat_baseline`
- `accepted_batch_roi_ci_low`
- `baseline_roi_ci_high`
- `expected_trajectory_utility`
- `false_high_priority_on_delay`
- `false_safe_rate_label_unsafe`
- `false_safe_rate_union`
- `coverage_non_ood`
- `delay_rate`
- `family_holdout_min_precision`
- `family_holdout_min_accepted_roi`
- `selected_thresholds`
- `selected_threshold_reason`
- `stage4_candidate_ready`
- `rejected_checkpoint_reasons`

Loss 设计：

- weighted BCE / focal loss；
- Huber loss for `delta_V` and `barrier_slack`；
- pairwise ranking loss within same context；
- false high-priority penalty > false delay penalty；
- calibration loss for conservative threshold。
- ROI-aware admission loss：
  false HIGH_PRIORITY on low/negative ROI batch 的惩罚必须大于 false DELAY on useful batch；
  high-ROI batch 被 delay 的惩罚只能作为 recall/coverage 压力，不能压过 safety / precision 约束。
- ROI / precision 硬约束必须参与训练循环：
  每个 epoch 都要产生 candidate threshold frontier，并用同一套 hard gate 标注
  `checkpoint_feasible` / `reject_reason`；不能先按 `validation_loss` 固定 epoch，
  再在该 epoch 上寻找好看的 ROI / precision。
- precision-constrained ROI selection loss：
  checkpoint selection 的主排序必须先看 feasible gate，再看 `accepted_batch_roi_ci_low` 和 `accepted_batch_roi_over_baseline`；classification loss 只能做 tie-breaker。
- gate-aware validation objective：
  validation loss 只在通过 precision / safety / ROI / coverage gate 的 checkpoint 之间比较。
- utility-weighted term：

```text
reward = w1 * objective_progress
       + w2 * tail_retry_reduction
       + w3 * dual_stability_improvement
       + w4 * support_changed_good
       - w5 * bad_mode_switch
       - w6 * final_judge_retry_increase
```

  该 reward 只能来自 offline label，不得作为 online feature。checkpoint selection 可以使用 holdout expected reward，但不能把 reward 的未来分量泄漏进模型输入。

禁止使用的特征：

- `state_next_*`
- `delta_*`
- `horizon_*`
- `label_*`
- 任何 online 时不可见的 post-addition features

### 验收标准

- 训练报告必须显式声明 `primary_objective=precision_constrained_roi_maximization`；未声明或仍以 classification loss / F1 / recall 为 primary objective 时，Stage 3 直接失败。
- `checkpoint_selection_policy` 必须是 gate-first：先过滤 precision、safe precision、false-safe、ROI、ROI-CI、baseline margin、coverage、holdout，再比较 utility / loss；任何先按 validation loss 选 epoch 再报告 ROI 的结果都只能算 diagnostic。
- 每个 checkpoint 的 threshold frontier 必须输出 machine-checkable reject reason；缺失 ROI / precision / CI / baseline 字段时，按 `training_contract_incomplete=true` 处理。
- GAT必须找到的是真负列。
- 训练有效样本总量不少于200个（不够就补）。
- main split 不使用 random-row。
- instance-level、family-level、context-level holdout 全部报告。
- training checkpoint selection 必须以 deployment gate 为主：
  先满足 safety / precision / ROI / accepted-count / confidence lower-bound 约束，再比较 validation loss 或 F1。
- checkpoint selection 必须显式使用 ROI 和 precision：
  `best_epoch` 不能只来自 `min(validation_loss)`；
  若 `best_loss_epoch` 未通过 ROI/precision gate，必须选择下一个可行 checkpoint 或声明无 Stage 4 candidate。
- 如果 dataset `ranking_ready=true`，trainer 必须真实启用同 context
  `score(high-ROI batch) > score(low-ROI batch)` 的 pairwise margin ranking loss；
  不能只在 manifest/report 里声明 ranking-ready。若 instance split 把全部同 context
  pair 放进 validation，必须做 pairwise-aware split 让至少一个可比 pair 留在 train，
  或明确报告 `pairwise_ranking_loss_active=false` 与原因。
- validation high-priority precision / safe precision 必须达到硬阈值：
  第一版 offline gate 不低于 `0.85`，进入 Stage 4 前目标不低于 `0.90`；进入 opt-in 前 safe precision 目标提高到 `0.95`，否则必须有 family-specific delay fallback。
- false high-priority on delay 必须接近 0：
  首选 `0`；实验上限 `<= 1%`；超过 `2%` 直接判定不可进入 Stage 4。
- validation false-safe union rate 必须 `<= 1% ~ 2%`；
  仅 audit-only 探索时可放宽到 `<= 5%`，但不能进入 online opt-in A/B。
- accepted batch count 必须 `> 0`，且 accepted batch rate 不能低到没有加速意义。
- accepted batch ROI 必须高于随机 / best-RC / old-GAT baseline：
  进入 Stage 4 前至少要求 `accepted_batch_roi >= baseline_roi + 0.20`，且绝对值建议 `>= 0.65`。
- 若 accepted batch ROI 与 baseline 差异不稳定，必须报告 confidence / bootstrap 区间；无法证明高于 baseline 时按失败处理。point estimate 过线但 lower bound 不过 baseline，也按失败处理。
- expected trajectory utility 必须为正，并在 instance/family/context holdout 上不为负。
- 非有限 loss / gradient / parameter update 只能少量跳过；`nonfinite_skipped_update_rate > 2%`
  时 checkpoint 必须标记为 unstable，不能进入 Stage 4。
- OOD / low confidence 一律 delay。
- threshold / OOD / fallback rule 必须冻结写入 checkpoint metadata；Stage 4 shadow 不允许重新调阈值后再宣称该 checkpoint 通过。
- checkpoint 写明 `production_ready=false`，直到阶段 4 opt-in A/B 通过。

### 失败风险

- zero-FP threshold 导致 accepted count = 0。
- calibrated threshold 有 false-safe，不能上线。
- pairwise ranking 只在同实例有效，跨 family 失败。
- label imbalance 让模型只预测 delay 或只预测 add。

### 进入下一阶段的 gate

- holdout metrics 同时满足 safety、precision、ROI、coverage 四类门槛：
  `false_high_priority_on_delay <= 1%`、`safe_precision >= 0.90`、`accepted_batch_count > 0`、`accepted_batch_roi >= baseline_roi + 0.20`。
- Stage 4 candidate 必须同时满足：
  `high_priority_precision >= 0.90`、`safe_precision >= 0.90`、`accepted_batch_roi >= max(0.65, baseline_roi + 0.20)`、
  `accepted_batch_count > 0`、`false_safe_rate_union <= 2%`。
- 每个 major family 的 holdout 都报告 precision / ROI；任何 family precision < `0.80` 时必须有 family-specific delay fallback，不能进入 online priority。
- zero-FP variant 如果 accepted batch count = 0，只能作为安全上界报告，不能作为 Stage 4 candidate。
- calibrated variant 如果 ROI 不高于 random / best-RC / old-GAT baseline，不能进入 Stage 4。
- checkpoint report 必须列出被拒绝的 checkpoint 及原因，例如 high recall but low precision、safe but no accepted batches、ROI positive but false-safe too high。

### 2026-06-16 v8 硬门槛落地状态

v8 已经把训练阶段从“loss/F1 优先”改成 deployment-facing 的硬目标：

- dataset `v8_mixed_v3_plus_worker_validation_context_fallback_20260616` 合并 v14 same-run、v3 worker validation 和 v8 validation-only worker rows，共 `320` 个 batch sample、`4595` 个 candidate，`ranking_ready=true`、`training_ready=true`。
- trainer 的 `training_objective=precision_constrained_roi_maximization`，checkpoint selection 为 `deployment_gate_first_then_utility_roi_loss`；`best_epoch=4`，不是单纯选择 `best_loss_epoch=7`。
- threshold frontier 找到一组本地可行 hard gate：`accepted_batch_count=35`、`high_priority_precision=1.0`、`high_priority_precision_ci_low=0.9928`、`safe_precision=1.0`、`safe_precision_ci_low=0.9011`、`accepted_batch_roi=8.8244`、`accepted_batch_roi_ci_low=4.9235`、`false_high_priority_on_delay=0`、`false_safe_rate_union=0`。
- 这组阈值依赖 `family_delay_fallback_families=['greedy-anchor', 'random-wave']`，也就是说当前真正被放行的是 validation sector-wave 区域；greedy/random 仍被 delay。

但是 v8 仍不能标成 Stage 4 candidate：

- strict global kNN/OOD (`k=3`, `max_neighbor_delay_fraction=0.0`) 只放行 `19` 个 batch，`safe_precision_ci_low=0.8318`、`accepted_batch_roi_ci_low=0.3377`，未通过硬门槛。
- family kNN/OOD 同样过保守，`accepted_batch_count=18`、`safe_precision_ci_low=0.8241`、`accepted_batch_roi_ci_low=0.3051`，未通过硬门槛。
- global kNN/OOD 若允许 `max_neighbor_delay_fraction=0.34`，硬 precision / ROI / false-safe 指标可过：`accepted_batch_count=35`、`safe_precision_ci_low=0.9011`、`accepted_batch_roi_ci_low=4.9235`、`false_safe_rate_union=0`。
- 即使该 kNN/OOD 变体通过数值门槛，`production_ready=false` 仍必须保留，因为 validation 中 `random-wave` 存在 oracle high-ROI opportunity 但当前 family fallback 全部 delay，`production_block_reasons=['family_holdout_accepted_batch_missing', 'validation_candidate_not_ready']`。

因此 v8 的正确结论是：训练阶段目标已经硬化并产生了强 sector-wave 候选，但 Stage 3 尚未完成。下一步不能降低 ROI / precision 门槛，而应补 `random-wave` same-context / target-worker intervention rows，或显式把 Stage 4 shadow 限定为 sector-wave-only safe source，并在报告中说明 coverage/ROI 适用范围。

### 2026-06-16 v10 random-wave 补样后的状态

v10 按 v8/v9 的 blocker 补了 task50 `random-wave` same-context target-worker rows，核心变化是：

- `5751b1799b606ad1` context 的 target-materialization worker rows 从 2 条扩到 4 条，形成同 context 下强正 / 中强正 / 弱正 / 极弱正四档 ROI 排序信号；
- dataset `v10_mixed_v8_plus_random_wave_task50_5751_20260616` 共 `324` 个 batch sample、`4599` 个 candidate，`random-wave` sample 增至 `197`，`random-wave same_context_pair_count=16`，`task50 same_context_pair_count=10`；
- trainer 仍使用 `training_objective=precision_constrained_roi_maximization` 和 deployment-gate-first checkpoint selection；
- validation hard gate 过线：`accepted_batch_count=35`、`high_priority_precision=1.0`、`high_priority_precision_ci_low=0.9958`、`safe_precision=1.0`、`safe_precision_ci_low=0.9011`、`accepted_batch_roi=8.9500`、`accepted_batch_roi_ci_low=5.0732`、`false_high_priority_on_delay=0`、`false_safe_rate_union=0`；
- 关键 blocker 已改变：`random-wave` 不再整体 fallback，validation 中 `random-wave accepted_batch_count=11`、`random-wave accepted_batch_roi=0.7334`、`random-wave safe_precision=1.0`；
- kNN/OOD (`k=3`, `max_neighbor_delay_fraction=0.34`) 通过 validation safety：`validation_candidate_ready=true`、`validation_safety_ready=true`、`production_block_reasons=[]`；
- safe-source export 成功：`safe_source_ready=true`、`safe_candidate_id_count=408`、`blockers=[]`。

因此 v10 的正确结论是：Stage 3 已经从“sector-wave-only diagnostic”推进到“offline safe-source candidate 可进入 Stage 4 shadow / opt-in A/B”。但这仍不是 production-ready：

- `production_ready=false`、`default_enabled=false` 必须保留；
- exported safe candidate ids 只能用于已经 true-RC verified negative journeys 的 admission scheduling；
- safe source 不能生成 official lower bound，不能成为 pricing oracle，不能参与 no-negative certificate；
- greedy-anchor 当前没有 high-ROI opportunity，因此 family fallback 合法，但后续若出现 greedy high-ROI opportunity，必须重新审计；
- opportunity mining 仍有 missed high-ROI：random-wave 2 个、sector-wave 3 个，下一轮应继续提高 candidate high-priority score，而不是降低 precision / ROI 门槛。

### 2026-06-16 v11 ROI-CI gate hardening 状态

v11 把上一段“训练必须考虑回报率和精准率”的合同进一步落到 trainer：

- `checkpoint_selection` 从旧的 `deployment_gate_first_then_utility_roi_loss` 改成
  `deployment_gate_first_then_roi_ci_baseline_utility_loss`；
- feasible checkpoint / threshold 的主排序先看 `accepted_batch_roi_ci_low`、
  `accepted_batch_roi_over_baseline_ci_low` 和三类 baseline margin，再看
  trajectory utility / loss；
- trainer 默认 high-priority / safe precision gate 提高到 `0.90`，CI lower bound
  可单独固定，例如 Stage 3/4 当前使用 `0.85`；
- metrics 增加 random / best-RC / old-GAT baseline margin 字段和 hard reject reason taxonomy。

v11 使用同一个 v10 dataset 重训，结果显示 ROI-CI gate 更保守：

```text
accepted_batch_count = 22
accepted_batch_roi = 13.7357
accepted_batch_roi_ci_low = 8.5162
accepted_batch_roi_over_baseline_ci_low = 8.0662
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9962
safe_precision = 1.0
safe_precision_ci_low = 0.8513
false_high_priority_on_delay = 0
false_safe_rate_union = 0
```

family holdout 变化：

```text
random-wave accepted_batch_count = 1
random-wave accepted_batch_roi = 1.1060
sector-wave accepted_batch_count = 21
sector-wave accepted_batch_roi = 14.3372
greedy-anchor accepted_batch_count = 0
greedy-anchor oracle_high_roi_count = 0
```

KNN/OOD (`k=3`, `max_neighbor_delay_fraction=0.34`) 后：

```text
accepted_batch_count = 21
accepted_batch_roi_ci_low = 8.3664
safe_precision = 1.0
safe_precision_ci_low = 0.8454
false_safe_rate_union = 0
validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']
```

因此 v11 的正确结论是：训练代码已经把 ROI / precision / CI gate 写硬，但
v11 本身只是 diagnostic，不应替代 v10 safe-source 进入 Stage 4。它暴露的新
优化方向是 Pareto-aware / coverage-aware checkpoint selection：在不降低
precision / ROI / false-safe 门槛的前提下，约束 random-wave / sector-wave
high-ROI opportunity capture，避免 ROI-CI 优先策略退化成过窄 safe shell。

### 2026-06-16 v12 coverage-aware selection 状态

v12 把 v11 暴露的 “ROI-CI 高但 coverage 过窄” 问题写进训练 gate。新增两个
默认关闭的显式约束：

```text
--min-family-accepted-high-roi-count
--min-family-high-roi-capture-rate
```

它们只作用于 offline threshold / checkpoint selection。默认值为 0，不改变旧
训练命令；显式启用后，任何存在 oracle high-ROI opportunity 的 family 如果
accepted high-ROI count 或 capture rate 不足，checkpoint 必须被拒绝。新增
hard reject reasons：

```text
family_accepted_high_roi_count_below_threshold
family_high_roi_capture_rate_below_threshold
```

v12 使用 v10 dataset，并设置：

```text
min_family_accepted_high_roi_count = 2
min_family_high_roi_capture_rate = 0.20
```

训练 local gate 结果：

```text
accepted_batch_count = 22
accepted_batch_roi = 13.9066
accepted_batch_roi_ci_low = 8.7552
safe_precision = 1.0
safe_precision_ci_low = 0.8513
false_safe_rate_union = 0.0
family_holdout_min_accepted_high_roi_count = 3
family_holdout_min_high_roi_capture_rate = 0.6
threshold_local_gate_pass = true
```

family capture：

```text
random-wave:
  oracle_high_roi_count = 5
  accepted_batch_count = 5
  accepted_high_roi_count = 3
  high_roi_capture_rate = 0.60

sector-wave:
  oracle_high_roi_count = 22
  accepted_batch_count = 17
  accepted_high_roi_count = 17
  high_roi_capture_rate = 0.7727

greedy-anchor:
  oracle_high_roi_count = 0
  family-specific delay fallback 合法
```

这比 v11 的 `random-wave accepted_batch_count = 1` 明显更符合 Stage 3 的
coverage-aware 目标。

第一轮 global kNN/OOD (`k=3`, `max_neighbor_delay_fraction=0.34`) 后：

```text
accepted_batch_count = 21
accepted_batch_roi = 13.9436
accepted_batch_roi_ci_low = 8.5413
safe_precision = 1.0
safe_precision_ci_low = 0.8454
false_safe_rate_union = 0.0
validation_candidate_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']
```

`max_neighbor_delay_fraction=0.35` 探测没有改变 accepted count 或 safe CI，因此
当前 blocker 不是单纯阈值边界，而是 kNN/OOD 后 accepted safe batch count 仍差
一个左右。随后使用已有的 `threshold_grouping=scale` 重新审计，结果通过：

```text
accepted_batch_count = 22
accepted_batch_roi = 13.9066
accepted_batch_roi_ci_low = 8.7552
safe_precision = 1.0
safe_precision_ci_low = 0.8513
false_safe_rate_union = 0.0
validation_candidate_ready = true
production_block_reasons = []
```

对比：

```text
global:       accepted=21, safe_ci=0.8454, candidate_ready=false
family:       accepted=6,  safe_ci=0.6097, candidate_ready=false
scale_family: accepted=6,  safe_ci=0.6097, candidate_ready=false
scale:        accepted=22, safe_ci=0.8513, candidate_ready=true
```

v12 scale safe-source export：

```text
BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/
safe_source_ready = true
safe_candidate_id_count = 142
high_priority_decision_record_count = 22
blockers = []
```

因此 v12 scale grouping 已经可以替代 v10 safe-source 进入 Stage 4 shadow /
guarded no-regression / coverage 审计，但仍不能声明 production-ready，也不能跳过
5/10 official no-regression、certificate audit、20-task shadow hit-rate 和 20-task
ROI A/B。后续 Stage 4 online coverage audit 已证明 v12 exact-id safe-source 在当前
20-task shadow 候选上仍无 exact 命中，见下文 v12 coverage audit 状态。

## 10. Stage 4: Testing

### 目标

先证明不退化，再证明有 ROI。该阶段才允许 shadow 和 opt-in online A/B，但默认仍关闭。

### 当前问题

- 当前已有 capture-only 5/10 no-regression，但没有 production online gate。
- 当前有单例 20-task positive smoke，但没有稳定 wall-time ROI。
- 当前 20-task smoke 多数仍 `TIME_LIMIT`，`dual_bound=None`。

### 应该修改的组件

- 增加 shadow-mode logging。
- 增加 opt-in GAT pricing priority。
- 增加 opt-in GAT admission scheduling。
- 增加 certificate mode delay queue safety checks。

### 不允许修改/不允许启用的组件

- 默认 benchmark 配置仍关闭新 gate / worker。
- certificate mode 不允许 GAT hard filter。
- delay queue 不参与 official certificate。
- exact proof budget 不因 delay queue 清空而扩展。

### 建议新增文件

- `BPC_future/tests/test_gat_target_mode_scheduler.py`
- `BPC_future/tests/test_gat_target_mode_certificate_safety.py`
- `BPC_future/scripts/run_gat_target_mode_shadow_ab.py`
- `BPC_future/scripts/audit_gat_target_mode_online_ab.py`

### 建议修改文件

- `BPC_future/solver/journey_driver.py`
  只增加 gated shadow / opt-in hooks。

- `BPC_future/pricing/journey_pricing.py`
  增加 priority ordering hooks 时必须保持 full fallback coverage。

- `BPC_future/scripts/run_bpc_future.py`
  仅接受 explicit config flags，不改变默认。

### 输入/输出 artifact

Unit tests：

- GAT scheduler 不会 reject true-RC negative。
- `DELAY_QUEUE` 语义正确。
- certificate mode 不允许 GAT hard filter。
- delay queue 不参与 official certificate。
- true-RC check 必须使用 `manual_journey_reduced_cost()`。
- GAT priority only changes ordering, not universe。

Offline validation metrics：

- `high_priority_precision`
- `high_priority_recall`
- `false_high_priority_on_delay`
- `predicted_high_priority_count`
- `OOD_delay_rate`
- family-level metrics for greedy-anchor / random-wave / sector-wave

Audit-only online shadow：

- GAT 打分但不改变 solver。
- 记录如果启用会 high-priority / delay 哪些列。
- 记录后续真实 RMP trajectory。
- 5/10 official result 必须完全一致。

Opt-in online A/B：

- baseline
- GAT admission only
- GAT pricing priority only
- GAT admission + pricing priority

记录：

- wall-time
- primal
- dual_bound
- gap
- RMP solves
- pricing calls
- exact pricing calls
- generated sequences
- evaluated timed trips
- `certificate_no_column_rounds`
- `final_judge_retry_count`
- `hidden_negative_count`
- active support movement
- basis turnover proxy

Certificate safety test：

- GAT 启用时仍由 exact pricing full scan 证明。
- exact pricing incomplete 时不能报告 official bound。
- delay queue 中存在当前 true-RC negative 时不能 certificate。

### 验收标准

- 5/10 official result exact match。
- 5/10 wall-time overhead 在约定阈值内，例如 avg <= 1%、max <= 5%，或完全 no-op。
- 20-task opt-in A/B 至少在 agreed hard-tail matrix 上有稳定 wall-time 或 tail retry ROI。
- no critical disagreement。
- `dual_bound` 只有 exact certificate closure 后出现。
- delay queue finite-delay audit 通过。

### 失败风险

- priority ordering 只改变列顺序但恶化 incumbent。
- admission delay 造成 useful column 太晚进入。
- delay queue 过大造成 memory/RMP 管理开销。
- GAT hook 在 5/10 产生固定开销。
- certificate mode 漏清当前 negative delayed columns。

### 进入下一阶段的 gate

- all unit tests pass。
- shadow mode 对 5/10 official result 0 regression。
- opt-in 20-task A/B 有 repeatable ROI。
- certificate safety audit 无 violation。
- 所有新增 flags 默认 false。

### 2026-06-16 v10 safe-source Stage 4 coverage audit 状态

v10 safe-source 已完成 guarded 5/10 full no-regression，但 20-task shadow hit gate
失败。最新 online coverage audit 使用：

```text
BPC_future/results/gat_batch_impact_safe_source_v10_random_wave_task50_5751_20260616/safe_source.json
BPC_future/results/gat_batch_impact_knn_ood_audit_v10_mixed_random_wave_task50_5751_knn34_20260616/decision_records.jsonl
BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/logs_sector_tranq20_01_shadow_fullsamples
```

诊断结论：

```text
safe_candidate_id_count = 408
online_sampled_candidate_journeys = 75
online_sample_coverage_complete = true

exact_safe_id_overlap_count = 0
route_no_start.overlap_key_count = 0
sequence.overlap_key_count = 0
task_set.overlap_key_count = 10
task_set.online_candidate_hit_count = 10
task_set.offline_conflict_key_count = 7
task_set.online_conflict_candidate_hit_count = 1
```

因此 v10 的失败不是 “20-task sector-wave 完全没有相似列族”，而是当前
safe-source 只导出 exact `JourneyColumn.signature` id，跨 seed / context /
timing 后在线 exact 命中为 0。更粗的 task-set key 虽然能覆盖 10/75 个 online
候选，但已经出现离线 delay 冲突，不能直接升级成 admission safe rule。

当前 Stage 4 判定：

```text
stage4_exact_safe_id_coverage_gate = failed
stage4_coarse_key_direct_admission_ready = false
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

下一步算法方向必须改成 context-aware / model-scored online safe-source：

- exact signature id 仍可作为最高置信白名单，但不能作为唯一 online coverage 机制；
- task-set / sequence / route-family 只能作为 candidate mining 或 pricing priority hint；
- 更宽 key 进入 `HIGH_PRIORITY` admission 前，必须重新经过 true-RC verified、
  precision / ROI / conflict / OOD gate；
- 不允许为了制造 hit-rate 直接把 task-set 白名单当成 safe-source。

### 2026-06-16 v12 scale safe-source Stage 4 coverage audit 状态

v12 scale safe-source 在 Stage 3 offline gate 上优于 v11，并修复了 random-wave
coverage 过窄问题；但用同一份 20-task sector-wave shadow full-samples 日志做
online coverage audit 后，exact-id coverage gate 仍失败。

输入：

```text
BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/safe_source.json
BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/decision_records.jsonl
BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/logs_sector_tranq20_01_shadow_fullsamples
```

诊断结论：

```text
safe_candidate_id_count = 142
online_sampled_candidate_journeys = 75
online_sample_coverage_complete = true

exact_safe_id_overlap_count = 0
route_no_start.overlap_key_count = 0
sequence.overlap_key_count = 0
task_set.overlap_key_count = 5
task_set.online_candidate_hit_count = 5
task_set.offline_conflict_key_count = 0
task_set.online_conflict_candidate_hit_count = 0
```

这 5 个 task-set 粗键命中的 online samples 都来自 `pricing_kind=exact`，且当前
true-RC 为负：

```text
[1,5]       rc = -19.76771125
[9,15,17]  rc = -5.350065
[4,15,17]  rc = -5.0754
[6,9]      rc = -1.397984
[9,17]     rc = -1.397984
```

这说明 v12 粗键能找到少量“真实负列族”，但仍缺少 trajectory ROI / tail-risk
证明；这些样本可进入下一轮 model-scored online safe-source audit，不能直接升级为
`HIGH_PRIORITY` admission rule。后续已完成该 audit，见下一小节。

v12 相比 v10 的变化是：task-set 粗键冲突降为 0，但 coverage 也只剩 5/75，
exact signature id 仍为 0。因此 v12 scale safe-source 仍不能作为 mutating
admission source：

```text
stage4_exact_safe_id_coverage_gate = failed
stage4_coarse_key_direct_admission_ready = false
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

当前结论不再是“换 v12 safe-source 就能进入 online admission”，而是：

- v12 offline training / kNN/OOD gate 可作为更干净的 diagnostic safe-source；
- exact-id 白名单跨 context/timing 泛化仍失败；
- task-set key 虽暂时无冲突，但覆盖率太低，且语义仍过粗；
- 下一步必须实现 context-aware / model-scored online safe-source 或在线模型打分审计，
  并保留 exact-id 作为最高置信辅助，而不是唯一 admission 机制。

### 2026-06-16 model-scored online safe-source audit 状态

基于上面 5 个 task-set 粗键命中，新增 audit-only model-scored online safe-source
审计。该审计仍只读 Stage 3 decision records 和 Stage 4 shadow 日志，不运行
BPC / pricing / RMP，不改变 admission，不产生 certificate。

审计逻辑：

- exact safe-id 仍是最高置信，但本轮命中为 0；
- route / sequence / task-set 只作为 coarse evidence；
- coarse evidence 必须无离线 delay conflict；
- coarse evidence 必须有 offline high-ROI / high-priority 记录；
- online family 和 task scale 必须与 offline evidence 兼容，避免把
  `random-wave:30` 证据迁移到 `sector-wave:20`；
- 即使通过以上过滤，也只能标记为 diagnostic priority hint，不允许 admission。

结果：

```text
online_sampled_candidate_journeys = 75
exact_safe_id_hit_count = 0
diagnostic_priority_hint_count = 2
diagnostic_priority_hint_by_key_level = {'task_set': 2}
diagnostic_priority_hint_by_pricing_kind = {'exact': 2}
admission_ready_count = 0
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
```

context-compatible 后只保留两个 `sector-wave:20` online exact-pricing true-RC
negative candidates：

```text
[1,5]       rc = -19.76771125
  offline evidence: sector-wave:20, high_roi_mean = 2.587969, batch_score_mean = 0.821297

[4,15,17]  rc = -5.0754
  offline evidence: sector-wave:20, high_roi_mean = 0.809451, batch_score_mean = 0.606470
```

三个被过滤掉的 task-set 粗键命中主要来自 cross-context evidence：

```text
[9,15,17], [6,9], [9,17]
offline evidence family/scale = random-wave:30
online family/scale = sector-wave:20
```

当前正确结论：

- context-aware 过滤能把 v12 粗键命中从 5 个压到 2 个更可信的 diagnostic hints；
- 这两个 hints 都是 exact pricing 返回的当前 true-RC negative；
- 但它们仍缺 online trajectory ROI / tail-risk 验证，因此 `admission_ready_count=0`；
- 下一步不是开启 mutating delay，而是围绕 `[1,5]` 和 `[4,15,17]` 做
  online trajectory ROI 采集或 target-materialization A/B，并把结果转成
  same-context positive / negative utility rows。

补充对齐已有 target-materialization A/B 后，训练标签必须更保守：

```text
[1,5]
  online true_rc = -19.76771125
  single target-materialization = returned 1 journey
  rmp/pricing/exact = 10/16/6 vs baseline 9/14/5
  generated/evaluated = 32443/53274 vs baseline 30378/48696
  training_label = hard_negative_or_delay

[4,15,17]
  online true_rc = -5.0754
  materialized inside batch5, not isolated positive
  batch5 rmp/pricing/exact = 9/14/5
  batch5 generated/evaluated = 30302/48610
  active_changed_task_set_count = 0
  training_label = weak_batch_signal_not_stage4_positive
```

这意味着 Stage 3 不能把模型打分高、offline high-ROI 或 true-RC negative
直接当作 `HIGH_PRIORITY` 正例。正例必须是 same-context 物化后能够证明
RMP trajectory / workload / tail-risk 改善的 batch；否则应进入 hard negative、
delay candidate 或 weak-signal bucket。`[1,5]` 已经是明确的 hard-negative
校准点，`[4,15,17]` 仍需要单独或 active-replacement-aware 归因，不能从
batch5 弱正信号中继承正标签。

训练 gate 已进一步收紧：`accepted_bad_mode_count` 默认必须为 0。理由是
sequential target-materialization 已经给出反例：active replacement / true-RC
negative 仍可能增加 RMP、pricing、exact 和 timed-trip workload。此类样本不能靠
`false_safe_rate_union` 的比例平均掉；只要 threshold 接受了 bad-mode batch，
checkpoint 就必须拒绝：

```text
max_accepted_bad_mode_count = 0
reject_reason = accepted_bad_mode_count_above_limit
hard_reject_category = accepted_bad_mode
```

当前 v12 scale decision records 已通过该补充 gate：

```text
accepted_bad_mode_audit =
  BPC_future/results/gat_accepted_bad_mode_gate_v12_scale_20260616/summary.json

decision_record_count = 102
high_priority_decision_count = 22
bad_mode_record_count = 8
accepted_bad_mode_count = 0
accepted_bad_mode_gate_pass = true
```

这只说明离线 Stage 3 safe-source 没有把已知 bad-mode batch 标成
`HIGH_PRIORITY`，不说明 online trajectory ROI 已通过，也不说明 Stage 4
mutating admission ready。

进一步复用已有 5/10 guarded full online logs 做 v12 scale safe-source coverage
审计后，exact safe-id 白名单在 5/10 online candidates 上仍为 0 命中：

```text
stage4_v12_scale_5_10_online_coverage_audit =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v12_scale_5_10_online_coverage_audit_zh.md

tasks5:
  online_sampled_candidate_journeys = 75
  exact_safe_id_overlap_count = 0
  task_set.online_candidate_hit_count = 9

tasks10:
  online_sampled_candidate_journeys = 254
  exact_safe_id_overlap_count = 0
  task_set.online_candidate_hit_count = 14
```

随后用同一批 5/10 logs 做 context-aware model-scored online safe-source
审计，修正 online log path 的 family/task 解析后，5/10 online candidates
被正确识别为 `balanced:5` / `balanced:10`。结果显示，粗键相似并不等于
同 context 可迁移：

```text
tasks5 model-scored:
  online_sampled_candidate_journeys = 75
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
  output =
    BPC_future/results/gat_model_scored_online_safe_source_v12_scale_tasks5_guarded_full_20260616/summary.json

tasks10 model-scored:
  online_sampled_candidate_journeys = 254
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
  output =
    BPC_future/results/gat_model_scored_online_safe_source_v12_scale_tasks10_guarded_full_20260616/summary.json
```

这一步很关键：5/10 的 task-set / sequence 粗键命中主要只是形状相似。
offline evidence 多来自 `sector-wave:20` 或更大 scale，而 online context 是
`balanced:5/10`，因此 `context_compatible=false`，不能把这些候选升级成
`HIGH_PRIORITY`。所以 v12 scale safe-source 若直接进入 5/10 guarded full
no-regression，预期仍是 `no_online_safe_hit` / pass-through，而不是产生真实
`HIGH_PRIORITY` ROI。

当前 Stage 4 判定：

```text
stage4_v12_scale_5_10_exact_safe_id_coverage_gate = failed
stage4_v12_scale_5_10_model_scored_context_gate = failed
stage4_v12_scale_5_10_mutating_admission_ready = false
stage4_v12_scale_5_10_high_priority_roi_ready = false
```

5/10 的正确用途是 no-regression / pass-through guard，不是用 v12 scale
证据做 mutating admission。当前 Stage 4 方向应继续在 20-task same-context
target-materialization / trajectory ROI 上采样，不要把 exact signature safe-id
或跨 context 粗键命中当成可用 online admission source。

### 2026-06-16 same-context target-materialization batch A/B 状态

基于 online shadow target candidates，已执行 20-task same-context target-materialization
A/B：

```text
shared_baseline:
  status = TIME_LIMIT
  primal = 632.987632
  dual_bound = None
  time = 53.477662
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30378/48696

single [1,5]:
  returned_journeys = 1
  true_rc = -19.76771125
  next_rmp_objective = 635.508935
  rmp/pricing/exact = 10/16/6
  generated/evaluated = 32443/53274

single [16,20]:
  returned_journeys = 1
  true_rc = -25.4432665
  next_rmp_objective = 655.276646
  rmp/pricing/exact = 10/16/6
  generated/evaluated = 32560/53368

batch5:
  returned_journeys = 5
  next_rmp_objective = 635.508935
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30302/48610

batch7:
  returned_journeys = 7
  next_rmp_objective = 635.508935
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30293/48612
```

关键发现：

- worker 能在 expected context 物化 true-RC negative columns；
- 单列 true-RC negative 会增加 RMP / pricing / exact 轮次，不能作为 ROI 正例；
- naive task-set overlap batch 只有弱 workload 降低，仍不足以通过 Stage 4 ROI gate；
- worker batch addition 的 `active_changed_task_set_count=0`，而 baseline 后续 exact batch
  的 `addition_productivity_class=active_replacement_task_set`，这才是 incumbent 变好的关键；
- 因此下一步不应继续扩大普通负列 batch，而应抽取并学习 active-support /
  replacement-aware batch impact。

当前判定：

```text
single_column_roi_gate = failed
naive_task_set_overlap_batch_roi_gate = weak_positive_but_insufficient
active_replacement_batch_needed = true
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

后续 Stage 3/4 的候选挖掘应优先使用 exact capture batch 中的
`active_changed_task_set_samples`、`replacement_task_set_samples` 和 basis movement
作为 target，而不是把 `rc < 0`、exact best-RC 或 task-set overlap 当成高质量标签。

### 2026-06-16 active-replacement sequential probe 状态

继续从 exact capture batch 中抽取可物化 active-replacement target 后，first-stage
只找到一个可直接物化的 active candidate：

```text
candidate = [15,20]
true_rc = -3.41733
expected_context_hash = ac056820151e9ad7
```

运行结果：

```text
shared_baseline:
  status = TIME_LIMIT
  primal = 632.987632
  time = 53.477662
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30378/48696
  columns = 236

active [15,20]:
  status = TIME_LIMIT
  primal = 632.987632
  time = 53.314711
  rmp/pricing/exact = 11/17/6
  generated/evaluated = 34828/58047
  columns = 271
  worker_addition_productivity_class = active_replacement_task_set
  next_rmp_objective = 653.567981
```

因此“单个 active replacement”也不是可靠 ROI 标签。它确实改变 active support，
但整体增加了后续 exact workload。随后新的 exact context 中又出现第二阶段
active-replacement candidate：

```text
candidate = [1,9]
true_rc = -1.397984
expected_context_hash = 7b430465c7ae76b3
```

当前 Stage 4 判定进一步收紧：

```text
single_active_replacement_roi_gate = failed
sequential_active_replacement_policy_needed = true
multi_context_target_materialization_needed = true
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

后续如果实现 default-off 多 context target-materialization，必须保持：

- 每个 context 的物化列都用当前 true dual / cut / branch 做 true-RC；
- worker 不能产生 certificate；
- exact fallback 仍覆盖完整配置宇宙；
- 训练标签必须是 sequential trajectory utility，而不是单列 active/replacement proxy。

### 2026-06-16 multi-context sequential target-materialization 状态

已实现并实测 default-off 多 context target-materialization worker。新配置：

```text
journey_sharded_pulse_hidden_negative_worker_target_materialization_contexts
```

允许在同一次 run 中表达：

```text
context ac056820151e9ad7 -> materialize [15,20]
context 7b430465c7ae76b3 -> materialize [1,9]
```

旧的单 `expected_context_hash` 配置仍优先，旧 runbook / 单 context 行为保持兼容。
多 context 命中后只是把当前 context 的 target payload 映射成旧式单 context
target-materialization config；进入 RMP 前仍由 `materialize_pulse_leaf_candidate()`
和当前 true dual / cut 做 true-RC 验证。

实测结果：

```text
both_expected_contexts_hit = true
cg7 [15,20] true_rc = -3.417330
cg9 [1,9] true_rc = -1.397984
worker_certificate_violations = 0
```

但 sequential active-replacement 仍未通过 ROI gate：

```text
baseline:
  status = TIME_LIMIT
  primal = 632.987632
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30378/48696
  columns = 236

active [15,20]:
  status = TIME_LIMIT
  primal = 632.987632
  rmp/pricing/exact = 11/17/6
  generated/evaluated = 34828/58047
  columns = 271

sequential [15,20] -> [1,9]:
  status = TIME_LIMIT
  primal = 632.987632
  rmp/pricing/exact = 14/22/8
  generated/evaluated = 41484/72055
  columns = 262
```

当前 Stage 4 判定：

```text
multi_context_target_materialization_correctness = passed
sequential_active_replacement_roi_gate = failed
stage4_20_mutating_opt_in_ready = false
stage5_ready = false
```

因此下一步不能继续把 active replacement movement 本身当成 positive label。
训练标签必须继续升级为 longer-horizon sequential trajectory utility，并显式惩罚
RMP / pricing / exact 轮次和 generated/evaluated workload 上升。

### 2026-06-16 sequential utility hard-negative rows 状态

已把上面的 sequential target-materialization 失败 run 转成 training hard-negative
utility rows。新增 artifact：

```text
BPC_future/results/gat_sequential_target_materialization_utility_rows_tranq20_01_20260616/
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_sequential_utility_rows_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_sequential_utility_dataset_probe_zh.md
```

标签口径已经从 “即时 objective / active replacement movement” 收紧为
longer-horizon workload-aware utility：

```text
accepted_batch_roi_label = -4.1412
rmp_solves_delta = +5
pricing_calls_delta = +8
exact_pricing_calls_delta = +3
generated_sequences_delta = +11106
evaluated_timed_trips_delta = +23359
positive_utility_row_count = 0
negative_utility_row_count = 2
bad_mode_row_count = 2
```

对应 dataset probe 结论：

```text
sample_count = 2
candidate_label_counts = {'delay_queue': 2}
batch_label_counts = {'non_improving': 2}
training_ready = false
production_ready = false
all_checks_pass = true
```

这说明训练阶段必须把 ROI / precision / workload 目标写进标签和 checkpoint
选择本身，而不是在训练结束后只做报告。即使 candidate 是 true-RC negative，
只要 sequential trajectory utility 为负、RMP / pricing / exact workload 变重、
或被标记为 bad-mode，就必须成为 `DELAY_QUEUE` / hard negative；不得因为
`label_objective_improved=1`、active support changed 或 replacement count > 0
而进入 `HIGH_PRIORITY`。

当前 hard-negative rows 只证明“这个 sequential active-replacement policy 应延迟”，
不能直接训练 production model：样本仍是单实例/单 family，且没有 same-context
positive/negative pair。下一步 Stage 3 数据采集必须补齐同 context 下的 high-ROI
positive batch、random / best-RC baseline batch 和 family/context holdout，再按
`precision-constrained ROI maximization` 选择 checkpoint。

### 2026-06-16 v13 sequential bad-mode refresh 状态

已把 sequential utility hard-negative rows 并入 v10 mixed dataset，形成 v13
hard-negative refresh：

```text
dataset =
  BPC_future/data/gat_batch_impact/v13_mixed_v10_plus_sequential_badmode_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v13_sequential_badmode_zh.md

sample_count = 326          # v10: 324
candidate_count = 4601      # v10: 4599
non_improving_batches = 69  # v10: 67
delay_candidates = 324      # v10: 322
sector_wave_samples = 75    # v10: 73
same_context_comparable_pair_count = 67
positive_negative_label_pair_count = 12
ranking_ready = true
training_ready = true
```

v13 训练继续使用 Stage 3 硬目标：

```text
training =
  BPC_future/results/gat_batch_impact_training_v13_sequential_badmode_20260616/metrics.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_sequential_badmode_training_zh.md

primary_objective = precision_constrained_roi_maximization
accepted_bad_mode_count = 0
max_accepted_bad_mode_count = 0
validation high_priority_precision = 1.0
validation safe_precision = 1.0
validation accepted_batch_roi = 12.850568531589074
validation accepted_batch_roi_ci_low = 7.4080270953516765
stage4_candidate_ready = false
```

v13 的正确结论不是“hard-negative refresh 已可进入 Stage 4”，而是：

```text
checkpoint_gate_pass = false
best_loss_epoch_gate_pass = false
reject_reasons =
  family_accepted_high_roi_count_below_threshold
  family_high_roi_capture_rate_below_threshold
  knn_ood_audit_missing
```

threshold frontier 和 opportunity mining 已补充证明：没有任何 feasible threshold，
主要 blocker 是 family high-ROI capture，尤其 random-wave holdout：

```text
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v13_sequential_badmode_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v13_sequential_badmode_20260616/summary.json

feasible_threshold_count = 0
best accepted_batch_count = 29
best safe_precision_ci_low = 0.8830264055344442
best accepted_batch_roi_ci_low = 5.286264888364512
best local reject =
  family_accepted_high_roi_count_below_threshold
  family_high_roi_capture_rate_below_threshold

validation high_roi_opportunities = 27
accepted_high_roi_opportunities = 18
missed_high_roi_opportunities = 9
random_wave missed_high_roi_opportunities = 4 / 5
sector_wave missed_high_roi_opportunities = 5 / 22
primary_missed_reason = no_candidate_above_threshold
```

随后尝试过一个 candidate-score boost 变体：

```text
training =
  BPC_future/results/gat_batch_impact_training_v13_candidate_boost_20260616/metrics.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_candidate_boost_training_zh.md

hard_roi_candidate_loss_multiplier = 2.0
pairwise_ranking_loss_multiplier = 2.0
bad_mode_loss_multiplier = 4.0
validation accepted_bad_mode_count = 0
validation accepted_batch_count = 28
validation accepted_batch_roi = 10.4123928632055
random_wave accepted_high_roi_count = 1 / 5
stage4_candidate_ready = false
```

该 boost 变体没有解决 random-wave coverage，且 train split 出现
`false_high_priority_on_delay_too_high` / `false_safe_rate_union_too_high` 风险。
因此这轮结论是：不能靠简单增大 hard-ROI candidate loss 或 pairwise loss 过关；
下一步应补 random-wave same-context high-ROI positive/negative pairs，或改进
candidate-level scoring/head 结构，使 high-ROI batch 内的 safe candidate score
能稳定高于 threshold，同时继续保持 `accepted_bad_mode_count=0`。

### 2026-06-16 candidate head context/batch audit 状态

对 v13 missed high-ROI blocker 做模型结构复核后，确认当前
`GATBatchImpactModel` 的 candidate-level priority head 已经接入 batch/context：

```text
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_context_batch_head_audit_zh.md

candidate_decision_dim =
  candidate_hidden_dim + batch_hidden_dim + context_hidden_dim

candidate_decision_input =
  concat(candidate_embedding, batch_embedding, context_embedding)

new_test =
  BPC_future.tests.test_gat_batch_impact_model.
  test_candidate_priority_head_depends_on_context_and_batch
```

该测试固定 graph、candidate membership、sequence positions 和 candidate features，
分别只改变 `context_features` 或 `batch_features`，要求 `high_priority_logit`
随之变化；同时检查 `high_priority_head` 输入维度确实包含 candidate、batch、
context 三段。

因此 v13 的 `primary_missed_reason = no_candidate_above_threshold` 不能归因于
candidate head 完全看不到 RMP/batch context。当前更合理的下一步是：

```text
primary_next_action =
  candidate score margin audit on missed high-ROI rows
  + random-wave same-context high-ROI positive/negative rows

do_not_repeat_as_primary_fix =
  merely reconnect context/batch to candidate head
  merely increase hard-ROI / pairwise loss multipliers
```

随后已用 opportunity mining 的 validation records 做 candidate score margin audit：

```text
script =
  BPC_future/scripts/audit_gat_batch_impact_score_margins.py
output =
  BPC_future/results/gat_batch_impact_score_margin_audit_v13_sequential_badmode_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v13_sequential_badmode_zh.md

missed_high_roi_opportunities = 9
missed_candidate_score_margin_mean = -0.29302062425348496
missed_candidate_score_margin_min = -0.46770481765270233
candidate_margin_buckets =
  deep_candidate_score_gap: 6
  moderate_candidate_score_gap: 2
  near_candidate_threshold: 1
missed_without_same_context_contrast_count = 4
```

该审计把下一步进一步收窄：不是主要靠调低 candidate threshold 或加大 loss 权重。
9 个 missed high-ROI 里只有 1 个接近阈值，6 个是 deep score gap；random-wave
的 4 个 missed 全部来自 task50，覆盖 context：

```text
random-wave missed contexts =
  5751b1799b606ad1
  a67f331bdb819d7d
  e6b17bbf825984ae

random-wave missed_candidate_score_margin_mean = -0.3019028417766094
random-wave missed_without_same_context_contrast_count = 2
```

因此下一轮 Stage 3 数据采集应优先补 `a67f331bdb819d7d`、
`e6b17bbf825984ae` 的 same-context positive/negative rows，并继续补
`5751b1799b606ad1` 的 hard margin pair；训练 gate 继续保持
`precision_constrained_roi_maximization`、`accepted_bad_mode_count=0` 和
family high-ROI capture hard gate。

已进一步把 random-wave task50 的 margin blocker 转成 guarded
target-materialization worklist：

```text
intervention_plan =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/summary.json
plan_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_random_wave_task50_margin_intervention_plan_zh.md
worker_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook/summary.json

planned_context_count = 3
selected_context_count = 2
pairwise_context_target_count = 2
candidate_count = 6
candidate_task_count_counts = {50: 6}
candidate_family_region_counts =
  random-wave|tranquillitatis_balmer_like_20km: 6
candidate_impact_bucket_counts =
  new_support_changing: 4
  new_task_set: 2
candidate_selection_ranking_counts =
  active_replacement: 2
  best_rc: 2
  impact: 2
skipped_counts =
  not_enough_unique_negative_targets: 1
worker_method = target_materialization_fixed
worker_batch_size = 1
all_checks_pass = true
```

这一步只生成同 context worker A/B runbook，不运行 BPC / pricing / RMP，也不产生
official bound 或 certificate。`5751b1799b606ad1` 与 `a67f331bdb819d7d`
已各选出 3 个 true-RC negative target-materialization 候选；`e6b17bbf825984ae`
因为当前 capture 下只有 1 个 unique negative target，暂不能构造同 context
positive/negative pair，必须先补 capture/harvest 样本，再进下一轮 worklist。

因此当前 Stage 3 训练证据的顺序是：

1. 先显式跑该 runbook 的 baseline / target worker A/B；
2. 再用 worker reachability、expected-context match、RMP trajectory、tail retry 和
   low-ROI/delay 结果生成 same-context rows；
3. 最后才允许把这些 rows 并入下一版 `precision_constrained_roi_maximization`
   训练。

worker 结果出来前，6 个候选都不能作为 positive label；跑出低 ROI 或 bad-mode
的 true-RC negative 必须进入 `DELAY_QUEUE` / hard-negative 监督，而不是因为
`rc < 0` 被强行标成 `HIGH_PRIORITY`。

### 2026-06-16 v14 random-wave task50 margin refresh 状态

已按上面的 worklist 对 `5751b1799b606ad1` 做了 guarded target-materialization
follow-up。原 85s worker A/B 虽然 CSV primal 改善，但因为 worker hit 发生在
time-limit 末尾，缺少 post-worker `journey_rmp`，严格 row builder 拒绝输出训练
row：

```text
85s worker =
  primal 1387.386078 vs baseline 1404.72385
  row_builder_status = no_rows
  skipped_counts = {'missing_worker_before_or_after_rmp': 1, 'missing_worker_logs': 5}
```

随后将同 context 的前两个 target worker 延长到 130s，只用于观察 post-worker
RMP trajectory，不改变 certificate 语义：

```text
tl130_worker_rows =
  BPC_future/results/gat_multibatch_worker_rows_v13_random_wave_task50_margin_tl130_20260616/summary.json
tl130_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v14_random_wave_task50_margin_tl130_refresh_zh.md

candidate_count = 2
row_count = 2
context_count = 1
pairwise_context_count = 1
all_checks_pass = true
```

两条 row 同属 `5751b1799b606ad1` / `cg_iter=44`：

```text
[4,40,3]:
  true_rc = -11.539468769
  rmp_objective 1349.923664 -> 1345.538039
  objective_improvement = 4.385625

[4,8,25,32,45,9]:
  true_rc = -2.633324538
  rmp_objective 1349.923664 -> 1349.898806
  objective_improvement = 0.024858
```

这说明该 context 下存在强/弱 ROI 的 true-RC negative 对照；训练目标必须学
`score(strong ROI) > score(weak ROI)`，不能把两个都因 `rc < 0` 视为等价正例。

追加这 2 条 row 后生成 v14 dataset：

```text
dataset =
  BPC_future/data/gat_batch_impact/v14_mixed_v13_plus_random_wave_task50_margin_tl130_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v14_random_wave_task50_margin_tl130_zh.md

sample_count = 328        # v13: 326
candidate_count = 4603    # v13: 4601
random_wave_samples = 199 # v13: 197
task50_samples = 95       # v13: 93
same_context_pair_count = 79
same_context_comparable_pair_count = 76
task50_same_context_pair_count = 21
training_ready = true
ranking_ready = true
```

v14 training 使用同一套 `precision_constrained_roi_maximization` 和 hard family
capture gate：

```text
training =
  BPC_future/results/gat_batch_impact_training_v14_random_wave_task50_margin_tl130_20260616/metrics.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v14_random_wave_task50_margin_tl130_training_zh.md

checkpoint_gate_pass = false
stage4_candidate_ready = false
best_epoch = 7
accepted_batch_count = 34
accepted_batch_roi = 9.270531552487656
accepted_batch_roi_ci_low = 5.325235030723549
high_priority_precision = 0.9980601357904947
high_priority_precision_ci_low = 0.9929545460660191
safe_precision = 1.0
safe_precision_ci_low = 0.8984820937803899
accepted_bad_mode_count = 0
```

v14 的正向结果是 family capture blocker 被明显改善：

```text
random-wave accepted_high_roi_count = 4 / 6  # v13: 1 / 5
random-wave high_roi_capture_rate = 0.6666666666666666
random-wave accepted_batch_roi = 1.4432105637388304
sector-wave accepted_high_roi_count = 19 / 22
```

但 v14 仍不能进入 Stage 4，因为主 blocker 已转移到 safety：

```text
false_high_priority_on_delay = 0.02531645569620253
false_high_priority_on_delay_count = 2
delay_label_count = 79
false_safe_rate_union = 0.02531645569620253
reject_reasons =
  false_high_priority_on_delay_too_high
  false_safe_rate_union_too_high
  knn_ood_audit_missing
```

因此下一步不应降低 safety gate 来凑 Stage 4 candidate，也不应继续只增加
accepted coverage。正确顺序是：

1. 对 v14 做 threshold / safety frontier，寻找 `false_safe_rate_union <= 1%~2%`
   且 random-wave high-ROI capture 仍过线的 frozen threshold；
2. 对 v14 做 kNN/OOD audit，检查能否过滤这 2 个 false HIGH_PRIORITY；
3. 若无 feasible safety shell，则回到 Stage 2/3 补这两个 false-safe context 的
   same-context hard-negative / delay rows；
4. 继续补 `a67f331bdb819d7d` 和 `e6b17bbf825984ae`，但不能牺牲
   `accepted_bad_mode_count=0`、false-safe 和 precision gate。

### 2026-06-16 v14 safety frontier / kNN-OOD / safe-source 状态

已按上面的顺序完成 v14 safety frontier：

```text
summary_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v14_safety_frontier_zh.md
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v14_random_wave_task50_margin_tl130_20260616/summary.json
```

threshold-only 仍没有 feasible gate：

```text
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0

best_global:
  accepted_batch_count = 35
  accepted_batch_roi_ci_low = 5.2559083249600445
  safe_precision_ci_low = 0.9010957324106112
  false_safe_rate_union = 0.3924050632911392

best_family_local:
  accepted_batch_count = 20
  accepted_batch_roi_ci_low = 6.838762183273009
  safe_precision_ci_low = 0.8388698745050667
  false_safe_rate_union = 0.0
```

这说明 raw threshold 不能解决 v14 safety：保留 ROI / coverage 会产生过高
false-safe；严格到 zero false-safe 又会丢掉 safe precision CI 和 family capture。

随后用 strict kNN/OOD shell 审计四种 grouping：

```text
knn_k = 3
max_neighbor_delay_fraction = 0.0
safe_radius_quantile = 1.0
safe_radius_multiplier = 1.0
```

结果：

```text
global:
  validation_candidate_ready = true
  accepted_batch_count = 25
  accepted_batch_roi = 8.059135420061647
  accepted_batch_roi_ci_low = 3.1138153528317707
  safe_precision_ci_low = 0.8668035060468212
  false_safe_rate_union = 0.0

scale:
  validation_candidate_ready = true
  accepted_batch_count = 23
  accepted_batch_roi = 7.057523978509657
  accepted_batch_roi_ci_low = 2.1087118375497003
  safe_precision_ci_low = 0.8568788745827373
  false_safe_rate_union = 0.0

family / scale_family:
  validation_candidate_ready = false
  accepted_batch_count = 14
  accepted_batch_roi_ci_low = 0.32354690958853094
  safe_precision_ci_low = 0.7846829880728186
```

因此 v14 的正确状态从 “training blocked by safety” 推进为：

```text
raw_training_gate_pass = false
knn_ood_repaired_raw_safety_blocker = true
global_safe_source_ready = true
scale_safe_source_ready = true
production_ready = false
stage4_mutating_admission_ready = false
```

为支持这个状态，`export_gat_batch_impact_safe_source.py` 的 gate 已收紧为：
raw training gate 通过，或 training reject reason 全部属于 kNN/OOD 可修复的
raw safety blocker 且 kNN/OOD validation candidate/safety 全部通过。允许被
kNN/OOD 修复的 training reject reason 仅有：

```text
false_high_priority_on_delay_too_high
false_safe_rate_union_too_high
knn_ood_audit_missing
```

ROI、ROI-CI、coverage、family capture、precision CI 等失败不能被 kNN/OOD
绕过。v14 global / scale safe-source export 结果：

```text
global_safe_source =
  BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_global_20260616/safe_source.json
  safe_source_ready = true
  safe_candidate_id_count = 1226
  high_priority_decision_record_count = 59
  blockers = []

scale_safe_source =
  BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616/safe_source.json
  safe_source_ready = true
  safe_candidate_id_count = 1198
  high_priority_decision_record_count = 56
  blockers = []
```

该结论仍然只是 Stage 3 offline safe-source candidate，不是 production-ready。
Stage 4 online coverage audit 已在下一节记录；审计前提保持不变：先检查
v14 global/scale safe-source 在 5/10/20 online shadow candidates 上的 exact-id /
context-compatible hit-rate，再做 model-scored online safe-source，不允许直接启用
mutating delay。

### 2026-06-16 v14 safe-source Stage 4 online coverage 状态

已复用 v10 guarded full 5/10 logs 和 20-task
`sector_tranq20_01` full-sample shadow logs，对 v14 global / scale safe-source
完成 online coverage audit：

```text
summary_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_online_coverage_audit_zh.md

global summaries =
  BPC_future/results/gat_safe_source_online_coverage_v14_global_tasks5_guarded_full_20260616/summary.json
  BPC_future/results/gat_safe_source_online_coverage_v14_global_tasks10_guarded_full_20260616/summary.json
  BPC_future/results/gat_safe_source_online_coverage_v14_global_tranq20_01_20260616/summary.json

scale summaries =
  BPC_future/results/gat_safe_source_online_coverage_v14_scale_tasks5_guarded_full_20260616/summary.json
  BPC_future/results/gat_safe_source_online_coverage_v14_scale_tasks10_guarded_full_20260616/summary.json
  BPC_future/results/gat_safe_source_online_coverage_v14_scale_tranq20_01_20260616/summary.json
```

5/10 exact safe-id coverage gate 仍失败：

```text
global tasks5:
  online_sampled_candidate_journeys = 75
  exact_safe_id_overlap_count = 0
  task_set_online_hit_count = 41
  task_set_conflict_candidate_hit_count = 20

global tasks10:
  online_sampled_candidate_journeys = 254
  exact_safe_id_overlap_count = 0
  sequence_online_hit_count = 3
  task_set_online_hit_count = 84
  task_set_conflict_candidate_hit_count = 12

scale tasks5 / tasks10:
  exact_safe_id_overlap_count = 0
  coarse overlap profile matches global
```

这说明 5/10 不能靠 task-set 粗键 admission。粗键 overlap 覆盖了若干
true-RC negative，但 conflict 明显，且没有 trajectory ROI 证明。

20-task `sector_tranq20_01` full-sample shadow 出现新的正向覆盖信号：

```text
global tasks20:
  online_declared_candidate_journeys = 75
  online_sampled_candidate_journeys = 75
  online_sample_coverage_complete = true
  exact_safe_id_overlap_count = 32
  exact_safe_id_overlap_rate_online = 0.4266666666666667
  route_no_start_online_hit_count = 32
  sequence_online_hit_count = 32

scale tasks20:
  online_declared_candidate_journeys = 75
  online_sampled_candidate_journeys = 75
  online_sample_coverage_complete = true
  exact_safe_id_overlap_count = 32
  exact_safe_id_overlap_rate_online = 0.4266666666666667
  route_no_start_online_hit_count = 32
  sequence_online_hit_count = 32
```

随后对六个组合做 model-scored online safe-source audit：

```text
tasks5 global/scale:
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0

tasks10 global/scale:
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0

tasks20 global/scale:
  exact_safe_id_hit_count = 32
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
```

因此 v14 Stage 4 状态不是“可以 online admission”，而是：

```text
stage4_v14_5_10_exact_safe_id_coverage_gate = failed
stage4_v14_20_sector_tranq20_exact_safe_id_coverage_gate = passed_for_this_shadow_only
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
```

20-task 的 blocker 已从 “exact id 完全打不到 online” 缩小为：

```text
exact_safe_id_overlap_is_not_trajectory_roi_proof
online_trajectory_roi_unverified
```

也就是说，v14 已经能在一个 20-task same-context shadow 中识别 32 个当前
true-RC negative journey，但还没有证明把这些列提前加入 RMP 后会改善 objective、
dual、basis、tail retry 或 final proof tail。下一步应只对这 32 个 exact-id hit
做 target-materialization / online A/B 采样，生成 trajectory utility label；
不能把 exact-id coverage、true-RC negative 或 task-set overlap 当成直接准入证据。

### 2026-06-16 v14 exact safe-hit target-materialization runbook 状态

已将 20-task `sector_tranq20_01` 的 32 个 exact safe-id hit 从 counterfactual
replay capture log 中导出为 target-materialization worker 可消费的候选：

```text
global_candidates =
  BPC_future/results/gat_exact_safe_hit_target_candidates_v14_global_tranq20_01_20260616/candidates.json
  BPC_future/results/gat_exact_safe_hit_target_candidates_v14_global_tranq20_01_20260616/summary.json

scale_candidates =
  BPC_future/results/gat_exact_safe_hit_target_candidates_v14_scale_tranq20_01_20260616/candidates.json
  BPC_future/results/gat_exact_safe_hit_target_candidates_v14_scale_tranq20_01_20260616/summary.json
```

global / scale 导出的 32 个候选完全一致：

```text
capture_exact_safe_hit_count = 32
selected_candidate_count = 32
selected_context_counts = {'ac056820151e9ad7': 32}
selected_pricing_kind_counts = {'exact': 32}
selected_true_reduced_cost_min = -25.4432665
selected_true_reduced_cost_max = -2.095736
all_checks_pass = true
```

每个候选均带完整 materialization 所需字段：

```text
expected_context_hash
true_dual_hash
cut_hash
branch_hash
forbidden_signature_hash
active_hash_before
pool_signature_hash
pool_task_set_hash
target_sortie_traces
```

随后用 global candidates 生成 batch8 target-materialization A/B runbook：

```text
runbook =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_runbook_zh.md

input_candidate_count = 32
worker_batch_size = 8
candidate_group_count = 4
candidate_batch_counts = [8, 8, 8, 8]
command_count = 10
all_checks_pass = true
```

该 runbook 只是下一轮采样入口：

```text
stage4_mutating_admission_ready = false
production_ready = false
certificate_ready = false
official_bound_effect = false
```

注意：本轮修复了 `build_gat_target_priority_worker_ab_runbook.py` 的 batch
分组截断问题。旧逻辑在同一 context 下 `worker_batch_size > 1` 时只保留第一组
候选；现在按 `(instance, expected_context_hash)` 分桶后连续切片，保证 32 个
exact safe-id hit 全部进入 runbook。新增测试覆盖 5 个同 context 候选、
`worker_batch_size=2` 时必须生成 `[2, 2, 1]` 三组。

### 2026-06-16 v14 exact safe-hit batch8 A/B 执行结果

已执行上述 runbook 的全部 10 条命令：

```text
execution_log =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/runbook_execution_log.jsonl
failed_command_count = 0
```

新增综合报告：

```text
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_ab_results_zh.md
```

5/10 no-regression 通过，4 个小规模实例均为 `OPTIMAL`：

```text
tasks5:
  apollo15 sector-wave 01: primal=dual=284.084294
  tranquillitatis sector-wave 01: primal=dual=179.982081
tasks10:
  apollo15 sector-wave 01: primal=dual=456.756326
  tranquillitatis sector-wave 01: primal=dual=330.363821
```

20-task batch8 A/B 没有 positive trajectory ROI：

```text
audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_audit_20260616/summary.json
audit_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_ab_audit_zh.md

record_count = 4
positive_trajectory_roi_count = 0
nonpositive_roi_count = 4
roi_class_counts = {'negative_retry_roi': 3, 'no_observed_roi': 1}
all_checks_pass = false
```

四组 `sector_tranq20_01` worker runs 均为 `TIME_LIMIT`，均无 official dual bound。
worker primal 与 baseline 相同 `632.987632`；r08/r16/r24 还分别增加
pricing/exact/RMP workload：

```text
r00 tasks16_20:
  roi_class = no_observed_roi
  time_delta = -0.067634
  rmp/pricing/exact_delta = 0/0/0

r08 tasks3_6_11:
  roi_class = negative_retry_roi
  time_delta = +0.285552
  rmp/pricing/exact_delta = +1/+2/+1

r16 tasks1_15:
  roi_class = negative_retry_roi
  time_delta = +0.518375
  rmp/pricing/exact_delta = +2/+3/+1

r24 tasks7_15_17:
  roi_class = negative_retry_roi
  time_delta = +0.173593
  rmp/pricing/exact_delta = +1/+2/+1
```

certificate audit 通过：

```text
certificate_audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_certificate_audit_20260616/summary.json
certificate_audit_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_certificate_audit_zh.md

all_checks_pass = true
violation_count = 0
global_certificate_pricing_events = 6
```

因此本轮判定为：

```text
stage4_v14_exact_safe_hit_batch8_roi_gate = failed
stage4_mutating_admission_ready = false
production_ready = false
certificate_ready = false
default_enabled = false
```

关键解释：exact safe-id hit 只能说明 GAT safe-source 能定位一批当前 true-RC
negative journey；它不能证明提前 admission 会改善 RMP trajectory。r00/r16/r24
都有局部 RMP objective 下降，但最终没有减少 tail retry；r08 甚至完全不改善
objective 并增加 retry。因此训练标签不能用 `rc < 0`、exact-id hit、task-set
overlap 或即时 objective delta 直接替代。下一轮必须继续采集 same-context
strong/weak/negative ROI 对照，并用 longer-horizon sequential trajectory utility
训练 admission scheduler。

### 2026-06-16 v15 exact safe-hit batch8 hard-negative 回流状态

根据 v14 batch8 A/B 的新证据，已把 Stage 4 的真实 trajectory ROI 结果回流到
Stage 3。新增报告：

```text
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_exact_safe_hits_batch8_ab_roi_refresh_zh.md
```

本轮修改了两个离线数据脚本：

```text
BPC_future/scripts/build_gat_multibatch_worker_batch_impact_rows.py
BPC_future/scripts/build_gat_batch_impact_dataset.py
```

核心语义变化：

- `build_gat_multibatch_worker_batch_impact_rows.py` 支持 `--ab-audit-summary`；
- 如果提供 A/B audit，最终 trajectory ROI 覆盖即时 RMP objective label；
- row 写入 `target_signature_samples`，dataset builder 按 signature samples
  保留整批 worker 返回候选，避免 batch8 退化为单列标签；
- true-RC negative 但 final A/B 非正 ROI 的候选进入 `DELAY_QUEUE` 标签，
  不能再被即时 objective 下降误标为 `HIGH_PRIORITY`。

v15 hard-negative rows：

```text
rows_summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v14_exact_safe_hits_batch8_ab_roi_20260616/summary.json

row_count = 4
positive_objective_improvement_count = 3
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
roi_class_counts = {'negative_retry_roi': 3, 'no_observed_roi': 1}
signature_sample_row_count = 4
all_checks_pass = true
```

v15 dataset 在 v14 基础上追加这 4 个 batch8 hard-negative rows：

```text
dataset =
  BPC_future/data/gat_batch_impact/v15_mixed_v14_plus_exact_safe_hits_batch8_ab_roi_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v15_exact_safe_hits_batch8_ab_roi_zh.md

sample_count = 332
candidate_count = 4635
batch_label_counts = {'non_improving': 73, 'roi_positive': 259}
candidate_label_counts = {'delay_queue': 356, 'high_priority': 4279}
same_context_pair_count = 93
same_context_comparable_pair_count = 90
positive_negative_label_pair_count = 16
training_ready = true
ranking_ready = true
```

v15 training 结果：

```text
training =
  BPC_future/results/gat_batch_impact_training_v15_exact_safe_hits_batch8_ab_roi_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_exact_safe_hits_batch8_ab_roi_training_zh.md

checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 13
accepted_batch_roi = 16.316478240948456
accepted_batch_roi_ci_low = 8.0292472538527
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
safe_precision = 1.0
safe_precision_ci_low = 0.7718981569447084
```

相对 v14，v15 消除了 false-safe：

```text
v14 false_safe_rate_union = 0.02531645569620253
v15 false_safe_rate_union = 0.0
```

但 v15 accepted batch count 从 34 降到 13，导致 safe precision CI lower bound
不过硬门槛。threshold frontier 和 strict global/scale kNN-OOD 都确认了同一 blocker：

```text
frontier_primary_blocker =
  confidence_lower_bound_sample_size_or_acceptance_count_blocker

global_knn_ood:
  accepted_batch_count = 10
  safe_precision_ci_low = 0.7224598312333834
  validation_safety_ready = false

scale_knn_ood:
  accepted_batch_count = 10
  safe_precision_ci_low = 0.7224598312333834
  validation_safety_ready = false
```

因此 v15 的判定是：

```text
v15_hard_negative_refresh_direction = correct
v15_stage4_candidate_ready = false
v15_safe_source_export_ready = false
production_ready = false
default_enabled = false
```

下一步不能降低 precision / ROI / CI 门槛。应补 same-context high-ROI positives，
尤其是 `sector_tranq20_01` 与 random-wave / sector-wave missed high-ROI contexts，
目标是把 accepted all-success count 提到足以支撑 CI lower bound 的区间，同时保留
batch8 hard-negative 的 delay 标签。

v15 后续 opportunity mining / score-margin audit 已确认 blocker 不是 batch score
差一点，而是 candidate head 对 high-ROI batch 内 safe candidate 的分数结构性偏低：

```text
opportunity_mining_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_opportunity_mining_v15_exact_safe_hits_batch8_ab_roi_zh.md
score_margin_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v15_exact_safe_hits_batch8_ab_roi_zh.md

validation_record_count = 110
high_roi_opportunities = 28
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
missed_reason_counts = {'no_candidate_above_threshold': 16}
candidate_margin_bucket_counts = {'deep_candidate_score_gap': 11, 'moderate_candidate_score_gap': 5}
missed_candidate_score_margin_mean = -0.3829170756507665
missed_candidate_score_margin_min = -0.8569196499884129
missed_without_same_context_contrast_count = 7
```

含义：

- `batch_threshold=0.0` 下 missed high-ROI 的 batch score 都不是主 blocker；
- 没有 near-threshold miss，不能把下一轮简化成降低 candidate threshold；
- random-wave 的 5 个 missed 全部是 task50 deep gap；
- sector-wave 的 11 个 missed 全部是 task20，其中 6 个 deep gap、5 个 moderate gap；
- 仍有 7 个 missed high-ROI 缺 same-context low-ROI / delay 对照，因此需要补
  target-materialization A/B 证据，而不是只调 loss。

基于该审计已生成 v15 multibatch intervention plan 和 guarded worker A/B runbook：

```text
intervention_plan =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_multibatch_intervention_plan_zh.md
intervention_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/summary.json
worker_ab_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook.md
worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_exact_safe_hits_batch8_ab_roi_20260616/worker_ab_runbook/summary.json

planned_context_count = 12
selected_context_count = 11
pairwise_context_target_count = 11
candidate_count = 32
candidate_task_count_counts = {'20': 26, '50': 6}
candidate_family_region_counts =
  {'random-wave|tranquillitatis_balmer_like_20km': 6,
   'sector-wave|apollo15_20km': 8,
   'sector-wave|tranquillitatis_balmer_like_20km': 18}
candidate_group_count = 32
worker_batch_size = 1
all_checks_pass = true
```

这一步只生成采样计划和 runbook，不等于已经运行 worker A/B，也不允许立即产生
训练标签。所有 candidate 虽然都是 materialized true-RC negative，但必须等显式
opt-in worker run 确认 expected-context reachability、target causal match 和
trajectory/tail ROI 后，才能经 `build_gat_multibatch_worker_batch_impact_rows.py`
回流为 positive / delay / bad-mode rows。

为了避免一次性串行执行完整 66 条 command，已从 32 个候选中筛出首批 top-3
missed high-ROI contexts，生成较小的 first-tranche runbook：

```text
first_tranche_subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_first_tranche_top3_runbook_subset_zh.md
first_tranche_subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/summary.json
first_tranche_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/summary.json

source_candidate_count = 32
eligible_context_count = 11
selected_context_count = 3
candidate_count = 9
candidate_task_count_counts = {'20': 9}
candidate_family_counts = {'sector-wave': 9}
candidate_context_counts =
  {'45baa40751a0bf77': 3,
   '79fde658840fe2b8': 3,
   'ac15bc4e7e3d6fff': 3}
worker_ab_command_count = 20
worker_ab_command_type_counts =
  {'kept_sentinel': 2, 'mainline_baseline': 9, 'target_priority_worker': 9}
all_checks_pass = true
```

该 first-tranche 仍然只是执行规模控制，不是 Stage 4 结论。它保留完整 exact-safe
边界：`runs_bpc_or_pricing=false` 仅表示 runbook builder 本身不运行求解；真正运行
20 条 command 后，仍需再审计 expected context reachability、target causal match、
RMP trajectory ROI 和 tail-risk，才能写 v16 rows。

first-tranche top-3 runbook 已经执行完毕，并完成 A/B、reachability、certificate
closure audit：

```text
execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v15_first_tranche_top3_audit_20260616/summary.json
reachability_summary =
  BPC_future/results/gat_target_intervention_reachability_v15_first_tranche_top3_20260616/summary.json
certificate_audit_summary =
  BPC_future/results/gat_target_mode_certificate_audit_v15_first_tranche_top3_20260616/summary.json

command_count = 20
executed_count = 20
failed_command_count = 0
record_count = 9
reachable_target_intervention_count = 9
positive_trajectory_roi_count = 2
nonpositive_roi_count = 7
roi_class_counts =
  {'negative_primal_roi': 4,
   'negative_retry_roi': 3,
   'positive_primal_roi': 1,
   'positive_retry_roi': 1}
certificate_violation_count = 0
all_checks_pass = true
```

这一步证明了 target-materialization worker 的 context reachability 是可用的，但也
证明了 true-RC negative 并不自动有利于 RMP trajectory：9 个候选里只有 2 个正
trajectory ROI，7 个应作为 hard-negative / delay 训练证据。certificate audit
为 0 violation，说明这批 opt-in worker 没有污染 official proof path。

这些 A/B 结果已回流为 v16 rows / dataset：

```text
worker_rows_summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/summary.json
v16_dataset =
  BPC_future/data/gat_batch_impact/v16_mixed_v15_plus_first_tranche_top3_ab_roi_20260616
v16_dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v16_first_tranche_top3_ab_roi_zh.md

row_count = 9
positive_trajectory_roi_count = 2
nonpositive_trajectory_roi_count = 7
sample_count = 341
candidate_count = 4644
same_context_pair_count = 138
same_context_comparable_pair_count = 135
positive_negative_label_pair_count = 44
training_ready = true
ranking_ready = true
```

v16 training / kNN-OOD 结果没有通过 Stage 4 gate：

```text
training =
  BPC_future/results/gat_batch_impact_training_v16_first_tranche_top3_ab_roi_20260616/metrics.json
global_knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v16_first_tranche_top3_ab_roi_global_20260616/summary.json
scale_knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v16_first_tranche_top3_ab_roi_scale_20260616/summary.json

checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 12
accepted_batch_roi = 15.887507483363152
accepted_batch_roi_ci_low = 6.949653955866234
safe_precision = 1.0
safe_precision_ci_low = 0.7574992425007574
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644
rejected_checkpoint_reasons =
  ['knn_ood_audit_missing',
   'safe_precision_ci_low_below_threshold_or_not_measurable']

global_knn_ood:
  accepted_batch_count = 9
  accepted_batch_roi = 11.456397010220421
  accepted_batch_roi_ci_low = 1.0586008970415683
  safe_precision = 1.0
  safe_precision_ci_low = 0.7008472464490406
  false_safe_rate_union = 0.0
  validation_safety_ready = false
```

关键新发现：v15 full intervention candidates、first-tranche candidates 和 v16
新增 rows 全部来自 validation split：

```text
v15_full_candidate_split = {'validation': 32}
v15_first_tranche_candidate_split = {'validation': 9}
v16_new_row_split = {'validation': 9}
```

因此 v16 增加的是 validation-side 对照和更难的 validation pair，不是 train-side
学习信号。这解释了为什么 pairwise coverage 变好，但 checkpoint / kNN-OOD 并没有
改善，甚至 accepted count 更低。下一步不能继续执行 validation-only A/B，也不能
用调 threshold 掩盖这个问题；必须生成 train split 的 same-context intervention
证据。

为避免再次混入 validation-only context，`build_gat_batch_impact_multibatch_intervention_plan.py`
已增加 split-aware 选择：

```text
--split-summary <training metrics json>
--split-mode all|train|validation
```

基于 v16 split 已生成 train-only intervention plan 和可控 top3 task20 runbook：

```text
train_split_plan =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v16_train_split_multibatch_intervention_plan_zh.md
train_split_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/summary.json
top3_subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v16_train_split_top3_task20_runbook_subset_zh.md
top3_subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/summary.json
top3_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/summary.json
top3_dry_run_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/runbook_execution_dry_run_summary.json

train_split_plan:
  split_mode = train
  split_instance_count = 40
  selected_context_count = 11
  candidate_count = 33
  candidate_task_count_counts = {'20': 27, '50': 6}

top3_task20_subset:
  selected_context_count = 3
  candidate_count = 9
  candidate_task_count_counts = {'20': 9}
  candidate_family_counts = {'random-wave': 9}
  candidate_context_counts =
    {'67c11b5ec80925ec': 3,
     'd519291840dd7000': 3,
     'ddcb5387bef3bf63': 3}
  worker_ab_command_count = 20
  dry_run_count = 20
  all_checks_pass = true
```

当前正确推进顺序改为：

1. 执行 train-split top3 task20 guarded worker A/B runbook，而不是继续扩大
   validation-only v15 runbook；
2. 审计 reachability、target causal match、trajectory ROI、tail-risk 和 certificate
   closure；
3. 只把通过 causal audit 的结果写成 train-side same-context rows；
4. 合并为 v17 dataset，确认 train split 中新增 pairwise contrast，而不仅是
   validation pair 增多；
5. 再重训 checkpoint，并检查 accepted count / safe precision CI / false-safe /
   family coverage 是否真正改善；
6. 若 train-side rows 后仍是 deep candidate score gap，再改 candidate head、
   context-local margin loss 或 batch diversity head；仍不得降低 Stage 3 gate。

### 2026-06-16 v16 train-split top3 A/B 与 v17 checkpoint 结论

已执行上一节的 train-split top3 task20 guarded worker A/B runbook，并把结果回流为
v17 dataset / checkpoint：

```text
runbook_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/summary.json
runbook_execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v16_train_split_top3_task20_audit_20260616/summary.json
reachability_audit =
  BPC_future/results/gat_target_intervention_reachability_v16_train_split_top3_task20_20260616/summary.json
certificate_audit =
  BPC_future/results/gat_target_mode_certificate_audit_v16_train_split_top3_task20_20260616/summary.json
worker_rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/summary.json
v17_dataset =
  BPC_future/data/gat_batch_impact/v17_mixed_v16_plus_train_split_top3_task20_ab_roi_20260616
v17_training =
  BPC_future/results/gat_batch_impact_training_v17_train_split_top3_task20_ab_roi_20260616/metrics.json
v17_knn_ood_global =
  BPC_future/results/gat_batch_impact_knn_ood_v17_train_split_top3_task20_ab_roi_global_20260616/summary.json
v17_threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v17_train_split_top3_task20_ab_roi_20260616/summary.json
v17_opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v17_train_split_top3_task20_ab_roi_20260616/summary.json
v17_score_margin_audit =
  BPC_future/results/gat_batch_impact_score_margin_audit_v17_train_split_top3_task20_ab_roi_20260616/summary.json
```

runbook 执行结果：

```text
command_count = 20
executed_count = 20
failed_command_count = 0
elapsed_s = 456.2131948899769
runs_bpc_or_pricing = true
all_checks_pass = true

ab_record_count = 9
positive_trajectory_roi_count = 4
nonpositive_roi_count = 5
roi_class_counts =
  {'negative_primal_roi': 1,
   'negative_retry_roi': 2,
   'no_observed_roi': 2,
   'positive_retry_roi': 4}

reachable_target_intervention_count = 9
certificate_violation_count = 0
```

这批 train-side target intervention 不改变 exact certificate path；certificate audit
仍为 0 violation。9 条 A/B 里 4 条 positive trajectory ROI、5 条非正收益，说明
train split 上确实补到了 useful positives 和 hard negatives，适合回流训练。

v17 dataset 相比 v16 增加了这 9 条 train-side rows：

```text
sample_count = 350
candidate_count = 4653
batch_label_counts = {'non_improving': 85, 'roi_positive': 265}
candidate_label_counts = {'delay_queue': 368, 'high_priority': 4285}
family_counts = {'greedy-anchor': 54, 'random-wave': 208, 'sector-wave': 88}
task_count_counts = {'5': 2, '10': 8, '20': 168, '30': 76, '50': 95, '100': 1}
same_context_pair_count = 165
same_context_comparable_pair_count = 161
positive_negative_label_pair_count = 56
training_ready = true
ranking_ready = true
```

v17 training / kNN-OOD 仍未通过 Stage 4 gate，但结论比 v16 更具体：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
selected_checkpoint_reason =
  no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons =
  ['knn_ood_audit_missing',
   'safe_precision_ci_low_below_threshold_or_not_measurable']

validation accepted_batch_count = 11
validation accepted_batch_roi = 14.885767099532215
validation accepted_batch_roi_ci_low = 5.299389622059389
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.7411599827511859
validation false_high_priority_on_delay = 0.00847457627118644
validation false_safe_rate_union = 0.00847457627118644

global / scale kNN-OOD 后：
  accepted_batch_count = 11
  accepted_batch_roi = 14.885767099532215
  accepted_batch_roi_ci_low = 5.299389622059389
  safe_precision = 1.0
  safe_precision_ci_low = 0.7411599827511859
  false_safe_rate_union = 0.0
  validation_safety_ready = false
  validation_candidate_ready = false
```

threshold frontier 说明当前 safety blocker 主要是置信界样本数不足，而不是已经观测到
false-safe：

```text
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 11
best_safe_precision_ci_low = 0.7411599827511859
min_all_success_samples_needed =
  {'high_priority_all_success_count': 35,
   'safe_all_success_count': 35}
```

同时，opportunity mining / score margin audit 把“missed high-ROI 是差一点还是
结构性分不开”拆开了：

```text
validation_record_count = 119
high_roi_opportunities = 30
accepted_high_roi_opportunities = 10
missed_high_roi_opportunities = 20
accepted_high_roi_capture_rate = 0.3333333333333333
missed_reason_counts = {'no_candidate_above_threshold': 20}

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 14,
   'moderate_candidate_score_gap': 3,
   'near_candidate_threshold': 3}
missed_candidate_score_margin_mean = -0.3219330845400691
missed_candidate_score_margin_min = -0.7948179505765438
missed_candidate_score_margin_max = -0.0122261643409729
missed_without_same_context_contrast_count = 6

missed_family_counts = {'random-wave': 5, 'sector-wave': 15}
missed_task_count_counts = {'20': 15, '50': 5}
```

这说明不能把下一步定义成“调低 candidate threshold”。只有 3 个 missed high-ROI
处在 near-threshold；14 个是 deep candidate score gap。batch score 对这些批次
已经多为正，但 candidate head 没有把具体列签名打过 HIGH_PRIORITY 阈值。当前
问题更像 candidate-level ranking / signature-context interaction 不够，而不是
batch-level ROI 头完全失效。

当前正确结论：

- v17 比 v16 更接近 Stage 4：kNN/OOD 后 false-safe union 已压到 0，accepted
  batch 从 v16 global kNN 的 9 增到 11；
- 但 v17 仍不能进入 mutating admission：safe precision CI low 只有 0.741，
  距离 0.9 hard gate 还差足够多的 all-success accepted samples；
- high-ROI 漏失主要是 candidate head 深分数缺口，不是阈值差一点；
- 下一轮必须继续补 train-side same-context positive/negative pairs，并优先覆盖
  `sector-wave` task20 与 `random-wave` task50 的候选列签名对照；
- 若第二批 train-side rows 后仍保持 deep candidate score gap，应进入模型结构修正：
  candidate head 加强 context-local margin / batch-candidate interaction / signature
  diversity，而不是继续堆普通 negative RC rows。

下一步执行约束：

1. 不降低 `safe_precision_ci_low >= 0.9`、`false_safe_rate_union <= 0.02`、
   `false_high_priority_on_delay <= 0.01` 等 Stage 3/4 hard gates；
2. 不把 GAT 的 HIGH_PRIORITY/DELAY_QUEUE 当作 certificate；
3. 继续用 exact pricing 在 final judge 下做 full closure；
4. 新 A/B runbook 应优先选 train split 未执行过的 context，并显式记录
   reachability / causal match / ROI / certificate audit 后再回流训练。

### 2026-06-16 v17 next3 mixed A/B 与 v18 hard-negative checkpoint 结论

已继续执行 train split 中尚未跑过的 next3 mixed context，并只把 reachability
审计允许的 causal rows 回流为 v18 dataset / checkpoint：

```text
next3_subset =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/summary.json
next3_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/summary.json
next3_execution =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v17_train_split_next3_mixed_20260616/worker_ab_runbook/runbook_execution_summary.json
next3_ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v17_train_split_next3_mixed_audit_20260616/summary.json
next3_reachability =
  BPC_future/results/gat_target_intervention_reachability_v17_train_split_next3_mixed_20260616/summary.json
next3_certificate =
  BPC_future/results/gat_target_mode_certificate_audit_v17_train_split_next3_mixed_20260616/summary.json
next3_worker_rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v17_train_split_next3_mixed_20260616/summary.json
v18_dataset =
  BPC_future/data/gat_batch_impact/v18_mixed_v17_plus_train_split_next3_hard_negative_20260616
v18_training =
  BPC_future/results/gat_batch_impact_training_v18_train_split_next3_hard_negative_20260616/metrics.json
v18_knn_ood_global =
  BPC_future/results/gat_batch_impact_knn_ood_v18_train_split_next3_hard_negative_global_20260616/summary.json
v18_threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v18_train_split_next3_hard_negative_20260616/summary.json
v18_opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v18_train_split_next3_hard_negative_20260616/summary.json
v18_score_margin_audit =
  BPC_future/results/gat_batch_impact_score_margin_audit_v18_train_split_next3_hard_negative_20260616/summary.json
```

next3 mixed runbook 选择了 9 个候选 batch，覆盖 3 个 train-side context：

```text
selected_context_count = 3
candidate_count = 9
candidate_task_count_counts = {'20': 3, '50': 6}
candidate_family_counts = {'random-wave': 6, 'sector-wave': 3}
excluded_already_run_context_count = 3

command_count = 20
executed_count = 20
failed_command_count = 0
elapsed_s = 537.066842264001
runs_bpc_or_pricing = true
all_checks_pass = true

5-task sentinel = 2 OPTIMAL
10-task sentinel = 2 OPTIMAL
task20/task50 A/B = TIME_LIMIT only
```

A/B ROI 表面上有 3 条 positive trajectory ROI，但 reachability 审计后不能全部当作
训练标签：

```text
ab_record_count = 9
positive_trajectory_roi_count = 3
nonpositive_roi_count = 6
roi_class_counts =
  {'negative_primal_roi': 2,
   'negative_retry_roi': 2,
   'no_observed_roi': 2,
   'positive_primal_roi': 3}

reachable_target_intervention_count = 4
reachability_class_counts =
  {'target_intervention_reachable': 4,
   'worker_context_not_reached': 5}
training_ready = false

certificate_violation_count = 0
```

这里有一个重要诊断：task50 的 positive primal ROI 多数来自
`worker_context_not_reached`，不能回流为 training label。为此已把
reachability worker-command 匹配从硬编码 `task020_...` 修正为按 candidate name
后缀匹配，并让 worker-row 构建器支持 `--reachability-summary` 过滤。最终 v18
只吸收 4 条 reachability-allowed rows：

```text
row_count = 4
reachability_record_count = 9
reachability_allowed_candidate_count = 4
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
roi_class_counts =
  {'negative_primal_roi': 1,
   'negative_retry_roi': 2,
   'no_observed_roi': 1}
skipped_counts = {'reachability_not_training_label': 5}
```

因此 v18 本质上不是“更多 positive ROI”版本，而是向 train split 注入了 4 条
hard-negative / nonpositive trajectory rows，用来约束低 ROI 误收。

v18 dataset 的结构如下：

```text
sample_count = 354
candidate_count = 4657
batch_label_counts = {'non_improving': 89, 'roi_positive': 265}
candidate_label_counts = {'delay_queue': 372, 'high_priority': 4285}
family_counts = {'greedy-anchor': 54, 'random-wave': 209, 'sector-wave': 91}
task_count_counts = {'5': 2, '10': 8, '20': 171, '30': 76, '50': 96, '100': 1}
same_context_pair_count = 172
same_context_comparable_pair_count = 168
positive_negative_label_pair_count = 60
training_ready = true
ranking_ready = true
```

v18 training 解决了 v17 的一部分置信界问题，但暴露出 family ROI 稀释：

```text
best_epoch = 6
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons =
  ['family_holdout_accepted_roi_below_threshold',
   'knn_ood_audit_missing']

validation accepted_batch_count = 39
validation accepted_batch_roi = 4.3838918669516245
validation accepted_batch_roi_ci_low = 1.0535803658133176
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.910330146399761
validation false_high_priority_on_delay = 0.00847457627118644
validation false_safe_rate_union = 0.00847457627118644
validation high_priority_precision_ci_low = 0.9930910774764203

family holdout:
  greedy-anchor accepted = 6, accepted_batch_roi = 0.11975858719658088,
    oracle_high_roi_count = 0
  random-wave accepted = 11, accepted_batch_roi = 0.2805267370051958,
    accepted_high_roi_count = 1 / oracle_high_roi_count = 6
  sector-wave accepted = 22, accepted_batch_roi = 7.598519871858033,
    accepted_high_roi_count = 11 / oracle_high_roi_count = 24
```

kNN/OOD 后 safety 仍接近可用，但 ROI CI 被 family 稀释压低：

```text
validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons =
  ['validation_accepted_batch_roi_ci_low_below_min',
   'validation_candidate_not_ready']

accepted_batch_count = 38
accepted_batch_roi = 3.4119277786693076
accepted_batch_roi_ci_low = 0.607449381373161
safe_precision = 1.0
safe_precision_ci_low = 0.90818706741616
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
knn_unsafe_count = 62
```

threshold frontier 没有任何 feasible threshold：

```text
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0

best_global:
  accepted_batch_count = 39
  accepted_batch_roi_ci_low = 1.0535803658133176
  safe_precision_ci_low = 0.910330146399761
  family_holdout_min_accepted_roi = 0.11975858719658088
  reject = family_holdout_accepted_roi_below_threshold + knn_ood_audit_missing

best_family_delay_fallback:
  accepted_batch_count = 22
  accepted_batch_roi_ci_low = 2.0509280500816995
  safe_precision_ci_low = 0.8513404742740388
  family_specific_delay_fallback_families = ['greedy-anchor']
  reject = safe_precision_ci_low_below_threshold_or_not_measurable
```

这说明 v18 不是简单“阈值太严”。global threshold 的 accepted count 和
safe precision CI 已经够，但会接收太多 low-ROI / bad rows；family-delay fallback
能显著提高 ROI，但 accepted count 降到 22，safe precision CI 又低于 0.9。

v18 opportunity mining 和 margin audit 对“missed high-ROI 是差一点还是结构性分不开”
的结论如下：

```text
accepted = 39
high_roi_opportunities = 30
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 18
accepted_high_roi_capture_rate = 0.4
accepted_low_roi_or_bad = 27
missed_reason_counts = {'no_candidate_above_threshold': 18}

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 9,
   'moderate_candidate_score_gap': 8,
   'near_candidate_threshold': 1}
missed_candidate_score_margin_mean = -0.231501843366358
missed_candidate_score_margin_min = -0.6960250288248062
missed_without_same_context_contrast_count = 6

missed_family_counts = {'random-wave': 5, 'sector-wave': 13}
missed_task_count_counts = {'20': 13, '50': 5}
contexts_needing_contrast =
  [{'context_hash': '9fadf4f7b39742a2', 'family': 'sector-wave',
    'missed_high_roi_opportunities': 4, 'task_counts': [20]},
   {'context_hash': 'a67f331bdb819d7d', 'family': 'random-wave',
    'missed_high_roi_opportunities': 1, 'task_counts': [50]},
   {'context_hash': 'e6b17bbf825984ae', 'family': 'random-wave',
    'missed_high_roi_opportunities': 1, 'task_counts': [50]}]
```

v18 相比 v17 的进展是：

- accepted high-ROI 从 10 / 30 提升到 12 / 30；
- deep candidate score gap 从 14 降到 9；
- selected validation safe precision CI 从 0.741 提升到 0.910；
- kNN/OOD 后 false-safe union 保持 0；
- 但 accepted low-ROI-or-bad 高达 27，greedy-anchor 无 oracle high-ROI 却仍被接收
  6 条，random-wave 只抓到 1 / 6 个 high-ROI。

当前硬结论：

1. 不应降低 candidate threshold 或放宽 Stage 3/4 gate。missed high-ROI 中只有
   1 条 near-threshold，绝大多数仍是 candidate head / signature-context
   interaction 没分开。
2. v18 的主要新 blocker 是 ROI 稀释，而不是单纯 safety 样本不足。下一步要减少
   greedy-anchor / random-wave 的低 ROI 误收，同时保持 accepted all-success 样本数。
3. task50 的正向 ROI 不能直接使用，必须先修复 target materialization / context replay
   的 reachability；否则 positive A/B 现象不是 causal training label。
4. 下一轮数据应优先补充 reachability-valid 的 same-context contrast，尤其是
   `sector-wave` task20 的 `9fadf4f7b39742a2`，以及修复 reachability 后的
   `random-wave` task50 `a67f331bdb819d7d` / `e6b17bbf825984ae`。
5. 模型侧应进入 candidate head 的结构性修正：加入 context-local margin、
   batch-candidate interaction、family/ROI-aware admission 或 family-specific
   delay fallback 的训练/选择目标；而不是继续堆普通 negative-RC rows。

### 2026-06-16 v19/v20 candidate pairwise margin ablation 结论

在 v18 暴露出 candidate head / signature-context interaction 分不开后，已做一轮
offline 结构性 ablation：在 `train_gat_batch_impact.py` 中加入
`--pairwise-candidate-ranking-loss-multiplier`，同 context 内用 high-ROI 样本的
labeled-safe candidate 最大 admission logit 对比 low-ROI / bad 样本的任意
candidate 最大 admission logit。该变更只影响 offline checkpoint 训练，不运行
BPC / pricing / RMP，不改变 exact certificate 边界。

```text
v19_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v19_candidate_pairwise_margin_training_zh.md
v19_knn =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_knn_ood_v19_candidate_pairwise_margin_global_zh.md
v19_opportunity =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_opportunity_mining_v19_candidate_pairwise_margin_zh.md
v19_score_margin =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v19_candidate_pairwise_margin_zh.md

v20_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v20_candidate_pairwise_margin025_training_zh.md
v20_knn =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_knn_ood_v20_candidate_pairwise_margin025_global_zh.md
v20_opportunity =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_opportunity_mining_v20_candidate_pairwise_margin025_zh.md
v20_score_margin =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v20_candidate_pairwise_margin025_zh.md
ablation_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v19_v20_candidate_pairwise_margin_ablation_zh.md
```

核心结果：

```text
v18 baseline:
  accepted = 39
  selected_roi = 4.3838918669516245
  selected_roi_ci_low = 1.0535803658133176
  safe_precision_ci_low = 0.910330146399761
  accepted_high_roi = 12 / 30
  missed_high_roi = 18
  accepted_low_roi_or_bad = 27
  candidate_margin_buckets =
    {'deep_candidate_score_gap': 9,
     'moderate_candidate_score_gap': 8,
     'near_candidate_threshold': 1}

v19 candidate_pairwise=0.75:
  accepted = 18
  selected_roi = 9.241468070281876
  selected_roi_ci_low = 2.623136213513141
  safe_precision_ci_low = 0.8241154494176252
  kNN/OOD accepted = 12
  kNN/OOD roi_ci_low = 0.4312704809602725
  accepted_high_roi = 11 / 30
  missed_high_roi = 19
  accepted_low_roi_or_bad = 9
  candidate_margin_buckets =
    {'deep_candidate_score_gap': 4,
     'moderate_candidate_score_gap': 10,
     'near_candidate_threshold': 5}

v20 candidate_pairwise=0.25:
  accepted = 10
  selected_roi = 10.493025609850884
  selected_roi_ci_low = 0.8042559559050559
  safe_precision_ci_low = 0.7224598312333834
  kNN/OOD accepted = 10
  accepted_high_roi = 8 / 30
  missed_high_roi = 22
  accepted_low_roi_or_bad = 2
  candidate_margin_buckets =
    {'deep_candidate_score_gap': 5,
     'moderate_candidate_score_gap': 11,
     'near_candidate_threshold': 6}
```

硬结论：

1. candidate-level pairwise margin 方向有效：v19 把 low-ROI / bad accepted 从 27
   降到 9，deep candidate gap 从 9 降到 4，说明 v18 的 blocker 确实在
   candidate admission head 上。
2. 但 v19/v20 都没有通过 Stage 3/4 gate。它们把 accepted all-success 样本数压得
   太低，safe precision CI 低于 0.9；kNN/OOD 后 coverage 更不足。
3. v20 降低 pairwise multiplier 后没有恢复 coverage，反而 accepted high-ROI 从
   11 降到 8、missed high-ROI 从 19 升到 22，因此这不是简单 loss 权重调参问题。
4. 下一步应补 reachability-valid 的 same-context contrast，而不是放松阈值：
   `sector-wave` task20 `9fadf4f7b39742a2` / `b6d808ebac2a6dd8` 优先；
   `random-wave` task50 `a67f331bdb819d7d` / `e6b17bbf825984ae` 必须先修复
   target replay reachability 后再回流 positive label。
5. 训练目标还需要进一步“写硬”：不是单纯 margin，而是 coverage-constrained ROI
   ranking/admission，即在 `accepted_batch_count >= 35`、safe precision CI、
   false-safe gate 不放松的前提下，最大化 ROI 并最小化 low-ROI / bad admission。

### 2026-06-16 v18/v19/v20 cross-checkpoint selector 审计结论

为避免继续盲调单个 checkpoint，已新增一个离线 cross-checkpoint selector 审计，
检查能否把 v18 的 coverage 与 v19/v20 的 low-ROI suppression 通过固定组合规则合并：

```text
script =
  BPC_future/scripts/audit_gat_batch_impact_cross_checkpoint_selector.py
test =
  BPC_future/tests/test_gat_batch_impact_cross_checkpoint_selector.py
summary =
  BPC_future/results/gat_batch_impact_cross_checkpoint_selector_v18_v19_v20_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_cross_checkpoint_selector_v18_v19_v20_zh.md
```

该审计只读取 v18/v19/v20 的 opportunity-mining validation records，不运行 BPC /
pricing / RMP / worker / certificate。它显式保持：

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

结果：

```text
validation_record_count = 119
minimum_all_success_count_for_safe_precision_ci = 35
rule_count = 15
feasible_rule_count = 0

best_diagnostic_rule = v18_and_v19
accepted_batch_count = 20
accepted_batch_roi = 8.33569827824831
accepted_batch_roi_ci_low = 2.2722559375239006
safe_precision_ci_low = 0.8388698745050667
accepted_high_roi = 11 / 30
accepted_low_roi_or_bad = 9
family_holdout_min_accepted_roi = 0.4911726514498393
reject_reasons =
  ['safe_precision_ci_low_below_threshold_or_not_measurable',
   'family_holdout_accepted_roi_below_threshold',
   'accepted_all_success_count_below_safe_precision_ci_requirement']
```

关键 frontier：

```text
v18_selected:
  accepted = 39
  safe_precision_ci_low = 0.910330146399761
  accepted_low_roi_or_bad = 27
  family_holdout_min_accepted_roi = 0.11975858719658088
  reject = family_holdout_accepted_roi_below_threshold

v18_no_greedy_anchor:
  accepted = 33
  safe_precision_ci_low = 0.8957265699643882
  accepted_low_roi_or_bad = 21
  family_holdout_min_accepted_roi = 0.2805267370051958
  reject = safe CI + family ROI + all-success count

v18_sector_only:
  accepted = 22
  safe_precision_ci_low = 0.8513404742740388
  accepted_low_roi_or_bad = 11
  family_holdout_min_accepted_roi = 7.598519871858033
  reject = safe CI + all-success count

v20_plus_v18_sector:
  accepted = 23
  safe_precision_ci_low = 0.8568788745827373
  accepted_low_roi_or_bad = 11
  family_holdout_min_accepted_roi = 1.1059776544570923
  reject = safe CI + all-success count
```

硬结论：

1. 组合 v18/v19/v20 不能绕过补数据。只要保留 v18 的 coverage，就保留了
   greedy/random family ROI 稀释；只要采用 v19/v20 的 stricter admission，accepted
   count 就低于 Wilson 下界所需的 35 个 all-success 样本。
2. `v18_no_greedy_anchor` 看起来只差 2 个 accepted，但 random-wave family ROI 仍只有
   0.2805，因此真实 blocker 不是“补两个样本”这么简单，而是要补
   reachability-valid 的 random/sector same-context positive/negative contrast。
3. 下一步仍是 Stage 2/3 数据闭环：优先 `sector-wave` task20
   `9fadf4f7b39742a2` / `b6d808ebac2a6dd8`，以及修复 task50 reachability 后再处理
   `random-wave` `a67f331bdb819d7d` / `e6b17bbf825984ae`。
4. exact boundary 不变：cross-checkpoint selector 只能决定离线 admission 排序，
   不能证明 reduced-cost universe 已关闭。

### 2026-06-16 v21 train-split sector contrast 计划状态

读完 v15 hard-negative refresh、v17/v18 train-split A/B、v19/v20 pairwise
margin ablation 和 v18/v19/v20 cross-checkpoint selector 后，当前下一步不能再
定义为阈值微调：

- v15 把 exact safe-hit batch8 的真实 trajectory ROI 回流为 hard-negative 是正确方向，
  但 accepted count 太低，CI gate 不过；
- v17/v18 证明 train-side same-context intervention 能提供可学习对照，但 v18
  也暴露出 family ROI 稀释；
- v19/v20 的 candidate pairwise margin 能减少 low-ROI / bad admission，却牺牲
  coverage 和 safe precision CI；
- cross-checkpoint selector 没有找到可行组合规则，说明不能靠拼接 checkpoint
  绕过补数据；
- validation 侧的 `9fadf4f7b39742a2` / `b6d808ebac2a6dd8` 对诊断很重要，但不能
  直接拿来做 train label，否则会继续污染 holdout。

因此已生成 v21 train-split `sector-wave` task20 contrast plan。为避免再次混入
validation-only context，`build_gat_batch_impact_multibatch_intervention_plan.py`
增加了 family 过滤：

```text
new_arg = --include-families
```

v21 full plan：

```text
plan_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v21_train_split_sector_contrast_plan_zh.md
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_20260616/summary.json
runbook_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_20260616/worker_ab_runbook/summary.json

split_mode = train
split_instance_count = 40
include_families = ['sector-wave']
include_task_counts = [20]
selected_context_count = 6
candidate_count = 18
candidate_task_count_counts = {'20': 18}
candidate_family_region_counts =
  {'sector-wave|apollo15_20km': 15,
   'sector-wave|tranquillitatis_balmer_like_20km': 3}
candidate_selection_ranking_counts =
  {'active_replacement': 6, 'best_rc': 6, 'impact': 6}
candidate_impact_bucket_counts =
  {'new_support_changing': 12, 'new_task_set': 2, 'replacement_like': 4}
all_checks_pass = true
```

为控制首轮执行规模，又从 v21 full plan 裁出 first-tranche：

```text
first_tranche_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v21_train_split_sector_contrast_first_tranche_zh.md
first_tranche_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
first_tranche_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/summary.json

selected_context_count = 3
candidate_count = 9
candidate_family_counts = {'sector-wave': 9}
candidate_task_count_counts = {'20': 9}
candidate_context_counts =
  {'0df8d5cea7864e69': 3,
   'b9550ffc9a42531a': 3,
   '4e481a6307fca228': 3}
candidate_group_count = 9
worker_method = target_materialization_fixed
worker_batch_size = 1
online_effect_scope = explicit_candidate_worker_commands_only
all_checks_pass = true
```

注意：上述 builder / selector / runbook builder 都没有运行 BPC、pricing、RMP、
worker 或 certificate。`runs_bpc_or_pricing=false` 只说明生成 artifact 本身是
offline；真正执行 first-tranche worker commands 后，必须再做：

1. runbook execution summary；
2. target intervention reachability audit；
3. same-context A/B ROI / tail-risk audit；
4. certificate boundary audit；
5. `--reachability-summary` 过滤后的 worker rows；
6. v21 dataset / training / kNN-OOD / threshold frontier；
7. 若仍是 deep score gap，再改 candidate head / context-local margin /
   batch-candidate interaction，而不是降低 Stage 3/4 gate。

当前 v21 结论是：

```text
v21_status = data_collection_plan_ready
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
```

### 2026-06-16 v21 first-tranche 执行、训练与审计结论

v21 train-split `sector-wave` task20 first-tranche 已完成执行与离线回流：

```text
synthesis_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v21_train_split_sector_contrast_first_tranche_synthesis_zh.md

execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v21_train_split_sector_contrast_first_tranche_audit_20260616/summary.json
reachability_audit =
  BPC_future/results/gat_target_intervention_reachability_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
certificate_audit =
  BPC_future/results/gat_target_mode_certificate_audit_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
dataset =
  BPC_future/data/gat_batch_impact/v21_mixed_v18_plus_train_split_sector_contrast_first_tranche_ab_roi_20260616
training =
  BPC_future/results/gat_batch_impact_training_v21_train_split_sector_contrast_first_tranche_20260616/metrics.json
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v21_train_split_sector_contrast_first_tranche_global_20260616/summary.json
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
```

first-tranche runbook 执行成功：

```text
command_count = 20
executed_count = 20
failed_command_count = 0
elapsed_s = 604.1773736650066
5/10 sentinels = OPTIMAL
task20 A/B = TIME_LIMIT diagnostic
certificate_violation_count = 0
```

A/B 与 reachability 结果：

```text
ab_record_count = 9
positive_trajectory_roi_count = 4
nonpositive_roi_count = 5
roi_class_counts =
  {'negative_primal_roi': 2,
   'negative_retry_roi': 2,
   'no_observed_roi': 1,
   'positive_primal_roi': 1,
   'positive_retry_roi': 3}

reachable_target_intervention_count = 9
training_label_allowed = 9 / 9
```

这批数据形成 3 个同 context 对照：`0df8d5cea7864e69` 偏负/无效，
`b9550ffc9a42531a` 偏正 retry ROI，`4e481a6307fca228` 同 context 内一正两强负。
因此它适合作为 candidate head 的监督信号，但不是 production evidence。

v21 dataset / training：

```text
sample_count = 363
candidate_count = 4666
family_counts = {'greedy-anchor': 54, 'random-wave': 209, 'sector-wave': 100}
same_context_pair_count = 208
same_context_comparable_pair_count = 203
positive_negative_label_pair_count = 72
training_ready = true
ranking_ready = true

pairwise_candidate_ranking_loss_multiplier = 0.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
validation accepted_batch_count = 4
validation accepted_batch_roi = 0.9555176049470901
validation accepted_batch_roi_ci_low = 0.7689567764619533
validation safe_precision_ci_low = 0.5100999795960008
validation false_safe_rate_union = 0.0
```

这里显式关闭 v19/v20 的 candidate-pairwise loss，是为了隔离“v21 数据增量”。
结论是 data-only checkpoint 过保守：没有 low-ROI/bad admission，但 accepted
batch 太少，safe precision CI 下界不足。

kNN/OOD 和 threshold frontier：

```text
validation_candidate_ready = false
validation_safety_ready = false
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
```

opportunity / score-margin 审计回答了“missed high-ROI 是差一点还是结构性分不开”：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 4
missed_high_roi_opportunities = 26
accepted_high_roi_capture_rate = 0.13333333333333333
accepted_low_roi_or_bad = 0

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 25,
   'near_candidate_threshold': 1}

missed_candidate_score_margin_mean = -0.2779155373573303
missed_candidate_score_margin_median = -0.2899966686964035
missed_candidate_score_margin_min = -0.3004484474658966
missed_candidate_score_margin_max = -0.0018556714057922363
```

硬结论：v21 first-tranche 不是阈值差一点。只有 1 个 missed high-ROI 接近
candidate threshold，其余 25 个是 deep candidate score gap。下一步应继续
补 reachability-valid same-context contrast，或改 candidate head /
batch-candidate interaction / context-local margin；不应降低 Stage 3/4 precision、
ROI、CI 或 certificate gate。

更新后的 v21 状态：

```text
v21_status = first_tranche_executed_trained_audited
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
primary_blocker = candidate_head_deep_score_gap_and_low_acceptance_ci
```

### 2026-06-16 v22 positive-candidate boost 训练与审计结论

v22 没有改变数据集，也没有运行 BPC / pricing / RMP。它只在 Stage 3 训练
surrogate 中新增并显式开启：

```text
hard_roi_positive_candidate_loss_multiplier = 2.0
```

含义：对达到 hard ROI gate 且非 bad-mode batch 内的真实 HIGH_PRIORITY 候选，
额外增加候选头召回压力。默认值仍为 `0.0`，所以 legacy 训练行为不被隐式改变。

新增代码与测试：

```text
training_code =
  BPC_future/scripts/train_gat_batch_impact.py
test =
  BPC_future/tests/test_gat_batch_impact_training.py

validation =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training
  Ran 14 tests in 0.240s
  OK
```

v22 产物：

```text
synthesis_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v22_positive_candidate_boost_synthesis_zh.md
training =
  BPC_future/results/gat_batch_impact_training_v22_positive_candidate_boost_v21_data_20260616/metrics.json
checkpoint =
  BPC_future/data/gat_batch_impact/v22_positive_candidate_boost_v21_data_20260616/gat_batch_impact.pt
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v22_positive_candidate_boost_global_20260616/summary.json
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v22_positive_candidate_boost_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v22_positive_candidate_boost_20260616/summary.json
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v22_positive_candidate_boost_20260616/summary.json
```

v22 training / threshold frontier：

```text
best_epoch = 8
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false

validation accepted_batch_count = 10
validation accepted_batch_roi = 16.32825751900673
validation accepted_batch_roi_ci_low = 6.201525818837059
validation high_priority_precision_ci_low = 0.965238155466207
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.7224598312333834
validation false_high_priority_on_delay = 0.00847457627118644
validation false_safe_rate_union = 0.00847457627118644

feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
safe_all_success_count_needed_for_ci_low_0.9 = 35
```

kNN/OOD 后：

```text
validation accepted_batch_count = 9
validation accepted_batch_roi = 13.5515608853764
validation accepted_batch_roi_ci_low = 4.003538240157702
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.7008472464490406
validation false_high_priority_on_delay = 0.0
validation false_safe_rate_union = 0.0
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min',
   'validation_candidate_not_ready']
```

v22 opportunity / margin：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 10
missed_high_roi_opportunities = 20
accepted_high_roi_capture_rate = 0.3333333333333333
accepted_low_roi_or_bad = 0

missed_reason_counts =
  {'no_candidate_above_threshold': 20}

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 12,
   'moderate_candidate_score_gap': 6,
   'near_candidate_threshold': 2}
```

对比 v21，v22 把 accepted high-ROI 从 `4 / 30` 提高到 `10 / 30`，
并把 deep candidate score gap 从 `25` 降到 `12`。因此 v21 blocker 不是完全
结构性不可分；训练目标硬化确实能拉动一部分高 ROI 候选。但 v22 仍未达到
Stage 4：

1. accepted safe 样本数不足，CI 下界离 `0.9` 还远；
2. 剩余 missed high-ROI 仍有 12 个 deep gap，不能靠降 candidate threshold；
3. 还有 6 个 missed high-ROI 缺少同 context 正负对照，下一轮数据采集应优先补：
   `9fadf4f7b39742a2`、`b6d808ebac2a6dd8`、`a67f331bdb819d7d`、
   `e6b17bbf825984ae`。

更新后的 v22 状态：

```text
v22_status = positive_candidate_boost_trained_audited
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
primary_blocker = safe_precision_ci_sample_count_and_remaining_deep_candidate_gap
next_step = collect_same_context_contrast_for_remaining_missed_contexts_or_add_context_local_margin
```

### 2026-06-16 v23 contrast collection plan 状态

读完 v22 synthesis、Stage 4 kNN/OOD、Stage 5 20-task exact target 后，下一步不应
继续盲目调 threshold 或把 v22 checkpoint 送入 online admission。v22 的 point
estimate 已经有 ROI，但 `safe_precision_ci_low` 证据量不足，且剩余 missed high-ROI
仍有 deep gap。因此 v23 回到 Stage 2/3 数据闭环：

```text
synthesis_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage2_stage3_v23_contrast_collection_plan_synthesis_zh.md
```

v23 train-split full plan：

```text
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_train_split_remaining_contrast_plan_zh.md

status = ready
all_checks_pass = true
split_mode = train
include_task_counts = [20]
selected_context_count = 12
candidate_count = 35
pairwise_context_target_count = 12
candidate_task_count_counts = {'20': 35}
candidate_family_region_counts =
  {'greedy-anchor|tranquillitatis_balmer_like_20km': 3,
   'random-wave|apollo15_20km': 11,
   'random-wave|tranquillitatis_balmer_like_20km': 12,
   'sector-wave|apollo15_20km': 6,
   'sector-wave|tranquillitatis_balmer_like_20km': 3}
```

v23 train first-tranche：

```text
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_train_split_remaining_contrast_first_tranche_zh.md
worker_runbook_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/summary.json

status = ready
all_checks_pass = true
selected_context_count = 4
candidate_count = 12
candidate_family_counts = {'random-wave': 9, 'sector-wave': 3}
candidate_task_count_counts = {'20': 12}
selected_contexts =
  ['d519291840dd7000',
   'ddcb5387bef3bf63',
   '67c11b5ec80925ec',
   '0df8d5cea7864e69']
worker_method = target_materialization_fixed
worker_batch_size = 1
```

v23 validation-missed diagnostic plan：

```text
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_validation_missed_diagnostic_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_validation_missed_diagnostic_plan_zh.md

status = ready
all_checks_pass = true
split_mode = validation
require_opportunity_context = true
selected_context_count = 8
candidate_count = 23
candidate_task_count_counts = {'20': 17, '50': 6}
selected_contexts =
  ['ac15bc4e7e3d6fff',
   '79fde658840fe2b8',
   '45baa40751a0bf77',
   '3d1bd8618099b573',
   '9fadf4f7b39742a2',
   '5751b1799b606ad1',
   'ce3508e12ad69da7',
   'a67f331bdb819d7d']
```

边界：

```text
v23_runs_bpc_or_pricing = false
v23_production_ready = false
v23_default_enabled = false
v23_certificate_ready = false
v23_official_bound_effect = false
training_label_allowed_before_worker_reachability = false
```

重要区分：`train_split_remaining_contrast` 可以作为下一轮训练数据采集 runbook；
`validation_missed_diagnostic` 只用于解释当前 v22 missed context 的可达性和
causal match，不能直接并入同一 validation gate 之后宣称 Stage 3/4 通过。若后续
把 validation diagnostic 结果回流，必须重新定义 holdout 或重新 split。

更新后的 v23 状态：

```text
v23_status = train_split_and_validation_diagnostic_plans_ready
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
next_step = execute_v23_train_first_tranche_then_audit_reachability_roi_certificate
```

### 2026-06-16 v23 first-tranche 执行、回流、训练与审计结论

v23 train first-tranche 已完成 guarded A/B、reachability / ROI / certificate 审计、
rows 回流、mixed dataset 重建和 v22-style positive-candidate boost 训练：

```text
synthesis_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v23_positive_candidate_boost_synthesis_zh.md

execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v23_train_split_remaining_contrast_first_tranche_audit_20260616/summary.json
reachability_audit =
  BPC_future/results/gat_target_intervention_reachability_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
certificate_audit =
  BPC_future/results/gat_target_mode_certificate_audit_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
dataset =
  BPC_future/data/gat_batch_impact/v23_mixed_v21_plus_train_split_remaining_contrast_first_tranche_ab_roi_20260616
training =
  BPC_future/results/gat_batch_impact_training_v23_positive_candidate_boost_v23_data_20260616/metrics.json
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v23_positive_candidate_boost_global_20260616/summary.json
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v23_positive_candidate_boost_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v23_positive_candidate_boost_20260616/summary.json
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v23_positive_candidate_boost_20260616/summary.json
```

A/B 与 exact-safe 边界：

```text
runbook_command_count = 26
executed_count = 26
failed_command_count = 0
5/10 sentinels = OPTIMAL
ab_record_count = 12
reachable_target_intervention_count = 12
certificate_violation_count = 0
roi_class_counts =
  {'negative_primal_roi': 1,
   'negative_retry_roi': 4,
   'no_observed_roi': 2,
   'positive_retry_roi': 5}
positive_trajectory_roi_count = 5
nonpositive_roi_count = 7
```

v23 dataset 在 v21 上追加 12 条 reachability-valid rows：

```text
sample_count = 375        # v21: 363
candidate_count = 4678    # v21: 4666
same_context_comparable_pair_count = 268  # v21: 203
positive_negative_label_pair_count = 88   # v21: 72
training_ready = true
ranking_ready = true
```

v23 训练仍使用 v22 的正候选强化目标：

```text
hard_roi_positive_candidate_loss_multiplier = 2.0
pairwise_candidate_ranking_loss_multiplier = 0.0
training_objective = precision_constrained_roi_maximization

best_epoch = 8
checkpoint_gate_pass = false
stage4_candidate_ready = false
validation accepted_batch_count = 56
validation accepted_batch_roi = 5.331371024134569
validation accepted_batch_roi_ci_low = 2.703146826585392
validation safe_precision_ci_low = 0.9358038555118847
validation false_high_priority_on_delay = 0.425531914893617
validation false_safe_rate_union = 0.425531914893617
```

结论：v23 把 accepted high-ROI 从 v22 的 `10 / 30` 提升到 `27 / 30`，missed
high-ROI 只剩 3 个，deep candidate gap 从 12 降到 1。但它同时接受了 39 个
low-ROI/bad opportunity，导致 false-safe / delay-risk 硬拒绝。因此 v23 不是
Stage 4 ready；当前 blocker 已从 high-ROI recall 转为 low-ROI / delay-risk
suppression。

kNN/OOD 后：

```text
accepted_batch_count = 37
accepted_batch_roi = 2.7717488413374567
accepted_batch_roi_ci_low = 0.16378971779217766
safe_precision_ci_low = 0.9059390425448562
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_block_reasons =
  ['validation_accepted_batch_roi_ci_low_below_min',
   'validation_candidate_not_ready']
```

kNN/OOD 能压住 false-safe，但 ROI CI-low 掉到 `0.164`，仍低于 `0.65` hard gate。
下一步应做 delay-risk / low-ROI suppression 或 kNN 后 ROI-CI 修复，而不是继续
加大 positive boost 或降低 Stage 3/4 hard gate。

更新后的 v23 状态：

```text
v23_status = first_tranche_executed_trained_audited
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
primary_blocker = false_safe_delay_risk_and_knn_roi_ci
next_step = train_delay_risk_suppression_or_collect_narrow_hard_negatives_then_reaudit
```

## 11. Stage 5: 20/30/50/100 Scale Acceleration

### 目标

在保证 exactness 和 5/10 no-regression 的前提下，让 20 规模在 200 秒内求得最优解，并为 30/50/100 规模加速建立路径。

### A. 20-task 目标

必须在 agreed benchmark matrix 上满足：

- 5-task no regression；
- 10-task no regression；
- 20-task `OPTIMAL` within 200s；
- official dual bound available；
- certificate comes only from exact pricing；
- no false lower bound；
- no default unsafe gate。

20-task 验收指标：

- optimal count / total；
- median and max wall-time；
- time to incumbent；
- final `dual_bound` availability；
- exact pricing closure reason；
- final judge retry count；
- hidden negative count；
- generated sequences / evaluated timed trips；
- RMP solves / pricing calls / exact pricing calls。

### B. 30/50/100 扩展目标

30/50/100 初期不要求证明最优，但必须定义可测加速指标：

- time to incumbent；
- primal improvement；
- gap improvement；
- pricing workload reduction；
- generated sequences reduction；
- evaluated timed trips reduction；
- RMP pool growth control；
- tail retry reduction；
- accepted batch ROI；
- OOD delay rate。

必须保持 exact-safe fallback path。只要 exact pricing incomplete，就不能报告 exact optimality。

### C. GAT 加速机制

Online GAT-guided pricing priority：

- first-task priority；
- transition priority；
- arc-option priority；
- residual-family priority。

Online GAT-guided admission：

- `HIGH_PRIORITY` 加入 RMP 或优先返回；
- `DELAY_QUEUE` 保留并有限延迟；
- `REJECT_NONNEGATIVE_ONLY` 仅用于非负列。

Certificate mode：

- reprice delay queue；
- add currently negative delayed columns；
- run full exact pricing closure；
- GAT only ordering, no pruning。

### 当前问题

- 20-task 仍有 `TIME_LIMIT` 和 `dual_bound=None`。
- 单一全局 knob 已被报告证伪或降级。
- 真正瓶颈是 context-aware active-family trajectory control 与 exact proof tail 的组合。

### 应该修改的组件

- opt-in pricing priority hooks。
- opt-in admission scheduler。
- delay queue finite-delay manager。
- certificate preflight queue repricing。
- benchmark report scripts。

### 不允许修改/不允许启用的组件

- 不默认启用任何 unsafe gate。
- 不禁用 final judge。
- 不把 GAT no-column 当 certificate。
- 不为 30/50/100 报告未证明的 exact optimality。

### 建议新增文件

- `BPC_future/pricing/gat_priority_scheduler.py`
- `BPC_future/solver/gat_admission_queue.py`
- `BPC_future/scripts/run_gat_target_mode_benchmark_matrix.py`
- `BPC_future/scripts/audit_gat_target_mode_certificate_closure.py`
- `BPC_future/logical_graph/run_reports/<date>_gat_target_mode_20_30_50_100_zh.md`

### 建议修改文件

- `BPC_future/solver/journey_driver.py`
- `BPC_future/pricing/journey_pricing.py`
- `BPC_future/configs/*_gat_target_mode_optin.yaml`
  只新增 opt-in configs，不修改 official baseline configs。

### 输入/输出 artifact

- agreed benchmark matrix
- baseline CSV/logs
- opt-in GAT priority CSV/logs
- opt-in GAT admission CSV/logs
- exactness audit summary
- no-regression report
- ROI report

### 验收标准

- 5/10 no-regression：official status/primal/dual/gap/node count 不变或在预先声明的 exact-equivalent tolerance 内。
- 20 ROI：repeatable wall-time 或 tail retry reduction，且 no exactness regression。
- 20 proof：`CERTIFIED_NO_NEGATIVE` 来源只来自 exact pricing full closure。
- 30/50/100：只报告 heuristic acceleration metrics，除非 exact closure 成功。

### 失败风险

- 20 加速不可泛化到 family holdout。
- GAT admission 改善 incumbent 但增加 final proof tail。
- priority ordering 与 branch path dependency 交互导致回退。
- 30/50/100 pool 过大，RMP solve 成为瓶颈。

### 进入生产候选的 gate

- 所有 previous gates 通过。
- agreed 5/10 matrix no regression。
- agreed 20 matrix 达到 200s exact target 或明确缩小 blocker。
- production flags 仍默认 false，只有用户显式 opt-in 才启用。

## 12. Proposed File-Level Change Map

建议新增：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- `BPC_future/learning/journey_candidate_encoder.py`
- `BPC_future/learning/rmp_context_encoder.py`
- `BPC_future/learning/batch_impact_model.py`
- `BPC_future/pricing/gat_priority_scheduler.py`
- `BPC_future/solver/gat_admission_queue.py`
- `BPC_future/scripts/build_gat_same_context_intervention_dataset.py`
- `BPC_future/scripts/build_gat_batch_impact_dataset.py`
- `BPC_future/scripts/train_gat_batch_impact.py`
- `BPC_future/scripts/audit_gat_batch_impact_knn_ood.py`
- `BPC_future/scripts/run_gat_target_mode_shadow_ab.py`
- `BPC_future/scripts/audit_gat_target_mode_online_ab.py`
- `BPC_future/scripts/audit_gat_target_mode_certificate_closure.py`
- `BPC_future/tests/test_gat_batch_impact_model.py`
- `BPC_future/tests/test_gat_same_context_intervention_dataset.py`
- `BPC_future/tests/test_gat_batch_impact_training.py`
- `BPC_future/tests/test_gat_target_mode_scheduler.py`
- `BPC_future/tests/test_gat_target_mode_certificate_safety.py`

建议修改：

- `BPC_future/learning/column_selector.py`
  保持 exact-safe scheduler semantics，补 batch-level wrapper。

- `BPC_future/learning/graph_builder.py`
  保持 backbone schema，必要时 versioned metadata extension。

- `BPC_future/scripts/build_gat_trajectory_cbf_dataset.py`
  抽出或扩展 batch-impact dataset builder。

- `BPC_future/scripts/train_gat_worker_roi.py`
  复用 loss/calibration helpers。

- `BPC_future/scripts/audit_gat_embedding_knn_ood_external_validation.py`
  扩展 family/context holdout metrics。

- `BPC_future/solver/journey_driver.py`
  只增加默认关闭的 shadow / opt-in hooks。

- `BPC_future/pricing/journey_pricing.py`
  只增加 default-off priority ordering hooks，确保 exact fallback covers full universe。

不建议修改：

- `manual_journey_reduced_cost()` formula。
- pricing state certificate semantics。
- official baseline configs。
- branch/cut math semantics。

## 13. Configuration Flags To Add

所有新增 flags 默认必须为 false：

```yaml
journey_gat_target_mode_shadow_enabled: false
journey_gat_pricing_priority_enabled: false
journey_gat_admission_scheduler_enabled: false
journey_gat_delay_queue_enabled: false
journey_gat_delay_queue_reprice_before_certificate: false
journey_gat_certificate_hard_filter_enabled: false
journey_gat_batch_impact_checkpoint_path: ""
journey_gat_batch_impact_device: "cpu"
journey_gat_knn_ood_shell_enabled: false
journey_gat_priority_first_task_enabled: false
journey_gat_priority_transition_enabled: false
journey_gat_priority_arc_option_enabled: false
journey_gat_priority_residual_family_enabled: false
journey_gat_admission_max_delay_rounds: 0
journey_gat_admission_max_delay_queue_size: 0
journey_gat_admission_log_shadow_decisions: false
journey_gat_admission_safe_source_ready: false
journey_gat_admission_allow_unsourced_delay: false
journey_gat_admission_require_online_safe_hit_for_delay: true
```

Hard safety flags：

```yaml
journey_gat_certificate_hard_filter_enabled: false
```

该 flag 应永久保持 false。若未来为了测试创建 test-only dummy path，必须只在测试中显式允许，且不能进入 benchmark configs。

Admission scheduler 还必须有 safe-source gate：

- `journey_gat_admission_scheduler_enabled=true` 只表示允许 scheduler 参与；
- 如果没有通过 Stage 3 gate 的 checkpoint / CBF / kNN / OOD safe source，或者没有显式 safe candidate ids，scheduler 不得把 true-RC negative 放入 `DELAY_QUEUE`；
- 即使存在 offline safe candidate ids，也必须先在当前 online candidate batch 中命中至少一个 safe id，才允许 mutating delay；否则记录 `reason=no_online_safe_hit` 并 pass-through；
- 默认 `journey_gat_admission_safe_source_ready=false`、`journey_gat_admission_allow_unsourced_delay=false`；
- `journey_gat_admission_require_online_safe_hit_for_delay=true` 是覆盖保护，不是功能开关；只有当 safe-source 已证明覆盖当前 benchmark / family / task-size 时，才允许在实验配置中显式设为 false；
- `journey_gat_admission_allow_unsourced_delay=true` 只能用于单元测试或 diagnostic experiment，不能进入 5/10/20 benchmark configs。

## 14. Metrics And Acceptance Criteria

### Training / Gate Model Acceptance

训练阶段必须把模型当成未来 admission scheduler 来验收，而不是普通分类器。

validation loss / F1 / recall 是诊断指标，不是 checkpoint 入场资格。训练验收必须先证明 precision、ROI、safety 和 coverage，再讨论 loss 是否更好。

训练验收的硬顺序固定为：

```text
1. precision / safe precision pass
2. precision CI lower bound pass
3. false-high-priority / false-safe pass
4. accepted ROI pass
5. accepted ROI over random / best-RC / old-GAT baseline pass
6. accepted ROI CI lower bound pass
7. nonzero useful coverage pass
8. family/context holdout pass
9. only then compare utility, tail proxy, validation loss, F1, recall
```

任一前置 gate 失败时，报告必须直接写 `stage4_candidate_ready=false`，不能用更高 recall、更低 loss、更好 AUC 或更漂亮 embedding 图来抵消。

必须报告：

- validation loss / F1 / recall；
- high-priority precision / safe precision；
- high-priority precision / safe precision 的 confidence lower bound；
- accepted batch count；
- accepted batch rate；
- accepted batch ROI；
- accepted batch ROI over baseline 和 confidence lower bound；
- expected trajectory utility；
- false high-priority on delay；
- false-safe union rate；
- OOD delay rate；
- family/context holdout worst-case precision；
- family/context holdout worst-case accepted ROI；
- baseline comparisons against random, best-RC, and old-GAT selection。
- selected threshold / OOD / fallback rule；
- rejected checkpoint reasons。

通过条件：

- high recall 不能抵消 low precision；
- high F1 不能抵消 low accepted ROI；
- zero-FP 但 accepted batch count = 0 不能进入 online A/B；
- accepted batch ROI 的 point estimate 和 lower bound 都必须高于 random / best-RC / old-GAT baseline；
- false high-priority on delay 和 false-safe union rate 必须满足 Stage 3 硬阈值；
- 训练选择、训练报告和 Stage 4 shadow 必须使用同一套 threshold / OOD / fallback rule；
- any family/context holdout failure must force family-specific delay fallback。

### 5/10 No-regression

必须报告：

- status counts；
- primal/dual/gap exact match；
- node count；
- RMP solves；
- pricing calls；
- exact pricing calls；
- wall-time avg/max overhead；
- official result mismatch count = 0。

通过条件：

- all 5/10 official statuses match baseline；
- no primal/dual/gap regression；
- no new certificate source；
- overhead 符合阶段阈值，优先要求 no-op 或近零开销。

### 20-task Wall-time ROI

必须报告：

- OPTIMAL count within 200s；
- median/max wall-time；
- time to incumbent；
- final primal；
- final dual bound；
- exact pricing closure state；
- RMP solves；
- pricing/exact calls；
- generated sequences；
- evaluated timed trips；
- final judge retry count；
- hidden negative count；
- accepted batch count；
- accepted batch ROI；
- delay rate；
- false high-priority on delay。

通过条件：

- agreed matrix repeatable improvement；
- no case with official result regression；
- tail retry 或 proof workload 有实证下降；
- accepted batch count > 0 且 ROI 高于 baseline selection。

### Exactness Safety

必须报告：

- `selector_is_pricing_oracle=false`
- `selector_can_certificate=false`
- `official_bound_effect=false` for audit/worker paths
- certificate source event
- pricing state distribution
- delay queue negative reprice summary
- incomplete reason if closure fails

通过条件：

- no GAT/OOD/kNN event creates `CERTIFIED_NO_NEGATIVE`。
- exact pricing incomplete 时 no official bound。
- delay queue 中 current true-RC negative 未清理或未 re-expose 时不能 certificate。
- branch/cut context changes invalidate stale GAT decisions。

## 15. Failure Modes And Rollback Plan

### Failure Modes

- GAT learns RC proxy instead of trajectory impact。
- Same-context labels are contaminated by branch/cut/dual drift。
- Delay queue silently behaves like reject。
- Zero-FP shell accepts no batch。
- Calibrated shell accepts harmful batch。
- 5/10 overhead appears from logging/model load even in no-op mode。
- 20-task incumbent improves but final certificate tail worsens。
- Exact pricing full fallback accidentally skipped after priority search。
- Certificate preflight forgets delayed negative columns under current duals。

### Rollback Plan

- All online flags default false; rollback is config-only disable。
- Keep baseline configs untouched。
- Keep GAT checkpoints diagnostic-only until gates pass。
- If 5/10 regression appears, disable all hooks for `task_count < 20` and remove model loading from small-scale path。
- If 20 ROI fails, keep dataset/report artifacts but do not merge opt-in config into mainline benchmark。
- If certificate safety test fails, block all online admission and pricing priority integration until exact fallback proof is restored。

## 16. Final Success Definition

最终成功必须同时满足：

1. Exactness 不变。
   `CERTIFIED_NO_NEGATIVE` 只来自 exact pricing full closure；GAT、CBF、kNN、OOD 不产生 official bound 或 certificate。

2. 5/10 no-regression。
   official result 不变，默认配置不启用新 gate/worker，固定开销可控或 no-op。

3. 20-task exact target。
   agreed 20-task benchmark matrix 在 200s 内稳定 OPTIMAL，official dual bound available，proof source 可审计。

4. 20-task ROI 可解释。
   wall-time、tail retry、pricing workload、generated/evaluated counts、basis/support movement 至少一组核心指标稳定改善。

5. 30/50/100 扩展路径明确。
   即使不能立即证明最优，也能在 exact-safe fallback 下报告 time-to-incumbent、primal/gap、pricing workload、pool growth 和 tail retry 改善。

6. Deployment gate 保守。
   任何 production default 前必须有 instance/family/context holdout、5/10 full no-regression、20-task repeat A/B、certificate safety test 全部通过。

## 下一步最小安全实现任务清单

1. 只实现 offline `JourneyCandidateEncoder` / `BatchImpactEncoder` 原型和 toy tests。
2. 新增 same-context intervention dataset schema，不接 online solver。
3. 扩展现有 post-injection audit，输出 H-step `delta_V`、`barrier_slack`、tail retry labels。
4. 训练一个 diagnostic-only batch-impact checkpoint，明确 `production_ready=false`。
5. 做 kNN/OOD holdout 审计，要求 false high-priority on delay 接近 0 且 accepted count > 0。
6. 通过后再进入 shadow-mode logging；shadow 不改变 solver。
7. shadow 5/10 no-regression 后，才允许指定 20-task hard-tail opt-in A/B。


## 需要避免陷入的局部

### 需要区分两种“局部”。

A. 不影响正确性的局部

这种是可接受的：

GAT 只优先搜某些 family
GAT 只 high-priority 某些 batch
其他 true-RC negative 进入 DELAY_QUEUE
最终 exact pricing 仍然 full scan

这种情况下，如果 GAT 判断局部错了，最多是：

加速效果不好
回到 baseline exact pricing

不会破坏证明。

这是你计划里要坚持的边界：GAT 只能改变搜索顺序和 admission priority，不能改变 official pricing universe。

B. 会导致算法变启发式的局部

这种必须禁止：

GAT 认为某些区域不重要
  ↓
pricing 永久不搜这些区域
  ↓
真实负列被漏掉
  ↓
RMP lower bound 被错误证明

或者：

GAT 把 true-RC negative 判为 unsafe
  ↓
直接 reject / discard
  ↓
delay queue 被当作 no-negative
  ↓
certificate 错误

### 可能陷入局部的具体原因
1）GAT 过度偏向某个 residual family

比如它在 sector-wave 上学到：

low_risk arc option + 某类 sequence 很有用

上线后可能一直优先搜这个 family，导致其他 family 的负列发现变慢。

解决：必须有 exploration / fallback：

GAT priority search
  +
baseline exact search
  +
periodic non-GAT patrol

GAT 只能重排搜索顺序，不能让某些 shard 永远不搜。

2）GAT high precision 但 recall 太低

现在 same-run 报告显示 precision 很好，但 recall 只有约 0.545。

这说明它可能：

很安全
但过度保守
大量好列进 DELAY_QUEUE
加速不明显

解决：训练阶段不能只追求 zero false positive，还要要求：

accepted_batch_count > 0
accepted_batch_ROI > baseline
predicted_high_priority_count > 0
family-level productivity signal

否则就是“安全但没用”。

3）它可能学到局部 RC proxy，而不是 trajectory impact

如果训练数据只是：

rc < 0

GAT 会学成：

reduced-cost 近似器

这不能解决拖尾。

same-run 报告已经指出：rc < 0 只能说明当前 dual 下可加，不说明会改变 RMP 轨迹；很多负列只是 replacement，能进池但不改变 active support、dual 震荡或 final-judge tail。

解决：必须用 same-context intervention label：

同一个 theta / basis / cuts / branch / pool context
加入 candidate batch
重新解 RMP
观察 objective / dual / basis / tail 的真实变化

报告里也已经把有效样本规则写清楚：positive label 应该是 trajectory_improves_objective_dual_or_tail，并且 required context 是同一 theta_basis_cuts_branch_pool。

4）GAT 可能造成新的反馈回路

一旦 GAT 上线，它会改变：

pricing search order
admitted batch composition
RMP dual trajectory
future training distribution

这可能形成新的 feedback loop：

GAT 总是偏向某些列
  ↓
RMP 总是进入某类 basis
  ↓
日志中又更多这种 family
  ↓
下轮训练更偏

解决：要加入：

family-balanced sampling
exploration batches
random true-RC negative control batches
best-RC baseline batches
support-repair batches
replacement-heavy negative controls

否则它会形成自我强化的局部策略。

5）branch node 下可能失效

root 上有效，不代表 branch node 有效。
branch constraint 会改变 feasible universe 和 reduced-cost landscape：

same_vehicle / separate_vehicle
task_vehicle_on / task_vehicle_off

如果训练数据主要来自 root，GAT 在 branch node 可能判断错误。

解决：训练和验证必须有：

root context
branch depth 1+
different branch constraint families
family-level / context-level holdout

否则 20-task proof tail 仍然可能卡在 branch-node pricing proof。

### 怎样降低“陷入局部”的风险？

我建议加 8 个机制。

1）GAT 只做 priority，不做 hard prune
允许：先搜 GAT 推荐区域
禁止：永远不搜非推荐区域

这是最重要的安全边界。

2）DELAY_QUEUE 必须有限延迟

不能无限 delay。文档里已经写了 finite-delay 条件：

forall p, true_reduced_cost(p) < 0:
    p in delay_queue or exact_reachable_backlog
    and exists finite T_p such that p enters RMP or is re-exposed to exact pricing

建议配置：

max_delay_rounds
max_delay_queue_size
release_on_tail
release_before_certificate
3）certificate mode 必须关闭 GAT hard gate

最终证明阶段应该：

reprice delay queue under current true duals
add currently negative delayed columns
disable GAT hard filtering
run exact pricing full scan

只有 exact pricing exhausted + no negative 才能 certificate。

4）训练时加入 pairwise ranking

同一个 context 下，让模型学：

score(high-ROI batch) > score(low-ROI batch)

而不是只学二分类。
这样更适合“本轮多批候选，哪批先加”的问题。

5）加入 exploration quota

例如每轮：

80% GAT high-priority
20% best-RC / diverse / random negative control

这样防止 GAT 早期过拟合导致永远只搜局部。

6）family-local threshold

不要一个全局阈值打天下。

至少分：

20|greedy-anchor
20|random-wave
20|sector-wave
branch-depth buckets
terrain region

不同 family 的 residual dynamics 不一样，统一阈值容易某些 family 过保守或过激进。

7）监控 tail ROI，而不是只看 primal

如果 GAT 只是改善 incumbent，但：

dual_bound=None
final_judge_retry_count 不降
certificate_no_column_rounds 不降
exact_pricing_calls 不降

那它没有解决拖尾。

当前报告里 target-priority worker 就是这种状态：primal 有改善，但仍然 TIME_LIMIT、dual_bound=None，没有证明 tail retry 稳定减少。

8）保留 baseline exact fallback

任何时候如果 GAT 信号低、OOD、不确定、family 不熟悉：

abstain
return to baseline exact pricing

这比错误 high-priority 更安全。

### 2026-06-17 v107 sector-wave context contrast 状态

本轮在 v105 coverage frontier 和 v106 sector-wave repair audit 之后，新增
same-context contrast 审计：

```text
report =
  BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v107_sector_wave_context_contrast_zh.md
summary =
  BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/summary.json
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
stage3_completed = false
stage4_candidate_ready = false
selector_can_certificate = false
```

核心结论：

```text
pair_count = 6
missed_high_roi_pair_count = 4
missed_raw_rank_failure_rate = 1.0
missed_safe_rank_failure_rate = 1.0
recommended_next_step = train_sector_wave_same_context_pairwise_ranking_with_trace_features
```

v99 仍是 low-ROI / unsafe accept 抑制问题；v102/v103 的
`3d1bd8618099b573` 和 `45baa40751a0bf77` 则不是单纯阈值近失。
在这些 same-context pair 中，high-ROI positive 相对 accepted low-ROI/bad
negative 的 raw candidate score 和 safe/risk-adjusted candidate score 都被反排。

因此下一步不应继续盲扫全局 threshold，也不能只调 risk penalty；应进入
sector-wave context-local pairwise ranking / representation repair，把训练目标明确写成：

```text
score(context, high_ROI_batch) > score(context, accepted_low_ROI_or_bad_batch)
```

并继续保留 Stage 3 hard gate：precision / safe precision、false-safe /
false-high-priority、accepted ROI、coverage、family/context holdout 任何一项失败，
都必须保持 `stage4_candidate_ready=false`。
