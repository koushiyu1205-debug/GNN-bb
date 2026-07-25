# P0 V2 反事实轨迹目标评审响应与实现结论

日期：2026-07-24

评审文件：
`plan/GAT/p0v2_counterfactual_trajectory_objective_review.md`

## 1. 总结

评审的核心判断正确，必须吸收。修订后的首阶段不再把“旧 grade
标签上的排序拟合”视为可晋级训练，而是只学习同一 frozen context
内、相对 P0 的 route-level harvest 单次干预收益。

当前代码路径已经可以表达和训练该目标，但当前仓库数据还没有满足
正式训练契约的 route-level harvest intervention。因此本轮结论是：

```text
目标与安全壳可行；
task/arc 机制敏感性已观测到；
正式 linear/MLP/GAT 训练尚未被数据证据授权。
```

这不是网络容量不足，也不是 exact solver 失效，而是正式监督数据仍
缺少可归因的 route action、treatment compliance 和 fixed-P0 rollout。

## 2. 直接采纳的意见

### 2.1 显式 P0 no-op

动作集合固定为：

$$
\mathcal A_c=\{\texttt{P0\_KEEP\_ORDER},a_1,\ldots,a_m\}.
$$

P0 的 solver advantage 固定为 0。模型输出独立 no-op score；在线
harvest 只能选择一个 promotion，或 abstain 回 P0。若最佳 learned
action 的 score 不严格高于 no-op，保持 P0 顺序。

运行时新增并实际使用：

```text
p0_noop_available
p0_noop_score
learned_action_selected
abstained_to_p0
abstention_reason
max_learned_promotions_per_context
```

### 2.2 真实 blocked repeats 与保守 advantage

每个 action 至少需要 3 个 blocked repeats。轨迹时间点不再被当作
独立 bootstrap 样本。每个 promotion 使用 paired P0 advantage：

$$
\widehat A_a^{solver}
=
\frac{1}{R}\sum_{r=1}^{R}
\left(U_{a,r}-U_{P0,r}\right),
$$

并以真实 repeats 的标准误构造：

$$
\widetilde A_a
=
\widehat A_a^{solver}-\kappa\,SE(\widehat A_a^{solver}).
$$

soft target 包含 no-op：

$$
q_a
=
\frac{\exp(\widetilde A_a/\tau)}
{\sum_{b\in\mathcal A_c}\exp(\widetilde A_b/\tau)}.
$$

默认 `kappa=1.96`、`tau=0.05`。这些是训练超参数，后续只能由
development/calibration 契约选择，不能接触 protected final test。

### 2.3 action propensity 与 probe support

每个 arm 强制记录：

```text
action_sampling_probability
propensity
probe_policy_id
candidate_pool_size
candidate_position_under_p0
action_selection_reason
random_seed
run_order
machine_block_id
```

固定种子 probe 使用带 seed 的确定性均匀 hash sampling，声明的
`k/N` inclusion probability 与采样实现一致。

### 2.4 intention-to-treat 与 treatment compliance

每个 arm 强制记录：

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

主标签使用 intention-to-treat。非执行或部分执行的 promotion 不会
被事后过滤。正式首阶段只接受能够观测这些字段的 route-level
harvest；task/arc cumulative priority 无法确认“下一动作确实执行”，
所以只保留诊断资格。

### 2.5 pre-treatment RC scale

同一 context 的所有 arms 必须共享干预前冻结的 `rho_c`，并记录：

```text
pre_treatment_rc_scale
pre_treatment_rc_scale_source
```

禁止使用 intervention 后的最佳 RC、probe 集合结果或未来完整求解
结果进行归一化。

### 2.6 memory competing risk

以下结束原因不进入普通 right-censored survival：

```text
MEMORY_LIMIT
FRONTIER_EXPLOSION
RESOURCE_SAFETY_TERMINATION
```

它们作为独立 memory adverse event 记录，并进入 checkpoint 的硬安全
门槛。wall-time 到期仍是 administrative censoring。

### 2.7 budget 与成本分离

每条记录必须明确选择一种停止契约：

```text
matched_wall_time
matched_label_count
matched_extension_count
```

不能同时声称 wall 和 label 完全匹配。forced intervention 的训练
标签只包含 model-independent solver benefit：

$$
A_{solver}(a)=U(a)-U(P0).
$$

具体 checkpoint 的晋级使用：

$$
A_{net}(a,m)=\widetilde A_a-C_{guidance}(m).
$$

模型 import、checkpoint load、tensorization、forward 和 native install
成本不能泄漏进 action oracle；它们只在 fresh-runtime promotion gate
中扣除。

### 2.8 fixed P0 rollout 与跨规模边界

`rmp_progress_auc` 记录若没有完整的 fixed-P0 rollout 合同会被拒绝。
至少必须绑定初始列、basis、dual stabilization、branch/cut context、
worker/queue policy、column pool、cache、thread 和 rollout horizon。

exact advantage 只在 5/10/20/30 计算；50/100 只承担 OOD、payload、
RSS/frontier、survival、no-filter 和 binding 安全评价，不能伪称已有
完整 BPC 加速证据。

## 3. 调整后采纳的意见

### 3.1 propensity correction

首阶段优先使用明确随机化且记录 inclusion probability 的 probe
设计，不立即对 listwise loss 施加高方差 inverse-propensity weight。
代码保存 clipped inverse-propensity weight 供 support audit 使用，
但标记为“不进入 randomized first-stage loss”。

原因是当前首要问题是取得可信 route intervention，而不是用统计校正
补救一个选择机制不清楚的数据集。以后若加入自适应 model-uncertainty
probe，再独立比较 clipped IPW 与 doubly robust estimator。

### 3.2 auxiliary gradient 上限

评审要求 survival 对共享 encoder 的梯度不超过主 head 的 25%。
首阶段采用更保守的实现：survival 输入从共享 encoder detach，即共享
梯度占比为 0；survival head 自身仍训练。

trajectory curve regression 不进入共享 encoder。主目标为：

$$
\mathcal L
=
\mathcal L_{CF-list}
+0.25\left(
\mathcal L_{survival}
+0.1\mathcal L_{concordance}
\right).
$$

PCGrad 不默认启用；只有连续 3 次 validation 的真实 head-gradient
cosine 小于 `-0.2` 才允许进入后续消融。

## 4. 实现边界

正式训练入口现在同时要求：

```text
training_objective = counterfactual_trajectory_v2
counterfactual_main_scope = harvest_only
candidate_kind = harvest
formal_first_stage_eligible = true
P0_KEEP_ORDER present
treatment compliance observable
```

deployment manifest 与 checkpoint loader 还要求：

```text
p0_noop_trained = true
trained_main_heads contains harvest
guidance_action_scope = route_harvest_single_promotion
max_learned_promotions_per_context = 1
```

task/arc 在线请求会在导入 Torch 前 fail-closed bypass；shadow 预测仍可
保留用于机制分析。正式 promotion 还必须通过 no-op calibration、
route-harvest、memory safety、net benefit、instance/snapshot bootstrap
和 scale50/100 safety-only gate。

## 5. 真实 snapshot 可行性检查

使用 development split 中已有 snapshot，分别在 scale5、scale20
运行了：

```text
3 blocked repeats
2 matched wall-time horizons: 0.02s, 0.05s
3 task probes + P0
3 arc probes + P0
```

结果：

| scale | kind | action-value range | identifiable | 解释 |
|---:|---|---:|---|---|
| 5 | task | 0 | 否 | 所有动作与 P0 轨迹相同 |
| 5 | arc | 0 | 否 | 所有动作与 P0 轨迹相同 |
| 20 | task | 0.222445 | 是 | 两个 promotion 有害，一个与 P0 持平 |
| 20 | arc | 0 | 否 | 所有动作与 P0 轨迹相同 |

scale20 task 的 no-op target probability 为 `0.471391`；与 P0 持平的
promotion 也是 `0.471391`，两个有害 promotion 分别为 `0.051706`
和 `0.005511`。这验证了 no-op 的必要性：旧目标会被迫从 promotion
中选一个，新目标不会。

这 4 条记录全部通过 propensity、no-filter、binding、no-leakage、
solver/model-cost separation 和 memory competing-risk schema 校验。
但它们均为 task/arc 诊断，正式 route-level harvest record 数量为 0。

旧 materialized 数据共 10,589 行：

```text
scale5    561
scale10  1084
scale20  2794
scale30  6150
```

它们全部是 `legacy_graded_listwise`，不会被重新贴成反事实标签，
counterfactual-trainable 行数为 0。

因此 feasibility audit 的正式结论是：

```text
DIAGNOSTIC_TASK_ARC_ONLY_ROUTE_HARVEST_REQUIRED
```

当前 blocker：

1. 尚无 formal route-level harvest interventions；
2. 尚无 scale5/10/20/30 每规模至少 24 个 development contexts；
3. 尚无 fixed-P0 rollout 的 addability/RMP gold trajectory；
4. 尚不能计算 worst-scale net-advantage LCB；
5. 因此不应启动 linear、MLP 或 GAT 的正式比较。

## 6. 验证

相关测试：

```text
62 passed, 246 deselected
```

覆盖：

- 所有 promotion 有害时 no-op 胜出；
- unprobed action 不成为负样本；
- blocked repeats 与 conservative soft target；
- noncompliance 保留在 ITT 数据中；
- memory event 不进入普通 right censor；
- RMP gold 缺少 frozen rollout 时拒绝；
- route-level formal eligibility；
- runtime no-op abstention；
- 单 context 最多一个 learned route promotion；
- task/arc pre-import bypass；
- checkpoint/manifest 新目标门槛；
- harvest zero-filter 与 exact-safe 既有回归。

可复核 artifact：

```text
runs/p0v2_gat_counterfactual_target_pilot_20260724/
  reviewed_scale5_task_arc.jsonl
  reviewed_scale20_task_arc.jsonl
  reviewed_feasibility_audit.json
```
