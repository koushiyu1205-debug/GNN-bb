# P0 V2 反事实轨迹训练目标方案：评审意见与修订建议

**评审日期：** 2026-07-24  
**评审对象：** Codex 提出的“以相对 P0 的反事实轨迹收益替代 `4/3/1/0` graded ListNet 主目标”方案  
**当前实验基准：** `FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`  
**当前生产默认：** `no_cut`

---

## 1. 执行结论

这版方案的核心方向是正确的，而且明显优于继续优化当前 `4/3/1/0` graded ListNet。

它完成了最重要的目标转换：

```text
从预测候选自身的属性
转向预测一次合法排序干预所产生的下游求解价值
```

当前实施报告已经说明：

- P0 V2 仍是实验 control，production 默认仍为 `no_cut`；
- linear 和两层 MLP 已完成离线五折训练，但未解锁在线 H/HA；
- 没有训练任何 GAT rung；
- 当前失败主要来自旧 harvest 契约、目标泄漏和离线代理指标缺少增量信号，而不是 exact solver 或证书链失效。

因此，重新定义训练目标是合法且必要的下一步。

### 综合评分

| 维度 | 评分 |
|---|---:|
| 与端到端求解性能的对齐 | 9.0/10 |
| exactness 与证书安全 | 9.5/10 |
| 干预归因设计 | 7.5/10 |
| timeout/删失处理 | 8.0/10 |
| 统计目标严谨性 | 6.5/10 |
| 首轮工程可执行性 | 7.0/10 |
| 综合 | **8.0/10** |

### 审批意见

**可以批准为新的研究设计方向，但不能原样进入实现。**

在正式采集 intervention 数据之前，至少必须补上以下五项：

1. 每个 context 强制加入 `P0_KEEP_ORDER` no-op/abstain 动作；
2. 不能在每个 action 仅运行一次时使用 bootstrap winner probability；
3. 必须处理 probe action 的选择偏差，并记录 action propensity；
4. memory kill 应作为 competing risk 或安全失败，而不是普通右删失；
5. solver action value 与具体模型的推理成本必须分离。

首轮只建议做 **route-level harvest intervention**。task/arc expansion、proof queue 和 branch 继续保持 shadow。

---

## 2. 方案中最正确的改动

## 2.1 将 `4/3/1/0` 降为诊断标签

当前 grade 定义不是 action value：

```text
useful negative    4
addable negative   3
duplicate          1
nonnegative        0
```

其主要问题是：

- `addable` 只说明列合法可加入，不说明提前该列会不会节省后续工作；
- `would_change_active_support` 是局部 selector fact，不是实际 RMP gain；
- duplicate 的真实时间成本没有进入标签；
- 未探索候选没有反事实结果；
- P0 已经经常把第一个 observed negative 排在第 1，membership 指标存在明显天花板。

实施报告还发现 grade 4 与 `would_change_active_support` 在大量样本上完全等价。若该字段进入模型，就是标签泄漏；若将其屏蔽，模型又只是在猜测 P0 已经知道的确定性事实。

因此，原 grade 适合保留用于：

- 数据审计；
- 分层统计；
- 检测 schema 漂移；
- encoder warm-up 的弱辅助任务；

但不应继续决定最终 checkpoint。

## 2.2 同一 snapshot 下做真实排序干预

方案将训练样本定义为：

```text
相同 canonical snapshot
相同合法候选宇宙
相同 branch/cut/dual/context
相同预算与 exact 规则
只改变候选处理顺序
```

这是正确的因果归因边界。

它最大限度消除了以下混杂因素：

- 实例整体难度；
- dual 状态差异；
- Phase-I/Phase-II 差异；
- branch context 差异；
- active-cut context 差异；
- worker budget 差异；
- cache 和 runtime 状态差异。

## 2.3 使用 paired advantage

定义：

\[
A_a^{(B)}
=
U(c,\pi_a,B)-U(c,\pi_0,B)
\]

比直接预测绝对运行时间或绝对 RMP gain 更合理。

它将目标解释为：

```text
在这个精确求解状态中，
该排序动作相对于当前 P0 好多少。
```

这对跨规模共享 checkpoint 尤其重要，因为 scale5 与 scale30 的绝对时间量级差异很大，而同 context 的 paired advantage 仍然可比较。

## 2.4 使用时间轨迹而非单点 rank

方案提出：

\[
v_\pi(t)=
\max_{r\in\mathcal D_\pi(t)}
\operatorname{clip}
\left(
\frac{-rc(r)}{\rho_c},0,1
\right)
\]

\[
U_{\text{disc}}(c,\pi,B)
=
\frac{1}{B}\int_0^B v_\pi(t)\,dt
\]

这一目标比 `first observed-negative rank` 更贴近实际求解过程，因为它同时奖励：

- 更早找到第一个 unique、addable negative；
- 更早找到 reduced cost 更好的列；
- 在固定预算内维持更好的 best-RC trajectory；
- duplicate、invalid 和无效探索因消耗时间但不提升曲线而自然受罚。

## 2.5 silver/gold 两级监督

建议使用：

- **silver：** 大量 snapshot 的 discovery trajectory；
- **gold：** 少量 snapshot 上固定 P0 roll-out 后的真实 RMP progress。

这个设计能够控制数据采集成本，又避免最终 checkpoint 只依赖 reduced cost 代理指标。

## 2.6 timeout 使用删失语义

将 timeout 表示为：

```text
真实事件时间至少大于当前 censor time
```

而不是：

```text
incomplete × 固定惩罚
```

这是正确方向。它保留了 incomplete run 中已经观测到的信息，同时避免伪造完整工作量。

---

## 3. 必须修改项一：强制加入 P0 no-op/abstain 动作

当前动作定义主要是：

```text
把某个候选提升为下一优先项
```

但每个 context 必须强制加入：

\[
a_0=\texttt{P0\_KEEP\_ORDER}
\]

并定义：

\[
A_{a_0}=0
\]

### 原因

若所有被 probe 的 promotion 都比 P0 差：

\[
A_1<0,\quad A_2<0,\quad A_3<0
\]

没有 no-op 时，softmax 仍会强迫模型从三个有害动作中选择一个“相对最好”的动作。

### 实施要求

每个 action set 必须为：

\[
P_c=\{a_0,a_1,\ldots,a_m\}
\]

部署时必须允许模型 abstain：

```text
若所有 learned promotion 的保守净收益都不高于 P0，
则保持 P0 原顺序。
```

建议新增 telemetry：

```text
p0_noop_available
p0_noop_score
learned_action_selected
abstained_to_p0
abstention_reason
```

---

## 4. 必须修改项二：bootstrap winner probability 需要真实重复单位

方案定义：

\[
q_a=
\Pr_{\text{bootstrap}}
\left(
A_a=\max_{b\in P_c} A_b
\right)
\]

这一表达能表示近似同优动作，但当前数据采集描述中，每个 snapshot-action 似乎只运行一次。

### 4.1 单次 trajectory 不能支持有效 bootstrap

时间轨迹内部的时间点高度相关，不能当作独立重复进行普通 bootstrap。

需要以下两种方案之一。

### 方案 A：blocked repeated interventions

对每个 snapshot-action 运行 3～5 次：

- 相同 frozen snapshot；
- 相同 budget；
- fresh process 或明确固定 warm-state；
- 固定 CPU/BLAS/HiGHS/Torch thread；
- P0 与 intervention 成对；
- 执行顺序随机化；
- 记录 machine block 与 run order。

### 方案 B：分层噪声模型

若重复成本过高，可以先通过大量 P0 repeats 估计：

- context 内时间噪声；
- scale-specific variance；
- machine block variance；
- cold/warm runtime variance。

然后用层级模型估计 action advantage 的后验分布。

### 4.2 winner probability 丢失收益幅度

“只快 0.1%”和“快 30%”可能得到相似的 winner probability，但部署意义完全不同。

更建议使用保守 advantage：

\[
\widetilde A_a
=
\widehat\mu_a-\kappa\widehat\sigma_a
\]

然后：

\[
q_a
=
\operatorname{softmax}
\left(
\widetilde A_a/\tau
\right)
\]

其中：

- \(\widehat\mu_a\)：paired advantage 均值；
- \(\widehat\sigma_a\)：标准误或后验不确定性；
- \(\kappa\)：风险系数；
- P0 no-op 的 advantage 固定为 0。

这样同时保留：

- 收益大小；
- 统计不确定性；
- near-tie；
- abstention。

---

## 5. 必须修改项三：处理 probe action 的选择偏差

“未探索候选永不作为负样本”是正确的，但仍不足以解决 behavior-policy bias。

若每个 context 有 100 个合法动作，只 probe 4 个，模型学到的是：

```text
这4个被挑选出来的动作中谁最好
```

而不是：

```text
全部100个合法动作中谁最好
```

### 推荐 probe set

每个 route-level harvest snapshot 至少包含：

1. `P0_KEEP_ORDER`；
2. P0 的下一候选之外，一个高 RC 备选；
3. 一个结构或 task-set 多样性候选；
4. 一个固定随机种子候选；
5. 一个当前模型高不确定候选。

### 必须记录的字段

```text
action_sampling_probability
probe_policy_id
candidate_pool_size
candidate_position_under_p0
action_selection_reason
random_seed
```

后续可使用：

- clipped inverse-propensity weighting；
- doubly robust correction；
- action-support audit；
- probe-policy 分层验证。

### 术语修正

对实际运行过的动作，应称为：

```text
paired intervention trajectory
interventional action value
```

未运行动作的结果仍然未知，因此不应将整个数据集描述为“完整反事实标签”。

---

## 6. 必须修改项四：记录 treatment compliance

“请求将候选提升为下一优先项”不一定等于该候选最终真正成为下一个有效执行动作。

可能出现：

- feasibility 拒绝；
- dominance 拒绝；
- branch compatibility 拒绝；
- cut-state compatibility 拒绝；
- exact queue 的主键仍有更高优先项；
- 动态状态变化使候选失效。

### 必须记录

```text
promotion_requested
promotion_candidate_id
promotion_installed
promotion_executed
actual_execution_rank
first_effective_action_id
treatment_compliance
noncompliance_reason
```

### 主分析原则

主标签应使用 **intention-to-treat**：

```text
请求安装该 promotion 后产生的真实轨迹收益
```

不能只保留成功执行的 intervention，否则会按照处理后结果筛选样本，产生选择偏差。

`treatment_compliance` 用于诊断和辅助建模，不应用来事后过滤失败动作。

---

## 7. 对 `U_disc` 的具体修订

## 7.1 `ρc` 必须是 pre-treatment 固定量

\(\rho_c\) 不能使用：

- 所有 intervention 中观察到的最好 RC；
- probe set 的最大负 RC；
- 后续完整求解得到的未来结果。

否则会产生 post-treatment normalization 或未来信息泄漏。

可选定义：

- 当前 RMP objective reference；
- 只依赖 snapshot 的 dual/objective 尺度；
- training split 上冻结的 phase-specific robust scale；
- P0 control 在预先固定短预算中的尺度。

必须保证：

```text
同一 snapshot 的所有 action 使用同一个、干预前冻结的 ρc。
```

## 7.2 `max` 只奖励单个最好列

一个策略可能快速找到一个非常负、但后续 RMP 价值有限的列；另一个策略可能找到多个互补列，对 RMP 更有价值。

因此：

- `U_disc` 保持 silver target；
- `U_rmp` 决定 gold checkpoint；
- 额外记录但不强行压入单一 utility：

```text
unique_addable_count_trajectory
top_k_rc_mass
task_set_diversity
active_support_entry_count
duplicate_regeneration_count
```

## 7.3 clipping 饱和需要敏感性分析

当：

\[
-rc(r)\ge\rho_c
\]

所有更强负列都得到 1，质量差异消失。

第一版可以保留 clipping，但必须：

- 冻结 \(\rho_c\)；
- 报告不同 \(\rho_c\) 下的敏感性；
- 同时保存未截断的 raw best-RC trajectory。

可选替代：

\[
v_\pi(t)
=
\frac{
\log(1+(-rc)_+/\rho_c)
}{
\log(1+\gamma)
}
\]

## 7.4 预算内零收益与右删失要区分

若在预算 \(B\) 内未发现负列：

```text
U_disc = 0
```

这是一个真实的预算内结果。

同时：

```text
time_to_first_negative > B
```

才是 survival head 中的右删失。

不要把预算内零收益当成 missing。

---

## 8. 必须修改项五：memory kill 不是普通右删失

wall-time budget 到期通常可以视为行政性删失，但 memory kill 往往是策略诱导的真实资源后果。

某种排序可能导致：

- frontier 更快膨胀；
- live labels 增长更快；
- RSS 更高；
- 最终触发 memory limit。

若仅将其当作：

```text
事件尚未观察到
```

模型可能偏好高风险、容易爆内存的策略。

### 建议区分

#### 行政性删失

```text
WALL_TIME_BUDGET_REACHED
EXTERNAL_LAUNCHER_STOP
```

用于普通 right-censoring。

#### 策略相关 competing risk

```text
MEMORY_LIMIT
FRONTIER_EXPLOSION
RESOURCE_SAFETY_TERMINATION
```

应采用至少一种处理：

- cause-specific hazard；
- competing-risk survival；
- 独立 adverse-event head；
- 部署硬约束；
- 将其纳入 action safety gate。

建议新增：

```text
memory_adverse_event
frontier_growth_slope
rss_growth_slope
resource_safety_gate_pass
```

---

## 9. wall-time budget 与 label budget 必须拆开

不能在一个实验中同时声称完全匹配：

- wall time；
- label count。

不同动作在相同 wall time 下通常会扩展不同数量 labels；在相同 label count 下也会消耗不同 wall time。

### 建议建立两套 utility

#### 算法效率轨迹

```text
matched-label-budget
matched-extension-budget
```

用于减少机器噪声，判断排序是否减少算法工作。

#### 真实部署轨迹

```text
matched-wall-time-budget
```

用于端到端部署评价，并包含：

- Native 扩展；
- tensorization；
- inference；
- binding validation；
- hint installation。

两套结果都应记录，但不能混用停止条件。

---

## 10. solver action value 与模型推理成本必须分离

forced intervention 数据本质上是在测试：

```text
若把动作 a 提前，solver 本身能获得多少收益
```

它通常没有运行具体 linear、MLP 或 GAT，因此不应把某个模型的推理成本写进 action oracle。

### 模型无关 solver benefit

\[
A_{\text{solver}}(a)
=
U_{\text{forced intervention}}(a)-U_{\text{P0}}
\]

### 具体模型的净收益

\[
A_{\text{net}}(a,m)
=
A_{\text{solver}}(a)-C_{\text{guidance}}(m)
\]

其中 \(m\) 是具体模型。

### 使用方式

- 训练 action ranker：使用 `A_solver`；
- checkpoint 晋级：使用 `A_net`；
- P0 no-op：模型成本为 0；
- scale5/10：允许在 import Torch 前直接 bypass。

建议记录：

```text
forced_intervention_solver_wall
model_inference_wall
model_import_wall
model_tensorize_wall
net_action_advantage
```

---

## 11. `U_rmp` 的实验契约必须冻结

对候选执行一次 intervention 后，后续必须使用固定 P0 rollout：

```text
P0 roll-in
执行一次 action intervention
P0 roll-out H轮
```

否则同时改变首个 action 和后续策略，收益无法归因。

### 必须冻结

```text
Phase-I / Phase-II
objective direction
initial active columns
initial basis / warm-start state
dual stabilization state
branch context
full cut context
projected pricing-cut context
subsequent worker policy
subsequent queue policy
column pool
cache state
thread count
wall-time budget
label/extension budget
```

### progress 符号

对于 minimization RMP，可定义：

\[
\operatorname{progress}(z_t,z_0)
=
\max(0,z_0-z_t)
\]

Phase-I artificial objective 与 Phase-II official objective 必须分开归一化和建模，不能直接混入同一个绝对尺度。

---

## 12. 单步 intervention 与连续在线策略之间存在分布偏差

当前数据学习的是：

```text
在 P0 state 上，把一个候选提前一步的价值
```

但连续部署的模型会改变：

- 后续发现的 columns；
- RMP dual；
- active support；
- 后续 snapshot 分布；
- branch/tree 路径。

### 第一版部署合同

必须限制为：

```text
每个 pricing context 最多执行一次 learned promotion；
其余排序继续 P0。
```

### 后续数据聚合

1. 在纯 P0 states 上训练 linear；
2. linear shadow；
3. development instances 上允许单次 opt-in；
4. 收集新的 learned-policy states；
5. 重训；
6. 重新做安全门槛；
7. 再决定是否允许连续排序。

这相当于安全版 DAgger / policy iteration。

不能从纯 P0 snapshot 的 one-step action value，直接跳到全程由 GAT 重排。

---

## 13. 第一版只做 route-level harvest intervention

以下动作的因果距离不同：

| 动作 | 到下游结果的距离 |
|---|---|
| route promotion | 可立即进入 master 候选流程 |
| harvest reorder | 直接影响本轮返回列 |
| task expansion | 需经过大量扩展才形成 route |
| arc/path expansion | 因果链更长，方差更大 |

不建议第一版将它们放入同一个 softmax 或共用同一个 action-value 标度。

### 推荐首轮范围

只研究：

```text
route-level harvest promotion
```

原因：

- candidate 是完整列；
- true RC 已知；
- addability 可精确审计；
- downstream RMP gain 可直接测量；
- treatment compliance 容易定义；
- action space 相对有限；
- 旧 harvest replay 已显示局部弱正信号，只是旧 schema 不足以支持 promotion。

### 暂缓

```text
task/arc expansion
proof queue
branch online
scale50/100 online
```

---

## 14. 主 loss 的修订建议

原方案建议：

\[
\mathcal L_{\text{pricing}}
=
\mathcal L_{\text{CF-list}}
+
\operatorname{EMA-Norm}(\mathcal L_{\text{survival}})
+
\operatorname{EMA-Norm}(\mathcal L_{\text{curve}})
\]

方向可以接受，但首轮略复杂。

### 问题

- EMA normalization 只能统一数值尺度，不能决定任务重要性；
- `CF-list` 已由 trajectory utility 生成；
- `curve` 又回归 trajectory utility，信息重复；
- survival 可能与主排序产生梯度冲突。

### 首轮建议

\[
\mathcal L
=
\mathcal L_{\text{CF-list}}
+
\lambda_s\mathcal L_{\text{survival}}
\]

并限制：

```text
辅助 survival head 对共享 encoder 的梯度范数
不得超过主 listwise head 的 25%。
```

`L_curve` 首轮只训练独立 calibration head，或作为离线诊断，不进入共享 encoder。

PCGrad 不应预先启用。先通过普通消融证明存在稳定负迁移，再考虑加入。

---

## 15. 修订后的主目标

### 15.1 动作集合

\[
P_c=\{a_0,a_1,\ldots,a_m\}
\]

其中：

\[
a_0=\texttt{P0\_KEEP\_ORDER}
\]

### 15.2 模型无关 solver advantage

\[
A_a^{\text{solver}}
=
U(c,\pi_a)-U(c,\pi_0)
\]

### 15.3 重复干预统计

\[
\mu_a=\mathbb E[A_a],
\qquad
\sigma_a=\operatorname{SE}(A_a)
\]

### 15.4 保守 action utility

\[
\widetilde A_a
=
\mu_a-\kappa\sigma_a
\]

### 15.5 soft target

\[
q_a
=
\frac{
\exp(\widetilde A_a/\tau)
}{
\sum_{b\in P_c}\exp(\widetilde A_b/\tau)
}
\]

### 15.6 主损失

\[
\mathcal L_{\text{CF-list}}
=
-\sum_c w_c
\sum_{a\in P_c}
q_a\log p_\theta(a\mid c)
\]

### 15.7 部署净收益

\[
A_{\text{net}}(a,m)
=
\widetilde A_a-C_{\text{guidance}}(m)
\]

只有在：

\[
\operatorname{LCB}(A_{\text{net}})>0
\]

时才允许改变 P0 顺序；否则选择 `P0_KEEP_ORDER`。

---

## 16. 跨规模训练与 checkpoint 选择

## 16.1 exact-benefit gate

仅对 5/10/20/30 计算：

```text
worst-scale paired solver-advantage LCB
5/10 fresh-runtime non-degradation
20/30 discovery trajectory gain
20/30 gold RMP progress gain
net advantage after model cost
```

## 16.2 large-scale safety gate

50/100 当前没有足够 exact closure，不应与 5–30 共用一个“六规模 advantage”指标。

50/100 只评价：

```text
OOD fallback
payload boundedness
RSS/frontier growth
observed-negative shadow recall
survival calibration
no-filter semantics
binding validity
```

## 16.3 bootstrap 单位

正式置信区间必须以：

```text
instance
```

或：

```text
instance -> snapshot
```

为抽样层级。

不能把数万个 action rows 当作独立样本，否则置信区间会严重偏窄。

## 16.4 checkpoint 字典序

建议：

1. exact/no-filter/binding safety；
2. 5/10 fresh-runtime 不退化；
3. 5–30 worst-scale net-advantage bootstrap LCB；
4. 20/30 gold RMP progress；
5. memory competing-risk 与 resource safety；
6. guidance 总开销；
7. 模型大小。

---

## 17. 建议的数据 schema

每个 intervention row 至少包含：

### 17.1 Snapshot identity

```text
snapshot_id
instance_content_hash
canonical_solve_binding_hash
phase
objective_mode
rmp_iteration_id
branch_context_hash
full_cut_context_hash
projected_cut_context_hash
queue_policy_id
```

### 17.2 Action universe

```text
legal_action_universe_hash
candidate_pool_size
action_id
action_type
p0_position
action_sampling_probability
probe_policy_id
selection_reason
```

### 17.3 Treatment

```text
promotion_requested
promotion_installed
promotion_executed
actual_execution_rank
treatment_compliance
noncompliance_reason
```

### 17.4 Budget

```text
wall_time_budget_sec
label_budget
extension_budget
memory_budget_bytes
budget_mode
```

### 17.5 Trajectory

```text
time_to_first_unique_addable_negative
best_rc_trajectory
unique_addable_count_trajectory
rmp_objective_trajectory
frontier_trajectory
rss_trajectory
duplicate_trajectory
```

### 17.6 Outcome

```text
u_disc
u_rmp
solver_advantage
censoring_reason
competing_risk_reason
memory_adverse_event
```

### 17.7 Model cost（单独记录）

```text
guidance_import_sec
guidance_checkpoint_load_sec
guidance_tensorize_sec
guidance_forward_sec
guidance_binding_validation_sec
guidance_install_sec
guidance_total_wall_sec
net_advantage
```

---

## 18. 推荐实施顺序

## G0：冻结 intervention 契约

必须先实现并测试：

- `P0_KEEP_ORDER`；
- canonical action ID；
- action propensity；
- treatment compliance；
- pre-treatment `ρc`；
- wall/label/extension budget 分离；
- censoring 与 competing risk；
- solver benefit 与 model cost 分离。

## G1：采集 route-level harvest intervention

每个 snapshot 的 probe set：

- P0 no-op；
- 一个 high-RC 备选；
- 一个 diversity 备选；
- 一个 fixed-random 备选；
- 一个 uncertainty 备选。

先只覆盖 5/10/20/30 development instances。

## G2：linear baseline

验证：

- action value 是否可学；
- no-op 是否被正确选择；
- utility regret@k；
- worst-scale solver-advantage LCB；
- gold RMP progress；
- abstention calibration。

只有 linear 通过，才进入下一阶段。

## G3：两层 MLP

要求：

- 相对 linear 有显著增量；
- net advantage 扣除推理成本后仍为正；
- 5/10 不退化；
- memory safety 通过。

## G4：tiny GAT

仅测试：

```text
GAT 1x32x1
GAT 2x32x2
```

只有 GAT 在相同 intervention 数据、相同 folds 和相同预算下显著提高 worst-scale LCB，才晋级。

## G5：development 在线单次 intervention

部署合同：

```text
每个 context 最多执行一次 learned promotion；
随后继续 P0 rollout。
```

## G6：安全数据聚合

收集 learned-policy states，重新训练并重新通过 gate，之后才能考虑连续排序。

## G7：后续模块

只有 route-level harvest 独立通过后，才能依次研究：

```text
task/arc expansion
proof queue
branch ranking
scale50/100 bounded opt-in
```

---

## 19. 建议的首轮晋级门槛

### 数据与语义

```text
legal_action_universe_preservation = 100%
guidance_filter_count = 0
action_propensity_present = 100%
treatment_compliance_recorded = 100%
p0_noop_present = 100%
post-treatment normalization leakage = 0
```

### 离线模型

```text
linear worst-scale solver-advantage LCB > 0
no-op selection calibration passes
utility regret@k better than P0/random probe baseline
gold RMP progress nonnegative on every exact scale
memory adverse-event rate not above P0
```

### 在线单次 intervention

```text
5/10 fresh-runtime net p50 <= 1.02 x P0
5/10 mean <= 1.03 x P0
20/30 discovery AUC improves
20/30 gold RMP progress improves
zero extra incomplete
zero certificate leak
zero permanent drop
```

若模型没有保守正净收益，应选择 P0 no-op，而不是强制 promotion。

---

## 20. 最终建议

这版 Codex 方案完成了最关键的思想升级：

```text
不再预测“哪个候选像好列”，
而是预测“把哪个合法候选提前，
相对于 P0 能否在相同预算内改善真实求解轨迹”。
```

这个方向与当前实施报告提出的下一步一致：重新定义不由当前输入直接给出的下游 target，重新采集契约一致的数据，并从 linear 五折重新开始。

但下一步不应立即训练 GAT。

正式建议是：

1. 先冻结带 `P0_KEEP_ORDER` 的 intervention schema；
2. 只采集 route-level harvest intervention；
3. 对关键 action 做 blocked repeats 或建立可靠噪声模型；
4. 以保守 paired solver advantage 构造 soft-listwise target；
5. 将 memory kill 作为 competing risk；
6. 将 solver benefit 与模型推理成本分离；
7. 先证明 linear 的 worst-scale 净收益 LCB 为正；
8. 再依次尝试 MLP 和 tiny GAT；
9. 首次在线仅允许每个 context 一次 learned promotion；
10. task/arc、proof queue 和 branch 继续保持 shadow。

**最终审批结论：**

> 批准作为新的数据采集与 linear baseline 研究方案；在上述必改项完成前，不批准直接训练 GAT，也不批准在线连续重排。
