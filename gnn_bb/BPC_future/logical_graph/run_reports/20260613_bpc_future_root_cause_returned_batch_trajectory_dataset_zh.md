# BPC_future 根因审计补充：returned-batch trajectory dataset

日期：2026-06-13

## 目标

本轮继续推进“为什么做了很多仍然不行”的证据链，但不改 solver、pricing、RMP、Pulse worker、certificate 或 official lower bound。

目标是把前面散落在多份报告中的 returned-batch / downstream trajectory 信号，整理成一个可复用的 stage-level calibration dataset。

新增只读脚本：

```text
BPC_future/scripts/analyze_returned_batch_trajectory_dataset.py
```

输出：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/summary.json
```

该脚本只读取已有 `summary.csv` 和 JSONL，不启动求解器，不影响默认 benchmark。

## 数据来源

默认纳入 7 个已有结果集：

```text
sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613
sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613
sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613
sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613
sharded_pulse_phase11a_profile_pricing_time_sensitivity_smoke_20260613
sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613
sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613
```

抽取结果：

```text
stage_rows = 1536
scale 5 rows = 270
scale 10 rows = 576
scale 20 rows = 690
```

run-level label 分布：

```text
baseline = 515
improved = 144
no_regression = 725
worsened = 152
```

20-task strict improved/worsened 子集：

```text
stage_rows = 288
improved = 136
worsened = 152
```

## 抽取字段

每一行对应一次 heuristic `journey_pricing` stage，包含：

- run context：
  - dataset；
  - instance；
  - scale；
  - profile；
  - repeat；
  - run improvement class；
- pricing context：
  - `cg_iter`；
  - pricing state / reason；
  - best reduced cost；
  - selected / materialized / returned counts；
- returned-batch features：
  - returned task-set union size；
  - average task-set size；
  - pair overlap；
  - pair Jaccard；
- active-basis relation：
  - active top sample count before pricing；
  - active average overlap；
  - active average Jaccard；
  - active redundant / bridge / disjoint fraction；
  - active hash before / after；
- addition result：
  - requested / changed / new / replacement counts；
  - active changed / inactive changed counts；
  - addition productivity class；
- downstream labels：
  - next RMP objective delta；
  - active hash changed after；
  - zero fractional within 2 CG rounds；
  - incumbent update within 2 CG rounds；
  - next negative count；
  - next incomplete count。

注意：`pool_active_top_task_set_value_samples` 是 capped sample，因此 active-relation 特征是保守观测，不是完整 active set。

## 20-task strict 子集的直接统计

20 strict improved rows：

```text
returned_count avg = 4.948529411764706
returned_pair_overlap avg = 0.20886384856973092
active_avg_overlap avg = 0.430453431372549
active_redundant_frac avg = 0.0
incumbent_within2 avg = 0.6470588235294118
zero_fractional_within2 avg = 0.6911764705882353
next_incomplete_count avg = 2.036764705882353
```

20 strict worsened rows：

```text
returned_count avg = 2.098684210526316
returned_pair_overlap avg = 0.061001224652540445
active_avg_overlap avg = 0.44694809941520464
active_redundant_frac avg = 0.006578947368421052
incumbent_within2 avg = 0.21052631578947367
zero_fractional_within2 avg = 0.34210526315789475
next_incomplete_count avg = 2.2302631578947367
```

这进一步支持前面的机制判断：

- improved rows 更常有更大的 returned batch；
- improved rows 的 returned batch 内部 pair overlap 更高；
- improved rows 后续更常出现 incumbent update / zero-fractional episode；
- worsened rows 的 next incomplete count 略高；
- active overlap 差异很小，不能单独作为 selector。

但这些是 group-level 差异，不是可上线规则。

## 单阈值扫描：有信号，但远不够

在 20 strict 子集上做简单单特征阈值扫描。

预测 final improved 的最佳几个规则：

```text
returned_count >= 2.0
accuracy = 0.6770833333333334
tp = 64
fp = 21
tn = 131
fn = 72

returned_pair_overlap >= 0.42857142857142855
accuracy = 0.6770833333333334
tp = 54
fp = 11
tn = 141
fn = 82

returned_pair_overlap >= 0.25
accuracy = 0.6736111111111112
tp = 60
fp = 18
tn = 134
fn = 76
```

预测 `incumbent_within2` 的最佳单特征：

```text
active_avg_overlap <= 0.41666666666666663
accuracy = 0.6770833333333334
tp = 95
fp = 68
tn = 100
fn = 25
```

解释：

- `returned_count` 和 `returned_pair_overlap` 对 final improved 有信号；
- `active_avg_overlap` 对 downstream incumbent 有信号；
- 但 false positive / false negative 仍然很大；
- 最好单阈值 accuracy 只有约 `0.677`；
- `returned_count >= 2` 会漏掉 72 个 improved；
- high pair-overlap 规则 false positive 少一些，但漏掉 82 个 improved；
- active-overlap 规则抓到更多 incumbent positives，但 fp 有 68。

这再次证明：

> 当前 features 可以做 calibration signal，不能直接写成 production selector。

## 对根因的进一步收紧

本轮把 v2 综合报告里的判断落到一个可复用数据资产上：

1. 20-task 的 returned-batch 特征确实和 outcome / downstream trajectory 有统计关系；
2. 这种关系不是单一维度；
3. 简单阈值不足以同时低 false positive 和低 false negative；
4. 当前最有希望的是多特征、stage-aware、context-aware selector；
5. 但它必须经过 leave-one-instance / leave-one-dataset 验证，不能用同样本规则上线。

因此当前“做了这么多都不行”的根因仍然是：

> 我们已经能生成 negative candidates，也能观测 batch-level trajectory 信号，但还不能在 addition 前稳定预测哪批 concrete returned JourneyColumn 会改善后续 RMP / pricing path。

## 当前不能做的结论

不能据此接入：

- `returned_count >= 2`；
- `returned_pair_overlap >= 0.25`；
- `active_avg_overlap <= 0.416...`；
- 任意单阈值 selector；
- 默认 return8 / return12；
- 默认 Pulse worker；
- official certificate gate。

原因是这些规则在当前 20 strict stage rows 上最多只能提供弱信号，且没有跨实例/跨数据集 selector 证明。

## 下一步边界

下一步如果继续，应在这个 dataset 基础上做 calibration-only：

1. 加入 candidate-level signature / start-time / arc-option features；
2. 区分 concrete JourneyColumn，而不是只看 task-set；
3. 使用 leave-one-instance / leave-one-dataset 验证；
4. 把 `next_incomplete_count` 作为负标签之一；
5. 先输出 selector report，不改 solver 主线；
6. 只有 selector 对 5/10 no-op gate 和 20 hard set 都有稳定证据，才允许 opt-in A/B。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/analyze_returned_batch_trajectory_dataset.py
```

数据抽取：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_returned_batch_trajectory_dataset.py \
--output-dir BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613
```

结果：

```text
stage_rows = 1536
twenty_strict_stage_rows = 288
```

## 目标状态

本轮是根因证据资产建设，不是优化完成。

目标仍未完成：

- 仍没有 production selector；
- 仍没有证明 5/10 不退化且 20 大幅加速；
- 仍不能默认启用 worker / return quota / profile-DP cap；
- 仍不能打开 Pulse certificate gate。

## 追加：signature / arc-option 特征与 leave-one-dataset 验证

脚本已扩展解析 `negative_journey_signature_samples`，额外抽取：

- returned sequence count；
- average sequence length；
- first-task unique count；
- average start time；
- `start_time=0` fraction；
- arc option family fractions：
  - low_time；
  - low_risk；
  - low_energy；
- compact returned sequence samples；
- compact arc-family samples。

重新抽取同一批数据后，20 strict improved rows：

```text
returned_avg_sequence_len = 3.017156862745098
returned_first_task_unique_count = 1.3602941176470589
returned_avg_start_time = 21.911541970281863
returned_start_time_zero_frac = 0.4580269607843137
returned_low_time_arc_frac = 0.21107945902509306
returned_low_risk_arc_frac = 0.7335672774451769
returned_low_energy_arc_frac = 0.05535326352973003
```

20 strict worsened rows：

```text
returned_avg_sequence_len = 3.0016447368421053
returned_first_task_unique_count = 1.5789473684210527
returned_avg_start_time = 28.44683363486842
returned_start_time_zero_frac = 0.45230263157894735
returned_low_time_arc_frac = 0.2845757403530359
returned_low_risk_arc_frac = 0.6550939526674735
returned_low_energy_arc_frac = 0.06033030697949063
```

观察：

- improved rows 的 low_risk arc fraction 更高；
- worsened rows 的 low_time arc fraction 更高；
- improved rows 的 average start time 更低；
- 但这些仍然只是 group-level signal，不能直接说明某个 concrete signature 一定有益。

最关键验证是 leave-one-dataset 单阈值外推。

在 20 strict `288` rows 上，每次留出一个 dataset，用其它 dataset 拟合最佳单阈值，再在 held-out 上测试：

```text
total = 288
accuracy = 0.5277777777777778
tp = 0
fp = 0
tn = 152
fn = 136
```

这说明：

- 加入 sequence / start-time / arc-option 聚合特征后，单阈值仍无法跨 dataset 找到 improved rows；
- 当前外推结果退化成几乎只预测 non-improved；
- 这比同样本 accuracy 更有代表性，因为 production selector 必须面对未见 context；
- 因此当前特征集仍不能上线。

对根因的进一步收紧：

> concrete signature / arc-option / start-time 的确是需要纳入 selector 的层级，但仅靠当前 stage-level 聚合仍不够。真正需要的是 candidate-level 或 batch-element-level 模型，能区分同一 task-set 下不同 JourneyColumn signature/timing 对后续 active-basis trajectory 的影响。

当前不能做：

- 不能按 low_risk fraction 偏好返回；
- 不能按 start_time 更低偏好返回；
- 不能按 low_time / low_energy fraction 过滤；
- 不能用任何 leave-one-dataset 失败的单阈值规则。

下一步如果继续，只能进一步细化到 candidate-level：

- 每个 returned candidate 一行；
- 保留 task-set、sequence、arc family sequence、start_time、true RC、rough RC；
- 标记该 candidate 是否 added、是否 future active、是否进入 incumbent-producing path；
- 再做 leave-one-instance / leave-one-dataset；
- 在这个通过前，不做 production selector。

## 追加：candidate-level / batch-element rows

脚本继续扩展，新增输出：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

每一行对应一个 returned negative candidate，task-set 由 signature 中的 sequence 反推，而不是直接使用 `negative_journey_task_set_samples` 的顺序。

这样处理是必要的，因为实际日志中存在：

```text
negative_journey_task_set_samples[0] = [1,15,20]
negative_journey_signature_samples[0] sequence = [20,15,5]
```

也就是说，task-set samples 与 signature samples 不能假设按位置一一对齐；candidate-level 分析必须以 concrete signature / sequence 为准。

candidate-level 抽取结果：

```text
candidate_rows = 2096
twenty_candidate_rows = 1250
twenty_strict_candidate_rows = 848
twenty_strict improved candidates = 553
twenty_strict worsened candidates = 295
```

20 strict improved candidate averages：

```text
candidate_sequence_len = 2.992766726943942
candidate_start_time = 23.89625568083183
candidate_low_time_arc_frac = 0.13580470162748642
candidate_low_risk_arc_frac = 0.8366184448462929
candidate_low_energy_arc_frac = 0.027576853526220614
candidate_active_overlap = 0.4282700421940928
candidate_active_jaccard = 0.32145871006630505
candidate_added = 0.8752260397830018
candidate_new_task_set = 0.840867992766727
candidate_future_active_within2 = 0.22965641952983726
incumbent_within2 = 0.6781193490054249
next_incomplete_count = 1.8535262206148282
```

20 strict worsened candidate averages：

```text
candidate_sequence_len = 2.986440677966102
candidate_start_time = 25.389270871186444
candidate_low_time_arc_frac = 0.291000807102502
candidate_low_risk_arc_frac = 0.6538498789346247
candidate_low_energy_arc_frac = 0.055149313962873286
candidate_active_overlap = 0.44615819209039553
candidate_active_jaccard = 0.35271186440677965
candidate_added = 0.9457627118644067
candidate_new_task_set = 0.8271186440677966
candidate_future_active_within2 = 0.3728813559322034
incumbent_within2 = 0.10847457627118644
next_incomplete_count = 2.6033898305084744
```

这组数据给出两个重要信息：

1. improved candidates 里 low_risk 比例更高、low_time 比例更低，这和 stage-level 聚合一致；
2. worsened candidates 反而更常被 added、更常在未来 active sample 中出现。

第二点很关键：

> candidate 被加入、甚至未来进入 active sample，并不自动意味着 run 会进入好 trajectory。

这再次说明 selector 不能只预测“是否 added”或“是否 future active”，还要预测它是否把后续 active basis 推向 incumbent-producing / low-incomplete path。

## candidate-level leave-one-dataset 验证

只使用 addition-before candidate + batch-context 特征做单阈值外推：

- candidate position in returned batch；
- sequence length；
- start time；
- arc count；
- low_time / low_risk / low_energy fraction；
- active overlap / active Jaccard；
- batch returned count；
- batch pair overlap / Jaccard；
- batch active overlap / redundancy / bridge fraction。

不使用后验字段：

- `candidate_added`；
- `candidate_future_active_within2`；
- `incumbent_within2`；
- `zero_fractional_within2`；
- `next_incomplete_count`。

验证结果：

```text
total = 848
accuracy = 0.34787735849056606
tp = 3
fp = 3
tn = 292
fn = 550
```

这个结果比 stage-level 还弱，说明：

- candidate-level 基础 signature 特征有 group-level 信号；
- 加入 batch-context 后，简单单阈值仍几乎不能跨 dataset 找到 improved candidates；
- 特别是 `tp = 3, fn = 550`，说明绝大多数 improved candidates 会被漏掉；
- 当前不能把 low_risk、low_time、start_time、active overlap、batch pair overlap 或 batch active overlap 任何一个字段写成 production rule。

## candidate + batch-context 二特征验证

为了检查“一个 candidate 字段 + 一个 batch 字段”的简单组合是否足够，本轮又做了分位点阈值的二特征 leave-one-dataset 验证。

验证结果：

```text
total = 848
accuracy = 0.6698113207547169
precision = 0.7349397590361446
recall = 0.7721518987341772
tp = 427
fp = 154
tn = 141
fn = 126
```

这个总数表面比单阈值好，但不能直接当作可上线 selector。原因是正例几乎全部来自一个 held-out dataset：

```text
held-out phase10h: tp = 427, fp = 154, tn = 13, fn = 54
其余 6 个 held-out datasets: tp = 0
```

也就是说，二特征规则仍然高度依赖数据集/context。它能在某个结果集上捕捉局部模式，但不能稳定跨 profile / result-set 外推。

因此二特征验证的结论不是“selector 已经可用”，而是：

> candidate signature + batch context 的方向是对的，但简单二特征阈值仍不是 production rule；当前失败点已经从“没有信号”收紧为“有信号但跨 context 泛化不稳定”。

## candidate + batch-context leave-one-instance 验证

为了进一步区分“只是跨 result-set 不稳定”还是“跨 instance 也不稳定”，本轮增加 leave-one-instance 验证。

单阈值结果：

```text
total = 848
accuracy = 0.27712264150943394
tp = 56
fp = 116
tn = 179
fn = 497
```

二特征结果：

```text
total = 848
accuracy = 0.4233490566037736
precision = 0.5883977900552486
recall = 0.38517179023508136
tp = 213
fp = 149
tn = 146
fn = 340
```

这个结果比 leave-one-dataset 的二特征总指标更弱，说明简单 candidate+batch selector 不是只在跨 result-set 时失效；在当前 20 strict 的三个 instance 之间外推也不稳定。

因此当前不能把二特征阈值改写成 production rule，也不能把它作为 20-task hard-tail 默认触发条件。

## 进一步根因判断

candidate-level 数据让根因更明确：

> 20-task 不是只需要“返回会进入 active 的列”。worsened candidates 甚至更常被 added 和 future-active。真正缺失的是判断这个 concrete candidate / batch 是否会引导后续 active-basis trajectory 进入 incumbent-producing、低 incomplete 的路径。

也就是说，根因不是：

- 没有 negative columns；
- 没有 added columns；
- 没有 future-active columns；
- 没有 low-risk / low-time / early-start signature。

更准确是：

> 缺少一个能在 addition 前预测 downstream trajectory quality 的 selector，而且这个 selector 需要同时看 candidate signature 与 batch context，而不是单个 candidate 的简单字段。

## 当前后续边界更新

下一步如果继续，不能再做单阈值 selector。

更合理的 calibration-only 方向是：

1. 保留 candidate-level rows；
2. 构造 batch-with-elements 表，把同一 stage 的 candidate 组合关系也纳入；
3. 加入 per-candidate true RC / rough RC / rank，如果日志可重建；
4. 把标签拆开：
   - candidate added；
   - candidate future active；
   - stage incumbent-within2；
   - stage next-incomplete-heavy；
   - run final improved；
5. 做 leave-one-instance / leave-one-dataset；
6. 只有在跨 dataset 下能抓到 improved 且 false positive 可控，才允许 opt-in A/B。

目标仍未完成。
