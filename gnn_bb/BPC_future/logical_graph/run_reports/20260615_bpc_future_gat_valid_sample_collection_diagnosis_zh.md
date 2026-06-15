# GAT 有效样本采集诊断报告

日期：2026-06-15

## 当前结论

无效样本多，不是因为 GAT 已经证明“没用”，而是因为大部分候选还没有形成可训练的因果干预样本。

### 2026-06-15 最新状态

已完成 cross-family high-diverse target-intervention A/B 的只读审计，并合并旧的 same-run / delay-queue / seed-apollo worker A/B 结果。

最新合并 ROI dataset：

```text
dataset = BPC_future/results/gat_same_run_combined_plus_seed_cross_family_worker_roi_dataset_20260615
row_count = 20
training_row_count = 18
unique_training_row_count = 18
label_counts = {'0': 10, '1': 8}
positive_training_label_count = 8
negative_training_label_count = 10
positive_family_count = 3
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
target_causal_match_count = 20
worker_context_match_count = 20
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 2}
sample_collection_gaps = []
training_ready = true
production_ready = false
certificate_ready = false
official_bound_effect = false
```

这说明当前已经从“样本因果性不足 / family 覆盖不足”推进到“可以做离线 ROI gate 训练”的状态。但它仍不是生产可用 GAT：样本只有 18 条可训练记录，不能默认启用，不能参与 certificate，也不能绕过 5/10 no-regression 与 20-task ROI A/B。

有效样本必须同时满足：

1. 同一个 `context_hash`；
2. 同一个 pricing stage；
3. worker 确实执行；
4. 目标序列被 materialized 或 returned；
5. worker 加列后能观测到 RMP / tail / objective / support 的变化。

只要其中任一条件不满足，该样本只能进入 invalid bucket，不能作为正样本，也不能作为负样本。

## 为什么无效样本多

### 1. 旧 runbook 没有 exact-stage worker hook

之前同上下文候选大多来自 `capture_pricing_kind=exact`，但 worker 命令设置为：

```text
journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False
```

而 B&B 节点路径原来只有 before-heuristic worker 入口，导致 exact-stage 候选即使通过 GAT+kNN/OOD，也没有真正触发 worker。

这类样本的本质是：

```text
候选存在，但干预没有发生
```

不能当作训练标签。

### 2. 修正 hook 后，发现首个候选目标不完整

修正后首个候选已经在目标 context 下执行 worker：

```text
expected_context_hash = 587e2ac350a8619b
expected_context_executed_event_count = 1
reachability_class = worker_executed_without_target_causal_match
```

但第一次失败不是 GAT 判断错，而是候选抽取只保留了第一段 sortie：

```text
抽取目标 = [3, 9]
真实负列 = [[3, 9], [11, 14]]
```

也就是说，worker 在追一个不完整目标，当然无法复现离线日志中的完整负列。

修正后，候选改为完整 journey trace：

```text
target_sequence = [3, 9, 11, 14]
target_sortie_traces = [[3, 9], [11, 14]]
```

重新跑第一个候选后，结果变为：

```text
reachability_class = target_intervention_reachable
pulse_worker_status = FOUND_NEGATIVE
pulse_worker_reason = target_materialized_negative_true_rc
pulse_worker_returned_journeys = 1
pulse_worker_best_rc = -7.298596667
pulse_worker_target_sequence_materialized = True
pulse_worker_target_sequence_negative = True
added_journeys = 1
global_certificate = False
```

这说明首个候选现在已经是一个有效的因果干预样本，而不是无效样本。

### 3. rc negative 不是有效标签

离线看到某个 journey 在某个日志里是 true-RC negative，只能说明它曾经在某个上下文下可负。

它不能自动说明：

```text
把它作为 target worker 加入当前 RMP 会改善 trajectory
```

因此 `rc_negative_only`、`appeared_in_positive_batch`、`replacement_without_support_change` 都不能直接作为正样本来源。

## 怎样采集有效样本

### Step 1：只从同上下文高优先级候选开始

候选必须来自 GAT+kNN/OOD high priority，并带完整上下文：

```text
context_hash
true_dual_hash
cut_hash
branch_hash
forbidden_signature_hash
active_hash_before
pool_signature_hash
pool_task_set_hash
target_sequence
target_arc_option_sequence
```

### Step 2：强制同阶段触发

如果候选来自 exact capture：

```text
before_heuristic = False
before_exact = True
```

如果候选来自 heuristic capture：

```text
before_heuristic = True
before_exact = False
```

### Step 3：必须记录 target causal match

只有以下任一情况成立，才允许进入 ROI label 构建：

```text
pulse_worker_target_sequence_materialized = True
```

或：

```text
returned / harvested sequence samples 命中 target_sequence
```

否则只能记为不可达、超时、context miss 或 target miss。

### Step 4：ROI 标签必须来自真实 worker 对照

有效标签不是 GAT 分数，也不是 reduced cost。

有效标签必须来自：

```text
baseline run
target worker run
```

对比：

```text
primal improvement
columns_delta
exact_pricing_calls_delta
support_changing_count
next RMP objective_delta
tail retry / hidden-negative change
```

### Step 5：负样本也必须是“有效干预后的无收益”

只有当：

```text
同 context
同 stage
worker executed
target causal match
returned or materialized target
```

并且 ROI 没有改善，才能作为负样本。

如果只是：

```text
worker missing
context mismatch
target not materialized
deadline before target
```

不能作为负样本。

## 本轮修正

已新增 exact-stage opt-in worker hook：

```text
journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True
```

并更新 runbook：

```text
capture_pricing_kind=exact -> before_exact=True
capture_pricing_kind=heuristic -> before_heuristic=True
```

当前首个候选已从：

```text
worker_hook_not_triggered
```

推进到：

```text
target_intervention_reachable
```

本轮还修正了候选抽取：

```text
不再只抽取 first-sortie target；
每个候选保存完整 target_sortie_traces；
worker 可直接按完整 trace 物化目标列；
物化目标列仍只作为 FOUND_NEGATIVE worker 输出，不参与 certificate。
```

第一条 reachable 样本的 baseline / worker 对照：

```text
baseline primal = 523.233925
worker primal = 519.413409
primal improvement = 3.820516
baseline columns = 337
worker columns = 341
columns_delta = 4
roi_class = positive_primal_roi
```

随后补跑剩余 5 个 high-priority 候选，最终 6 个候选全部完成 target intervention：

```text
reachable_target_intervention_count = 6
reachability_class_counts = {target_intervention_reachable: 6}
certificate_ready = false
official_bound_effect = false
```

最终 ROI 分布：

```text
positive_primal_roi_count = 3
negative_primal_roi_count = 2
no_observed_roi_count = 1
nonpositive_roi_count = 3
all_checks_pass = true
```

已生成离线 ROI 标签数据集：

```text
row_count = 6
training_row_count = 6
unique_training_row_count = 6
label_counts = {0: 3, 1: 3}
target_causal_match_count = 6
worker_context_match_count = 6
worker_context_mismatch_count = 0
training_ready = false
production_ready = false
```

`training_ready=false` 是正确结果：默认门槛要求正/负样本数和跨实例/family 分布都达标，当前 6 条只能证明采样链路有效，不能直接训练生产 GAT。

随后补充 DELAY_QUEUE 候选作为对照样本，并与 HIGH_PRIORITY 候选合并审计。

合并后的 reachability：

```text
record_count = 12
reachable_target_intervention_count = 12
reachability_class_counts = {target_intervention_reachable: 12}
certificate_ready = false
official_bound_effect = false
```

合并后的 ROI 分布：

```text
positive_primal_roi_count = 3
negative_primal_roi_count = 3
no_observed_roi_count = 5
columns_only_roi_count = 1
nonpositive_roi_count = 8
all_checks_pass = true
```

合并后的离线 ROI 标签数据集：

```text
row_count = 12
training_row_count = 11
unique_training_row_count = 11
label_counts = {0: 8, 1: 3}
target_causal_match_count = 12
worker_context_match_count = 12
worker_context_mismatch_count = 0
training_ready = false
production_ready = false
```

`training_ready=false` 仍然是正确结果：

```text
positive_training_label_count = 3 < 5
positive_family_count = 1 < 2
negative_family_count = 1 < 2
positive_region_count = 1
positive_region_counts = {tranquillitatis_balmer_like_20km: 3}
negative_region_count = 2
negative_region_counts = {apollo15_20km: 3, tranquillitatis_balmer_like_20km: 5}
```

也就是说，现在有效干预样本已经从 6 条扩到 12 条，但还只是“可用于校准采样链路”的小样本，不是可用于训练生产 GAT 的数据集。
更具体地说，当前正样本全部来自 Tranquillitatis，Apollo 目前只贡献了无收益 / 负 ROI / columns-only 样本，因此还不能让 GAT 学到跨 region 稳定的正向规律。

随后增加一轮 20-task seed 扩采：

```text
seed_capture_instances = 5
seed_capture_status = TIME_LIMIT for all 5, logs complete
seed_same_run_rows = 28
seed_graph_samples = 28
seed_candidate_labels = {add: 559, abstain: 48}
seed_decision_scope = all
seed_decision_records = 28
seed_HIGH_PRIORITY_candidates = 12
seed_DELAY_QUEUE_candidates = 12
```

这里的 `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过，也不能作为 production gate 证据。

从 seed HIGH_PRIORITY 中抽取 Apollo 候选并跑了 4 个 target-intervention A/B：

```text
record_count = 4
reachable_target_intervention_count = 4
pulse_worker_status = FOUND_NEGATIVE for all 4
positive_primal_roi_count = 3
no_observed_roi_count = 1
certificate_effect = false
official_bound_effect = false
```

合并 seed 后的 ROI 数据集：

```text
row_count = 16
training_row_count = 15
unique_training_row_count = 15
label_counts = {0: 9, 1: 6}
positive_training_label_count = 6
negative_training_label_count = 9
positive_region_count = 2
positive_region_counts = {apollo15_20km: 3, tranquillitatis_balmer_like_20km: 3}
negative_region_count = 2
negative_region_counts = {apollo15_20km: 4, tranquillitatis_balmer_like_20km: 5}
positive_family_count = 1
negative_family_count = 1
sample_collection_gaps = [
  {name: positive_family_count, observed: 1, required: 2, missing: 1},
  {name: negative_family_count, observed: 1, required: 2, missing: 1}
]
training_exclusion_reason_counts = {unsupported_roi_class:columns_only_roi: 1}
training_ready = false
production_ready = false
```

这一步的价值是：Apollo / Tranquillitatis 都已经有正负 ROI，正样本不再只来自 Tranquillitatis。
当前 `training_ready=false` 的原因也更具体了：不是有效样本数量不够，也不是 region 不平衡，
而是默认训练门槛要求跨 family，当前 Moon Trek ROI 样本仍只有 `sector-wave` 一个 family。
这可以防止我们把单 family 规律误当成可泛化的生产 GAT 规律。

这说明同样是 GAT+kNN/OOD 通过的 HIGH_PRIORITY true-RC negative，真实干预后仍然分成三类：

```text
改善 RMP/primal trajectory 的正样本；
损害 trajectory 的负样本；
无明显变化的中性样本。
```

因此 GAT 标签不能用 `rc < 0`，也不能用 `HIGH_PRIORITY`，必须用同 context target intervention 后的 ROI 结果。

## 下一步

不要把 context miss、worker missing、target miss 记为负样本。

下一步应做：

1. 只把 `target_intervention_reachable` 且有 ROI 对照的记录进入训练集；
2. 正样本必须来自 `positive_primal_roi`、support-changing 或 tail 改善；
3. 负样本必须来自 reachable 但无 ROI / negative ROI 的真实干预，不能来自未触发/未到达；
4. 当前 15 条训练样本只能证明采样链路有效，不能直接训练生产 GAT；
5. 如果只做 `sector-wave` 内部实验，可显式降低 family 门槛，但必须保留 region / instance holdout；
6. 若要进入生产 GAT，继续从不同 family 或不同生成机制采集 positive / negative ROI，尤其是 support-changing / tail-retry-reducing 样本；
7. 仍然不允许 GAT / kNN / worker 参与 certificate 或 official lower bound。
