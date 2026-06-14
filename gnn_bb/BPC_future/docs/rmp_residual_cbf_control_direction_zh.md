# RMP-Residual Switching System 与 CBF 稳定化方向

日期：2026-06-14

本文档把当前 BPC_future 的根因判断压缩成一个可执行的控制论方向。
它不是 production 证明，也不声称 20-task 已经可解；它定义下一步应该
采集什么、训练什么、如何保持 exactness，以及哪些路径暂时不应继续扩大。

## 一句话结论

当前瓶颈不是单次 pricing/search/selector 不够强，而是 RMP dual、active
basis 与 residual negative family 形成了一个 state-dependent switching
feedback system。现有 Pulse / worker / GNN selector 主要在当前 residual
snapshot 上找 true-RC negative columns，但没有控制加列后
`theta_{t+1}` 和 residual mode `z_{t+1}` 是否更稳定。

因此下一步不应继续把 GNN 作为 pricing oracle 或静态 column scorer，而应
把它改造成 trajectory-level RMP-impact / CBF slack predictor，只对已经通过
true-RC 验证的候选列批次做 admission ranking。这里的控制对象不是单列
`p`，而是当前系统状态 `x_t` 下的一批候选列 `u_t` 对后续 RMP trajectory
的影响。

## 最小系统模型

离散化后的控制系统写成：

```text
x_t = (theta_t, B_t, z_t)

theta_t : 当前 RMP true dual
B_t     : 当前 active basis / active support 结构
z_t     : residual family mode signature
sigma_t : residual family switching mode
u_t     : column admission / batch composition action

x_{t+1} = F_{sigma_t}(x_t, u_t)
```

这里唯一直接改变 RMP 动力学的合法控制入口是：

```text
u_t = 本轮向 RMP 加入哪些已经验证 true-RC negative 的 JourneyColumn，
      以及这些列的 batch composition。
```

Pulse、worker、exact pricing 的职责是产生候选；pruning、archive、shard 的
职责是降低搜索成本；GNN 不能生成 certificate，也不能替代 true-dual exact
pricing。GNN 最多只能影响 `u_t` 的排序、筛选和 abstain。

更准确地说，当前 gate 不应是：

```text
p -> score(p) -> add / skip
```

而应是：

```text
(x_t, u_t) -> predicted_delta_V_{t->t+H}
(x_t, u_t) -> predicted_barrier_slack_{t->t+H}
(x_t, u_t) -> P(stable trajectory transition)
```

其中 `u_t` 是已经 true-RC 验证过的 column batch。单列的 reduced cost、
路径、能耗、时间窗只是不完整的局部特征；真正的控制状态还必须包含
`theta_t`、active support `B_t`、recent dual/support movement，以及
residual family signature `z_t`。

## 为什么之前方法没有形成稳定收益

已有证据显示 worker 可以安全找到并加入 true-RC negative columns，但
Phase 7O / 8Q 类实验中，更多负列没有稳定转化为 wall-time、tail retry 或
RMP trajectory 改善。统一解释是：

```text
find negative columns       -> local snapshot improvement
add columns to RMP          -> B_{t+1}, theta_{t+1} change
theta_{t+1} reshapes z_{t+1}-> new residual family appears
```

如果 `z_t -> z_{t+1}` 进入新的 hard mode，负列本身真实且可加也不够。
因此“继续加大 worker 时间、加更多最负列、扩大 Pulse search”不是当前证据
支持的主线。

## Lyapunov Surrogate

先不追求数学闭式 Lyapunov 函数，而定义一个可观测 surrogate energy：

```text
V_t =
  a1 * dual_l1_delta_t
+ a2 * basis_turnover_t
+ a3 * residual_mode_entropy_t
+ a4 * hidden_negative_count_t
+ a5 * final_judge_retry_count_t
+ a6 * replacement_ratio_t
- a7 * objective_progress_t
- a8 * support_changing_progress_t
```

各分量必须来自 RMP / pricing / worker 日志或新增 no-certificate-effect
audit 字段。权重第一版不需要学习；可以从固定正权重和归一化分位数开始。

## CBF 约束

定义 safe set：

```text
S = { x : V(x) <= V_crit }
```

定义 barrier：

```text
h(x) = V_crit - V(x)
```

对当前离散 RMP 迭代，one-step 诊断约束是：

```text
h(x_{t+1}) - h(x_t) + alpha * h(x_t) >= 0
```

等价地：

```text
V(x_{t+1}) <= (1 - alpha) * V(x_t) + alpha * V_crit
```

如果候选 batch `u` 的预测 `barrier_slack` 为负，则该 batch 不能作为
默认加列策略，只能：

- abstain，交回现有 exact path；
- 缩小 batch；
- 改变 family composition；
- 提高 support-changing 比例；
- 降低 replacement 比例；
- 或仅在 audit-only 模式记录。

这里有一个必须保持的 exactness guard：

```text
CBF gate 是稳定性调度层，不是负列过滤器；
CBF gate 可以排序、延迟、缩小 batch、或本轮 abstain；
CBF gate 不允许永久丢弃任何 true-RC negative column。
```

标准 column generation 的精确性依赖完备性：

```text
forall p in Omega, rc(p) < 0  =>  p eventually remains reachable by pricing/RMP
```

因此 trajectory gate 只能是 soft control / admission priority。它不能成为
hard filter。如果某个 true-RC negative batch 被 gate 判为当前不稳定，
正确处理是：

- 不作为本轮优先加列；
- 保留在 exact path、候选 backlog 或后续重新定价可达空间中；
- 继续允许现有 true-dual exact pricing / fallback 发现并加入它；
- 绝不把 `gate reject` 解释成 `no negative` 或 certificate。

只要 gate 只是改变进入 RMP 的顺序，最优性证明仍可由现有 exact pricing
完备路径承担；一旦 gate 永久屏蔽负列，系统就退化成启发式过滤 CG，
不能再声称精确最优。

正确的 CBF admission 结构必须拆成三层：

```text
Layer 1: completeness set
N_t = { p : true_reduced_cost(p) < 0 }
所有 p in N_t 必须最终保持可达，不能被 gate 永久丢弃。

Layer 2: soft barrier
safe(p or batch) = 1[ predicted_barrier_slack_{t->t+H} >= 0 ]
它只改变优先级，不改变 p 是否允许最终进入系统。

Layer 3: scheduler
if rc(p) < 0 and safe(p):
    decision = HIGH_PRIORITY
elif rc(p) < 0 and not safe(p):
    decision = DELAY_QUEUE
else:
    decision = REJECT_NONNEGATIVE_ONLY
```

因此 `unsafe` 的含义是 `delay`，不是 `reject`。CBF 在这里的数学意义是
ordering / scheduling constraint，而不是改变 CG 的 completeness condition。

还必须补一个有限延迟引理：

```text
forall p, true_reduced_cost(p) < 0:
    p in delay_queue or exact_reachable_backlog
    and exists finite T_p such that p enters RMP or is re-exposed to exact pricing
```

这保证 proof 阶段不会因为稳定性 gate 被无限拖住。换句话说，CBF scheduler
可以改变负列进入 RMP 的时间顺序，但不能让任何负列无限期悬挂在
DELAY_QUEUE 中，也不能把 delay queue 当作 no-negative 证明。

但这只是第一层诊断。用户目标不是让 `V_{t+1}` 偶然下降，而是让
RMP / residual mode trajectory 进入更稳定 basin。因此真正的 gate 应升级为
horizon 版本：

```text
h(x_{t+H}) - h(x_t) + alpha * h(x_t) >= 0
```

等价地预测：

```text
Delta V_{t->t+H}(x_t, u_t)
barrier_slack_{t->t+H}(x_t, u_t)
bad_mode_switch_{t->t+H}(x_t, u_t)
```

当前 one-step gate 只能作为 calibration seed；不能因为 one-step 标签可学习，
就认为 production worker gate 或 official certificate gate 可用。

## GNN 的唯一合法位置

GNN 不学习：

```text
column -> good / bad
```

而学习：

```text
(state_t, candidate_batch) -> predicted_delta_V_{t->t+H}
(state_t, candidate_batch) -> predicted_barrier_slack_{t->t+H}
(state_t, candidate_batch) -> P(bad_mode_switch_{t->t+H})
```

也就是近似：

```text
U_safe(x_t) = { u : h(x_{t+1}) - h(x_t) + alpha h(x_t) >= 0 }
```

GNN 输出只能用于 conservative admission controller。即使 GNN 预测错误，
系统也必须继续保留 exact fallback：

- 不跳过 true-dual exact pricing；
- 不产生 official lower bound；
- 不生成 no-negative certificate；
- 不把未经 `manual_journey_reduced_cost()` 验证的列加入 RMP；
- 低置信或 out-of-distribution context 一律 abstain。

因此 GNN 的角色是 trajectory impact model，而不是 column-level
classifier。一个负列 batch 只有在预测能降低 Lyapunov surrogate 或至少不
违反 CBF horizon slack 时，才可作为 experimental admission 候选；否则
即使所有列 true-RC negative，也只能交回现有 exact path 或 audit-only 记录。

## residual mode signature `z_t`

第一版 `z_t` 不需要完整表示 residual field，只需要低秩可观测 signature：

```text
task-set family histogram
first-task / second-action shard histogram
time-window bucket histogram
path-option family histogram
support-overlap histogram
replacement vs support-changing ratio
best true-RC per family
negative candidate count per family
forbidden-signature hit count
duplicate/signature replacement count
```

这些字段的目标不是证明最优性，而是让模型观察 residual family 是否从一个
mode 跳到另一个 mode。

## 下一步工程阶段

### CBF-1：mode transition audit

只加日志和离线审计，不改变 solver 行为。

每个 CG/RMP round 记录：

```text
theta_t summary
active basis / support summary
column pool signature
candidate negative family signature
added batch family signature
z_t
z_{t+1}
dual_l1_delta
basis_turnover
RMP objective_delta
hidden_negative_count
final_judge_retry_count
replacement_ratio
support_changing_ratio
V_t
V_{t+1}
barrier_slack
```

验收：

- 5/10 默认行为不变；
- audit-only 不产生 certificate / lower bound side effect；
- 能区分 5/10/20 的 mode switching 和 `V` 变化；
- 能重建 `state_t, action_t, state_{t+1}` 数据。

### CBF-2：offline trajectory barrier dataset

从 audit 日志构造 batch-level 样本：

```text
input  = state_t + candidate_batch_features
label  = horizon_delta_V / horizon_barrier_slack / horizon_bad_mode_switch / tail_improved
split  = instance-level holdout, not random-row split
```

验收：

- 必须包含 5、10、20 多实例；
- 必须包含 noop / worsened / improved / support-changing / replacement；
- 不允许用 post-addition unavailable features 伪造 online signal；
- 所有 label 可由日志复算。
- 训练特征必须排除 `state_next_*`、`delta_*`、`horizon_*` 与所有 label；
- one-step dataset 可作为诊断起点，但 production gate 前必须通过
  horizon-level holdout。
- audit 必须显式记录 `gate_can_permanently_discard_negative_columns=false`。

### CBF-3：GAT impact / barrier model

模型可以复用现有 GAT encoder，但 head 改为 RMP-impact / barrier head。

输出：

```text
predicted_horizon_delta_V
predicted_horizon_barrier_slack
predicted_horizon_bad_mode_switch_probability
predicted_tail_improvement_probability
```

验收：

- conservative threshold 下 false safe rate 必须极低；
- OOD / missing context 必须 abstain；
- 5/10 no-regression guard 必须优先于 20 speedup。

### CBF-4：opt-in conservative admission controller

仅在 experimental opt-in 下启用。

控制逻辑：

```text
if exact candidate batch exists
and GNN predicts positive barrier_slack with high confidence
and small-scale no-regression gate passes
and context is in-distribution:
    add selected batch
else:
    abstain for this controller turn and use existing exact path
```

这里的 `abstain` 不是永久拒绝；它只表示 CBF controller 不接管本轮 admission。
候选负列仍必须通过现有 exact path 保持 eventually reachable。

验收：

- 5/10 不退化；
- no certificate side effect；
- no false lower bound；
- worker no-column / incomplete 不改变 official state；
- 20-task wall-time、retry count、dual trajectory 至少有稳定改善信号。

### CBF-5：production A/B gate

只有同时满足以下条件，才允许考虑默认启用：

```text
5-task no regression
10-task no regression
20-task exact solution within target budget on agreed matrix
no critical disagreement
official lower bounds identical in semantics
GNN never certifies no-negative
fallback exact path remains complete
```

当前目标“20 规模 200 秒内精确解”只有在这一阶段通过后才能声称完成。

## Delay-Queue Scheduler：精确性保护层

CBF gate 不能实现为 hard reject。正确结构是一个延迟调度层：

```text
if true_reduced_cost(p) < 0 and predicted_safe(p):
    decision = HIGH_PRIORITY
elif true_reduced_cost(p) < 0 and not predicted_safe(p):
    decision = DELAY_QUEUE
else:
    decision = REJECT_NONNEGATIVE_ONLY
```

这里 `DELAY_QUEUE` 的含义是“当前不优先进入 RMP”，不是“丢弃”。上线前
必须满足有限延迟引理：

```text
forall p, true_reduced_cost(p) < 0:
    p remains in delay_queue or exact_reachable_backlog
    and exists finite T_p such that p enters RMP or is re-exposed to exact pricing
```

因此：

- CBF scheduler 可以排序、延迟、缩小 batch；
- CBF scheduler 不能永久屏蔽任何 true-RC negative column；
- delay queue 不能被解释成 no-negative；
- delay queue 不能参与 certificate；
- proof 阶段不能因为 CBF scheduler 花掉大块求解时间；
- 只要 scheduler 未 ready，默认行为必须是 delay / abstain，并交回现有
  exact path。

当前 `BPC_future/scripts/audit_cbf_delay_queue_scheduler.py` 已把该语义做成
离线审计。基于全局 H=2 dataset 的最新结果为：

```text
row_count = 139
label_counts = {"0": 103, "1": 36}
min_high_priority_threshold = 0.8
scheduler_ready = false
scale_scheduler_ready = false
family_scheduler_ready = false
ready_task_counts = []
ready_families = []
production_ready = false
```

这说明当前 delay-queue 结构是正确的，但模型还没有资格进入 production
admission controller。尤其 20-task scale、random-wave 和 sector-wave 仍有
unsafe high-priority holdout fold。现阶段只能保留为 audit-only，不允许接
worker、certificate 或 official lower bound。

对应的 false-positive 目录已经生成：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_false_positive_catalog.py
summary = BPC_future/results/cbf_delay_queue_false_positive_catalog_global_all_h2_20260614/summary.json
records = BPC_future/results/cbf_delay_queue_false_positive_catalog_global_all_h2_20260614/false_positive_records.jsonl
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_false_positive_catalog_global_all_h2_zh.md
```

最新目录显示：

```text
false_positive_record_count = 6
false_positive_by_scope = {"family": 4, "scale": 2}
false_positive_by_family = {
  "20|greedy-anchor": 1,
  "20|random-wave": 1,
  "20|sector-wave": 4
}
```

这些样本一律要求：

```text
predicted_decision = HIGH_PRIORITY
required_safe_decision = DELAY_QUEUE
exactness_action = force_delay_not_discard
```

所以当前阻塞不是 CG 完备性理论，而是 trajectory gate 的在线 state 信息仍
不足以区分部分 H=2 unsafe transitions。下一步如果继续，应补这些
false-positive 邻域的数据或特征，而不是放开 scheduler。

feature-gap 审计进一步确认了这一点：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_feature_gap.py
summary = BPC_future/results/cbf_delay_queue_feature_gap_audit_global_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_feature_gap_audit_global_all_h2_zh.md
```

最新结果：

```text
unique_false_positive_row_count = 5
safe_like_false_positive_count = 3
safe_like_false_positive_ratio = 0.6
single_feature_guard_available = true
production_ready = false
```

含义是：多数唯一 false-positive 在当前在线特征空间里更像 safe transition。
因此，单纯训练更久或降低阈值不是主线；需要补充能在线观测的
trajectory/context 特征，尤其是能提前识别 H=2 mode switch 和 barrier slack
恶化的状态变量。当前找到的单特征 guard 只能作为诊断线索，不能作为
production admission rule。

已尝试一个最小 history 特征版本：

```text
script = BPC_future/scripts/build_cbf_trajectory_history_dataset.py
summary = BPC_future/results/cbf_trajectory_history_dataset_global_all_h2_20260614/summary.json
```

它只添加更早 transition 的 `history_prev_*` 在线字段，未使用当前未来字段。
但重跑 scheduler 后结果变差：

```text
baseline false_positive_record_count = 6
history false_positive_record_count = 11
baseline 20-scale unsafe_high_priority_fold_count = 2
history 20-scale unsafe_high_priority_fold_count = 5
```

因此，下一步不能简单堆 lag/history 特征。需要更结构化的在线状态表示：
mode-signature distance、family-local risk density、neighbor-risk score、
或针对 false-positive 邻域补采后再做 conservative abstain。

已进一步审计 kNN neighbor-risk scheduler：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_risk_scheduler.py
summary = BPC_future/results/cbf_delay_queue_knn_risk_scheduler_audit_global_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_risk_scheduler_audit_global_all_h2_zh.md
```

结果：

```text
knn_k = 5
max_neighbor_unsafe_fraction = 0.0
scale_scheduler_ready = true
family_scheduler_ready = false
production_candidate_ready = false
production_ready = false
```

它把 20-scale unsafe high-priority fold 从 2 降到 0，并保留 4 个
high-priority，是目前最有希望的调度信号。但 family-level 仍未通过，
尤其 `20|sector-wave` 仍有 false-positive。因此它只能作为下一步
family-local risk memory / sector-wave 补采方向，不能直接接 production。

参数网格审计进一步确认：在当前特征空间里，单纯调 `k / neighbor risk /
probability threshold` 不足以通过 production gate。

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_risk_grid.py
summary = BPC_future/results/cbf_delay_queue_knn_risk_grid_audit_global_all_h2_20260614/summary.json
trial_count = 40
best_scale_ready_count = 27
best_production_candidate_ready = false
production_candidates = []
```

所有 40 个组合都未能同时满足 family-level safety 与 productivity。
因此下一步不应继续在同一特征空间调参，而应做 family-local risk memory、
sector-wave false-positive 补采，或引入更能表示 residual mode geometry 的
在线特征。

## kNN + OOD Safe-Radius Delay Scheduler

在 kNN neighbor-risk 基础上，又加了一层 safe-manifold radius guard：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_ood_scheduler.py
summary = BPC_future/results/cbf_delay_queue_knn_ood_scheduler_audit_global_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_ood_scheduler_audit_global_all_h2_zh.md
```

规则是：

```text
先满足 train zero-FP probability threshold；
再要求 kNN neighbor unsafe fraction <= 0.0；
再要求 row 落在训练 safe manifold 的 radius 内；
否则 true-RC negative 只能进入 DELAY_QUEUE。
```

当前结果：

```text
knn_k = 5
max_neighbor_unsafe_fraction = 0.0
safe_radius_quantile = 0.9
safe_radius_multiplier = 1.0
scale_scheduler_ready = true
family_scheduler_ready = true
production_candidate_ready = true
production_ready = false
ready_task_counts = [20]
ready_families = [{"task_count": 20, "family": "sector-wave"}]
```

具体留出表现：

```text
20-scale:
  evaluated_count = 18
  unsafe_high_priority_fold_count = 0
  total_high_priority_count = 3
  productive_high_priority_fold_count = 3

20|sector-wave:
  evaluated_count = 6
  unsafe_high_priority_fold_count = 0
  total_high_priority_count = 3
  productive_high_priority_fold_count = 3
```

这是目前第一个同时通过 scale-level 和 family-level candidate 条件的离线调度器。
但它仍只是 `production_candidate_ready=true`，不是 `production_ready=true`：

- 只读 H=2 dataset，不运行 BPC / pricing / RMP；
- 不生成列；
- 不影响 certificate 或 official lower bound；
- 不能作为 pricing oracle；
- 仍需要独立验证和 opt-in audit smoke。

为避免 proof 阶段变成新瓶颈，delay queue scheduler 的机器合同进一步固定为：

```text
delay_queue_can_extend_proof_budget = false
delay_queue_runs_proof_sweep = false
proof_stage_budget_effect = none_existing_exact_deadlines_unchanged
proof_stage_policy = delay_queue_never_replaces_or_extends_exact_final_judge
```

也就是说，CBF scheduler 可以改变 true-RC negative columns 的进入顺序，但不能
要求 final judge 为了清空 delay queue 额外花大块时间。有限延迟只能通过
RMP admission / exact reachable backlog 的调度实现，不能通过延长证明阶段实现。

随后做了 kNN+OOD 参数鲁棒性网格：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_ood_grid.py
summary = BPC_future/results/cbf_delay_queue_knn_ood_grid_audit_global_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_ood_grid_audit_global_all_h2_zh.md
```

网格：

```text
k = [3, 5, 7]
max_neighbor_unsafe_fraction = [0.0]
min_high_priority_threshold = [0.8, 0.85, 0.9]
safe_radius_quantile = [0.8, 0.9, 1.0]
safe_radius_multiplier = [0.75, 1.0, 1.25]
trial_count = 81
```

结果：

```text
production_candidate_count = 14
robust_candidate_ready = true
production_ready = false
radius_candidate_histogram = {
  "q=0.8,m=1.0": 3,
  "q=0.9,m=0.75": 2,
  "q=0.9,m=1.0": 3,
  "q=1.0,m=0.75": 6
}
```

这说明第一个 kNN+OOD candidate 不是单点偶然通过，而是在当前 H=2 数据上形成了
一个小的保守参数区域。最佳候选集中在 `k=5` 附近，`20-scale` 和
`20|sector-wave` 都保持 `unsafe_high_priority_fold_count=0`，同时仍有少量
high-priority。

但生产化判断仍不变：

- 这是同一 H=2 offline dataset 上的鲁棒性，不是独立数据验证；
- 当前 ready family 仍主要是 `20|sector-wave`，不是全 family；
- high-priority 数量很少，仍需验证真实 RMP trajectory ROI；
- 因此下一步只能做 independent holdout / opt-in audit-only smoke；
- 仍不能接 active worker、official certificate 或默认 benchmark。

随后新增独立 train/validation 审计：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_ood_external_validation.py
summary = BPC_future/results/cbf_delay_queue_knn_ood_external_validation_global_h2_to_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_ood_external_validation_global_h2_to_all_h2_zh.md
```

设置：

```text
train = cbf_trajectory_gate_dataset_global_h2_20260614
validation = cbf_trajectory_gate_dataset_global_all_h2_20260614
exclude_train_keys = true
knn_k = 5
max_neighbor_unsafe_fraction = 0.0
safe_radius_quantile = 1.0
safe_radius_multiplier = 0.75
```

结果：

```text
validation_row_count = 99
validation_candidate_ready = false
fp = 0
predicted_positive = 0
tp = 0
fn = 18
tn = 81
```

解释：严格外部验证下没有 unsafe high-priority，但也没有任何 high-priority。
这不是 exactness 风险，而是 productivity/ROI 风险。当前 kNN+OOD scheduler
在同集鲁棒性上有信号，但离开训练覆盖后太保守，还不能证明能加速真实求解。
因此下一步必须补独立验证数据或做 audit-only smoke 观察真实 RMP trajectory，
不能直接把该候选接入 active worker。

进一步把现有 capture JSONL 日志转成 validation trajectory dataset 后做只读验证：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_ood_capture_validation.py
summary = BPC_future/results/cbf_delay_queue_knn_ood_capture_validation_holdout_config_matched_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_ood_capture_validation_holdout_config_matched_zh.md
capture_paths = BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614
```

结果：

```text
validation_row_count = 33
task_count_histogram = {"20": 33}
family = 20|greedy-anchor
validation_candidate_ready = false
fp = 0
predicted_positive = 0
negative_count = 33
positive_count = 0
```

这说明在已有真实 capture 日志上，scheduler 仍然安全地全 delay，但该验证集本身
没有 positive trajectory label，无法证明 productivity。当前生产化 blocker 更明确：
需要收集包含 positive / mixed trajectory 的独立 20-task capture，或者做 opt-in
audit-only smoke 观察真实 high-priority 是否出现并产生 RMP movement。

随后做外部验证参数网格，允许 `k / threshold / safe radius` 在 train/validation
分离下重新选择：

```text
script = BPC_future/scripts/audit_cbf_delay_queue_knn_ood_external_grid.py
summary = BPC_future/results/cbf_delay_queue_knn_ood_external_grid_global_h2_to_all_h2_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_delay_queue_knn_ood_external_grid_global_h2_to_all_h2_zh.md
```

结果：

```text
trial_count = 81
external_candidate_count = 36
external_candidate_ready = true
false_positive_histogram = {"0": 81}
predicted_positive_histogram = {"0": 45, "1": 9, "4": 3, "5": 6, "6": 6, "7": 3, "8": 9}
```

典型候选：

```text
knn_k = 3
max_neighbor_unsafe_fraction = 0.0
min_high_priority_threshold = 0.8
safe_radius_quantile = 1.0
safe_radius_multiplier = 1.0
validation fp = 0
validation predicted_positive = 8
validation tp = 8
validation recall = 0.4444444444
```

这修正了上一条固定参数结论：`k=5` 确实过保守，但外部验证参数网格能找到
zero-FP 且有 productivity 的候选。候选信号主要来自 `20|sector-wave`；
`20|greedy-anchor` 在验证集中基本保持全 delay。

用同一个 `k=3` 候选复查已有真实 greedy-anchor capture：

```text
summary = BPC_future/results/cbf_delay_queue_knn_ood_capture_validation_holdout_config_matched_k3_20260614/summary.json
validation_row_count = 33
fp = 0
predicted_positive = 0
negative_count = 33
positive_count = 0
```

因此当前生产化方向进一步收窄为：

- 只考虑 `20|sector-wave` 的 opt-in audit-only smoke；
- 不对 greedy-anchor 放行；
- 不接 official certificate；
- 不接默认 worker；
- 先验证真实 solver 日志中是否出现 high-priority，以及这些 high-priority 是否
  对 RMP movement / tail retry 有实际贡献。

## 明确禁止的下一步

在 CBF-1 / CBF-2 数据未闭合前，不应做：

- 默认启用 worker；
- official certificate gate；
- 继续单纯增加 worker/Pulse time limit；
- 把 GNN 当 pricing oracle；
- 用 post-addition 特征训练 online selector；
- 用 narrow focused test 证明 5/10 no-regression 或 20 speedup；
- 把 true-RC negative count 当作 ROI 充分证据。

## 当前状态

```text
root_cause_direction = dual_driven_switching_system
control_entry = exact_verified_column_batch_admission
gnn_role = conservative_barrier_slack_predictor
production_ready = false
goal_complete = false
```

这表示理论方向已经收束，但还没有完成用户目标。下一步应先实现
CBF-1 mode transition audit，而不是继续扩大 snapshot-level worker 或
column selector。

## 2026-06-14 sector-wave smoke 后的生产化判断

已执行 `20|sector-wave` 的 opt-in audit-only smoke，验证 `k=3, threshold=0.8,
q=1.0, m=1.0` 的 kNN+OOD delay scheduler 候选。

证据路径：

```text
runbook = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/summary.json
validation = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_knn_ood_sector_wave_smoke_result_zh.md
```

结果：

```text
capture_event_count = 16
trajectory_validation_row_count = 8
validation_candidate_ready = false
fp = 0
predicted_positive = 0
tp = 0
fn = 5
tn = 3
production_ready = false
```

逐行 decision 诊断显示：

```text
decision_reason_counts = {
  delay_probability_below_threshold: 5,
  delay_neighbor_unsafe_fraction: 3
}
positive_delay_reason_counts = {
  delay_probability_below_threshold: 3,
  delay_neighbor_unsafe_fraction: 2
}
```

因此当前 CBF/kNN+OOD 候选仍然只证明“安全保守”，没有证明“有生产 ROI”。
它在真实 sector-wave smoke 中没有放出 high-priority，所以不能继续到 active
worker，更不能作为 production admission gate。当前阻塞主要在 probability
threshold 与 kNN unsafe-neighbor，而不是 OOD radius。GAT 的生产化价值应放在
trajectory/residual-family embedding：改善“稳定正例附近有 unsafe 邻居”和
“概率略低但实际稳定”的表示，而不是绕过 delay queue 安全壳。下一步如果继续
该方向，应先补 mixed / positive 真实 trajectory，或调整只读 scheduler 的
productivity，而不是放开 worker、certificate、parallel、resume 或
final-judge 预算。

## 2026-06-14 GAT 与 kNN/OOD 的当前边界

已增加只读 readiness audit，专门检查现有 GAT checkpoint 是否可以进入
CBF/kNN/OOD 生产化链路：

```text
script = BPC_future/scripts/audit_gat_cbf_knn_ood_readiness.py
summary = BPC_future/results/gat_cbf_knn_ood_readiness_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_cbf_knn_ood_readiness_zh.md
```

审计结论：

```text
all_checks_pass = true
embedding_candidate_ready = false
production_ready = false
gat_checkpoint_is_column_level_add_skip_not_trajectory_cbf = true
gat_training_contract_missing_label_horizon_cbf_feasible = true
sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal = true
```

这说明 GAT 没有被放弃，但现有 checkpoint 仍是旧的 column-level
add/skip/abstain selector。它有 exactness contract，不能 certificate，也
不是 pricing oracle；但它没有用 `label_horizon_cbf_feasible` 训练，因此还
不能作为 trajectory CBF gate 或 GAT embedding + kNN/OOD 的生产候选。

当前正确关系是：

```text
GAT = trajectory / residual-family embedding 或 impact predictor
kNN+OOD = conservative safety shell
unsafe negative = DELAY_QUEUE, not discard
certificate / official lower bound = unchanged exact path only
```

下一步若继续 GAT 方向，必须先构造 trajectory-labeled GAT dataset，训练
impact/barrier head 或导出 embedding，再用 kNN/OOD 在独立 sector-wave capture
上验证 high-priority productivity。没有该证据前，不应接 active worker 或
production admission gate。

## 2026-06-14 Trajectory-labeled GAT 数据集

已完成第一版离线 trajectory-labeled GAT 数据集构造：

```text
script = BPC_future/scripts/build_gat_trajectory_cbf_dataset.py
summary = BPC_future/data/gat_trajectory_cbf/v1/summary.json
manifest = BPC_future/data/gat_trajectory_cbf/v1/manifest.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_trajectory_cbf_dataset_zh.md
```

结果：

```text
all_checks_pass = true
sample_count = 136
candidate_count = 1599
instance_count = 23
label_counts = {add: 34, skip: 102}
has_mixed_horizon_labels = true
skipped_counts = {invalid_logical_graph: 3}
```

这里的 `add/skip` 是 `label_horizon_cbf_feasible` 的 H=2 batch-level
trajectory label，广播到 capture event 的 returned candidate journeys；它不是
旧的单列 immediate-impact 标签。因此该数据集可用于下一步训练
trajectory-aware GAT impact/barrier head，但不能直接替代 exact pricing 或
online gate。当前仍需新的 horizon checkpoint、GAT embedding + kNN/OOD
独立验证，以及 5/10 no-regression 和 20-task ROI smoke。

## 2026-06-14 Trajectory-CBF GAT checkpoint

已用上述 trajectory-labeled dataset 训练第一版 horizon-CBF GAT checkpoint：

```text
script = BPC_future/scripts/train_gat_trajectory_cbf.py
checkpoint = BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt
summary = BPC_future/results/gat_trajectory_cbf_training_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_trajectory_cbf_training_zh.md
readiness = BPC_future/results/gat_trajectory_cbf_knn_ood_readiness_20260614/summary.json
```

训练结果：

```text
target_label = label_horizon_cbf_feasible
sample_count = 136
candidate_count = 1599
train_add_precision = 0.7956
train_add_recall = 0.8825
validation_add_precision = 0.6522
validation_add_recall = 0.9880
selector_can_certificate = false
selector_is_pricing_oracle = false
production_ready = false
```

readiness 结果：

```text
embedding_candidate_ready = true
production_ready = false
production_blockers = [
  sector_wave_knn_ood_smoke_has_no_high_priority_productivity_signal,
  no_gat_embedding_knn_ood_external_validation_yet,
  no_5_10_no_regression_bpc_ab_yet,
  no_20_task_wall_time_roi_ab_yet,
  no_online_opt_in_solver_integration_yet
]
```

解释：GAT 已经从旧 column-level selector 推进到 trajectory-CBF checkpoint，
但它仍不能单独决定 add/skip。验证 precision 说明它会产生较多 false
positive，必须继续放在 kNN/OOD safety shell 下面；不通过 safety shell 的
true-RC negative 只能进 delay queue，不能永久过滤。

## 2026-06-14 GAT embedding + kNN/OOD external validation

已把 trajectory-CBF GAT checkpoint 的 embedding 接到 kNN/OOD safety shell 做
sector-wave 外部验证：

```text
script = BPC_future/scripts/audit_gat_embedding_knn_ood_external_validation.py
train_dataset = BPC_future/data/gat_trajectory_cbf/v1
validation_dataset = BPC_future/data/gat_trajectory_cbf/sector_wave_validation_20260614
summary = BPC_future/results/gat_embedding_knn_ood_sector_wave_validation_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_embedding_knn_ood_sector_wave_validation_zh.md
readiness = BPC_future/results/gat_trajectory_cbf_knn_ood_readiness_20260614/summary.json
```

结果：

```text
validation_candidate_ready = true
validation_row_count = 8
predicted_positive = 4
tp = 4
fp = 0
fn = 1
tn = 3
precision = 1.0
recall = 0.8
production_ready = false
```

这和上一版表格 kNN/OOD 的 `predicted_positive=0` 形成对照，说明 GAT
embedding 确实改善了“过于保守”的表示问题。当前 readiness blocker 已缩小为：

```text
no_5_10_no_regression_bpc_ab_yet
no_20_task_wall_time_roi_ab_yet
no_online_opt_in_solver_integration_yet
```

因此下一步才可以做 opt-in audit-only online smoke，验证 high-priority 是否
真的带来 RMP movement / tail retry 改善。仍禁止默认启用、禁止 certificate
effect、禁止 official lower-bound effect。

## 2026-06-14 GAT embedding capture-validation 链路

已新增端到端只读验证脚本，把真实 capture 日志直接串到 GAT embedding
kNN/OOD safety shell：

```text
script = BPC_future/scripts/audit_gat_embedding_knn_ood_capture_validation.py
capture_logs = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs
summary = BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_embedding_knn_ood_sector_wave_capture_validation_zh.md
```

结果：

```text
validation_candidate_ready = true
validation_row_count = 8
predicted_positive = 4
tp = 4
fp = 0
fn = 1
tn = 3
precision = 1.0
recall = 0.8
production_ready = false
```

readiness 现在优先读取该 capture-validation 结果作为更强证据：

```text
gat_embedding_validation_contract.evidence_source = capture_validation
production_blockers = [
  no_5_10_no_regression_bpc_ab_yet,
  no_20_task_wall_time_roi_ab_yet,
  no_online_opt_in_solver_integration_yet
]
```

这说明 GAT 没有被放弃，而是被放在正确位置：GAT 产生 trajectory /
residual-family embedding，kNN/OOD 做安全外壳。当前仍只是 audit-only：
不能做 pricing oracle，不能产生 certificate，不能改变 official lower bound；
unsafe true-RC negative 只能进入 delay queue，不能永久丢弃。

同时已生成 `20|sector-wave` 的下一步 smoke runbook：

```text
script = BPC_future/scripts/build_gat_embedding_sector_wave_smoke_runbook.py
summary = BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_embedding_sector_wave_smoke_runbook_zh.md
```

该 runbook 只生成 capture + validation 命令，不默认启用 worker 或证书。
下一步如果继续推进，应先跑 audit-only 的 5/10 no-regression 与 20-sector-wave
ROI smoke，再考虑任何 online opt-in 调度。

## 2026-06-14 GAT embedding audit-only A/B runbook

已补生产化前的 GAT embedding A/B 协议生成器：

```text
script = BPC_future/scripts/build_gat_embedding_audit_ab_runbook.py
summary = BPC_future/results/gat_embedding_audit_ab_runbook_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_gat_embedding_audit_ab_runbook_zh.md
analysis_script = BPC_future/scripts/audit_gat_embedding_audit_ab_results.py
```

该 runbook 生成 8 条命令：

```text
task005_baseline
task005_capture
task010_baseline
task010_capture
task020_baseline
task020_capture
task020_gat_embedding_capture_validation
audit_ab_result_analysis
```

当前检查：

```text
all_checks_pass = true
production_ready = false
active_worker_ready = false
certificate_ready = false
online_effect_enabled = false
```

语义边界：

- 5/10 pair 只验证 capture-only 是否保持 official result 不变；
- 20 pair 只收集 GAT embedding validation 所需日志；
- `audit_gat_embedding_audit_ab_results.py` 可以在命令跑完后判断 pre-online
  audit gate 是否通过；
- 这仍不能证明 wall-time ROI，因为没有 online opt-in effect；
- 任何 true-RC negative 仍不能被 GAT/kNN/OOD 永久丢弃。

因此这一步是把“下一步该怎么跑”固化为可回归协议，而不是生产化。
真正生产化还需要：

```text
5/10 online no-regression
20-task online wall-time ROI
online opt-in solver integration
```
