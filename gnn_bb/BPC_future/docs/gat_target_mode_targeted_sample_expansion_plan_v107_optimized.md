# GAT Target Mode：有针对性扩充训练样本计划（优化版）

版本：2026-06-18  
适用阶段：Stage 3 数据补强 → Stage 4 候选前置准备  
唯一目标：**合理扩充训练样本数量，并形成 Stage 3 retraining / Stage 4 audit precondition 数据合同**  
计划规模：**5000 条有效 target-level 样本行**  
执行边界：**只做数据扩充与样本组织；允许 diagnostic-only replay capture / artifact tooling 补齐；不改模型、不训练、不改变 solver 决策语义、不启用 GAT、不接 production**

---

## 1. 一句话目标

本计划只做一件事：

> 构建一批高质量、可回放、same-context、target-level 的训练样本，使 GAT batch-impact / admission model 能更好地区分：在同一 RMP context 下，哪些 candidate target 具有真实 RMP trajectory ROI，哪些 true-RC negative target 应进入 `DELAY_QUEUE`。

本计划不是：

```text
不是模型结构优化计划
不是训练计划
不是测试计划
不是 online A/B 计划
不是 solver 接入计划
不是 production 启用计划
```

本计划完成后，只能声明：

```text
Stage 3 retraining data ready
Stage 4 audit precondition data ready
```

不能声明：

```text
Stage 3 completed
Stage 4 candidate ready
production_ready
20-task exact target improved
```

训练、阈值校准、kNN/OOD gate、online shadow、20-task A/B 都不属于本计划范围。

---

## 2. 固定边界

样本扩充不能改变任何 exact-safe 求解语义。

必须保持：

```text
1. GAT 不是 pricing oracle。
2. GAT 不产生 certificate。
3. GAT 不产生 official lower bound。
4. GAT 不替代 true reduced-cost 公式。
5. GAT 不永久丢弃 true-RC negative column。
6. DELAY_QUEUE 不是 reject。
7. final certificate 仍由 exact pricing / final judge 完成。
8. 本计划生成的样本只能用于 offline training / audit。
9. 本计划不能把 true-RC negative 的 delay label 解释为 reject label。
10. 本计划不能把 kNN/OOD audit 结果写入 GAT model input feature。
```

样本标签只能表达：

```text
在某个固定 same-context intervention 中，
某个 target 或 batch 是否产生了 trajectory ROI。
```

样本标签不能表达：

```text
这个 target 可以证明最优；
这个 target 可以替代 pricing；
这个 target 可以绕过 final judge；
这个 target 可以永久删除其他负列。
这个样本本身已经是 Stage 4 ready；
这个样本换 checkpoint 后仍然通过 kNN/OOD gate。
```

---

## 3. 当前问题定位

当前 Stage 3 的问题不是简单“样本数量少”，而是样本结构存在偏差。

核心问题：

```text
1. 同 context 下 high-ROI target 被 low-ROI / delay-risk target 反排。
2. batch-level 粗标签污染 individual target-level 正负混合。
3. family 与 scale 覆盖不足，尤其 random-wave、greedy-anchor、30/50/100。
4. kNN/OOD audit 字段不完整，即使训练指标改善，也可能无法通过 Stage 4 gate。
```

因此，本次扩样不是平均撒点，而是：

```text
优先补 hard pair；
优先补 missed high-ROI；
优先补 target-level causal label；
优先补 family × scale 空洞；
同步补 kNN/OOD audit 字段。
```

---

## 4. 样本单位：target rows、batch samples、hard pairs 必须区分

本计划同时产出三种数据单位。

### 4.1 Target-level row

基本样本单位是：

```text
individual target-level row
```

一条 target-level row 表示：

```text
在固定 RMP context 下，
某一个 candidate target / target signature / target intervention
带来的 trajectory outcome。
```

它主要用于训练 candidate-level heads：

```text
y_candidate_high_priority
y_candidate_delay_risk
y_candidate_true_rc_negative
```

### 4.2 Batch-level sample

训练模型时还需要 batch-level sample。多个 target rows 需要按：

```text
context_hash + candidate_batch_id
```

聚合成一个 batch sample。

Batch sample 用于训练 batch-level heads：

```text
y_batch_roi_positive
y_objective_progress
y_tail_improved
y_bad_mode_switch
y_support_changed_good
y_delta_v
y_barrier_slack
y_accepted_batch_roi
```

### 4.3 Same-context hard pair

Hard pair 是训练 pairwise ranking 的单位。

一个 hard pair 是：

```text
同一 context 下，
一个 high-ROI positive target
和一个 low-ROI / bad-mode / delay-risk negative target
组成的有序对。
```

Hard pair 用于训练：

```text
score(positive_target) > score(negative_target) + margin
```

### 4.4 三个数量指标都必须满足

最终样本集必须同时满足：

```text
有效 target-level rows >= 5000
有效 batch-level samples >= 500
有效 same-context hard pairs >= 1200
```

只达到 5000 target rows 但 batch samples 很少，仍然不合格；只达到 batch samples 但没有 hard pairs，也不合格。

训练粒度必须保持分离：

```text
5000 条 target-level rows:
    主要训练 candidate-level heads 和 same-context pairwise ranking。

按 context_hash + candidate_batch_id group 后的 batch samples:
    训练 batch-level ROI / tail / CBF heads。

candidate 和 batch 一起训练，但 label 粒度不同；
batch label 不得广播成 individual candidate label。
```

---

## 5. Context 一致性要求

Target-level causal label 必须来自同一个 RMP context。

最小主键：

```text
context_hash
target_id
intervention_signature
```

推荐完整 context key：

```text
context_hash
true_dual_hash
fleet_dual_hash
cut_dual_hash
cut_hash
branch_hash
pool_signature_hash
active_support_hash
pricing_config_hash
forbidden_signature_hash
logical_graph_hash
path_option_universe_hash
start_time_candidate_hash
active_fleet_limit
rc_formula_version
feature_schema_version
target_id
intervention_signature
```

如果以下字段不一致，不能组成 same-context pair，也不能贴 causal label：

```text
true dual
fleet dual
cut dual
cut set
branch constraints
pool / active support
forbidden signatures
pricing config
logical graph
path-option universe
start-time candidate universe
active fleet limit
RC formula version
```

---

## 6. 标签定义

### 6.0 统一阈值与 horizon 字段

所有 label 必须绑定同一份 label-threshold manifest。manifest 至少包含：

```text
label_threshold_manifest_id
horizon_H
true_rc_negative_eps
min_positive_primal_roi
min_positive_retry_roi
min_positive_accepted_impact_delta
max_low_roi_primal_roi
max_low_roi_retry_roi
min_hard_pair_roi_gap
bad_mode_retry_delta_threshold
bad_mode_hidden_negative_delta_threshold
bad_mode_dual_l1_delta_threshold
support_changed_good_definition
normalized_roi_scale_by_task_count
```

默认解释：

```text
high_roi_positive 必须达到 positive 阈值；
accepted_low_roi_negative 必须低于 low-ROI 阈值，或低于 accepted impact 阈值；
hard pair 必须满足 roi_gap >= min_hard_pair_roi_gap；
delay_risk_negative 必须是 true-RC negative，且在 horizon_H 内没有正向 trajectory ROI；
nonnegative_reject_only 只由 current true dual 下 rc >= -true_rc_negative_eps 决定。
```

如果缺少 threshold manifest，样本只能进入 raw archive，不能进入 effective
target rows / hard pairs / Stage-4-gate-evaluable subset。

### 6.1 Candidate-level positive labels

#### `high_roi_positive`

满足：

```text
true-RC negative；
individual target ROI 高于 label_threshold_manifest 中的 positive 阈值；
bad_mode_switch = false；
有可回放 causal evidence。
```

用于训练：

```text
HIGH_PRIORITY
positive ranking target
```

#### `missed_high_roi_positive`

满足：

```text
属于 high_roi_positive；
但旧模型 / 当前 gate 将其 delay、低分或未选中。
```

这是本次最优先补充的样本类型。

---

### 6.2 Candidate-level negative / delay labels

#### `accepted_low_roi_negative`

满足：

```text
旧模型或旧 gate 接受；
但 individual target ROI 低于 low-ROI 阈值，或 accepted impact 不足。
```

用于压低错误 HIGH_PRIORITY。

#### `bad_mode_negative`

满足：

```text
加入后触发 bad_mode_switch；
或 dual / basis / tail retry 明显恶化。
```

用于训练 delay-risk / bad-mode 抑制。

#### `delay_risk_negative`

满足：

```text
true-RC negative；
但 same-context intervention 在 horizon_H 内没有正向 trajectory impact。
```

它的正确语义是：

```text
DELAY_QUEUE
```

不是 reject。

---

### 6.3 Nonnegative label

#### `nonnegative_reject_only`

满足：

```text
current true dual 下 rc >= 0。
```

只能用于：

```text
REJECT_NONNEGATIVE_ONLY 边界。
```

不能与 true-RC negative 的 delay 样本混淆。

`nonnegative_reject_only` 不得参与 true-RC-negative admission precision 统计；
它只用于训练 / 审计 `REJECT_NONNEGATIVE_ONLY` 边界。

---

## 7. 禁止标签污染

禁止以下做法：

```text
1. 把 rc < 0 直接标成 high quality。
2. 把 batch-level ROI 直接广播给 batch 内所有 target。
3. 把 context-level 一个标签映射给所有 target。
4. 把 replacement negative 自动标成 positive。
5. 跨 dual / cuts / branch / pool context 贴 causal label。
6. 用 future / post-addition 特征作为模型输入。
7. 把 kNN/OOD audit 字段当作 GAT 训练输入。
8. 把 true-RC negative delay 样本和 rc>=0 reject 样本混成一类。
```

特别注意：

```text
target-level label 和 batch-level label 可以不一致。
```

例如：

```text
batch 整体 ROI 为正，
但其中某个 target 是 low-ROI / bad-mode / replacement-heavy。
```

这种情况必须保留，而不是强行统一。

---

## 8. 样本数量目标

这里的 `5000` 指通过去重、causal evidence 审核、context 一致性审核、泄漏检查后，
再按 Stage 4 偏置配额选出的 `selected_for_training=true` target-level rows。

如果 raw collection 超过 5000 行，不能把全部 raw rows 都计入质量门禁；必须先输出一个
quota-selected training subset，再只用这个 subset 统计 family、scale、evidence、hard-pair
和 Stage 4 audit 门禁。多余 raw rows 只能作为候选池、诊断背景或下一轮补样来源。

建议 raw collection 额外多采 20%–30%，用于去重和剔除。

---

### 8.1 按任务规模

| 任务规模 | 目标有效 target rows | 占比 | 80% 最低线 |
|---:|---:|---:|---:|
| 20 | 2500 | 50% | 2000 |
| 30 | 500 | 10% | 400 |
| 50 | 1000 | 20% | 800 |
| 100 | 1000 | 20% | 800 |
| **合计** | **5000** | **100%** | - |

规模用途边界：

```text
20-scale:
    是 Stage 4 online shadow / opt-in 前的主验收规模。
    5000 样本集中按 50% 配额配置，是本计划的主支撑规模。

30/50/100-scale:
    用于 scale generalization、family/scale holdout 和 heuristic acceleration
    辅助证据；
    不得直接用来声明 20-task exact proof 改善；
    不得把 local same-context ROI 解释成 exact optimality 或 certificate signal。

    30/50/100 的 runbook execution success 不能自动计为可训练 causal row。
    只有同时捕获到同 context 的 worker materialization / ablation evidence，
    并通过 `worker_target_causal_match=true` 或等价 Level A/B 审核后，
    才能进入 selected training subset 的 Level A/B 统计。

    2026-06-18 的 100-scale 诊断说明：
    exact-context / before_exact 路径在短时 task100 fallback run 中没有进入 exact pricing，
    因而无法产出 worker materialization row；
    open-context target_materialization / before_legacy_final_judge 路径可以产出
    `journey_sharded_pulse_hidden_negative_worker`、matching replay capture、
    同阶段 column addition 和下一轮 RMP improvement。

    后续 100-scale 补样应先用 open-context materialization 发现实际 context，
    再把实际 worker context_hash 绑定成 self-context Level A/B 行；
    这些行只能作为 local trajectory ROI / ranking 训练证据，
    不能声明 Stage 4 gate ready，也不能当 exact certificate signal。

    2026-06-18 first238 追加诊断：
    两段式 `plain capture -> negative returned_journey payload -> open-context worker`
    可以为 100-scale greedy-anchor、random-wave 和 sector-wave 产出
    self-context Level A/B rows。sector-wave 的关键问题不是无可训练样本，
    而是 node/B&B heuristic pricing 分支此前缺少 replay capture diagnostic event；
    补齐 diagnostic-only capture 后，100-scale 三个 family 的 80% family×scale
    门槛均已可过线。

    该补齐只允许作为样本采集和审计诊断，不得改变 pricing 选择、
    exact certificate、bound 或 production solver 语义。

    2026-06-19 first362 / followup40 当前状态：
    Stage 4 偏置的 5000-row selected subset 已满足样本质量合同。
    selected rows = 5000，20-scale rows = 2660，Level A/B rows = 1644，
    20-scale Level A/B rows = 814，Level C weak rows = 3356，
    same-context hard pairs = 5560。除 Stage4 audit binding 外，
    数量、scale、family、family×scale、hard-pair 和 20-scale Level A/B
    门槛均已过线。

    因此，后续不应继续用普通 20-scale 总量扩张作为默认动作。
    新 20-scale 样本只有在能提供 checkpoint-bound audit row、
    替换 Level C weak row、或补充明确 failure case 时才优先进入下一轮。
    Stage 4 readiness 需要训练后 checkpoint、kNN/OOD audit 和 online shadow
    绑定，不能由当前离线样本配额直接推出。
```

---

### 8.2 按 family

| family | 目标有效 target rows | 占比 | 80% 最低线 |
|---|---:|---:|---:|
| sector-wave | 2000 | 40% | 1600 |
| random-wave | 1800 | 36% | 1440 |
| greedy-anchor | 1200 | 24% | 960 |
| **合计** | **5000** | **100%** | - |

---

### 8.3 family × scale 交叉配额

只看边际配额不够，必须防止某个 family 只集中在某个规模。

建议交叉配额如下：

| scale | sector-wave | random-wave | greedy-anchor | 合计 |
|---:|---:|---:|---:|---:|
| 20 | 1000 | 900 | 600 | 2500 |
| 30 | 175 | 200 | 125 | 500 |
| 50 | 425 | 350 | 225 | 1000 |
| 100 | 400 | 350 | 250 | 1000 |
| **合计** | **2000** | **1800** | **1200** | **5000** |

最低要求：

```text
每个 scale × family cell 至少达到目标的 80%。
每个非空 cell 必须同时包含 positive 和 negative / delay 样本。
每个 cell 至少覆盖多个 context，避免单 context 过拟合。
```

Stage 4 20-scale 支撑还需要单独统计：

```text
20-scale total rows >= 2000
20-scale Level A/B target rows >= 800
20-scale hard pairs >= 600
20-scale sector/random/greedy 均有 positive 和 delay/bad/hard-negative 样本
```

动态边界：

```text
Stage 4 偏置不是无限继续加 20-scale。

当 20-scale total rows 和 hard pairs 已过线，但 20-scale Level A/B 仍不足时，
新的 20-scale 样本只有在满足以下至少一个条件时才优先进入 selected subset：
    1. 新增 Level A/B target row；
    2. 新增 Level A/B-supported hard pair；
    3. 新增 Stage4 audit-evaluable row；
    4. 替换现有 Level C weak row。

否则，补样资源应优先转向：
    1. 100-scale sector-wave / greedy-anchor 空 cell；
    2. 100-scale random-wave 的 Level A/B 扩充；
    3. Stage4 audit binding 和 kNN/OOD audit 字段回填。
```

---

### 8.4 按样本类型

| 样本类型 | 目标行数 | 说明 |
|---|---:|---|
| same-context hard-pair target rows | 2400 | 约 1200 个 hard pairs，每个 pair 至少一正一负 |
| non-pair high_roi_positive | 1000 | 补充正向 trajectory signal |
| standalone hard-negative / delay-risk | 1100 | 压制 false-safe、bad-mode、low-ROI accept |
| kNN/OOD boundary rows | 500 | 训练与审计边界稳定性 |
| **合计** | **5000** | - |

说明：

```text
2400 条 hard-pair target rows ≈ 1200 个 same-context positive-negative pairs。
```

---

### 8.5 按证据强度

5000 条不是简单堆弱标签。建议强弱比例：

| evidence level | 目标行数 | 最低线 | 说明 |
|---|---:|---:|---|
| Level A target-only | 750-1000 | 600 | 校准 individual target 边界 |
| Level B ablation / marginal | 750-1000 | 600 | 校准边际贡献与 pairwise ranking |
| Level C weak same-context trace | 3000-3500 | - | 扩大 family / scale 覆盖 |

硬门槛：

```text
Level A/B target rows >= 1500
Level C weak rows <= 3500
Level A/B-supported hard pairs >= 500
```

---

## 9. Hard pair 定义与索引

Hard pair 记录最少包含：

```json
{
  "pair_id": "...",
  "context_hash": "...",
  "positive_target_id": "...",
  "negative_target_id": "...",
  "positive_roi": 0.0,
  "negative_roi": 0.0,
  "roi_gap": 0.0,
  "raw_score_gap_before": 0.0,
  "safe_score_gap_before": 0.0,
  "pair_type": "missed_high_roi_vs_low_roi_accept",
  "causal_evidence_id": "..."
}
```

优先采集的 pair 类型：

```text
1. missed_high_roi_vs_accepted_low_roi
2. missed_high_roi_vs_bad_mode_negative
3. missed_high_roi_vs_delay_risk_negative
4. accepted_high_roi_vs_accepted_low_roi_suppression
5. high_roi_positive_vs_replacement_heavy_negative
```

---

## 10. Target-level row schema

每条 target-level row 至少包含：

```text
sample_id
context_hash
true_dual_hash
fleet_dual_hash
cut_dual_hash
cut_hash
branch_hash
pool_signature_hash
active_support_hash
pricing_config_hash
forbidden_signature_hash
logical_graph_hash
path_option_universe_hash
start_time_candidate_hash
active_fleet_limit
rc_formula_version
feature_schema_version
label_threshold_manifest_id

instance
instance_path
region
family
task_count

candidate_batch_id
target_id
candidate_signature_id
intervention_signature
intervention_type

true_reduced_cost
target_task_set
target_task_sequence
target_transition_sequence
target_arc_option_sequence
target_path_type_pattern

primal_roi
normalized_primal_roi
retry_roi
normalized_retry_roi
accepted_impact_delta
bad_mode_switch
support_changed_good
tail_improved
final_judge_retry_delta
hidden_negative_delta

label_group
same_context_pair_group
causal_evidence_id
replay_script_hash
replay_artifact_path
evidence_level
audit_missing
audit_ready_for_checkpoint
stage4_gate_evaluable
stage4_ready_for_checkpoint_id
```

说明：

```text
stage4_gate_evaluable 只表示该样本对某个 checkpoint / threshold / OOD rule
具备完整审计字段，可以进入 Stage 4 gate 统计。

stage4_ready_for_checkpoint_id 只能绑定具体 checkpoint，不能作为样本永久属性。
换 checkpoint、threshold、training split 或 OOD rule 后必须重算 audit。
```

---

## 11. Batch-level sample schema

Batch-level sample 由 target rows group 得到，group key 为：

```text
context_hash + candidate_batch_id
```

每条 batch sample 至少包含：

```text
batch_sample_id
context_hash
candidate_batch_id
target_ids[]
positive_target_count
negative_target_count
true_rc_negative_count
nonnegative_count

batch_features
batch_type
batch_roi
normalized_batch_roi
batch_objective_progress
batch_tail_improved
batch_bad_mode_switch
batch_support_changed_good
batch_delta_v
batch_barrier_slack
batch_accepted_roi
```

要求：

```text
batch label 不得覆盖 individual target label；
individual target label 不得直接推断 batch label。
```

二者共同存在，但监督粒度不同。

---

## 12. kNN/OOD audit 字段

每条 Stage-4-gate-evaluable 样本必须补齐 kNN/OOD audit 字段。

但注意：

> kNN/OOD 字段不作为 GAT 训练输入，只作为 audit / gate / calibration 证据。

原因：这些字段依赖 checkpoint、embedding、training split、threshold config 和 safe radius。换模型后必须重算。

---

### 12.1 必填 kNN/OOD 字段

```text
checkpoint_id
embedding_model_config_hash
training_manifest_hash
threshold_config_hash
knn_train_split_id
threshold_group_key
stage4_gate_rule_id
safe_source_export_id

knn_k
knn_max_neighbor_delay_fraction
knn_candidate_delay_count
knn_candidate_count
knn_neighbor_delay_rate
knn_neighbor_ids
knn_neighbor_distances
knn_neighbor_labels

knn_in_distribution
knn_safe_radius
knn_safe_radius_multiplier
knn_nearest_safe_distance

ood_distance
safe_distance_margin_ratio

candidate_delay_risk_score
candidate_delay_risk_threshold_used
candidate_delay_gate_blocked

fallback_to_delay_queue
fallback_reason
stage4_gate_evaluable
audit_ready_for_checkpoint
```

---

### 12.2 字段缺失处理

如果样本缺 kNN/OOD audit 字段：

```text
可以进入 raw sample archive；
不能进入 Stage-4-gate-evaluable subset；
不能参与 safe precision / accepted ROI / false-safe gate；
不能用于声明 Stage 4 candidate readiness。
```

建议标记：

```text
audit_missing = true
stage4_gate_evaluable = false
audit_ready_for_checkpoint = false
```

kNN/OOD 字段随 checkpoint、embedding、training split、threshold config、
safe radius 和 fallback rule 变化。任何新 checkpoint 训练完成后，旧 audit
只能作为历史诊断，不能复用来声明新 checkpoint 的 Stage 4 readiness。

---

## 13. 证据等级

每个 target label 必须有 causal evidence。

证据等级：

```text
Level A: target-only intervention
    只加入该 target，重新解 RMP，观察 trajectory outcome。

Level B: batch ablation
    比较 U 与 U \ {target} 或 target-only 的差异。

Level C: signature-matched same-context causal trace
    只在 context / dual / cut / branch / pool 完全匹配时允许。
```

主训练优先使用：

```text
Level A / Level B
```

Level C 可以作为弱标签或补充样本，但必须单独标记。

使用规则：

```text
missed_high_roi_positive:
    优先 Level A / Level B；
    Level C 只能作为弱标签或 hard-pair seed，不能单独支撑 Stage 4 gate 主结论。

accepted_low_roi_negative:
    至少需要 Level B 或同 context accepted-vs-ablation 证据；
    不能只因旧 gate 接受且后续整体结果差就标负。

bad_mode_negative:
    必须有 Level A / Level B，或完整 causal trace 显示 retry / hidden negative /
    dual / basis 指标越过 bad-mode threshold。

delay_risk_negative:
    必须是 true-RC negative；
    正确语义是 DELAY_QUEUE；
    不能与 rc>=0 的 nonnegative_reject_only 合并。

same-context hard pair:
    positive 和 negative 必须共享完整 context key；
    至少一侧应有 Level A / Level B；
    pairwise 主训练和 Stage 4 gate 报告必须单独统计 Level C-only pair 占比。
```

主报告必须按 evidence level 分层统计 precision、ROI、hard-pair count 和
false-safe。若 Stage 4 gate 的主通过证据主要来自 Level C-only 样本，结论仍应为
`stage4_candidate_ready=false`。

---

## 14. 数据产生流程

### 阶段 A：现有证据挖掘

目标：优先补已知 hard pair。

执行：

```text
1. 读取 v99 / v102 / v103 / v107 context contrast rows。
2. 抽取 missed_high_roi_raw_and_safe_rank_reversal。
3. 抽取 accepted_high_roi_low_roi_suppression_pair。
4. 从 v53 / individual follow-up 中重建 target-level 正负混合证据。
5. 建立 initial hard_pair_index。
```

输出：

```text
seed_target_rows.jsonl
seed_pair_index.jsonl
seed_context_inventory.json
```

---

### 阶段 B：target-level causal replay

目标：把 batch-level 粗标签改成 target-level causal label。

执行：

```text
1. 固定 same context。
2. 对同一 context 内多个 target 做 target-specific intervention。
3. 记录每个 target 的 primal_roi、retry_roi、bad_mode_switch、support_changed_good。
4. 如果条件允许，做 batch ablation：U、U \ {target}、target-only。
5. 把 target 的边际影响写入 target-level row。
```

---

### 阶段 C：scale × family 受控补样

目标：补齐 20 / 30 / 50 / 100 和 sector / random / greedy 的交叉空洞。

执行：

```text
1. 先补缺口最大的 scale × family cell。
2. 每个 cell 同时采 positive 和 negative。
3. 每个 context 最多贡献固定数量 target rows。
4. 每个规模至少保留多个 instance / region。
5. 每个 family 至少保留多个 instance / region。
```

---

### 阶段 D：kNN/OOD audit 回填

目标：让样本不仅可训练，也可用于 Stage 4 safety audit。

执行：

```text
1. 对同一 checkpoint / training manifest / threshold config 重算 embedding。
2. 计算 neighbor_delay_rate、nearest_safe_distance、safe_radius、OOD margin。
3. 写入独立 audit artifact。
4. 生成 `stage4_gate_evaluable` 和 `audit_ready_for_checkpoint` 标记。
```

---

### 阶段 E：去重与一致性收口

去重主键：

```text
context_hash
target_id
intervention_signature
```

冲突检查：

```text
同一 target 不允许同时 high_roi_positive 与 bad_mode_negative；
same-context pair 不允许跨 true_dual_hash / cut_hash / branch_hash；
same sample 不允许缺 causal_evidence_id；
same target_sequence / arc_option_sequence 大量重复时要降权或去重；
same context 贡献过多 target rows 时要截断或降权。
```

---

## 15. Split 策略

本计划只生成数据，但必须提前写入 split 标签，避免后续训练误用 random-row split。

推荐 split：

```text
train
validation
family_holdout
scale_holdout
context_holdout
```

硬规则：

```text
同一个 context_hash 下的 target rows 不能拆到 train 和 validation 两边；
同一个 same_context_pair_group 不能拆开；
primary validation claim 中，同一个 instance_path 不能跨 train/validation；
如果为了诊断临时跨 instance_path，只能标 diagnostic split，不能声明 Stage 4 candidate ready；
family_holdout 必须至少覆盖 random-wave 或 greedy-anchor；
scale_holdout 必须至少覆盖 50 或 100；
family_holdout / scale_holdout / context_holdout 必须各自输出 precision / ROI / coverage / false-safe 统计；
训练报告不能使用 random-row split 作为主结论。
```

---

## 16. 质量门禁

### 16.1 数量门禁

```text
有效 target-level rows >= 5000
有效 batch-level samples >= 500
有效 unique contexts >= 350
有效 hard pairs >= 1200
Level A/B target rows >= 1500
Level A/B hard pairs >= 500
Level C weak rows <= 3500
Level C-only hard pair ratio <= 40%
20-task rows >= 2000
30-task rows >= 400
50-task rows >= 800
100-task rows >= 800
20-task Level A/B target rows >= 800
20-task hard pairs >= 600
sector-wave rows >= 1600
random-wave rows >= 1440
greedy-anchor rows >= 960
每个 scale × family cell >= 目标的 80%
```

---

### 16.2 标签门禁

```text
每个 family 至少包含 high_roi_positive 和 delay/bad/hard_negative。
每个 scale 至少包含 high_roi_positive 和 delay/bad/hard_negative。
每个 hard pair 必须 ROI gap > min_roi_gap。
每个 hard pair 必须绑定 label_threshold_manifest_id。
positive label 必须有 causal evidence。
negative label 必须区分 true-RC negative delay 与 rc>=0 reject。
true-RC negative delay label 不得进入 reject/nonnegative 类。
nonnegative_reject_only 不得参与 HIGH_PRIORITY / DELAY_QUEUE precision 主统计。
```

---

### 16.3 kNN/OOD 门禁

```text
Stage-4-gate-evaluable subset 中 kNN/OOD audit 字段完整率 = 100%。
所有 audit 字段必须绑定 checkpoint_id / threshold_config_hash。
所有 audit 字段必须绑定 stage4_gate_rule_id / safe_source_export_id。
audit_missing=true 的样本不能进入 Stage 4 gate。
换 checkpoint / threshold / OOD rule 后必须重新生成 audit rows。
```

---

### 16.4 泄漏门禁

禁止样本输入字段包含：

```text
state_next_*
delta_*
horizon_*
label_*
post_addition_*
future_objective
future_dual
future_support
future_retry
knn_*
ood_*
threshold_*
stage4_gate_*
```

这些只能作为 label 或 audit outcome，不能作为 model input。

---

## 17. 交付物

最终交付以下文件：

```text
1. stage3_targeted_sample_plan_manifest_v107_optimized.json

2. stage3_targeted_target_rows_v107_optimized.jsonl
   目标：至少 5000 条有效 target-level rows

3. stage3_targeted_batch_samples_v107_optimized.jsonl
   目标：至少 500 个有效 batch-level samples

4. stage3_targeted_pair_index_v107_optimized.jsonl
   目标：至少 1200 个 same-context hard pairs

5. stage3_targeted_knn_ood_audit_v107_optimized.jsonl
   目标：Stage-4-gate-evaluable 样本 audit 字段完整，且绑定 checkpoint / rule

6. sample_allocation_report_v107_optimized.md
   包含 family、scale、family×scale、label、hard pair、audit_missing、剔除原因分布

7. selection_manifest_v107_optimized.json
   记录 raw pool 到 5000 行 selected training subset 的选择规则、配额缺口和未选中有效行数
```

建议额外交付：

```text
rejected_sample_rows_v107_optimized.jsonl
causal_evidence_manifest_v107_optimized.json
split_manifest_v107_optimized.json
schema_manifest_v107_optimized.json
label_threshold_manifest_v107_optimized.json
stage4_gate_audit_binding_manifest_v107_optimized.json
```

---

## 18. 风险与控制

### 风险 1：过度聚焦 missed 场景导致泛化下降

控制：

```text
至少 30% 非 missed anchor 样本；
每个 context 设置最大贡献上限；
每个 scale × family 保留普通 positive / negative 样本。
```

---

### 风险 2：20-scale 过拟合，50/100 无效

控制：

```text
硬性 family × scale 配额；
scale-specific normalized ROI；
每个 scale 独立统计 positive / negative。
```

---

### 风险 3：kNN/OOD 字段随 checkpoint 变化

控制：

```text
kNN/OOD audit 字段版本化；
字段不作为模型输入；
训练新 checkpoint 后必须重算 audit。
```

---

### 风险 4：target-level 标签仍被 batch label 污染

控制：

```text
优先 target-only intervention；
其次 batch ablation；
弱 causal trace 必须单独标记；
禁止 batch label 直接广播给 target。
```

---

### 风险 5：100-scale 样本无法获得完整 long-horizon proof outcome

控制：

```text
100-scale 样本只定义 local same-context trajectory ROI；
不声称 exact optimality improvement；
不把 100-scale local ROI 当 certificate signal。
```

---

### 风险 6：正负样本比例看似平衡，但 pairwise 信息不足

控制：

```text
单独统计 hard pair 数量；
单独统计 same-context positive-negative pair coverage；
pairwise group 不得跨 context。
```

---

### 风险 7：target rows 足够，但 batch samples 不足

控制：

```text
同时设置 target rows、batch samples、unique contexts 三重门禁；
同一 batch 内 target rows 过多时做截断或降权。
```

---

## 19. 完成定义

本计划完成的标准：

```text
1. 至少 5000 条有效 target-level rows。
2. 至少 500 个有效 batch-level samples。
3. 至少 350 个有效 unique contexts。
4. 至少 1200 个有效 same-context hard pairs。
5. 至少 1500 条 Level A/B target rows。
6. 至少 500 个 Level A/B-supported same-context hard pairs。
7. Level C weak rows 不超过 3500 条。
8. 20/30/50/100 四档均达到最低样本线。
9. 20-task Level A/B target rows 和 hard pairs 达到 Stage 4 支撑线。
10. sector/random/greedy 三类 family 均达到最低样本线。
11. family × scale 交叉分布无明显空洞。
12. candidate-level labels 与 batch-level labels 分离，无 batch label 广播污染。
13. Stage-4-gate-evaluable 样本 kNN/OOD audit 字段完整，并绑定 checkpoint / threshold / OOD rule。
14. 所有样本有 causal_evidence_id。
15. 所有样本通过去重、context 一致性和泄漏检查。
16. 输出 label_threshold_manifest，所有 label 可追溯到统一阈值。
17. 输出 split_manifest，主结论不依赖 random-row split。
18. 输出 final manifest、target rows、batch samples、pair index、audit rows、allocation report。
```

本计划完成后，下一步才是：

```text
使用该样本集训练新的 GAT batch-impact model。
```

训练、测试、online A/B、solver 接入都不属于本计划范围。

本计划完成后的唯一正向声明应为：

```text
targeted_sample_expansion_complete = true
stage3_retraining_data_ready = true
stage4_audit_precondition_data_ready = true
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
```

---

## 20. 最终结论

这版计划只做一件事：

> 补一批真正有训练价值的样本。

不是：

```text
改模型；
调阈值；
接 solver；
启用 worker；
证明 20-task 200 秒目标。
```

而是：

```text
用 target-level、same-context、可回放、带 kNN/OOD audit 闭环的数据，
把 v107 暴露出的 rank failure、label pollution、family/scale 空洞
转化成可训练约束。
```

执行优先级：

```text
1. 先满足 20-scale 主验收规模的 hard pair 与 Level A/B 支撑线；
2. 20-scale total / hard pairs 过线后，只继续收 Level A/B、audit-evaluable 或可替换 Level C weak 的 20-scale 行；
3. 同步优先补 100-scale sector-wave / greedy-anchor 空 cell 和 random-wave Level A/B；
4. 再补 kNN/OOD audit binding，使样本能进入 Stage4 gate 统计；
5. 最后做去重、quota-selected subset 和质量门禁收口。
```

如果这批样本质量足够，后续训练才有可能真正修复：

```text
missed high-ROI；
false-safe；
low-ROI accepted；
family holdout collapse；
Stage 4 gate 不通过。
```

如果只是盲目扩大样本量，仍然会得到一个更大的但同样有偏的数据集。
