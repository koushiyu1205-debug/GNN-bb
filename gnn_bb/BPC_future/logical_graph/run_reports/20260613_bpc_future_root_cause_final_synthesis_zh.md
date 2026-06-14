# BPC_future 根因综合报告：为什么 5/10 不能退化、20 又不能稳定优化

日期：2026-06-13

## 结论先行

当前已经可以把失败原因收紧到一个具体层级：

> 现有求解器在 20-task hard tail 中并不是单纯“找不到负列”，而是缺少一个能在 addition 前判断 returned batch 是否会改善后续 RMP/dual/pricing trajectory 的 selector。profile-DP / ordinary pricing 可以产生很多 true-RC negative candidates，但当前 returned batch ordering / truncation 主要按 rough RC、scan order、简单 diversity 或 return limit 决定，可能返回更负但轨迹更差的 JourneyColumn signature，截掉较弱但更有利的 candidate。

这解释了为什么前面很多方向都“不行”：

- Pulse worker 能安全加 true-RC negative columns，但它加到的列不稳定减少 tail；
- 扩大 returned count 有时改善、有时恶化，因为它只是扰动 batch，而不是选择好 batch；
- 提高 profile-DP cap / pricing time / selection mode 能改变候选域，但不保证 returned cut 选对；
- 单列 rank、rough RC、best RC 不是 usefulness predictor；
- batch-level 特征有弱相关，但反例仍存在，不能作为 production rule；
- 5/10 的收益空间太小，任何真实 worker/probe/search 固定开销都可能造成回退；当前全 results scan 中 task10 triggered rows `worsened=133` 且 `official_changed=61`，因此当前 5/10 no-regression 主要靠 no-op / 20-only gate 保住，不是 worker/probe 本身已经有生产收益。

所以当前“做了这么多还不行”的根因不是某个 Pulse bug，也不是简单参数没调够，而是：

> 20-task 的有效改进依赖 returned JourneyColumn batch 对 RMP active basis 的非线性轨迹影响；我们现在能观测到这个机制，但还没有找到 addition 前可见、可泛化、能保护 5/10 的 selector。target002 复核进一步显示，早期 cg1 returned-batch composition 一变，后续 active trajectory 就不再到达旧的 cg3 exact context。

最新 `mt20_greedy_apollo_01` exact-context counterfactual replay 把这个判断进一步收紧：同一 RMP pool / true dual / cuts / effective fleet context 下，captured Pulse returned batch 能把局部 RMP objective 从 `1061.554044` 降到 `924.43786`，说明“有用的 returned batch”真实存在；但这仍只是单个 capture context 的局部 RMP treatment impact，不是全 BPC wall-time / optimality speedup，也没有给出 addition-before selector。

最新 exact-context replay selector gate 进一步排除了一个诱人的错误方向：用全样本 `true_reduced_cost` 阈值做 selector。当前 280 条 exact replay impact rows 里，推荐规则 `true_reduced_cost <= -12.430587` 的 full-sample precision 为 `0.89`、recall 为 `0.8516746411483254`，但仍有 `22` 个 false positives 和 `31` 个 false negatives；不能作为 production selector。

进一步检查 feature/model/rule-family gate 后，仍然不能形成 production selector。`selector_micro_vs_fold_gate` 中 `robust_all_fold_passing_feature_count = 0`，`selector_model_micro_vs_fold_gate` 中 `robust_all_fold_passing_model_count = 0`；`18887` 个单条件/两条件 addition-before conjunction 中 `material_all_fold_passing_rule_count = 0`，只保留 20-task rows 后 `18901` 个规则中仍为 `0`。

训练式 rule-family holdout 给出更细的边界：每个 fold 都用训练集重新选规则，context material folds 仍只有 `17/28`，20-only 仍只有 `17/27`。20-only context folds 同时有 `4` 个 false-positive/no-positive contexts 和 `3` 个 missed-positive contexts；同一 instance 内有 `2` 组、同一 dataset 内有 `2` 组同时包含 low-positive 与 high-positive context。这说明失败不是阈值整体偏松/偏紧，也不是粗粒度 instance/dataset 差异，而是当前 RMP/context trajectory 改变了列局部特征与 downstream impact 的关系。

随后对 `mt20_greedy_tranq_01` 和 `tranq20_01` 做同类 capture 扩展尝试，两者都停在 `INCOMPLETE_LIMIT / profile_dp_state_cap_tail`，worker events 为 `0`，capture events 为 `0`。这说明 exact-context replay 工具链已经可用，但高质量 replay 样本的瓶颈转为：如何稳定产生 no-certificate-effect returned-batch capture。它进一步反对“简单扩大 worker / probe 就能稳定优化”的解释。

## 证据链

### 1. Pulse worker 路线安全，但没有稳定 ROI

Phase 11D 汇总了 Phase 7O 到 Phase 11C 的负结果：

- Phase 7O hard-tail worker ROI A/B：
  - 24 行全部 `TIME_LIMIT`；
  - 24 行 official pricing state 全部 `INCOMPLETE_LIMIT`；
  - critical disagreement 为 0；
  - worker events 为 14；
  - legacy final judge calls 为 48；
  - completion-bound retry count 为 0；
  - audit shards incomplete 为 152。
- Phase 8Q passed-source validation：
  - 35 行全部 `TIME_LIMIT`；
  - critical disagreement 为 0；
  - worker returned / added journeys 为 10 / 10；
  - worker added new task sets 为 8；
  - worker added support-changing 为 2。

这些结果说明：

- Pulse worker 的 exactness 接线是安全的；
- worker 返回列可以进入正常 add-column path；
- 但“能加负列”没有稳定转化为 wall time、gap、status 或 final-judge tail 改善。

因此继续扩大 worker budget、打开 worker default、或者开放 official certificate gate 都没有证据基础。

### 2. Profile-DP / selection / budget 调参不能稳定解决 20-task

Phase 11D 同时总结了 profile-DP 与 selection mode 的负结果：

- Phase 11B 中，20-task state1000 smoke 的 selected counts 可以被扰动到 `72 / 18 / 18`，但没有 official 改善；
- 5/10 guard 的 15 行全部 `TIME_LIMIT / INCOMPLETE_LIMIT`，critical disagreement 为 0，official result changed 为 0；
- Phase 11C 中，adaptive refinement 没有降低 incomplete：
  - audit_no_refine：shards total 120，certified 2，incomplete 108，negative 10，refined 0；
  - audit_refine：shards total 120，certified 2，incomplete 108，negative 10，refined 0。

这说明：

- 提高搜索预算或改变 selection mode 可以改变候选数量；
- 但没有稳定改善 hard tail；
- adaptive refinement 当前也没有进入有效 proof-completion path；
- 不能把“搜得更多”当成“解得更好”。

### 3. Returned cut 边界是真实机制，但扩大 returned count 不是解法

returned-boundary calibration 在 Apollo20 / dp1000 上直接观测到：

- baseline 每轮只返回 rank0；
- rank1+ 仍有 strong negative candidates，但被 return limit 截断；
- early quota return8 把 baseline 会截断的 rank1-rank7 带入 returned batch；
- Apollo20 该单点 primal 从 baseline `921.640296` 改善到 return8 `793.914380`。

关键 cg1 returned batch：

```text
rank0  [5,8,15]   rough=-139.913748
rank1  [4,5,8]    rough=-137.150710
rank2  [5,8,18]   rough=-136.660461
rank3  [4,5,15]   rough=-136.347326
rank4  [4,8,15]   rough=-136.011232
rank5  [4,5,18]   rough=-134.743366
rank6  [8,15,16]  rough=-132.930824
rank7  [8,15,18]  rough=-132.886574
```

直接含义：

- baseline 不是没有候选；
- returned cut 确实截掉了很多 negative candidates；
- 单点改善不是因为 rank0 `[5,8,15]`，因为 baseline 和 return8 都返回它；
- 改善更像 rank1-rank7 的 batch effect 改变后续 RMP trajectory。

但这不是 production 解法，因为 Phase 10H / cross-log audit 已经证明：

- return8 / return12 在不同 20-task contexts 上方向相反；
- `mt20_greedy_tranq_01` return8 worsened，而 return12 improved；
- `mt20_greedy_apollo_01` return12 三次 worsened；
- final fractional sum、best RC、returned count 都不能单独解释 outcome。

因此根因不是“returned 太少”，而是“缺少选择有益 returned batch 的 selector”。

### 4. Candidate-level 对照证明：更负 RC 不等于更有用

candidate-level contrast 比较了 `mt20_greedy_apollo_01` return8 的 r0 / r2。

cg3 前 context 完全一致：

- cg1 / cg2 RMP objective 一致；
- cg1 / cg2 active hash 一致；
- cg1 / cg2 dual hash 一致；
- cg3 前 objective 都是 `780.586496`；
- cg3 前 active hash 都是 `16862add48072518`；
- cg3 前 dual hash 都是 `350001260a512742`；
- cg3 前 fractional sum 都是 `7.0`。

分叉发生在相同 RMP/dual context 的 candidate / materialization / return path。

r0 worsened：

```text
best_rc = -64.283449
negative_candidate_count = 86
selected_candidate_count = 16
returned_count = 8
return_limit_truncated_count = 8
```

`[5,10,18]` 出现在 negative / selected samples 中，但没有进入 materialized / returned samples。

r2 improved：

```text
best_rc = -20.1912655
negative_candidate_count = 78
selected_candidate_count = 14
returned_count = 8
return_limit_truncated_count = 6
```

`[5,10,18]` 进入 materialized / returned samples，并触发后续 incumbent update。

这直接排除几个错误解释：

- 不是有益 family 不存在；
- 不是前序 RMP/dual context 不同；
- 不是 best RC 越负越好；
- 不是 selected 就够，必须进入 materialized / returned cut；
- 问题集中在 selected candidate scan / materialization / return cut 的排序与截断。

### 5. 单列和 batch 特征都还不够成为 selector

selector feature audit 显示 Apollo20 dp1000 return8 cg1 中：

- rank0-rank3 更负，但后续 active top sample 未出现；
- rank4-rank7 较弱，但后续 active top sample 出现。

但 cg2 又相反：

- rank0 出现于 active；
- rank1-rank7 不 active。

因此“较弱 rank 更好”也不是规则。

batch selector audit 给出弱相关：

| group | future-hit ratio | union | pairwise Jaccard |
|---|---:|---:|---:|
| Phase 10H improved | 0.278 | 15.0 | 0.173 |
| Phase 10H worsened | 0.203 | 13.0 | 0.197 |
| RC-C / return12 improved | 0.306 | 17.5 | 0.139 |

这些信号说明 batch-level 特征比单列特征更接近机制。

但反例仍然存在：

- `mt20_greedy_tranq_01` return8 三次 worsened，future-hit ratio `0.348`、union `15`，高于不少 improved rows；
- Apollo20 return12 第三次 pairwise Jaccard `0.169`，接近 improved rows，但仍 worsened。

因此当前 batch features 只能作为 calibration signal，不能作为 production selector。

同样，exact replay impact rows 上的全样本 `true_reduced_cost` 阈值、二特征 pair gate 和当前简单多特征模型都只能作为 calibration signal。它们在同样本或部分 holdout 中看起来强，但跨 dataset 不稳定；因此不能把 `true_reduced_cost <= -12.430587`、`new_task_set`、`duplicate_signature`、`active_support_changing`、简单 `true_reduced_cost OR cost` 组合，或当前 nearest-centroid / shallow-tree 模型上线为 production selector。

### 6. candidate + batch-context 外推仍然不稳定

returned-batch trajectory dataset 已经把 stage-level rows 扩展到 candidate-level / batch-element rows：

```text
candidate_rows = 2096
twenty_candidate_rows = 1250
twenty_strict_candidate_rows = 848
twenty_strict improved candidates = 553
twenty_strict worsened candidates = 295
```

新的负证据是：

- 20 strict improved candidates 的 `candidate_added` 平均为 `0.8752260397830018`；
- 20 strict worsened candidates 的 `candidate_added` 平均反而更高，为 `0.9457627118644067`；
- 20 strict improved candidates 的 `candidate_future_active_within2` 为 `0.22965641952983726`；
- 20 strict worsened candidates 的 `candidate_future_active_within2` 反而更高，为 `0.3728813559322034`。

因此 candidate 被加入、甚至后续进入 active sample，都不是 good trajectory 的充分条件。

只使用 addition-before candidate + batch-context 特征做 leave-one-dataset 验证：

```text
single-threshold:
  total = 848
  accuracy = 0.34787735849056606
  tp = 3
  fp = 3
  tn = 292
  fn = 550

two-feature quantile-threshold:
  total = 848
  accuracy = 0.6698113207547169
  precision = 0.7349397590361446
  recall = 0.7721518987341772
  tp = 427
  fp = 154
  tn = 141
  fn = 126
```

二特征总指标表面变好，但正例几乎全部来自一个 held-out dataset：

```text
  phase10h held-out: tp = 427, fp = 154
  other 6 held-out datasets: tp = 0
```

leave-one-instance 进一步验证：

```text
single-threshold:
  accuracy = 0.27712264150943394
  tp = 56
  fp = 116
  tn = 179
  fn = 497

two-feature:
  accuracy = 0.4233490566037736
  precision = 0.5883977900552486
  recall = 0.38517179023508136
  tp = 213
  fp = 149
  tn = 146
  fn = 340
```

这说明当前失败点已经从“没有可观测信号”收紧为：

> candidate signature + batch context 有信号，但简单单阈值/二特征规则高度依赖 dataset/context，不能跨 profile / result-set 稳定外推；即使只做 leave-one-instance，二特征规则也仍然很弱。

这进一步排除“加一个简单 selector 就能上线”的解释。

### 7. 稍强的简单模型仍不能形成 production selector

为了确认失败不是因为单阈值 / 二特征太弱，本轮又做了 calibration-only 模型审计：

```text
BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_candidate_selector_model_audit_zh.md
```

使用同一批 `848` 个 20 strict candidate rows，只用 addition-before 特征，评估：

- `nearest_centroid`
- `linear_mean_diff`
- `shallow_tree_depth3`

leave-one-dataset 中表现最好的简单模型是 `linear_mean_diff`：

```text
accuracy = 0.5778301886792453
precision = 0.6633165829145728
recall = 0.7160940325497287
tp/fp/tn/fn = 396 / 201 / 94 / 157
```

leave-one-instance 中 `linear_mean_diff` recall 较高，但 false positives 仍多：

```text
accuracy = 0.6898584905660378
precision = 0.7230769230769231
recall = 0.8499095840867993
tp/fp/tn/fn = 470 / 180 / 115 / 83
```

按一个保守 production selector 起点：

```text
precision >= 0.75
recall >= 0.5
```

没有任何简单模型在 leave-one-dataset 和 leave-one-instance 下同时通过。

这说明当前不是“换个简单模型就好”，而是仍缺少更强、更稳定的 trajectory selector。

## 已证伪或不足的解释

### 解释 A：Pulse 不够强

不足。

Pulse 能安全生成 true-RC negative columns，也能加列。问题是这些列没有稳定减少 tail。Phase 7O / 8Q / 11D 已经证明“能加列”不等于“能优化”。

### 解释 B：profile-DP cap 太小

不足。

cap 太低确实可能让候选层不可观测，但提高 cap / selected counts 只会产生更多候选，不保证 returned cut 选对。Phase 11B 没有给出 stable improvement。

### 解释 C：returned count 太小

不足。

Apollo20 dp1000 单点显示 return8 能改善；但 Phase 10H / cross-log 显示 return8 / return12 也能恶化。returned count 是扰动器，不是 selector。

### 解释 D：best RC / rough RC 排序错

不足。

候选对照已经证明更负 RC 可以 worsened，较弱 RC 可以 improved。但反过来选择较弱也不是普适规则。

### 解释 E：active support / duplicate pool pressure

不足。

之前 active pool / pool pressure 诊断没有显示高 active duplicate ratio 或大量 tiny fractional 支持这个主线。早期 inactive columns 后续可能进入 active basis，但是否有益仍依赖 batch context。

### 解释 F：需要打开 certificate gate

错误方向。

当前 no-negative proof route 没有形成稳定 certified path，Pulse incomplete / duplicate-only / empty-harvest 不能更新 official lower bound。打开 certificate gate 会破坏 exactness 边界。

## 为什么 5/10 和 20 同时很难

### 5/10 的问题

5/10 规模本来 tail 很短，RMP / pricing / final judge 的绝对时间小。任何真实 worker、audit、probe、extra pricing pass 都有固定开销。

当前拆分后的证据更明确：

```text
task5_nontriggered_official_changed = 0
task10_nontriggered_official_changed = 0
task10_triggered_worsened = 133
task10_triggered_official_changed = 61
```

当前多轮 5/10 no-regression 主要靠：

- 默认关闭；
- 20-only profile；
- hard-tail gate；
- min-task gate；
- 不让 worker 在小快实例上触发。

这说明 5/10 不是被 Pulse “优化好了”，而是必须避免引入额外工作。尤其是 10-task，触发路径已经出现 official result 变化；任何 production 方向如果不能做到接近零开销触发，就会回退。

### 20 的问题

20-task hard tail 中，列空间和 RMP trajectory 的非线性更强：

- negative candidates 很多；
- returned cut 会截断候选；
- 不同 returned batch 会改变后续 dual / active basis / pricing residual tail；
- 有些 batch 让 incumbent 改善，有些 batch 带来更差轨迹；
- 现有前置特征还不能稳定区分。

所以 20 不是“多算一点就好”，而是“必须选对 batch”。没有 selector 时，更多搜索和更多返回只是随机扰动。

## 当前可信根因

当前最可信、且由多轮只读证据支持的根因是：

> BPC_future 当前的 20-task hard-tail 性能瓶颈，是 returned JourneyColumn batch 的 candidate/signature/timing composition 与 RMP active-basis trajectory 之间存在强非线性耦合；profile-DP / ordinary pricing 能产生负列，但 returned cut 的 ordering / materialization / truncation 会决定哪些具体 signature 进入 pool。现有规则不能在 addition 前稳定预测这个 batch 是否会改善后续 RMP/dual/pricing trajectory；并且现有 run-level improved/worsened 观测标签不是 batch-level 因果标签，同 exact context / returned batch descriptor 下仍会冲突。5/10 由于固定开销敏感，任何未证明高 ROI 的真实 worker/probe/search 都必须被 gate 掉，因此不能用同一个粗暴策略同时满足 5/10 no-regression 和 20 大幅加速。

## 当前还没有完成的事

目标仍未完成。原因是还没有证明一个优化方向能同时满足：

1. exactness 不变；
2. 5/10 不退化；
3. selected 20-task hard set 稳定大幅加速；
4. 不依赖后验信号；
5. 不只是单实例 / 单 repeat / 单 profile 的偶然改善。

已经有根因层级证据，但还没有 production selector。

## 需求-证据-缺口矩阵

| 用户要求 | 当前证据 | 状态 |
|---|---|---|
| 查清为什么 5/10 不能不退化 | small-scale audit 中真实触发 worker/audit/probe 的小规模 rows `220/220` wall-time 变差，未触发 rows official result 全部不变；当前全 results scan 中 task10 triggered `worsened=133` 且 `official_changed=61` | 已有强证据：小规模根因是固定开销，必须 early no-op；10-task 还需要 production-safe gate |
| 查清为什么 20 不稳定优化 | returned-boundary、candidate contrast、cross-log selector、candidate+batch leave-one-dataset 都显示“有负列但选不稳 batch” | 已有强证据：20 根因是 returned-batch trajectory selector 缺失 |
| 不局限 Pulse | 证据覆盖 Pulse worker、profile-DP cap、return8/12、rough RC/rank、active relation、RMP movement、small-scale overhead | 已覆盖多组件，不是 Pulse 单点 |
| 不能猜测 | 所有结论来自已有 summary/jsonl 抽取、cross-log validation、leave-one-dataset、focused tests | 当前结论有证据支撑 |
| 找到可优化方向才算完成 | 目前没有任何 selector 在跨 dataset 下稳定正向，同时保护 5/10 | 未完成 |
| 保证 exactness | certificate / duplicate-only / incomplete 边界已守住；但 production selector 尚未出现 | exactness 机制安全，但优化方向未完成 |
| 5/10 不退化且 20 大幅加速 | 现有候选方向没有同时满足；小规模真实触发会退化，20 简单 selector 不泛化 | 未完成，不能宣称成功 |

## 证据源索引

| 核心断言 | 主要证据文件 | 可复查数据/命令 |
|---|---|---|
| 5/10 真实触发会退化 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_small_scale_overhead_guard_audit_zh.md` | 查看该报告中的 21 个 small / guard result-set 汇总；关键数字为 triggered small rows `220/220` wall-time 变差 |
| Pulse/worker 能安全加列但没有稳定 ROI | `BPC_future/logical_graph/run_reports/20260613_sharded_pulse_worker_negative_result_synthesis_zh.md`；`BPC_future/logical_graph/run_reports/20260613_sharded_pulse_phase11d_final_negative_result_pivot_zh.md` | `BPC_future/results/sharded_pulse_phase7o_hard_tail_worker_roi_ab_20260612/summary.csv`；`BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613/summary.csv` |
| Apollo20 存在 returned-boundary 截断，rank1-rank7 strong negatives 被 baseline 截掉 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_returned_boundary_calibration_zh.md` | `BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613/summary.csv`；重点看 rank0-rank7 rough RC 与 return8 primal 改善 |
| 更负 RC 不等于更有用，同一 RMP/dual context 下 returned candidate 导致分叉 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_candidate_level_contrast_zh.md` | 对照 `mt20_greedy_apollo_01` return8 r0/r2 的 cg3 context、best_rc、returned/materialized samples |
| active-relation / batch-coherence 有信号但跨日志不泛化 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_cross_log_selector_generalization_audit_zh.md` | 查看 7 个 result-set 的 leave-one-dataset 结果；final improved selector `tp=3, fn=95` |
| candidate + batch-context 简单规则仍不稳定 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_returned_batch_trajectory_dataset_zh.md` | `BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_returned_batch_trajectory_dataset.py --output-dir BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613` |
| 稍强的简单 selector models 仍不能上线 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_candidate_selector_model_audit_zh.md` | `BPC_future/results/root_cause_candidate_selector_models_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_candidate_selector_models.py --output-dir BPC_future/results/root_cause_candidate_selector_models_20260613` |
| exact replay selector gate 排除全样本 true-RC 阈值 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_replay_calibrated_selector_candidate_zh.md` | 280 rows 中推荐规则 `true_reduced_cost <= -12.430587` 的 full-sample precision 为 `0.89`、recall 为 `0.8516746411483254`，但仍有 `22` 个 false positives 和 `31` 个 false negatives，不能作为 production selector |
| rule-family / context anatomy 排除简单 addition-before selector | `BPC_future/logical_graph/run_reports/20260614_bpc_future_root_cause_selector_rule_family_search_zh.md`；`BPC_future/logical_graph/run_reports/20260614_bpc_future_root_cause_selector_context_feature_anatomy_zh.md` | `rule_family_material_all_fold_passing_rule_count = 0`，20-only 也为 `0`；同一 instance / dataset 内分别有 `2` 组 low/high positive context，说明必须解释 RMP/context trajectory |
| exact replay pair selector gate 排除简单二特征组合 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_pair_selector_gate_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_pair_selector_gate_20260613/summary.json`；全样本 pair precision/recall 为 `0.951/0.531`，但 context recall 为 `0.272`，instance/dataset precision 低于 `0.75` |
| exact replay model selector gate 排除当前简单多特征模型 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_model_selector_gate_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_model_selector_gate_20260613/summary.json`；context/instance 有 passing models，但 dataset passing models 为空，all-holdout passing models 为空 |
| selector 失败来自标签集中和跨上下文方向翻转 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_selector_failure_anatomy_zh.md` | `BPC_future/results/root_cause_selector_failure_anatomy_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_selector_failure_anatomy.py --output-dir BPC_future/results/root_cause_selector_failure_anatomy_20260613` |
| 后验 trajectory 可分，但 addition-before 预测不足 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_hindsight_oracle_gap_zh.md` | `BPC_future/results/root_cause_hindsight_oracle_gap_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_hindsight_oracle_gap.py --output-dir BPC_future/results/root_cause_hindsight_oracle_gap_20260613` |
| candidate labels 是 batch/run 级展开，不是单列因果标签 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_candidate_label_granularity_zh.md` | `BPC_future/results/root_cause_candidate_label_granularity_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_candidate_label_granularity.py --output-dir BPC_future/results/root_cause_candidate_label_granularity_20260613` |
| 回到 batch 粒度后 addition-before selector 仍然不稳 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_batch_level_selector_audit_v2_zh.md` | `BPC_future/results/root_cause_batch_level_selector_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_batch_level_selector.py --output-dir BPC_future/results/root_cause_batch_level_selector_20260613` |
| 信号按时间层级看，pre/immediate 都不够，hindsight trajectory 才更强 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_trajectory_signal_ladder_zh.md` | `BPC_future/results/root_cause_trajectory_signal_ladder_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_trajectory_signal_ladder.py --output-dir BPC_future/results/root_cause_trajectory_signal_ladder_20260613` |
| 简单 trigger/no-op gate 在 aggregate 上好看，跨数据集/实例不稳 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_batch_gate_stability_zh.md` | `BPC_future/results/root_cause_batch_gate_stability_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_batch_gate_stability.py --output-dir BPC_future/results/root_cause_batch_gate_stability_20260613` |
| aggregate gate 失效来自上下文基准率和方向混杂 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_context_stratification_zh.md` | `BPC_future/results/root_cause_context_stratification_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_context_stratification.py --output-dir BPC_future/results/root_cause_context_stratification_20260613` |
| 仅用 context identity 有信号但不够上线 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_context_only_baseline_zh.md` | `BPC_future/results/root_cause_context_only_baseline_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_context_only_baseline.py --output-dir BPC_future/results/root_cause_context_only_baseline_20260613` |
| matched context 内样本稀疏且方向仍不稳 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_matched_context_audit_zh.md` | `BPC_future/results/root_cause_matched_context_audit_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_matched_context_audit.py --output-dir BPC_future/results/root_cause_matched_context_audit_20260613` |
| matched context 成对排序仍无 production 特征 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_matched_context_pairwise_contrast_zh.md` | `BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_matched_context_pairwise_contrast.py --output-dir BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613` |
| 同 exact context / returned batch 仍有标签冲突 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_exact_context_label_conflicts_zh.md` | `BPC_future/results/root_cause_exact_context_label_conflicts_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_exact_context_label_conflicts.py --output-dir BPC_future/results/root_cause_exact_context_label_conflicts_20260613` |
| 现有日志只有少量 replay 候选，不能直接训练 production selector | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_coverage_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_coverage_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/analyze_counterfactual_replay_coverage.py --output-dir BPC_future/results/root_cause_counterfactual_replay_coverage_20260613` |
| controlled replay 首批候选已收窄到 3 个 exact-context pairs | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_candidates_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json`；`BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/candidates.csv`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/select_counterfactual_replay_candidates.py --output-dir BPC_future/results/root_cause_counterfactual_replay_candidates_20260613 --top-n 3` |
| 首批 replay 候选仍不是 exact replay payload | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_readiness_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_readiness_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_counterfactual_replay_readiness.py --output-dir BPC_future/results/root_cause_counterfactual_replay_readiness_20260613` |
| replay 候选的已观测 entries 可局部物化，但完整 batch 快照仍缺失 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_materialization_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_materialization_20260613/summary.json`；复跑：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_counterfactual_replay_materialization.py --output-dir BPC_future/results/root_cause_counterfactual_replay_materialization_20260613` |
| 首个真实 20-task exact-context replay 证明局部 RMP impact 存在 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_real_capture_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2/summary.json`；关键数字：control `1061.554044`，full batch `924.43786`，delta `-137.116184` |
| replay impact dataset 将 high-impact 与 no-op 放进同一校准格式 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_impact_dataset_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo/summary.json`；`BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/summary.json` |
| exact-context capture 扩展显示 current probe 触发不稳定 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_capture_expansion_attempt_zh.md` | `BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613/audit/summary.json`；`BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613/audit/summary.json`；两者 `has_capture_events=false` |
| replay payload 质量边界 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_payload_quality_audit_zh.md` | Apollo all-logs manifest 现在把缺少 `vehicle_count` 的 `capture_t10` 标成 non-ready 并在 replay runner 跳过；impact analyzer 已要求 control solved 和 finite delta |
| 全局 capture 覆盖缺口 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_replay_global_capture_scan_zh.md` | 扫描 `8659` 个 JSONL 只发现 `4` 个 capture events，其中只有 `1` 个 ready 20-task context；现有 clean replay calibration 样本不足 |
| replay candidate 到 clean capture 的缺口 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_replay_candidate_to_capture_gap_zh.md` | 已有 `40` 个 observational replay candidates 和 `3` 个首批推荐候选，但全局只有 `1` 个 ready 20-task clean replay context；推荐候选仍需转成 no-certificate-effect exact-context capture |
| exact-context capture targets 已生成 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_capture_targets_zh.md` | 从首批推荐候选生成 `3` 个 diagnostic-only / no-certificate-effect capture targets，覆盖 `3` 个 exact contexts；它们是下一步抓 payload 的计划，不是 replay-ready treatment |
| capture targets 在 pt0.3 复核后全部 exact covered | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_capture_target_coverage_zh.md`；`BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_target002_pt03_recovery_and_selector_shift_zh.md` | 最新复核为 `capture_event_count = 114`、`target_with_exact_capture_count = 3`、`uncovered_target_count = 0`；`capture_target_002` 的 pt0.3 exact replay 扩展了 calibration 数据，但不是 production selector 或 wall-time speedup 证明 |
| tranq20 target exact replay 证明第二个 20-task local impact 样本族 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_target_tranq20_replay_zh.md` | `BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/impact/summary.json`；`4` 个 ready cases，`26` 个 high-impact candidates，full batch `4/4` 改善，best delta `-70.009099` |
| target001/002 dp1000 replay 扩大 calibration，同时保留 selector 缺口 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_counterfactual_target_001_002_replay_zh.md`；`BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_target002_pt03_recovery_and_selector_shift_zh.md` | `target001/002` sweep 有 `66` 个 ready cases、`176` 个 candidates、`117` 个 high-impact candidates、`59` 个 no-op candidates，best delta `-267.639664`；target002 pt0.3 后 exact covered，并新增 `73` 个 impact candidate rows，但仍只说明 calibration 数据扩展，不说明 selector 已可上线 |
| 用户目标逐项审计 | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_requirement_audit_zh.md` | 将 5/10 no-regression、20 improvement、exactness、selector 缺口逐项映射到 evidence ledger；结论是根因解释有强证据但 production 优化方向未完成 |
| production 优化方向 readiness | `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_optimization_direction_readiness_audit_zh.md` | `optimization_direction_readiness` 显示 5/10 guard、20 negative columns、local RMP impact、multi-context clean replay calibration 为 true，但 stable selector 和 20 wall-time speedup evidence 仍为 false |
| 当前结论不是 Pulse 单点 | 本报告的“已证伪或不足的解释”与上述所有报告 | 证据覆盖 Pulse、profile-DP、return count、RC/rank、active relation、RMP movement 和 small-scale overhead |

这些证据源共同支持当前判断：根因解释已经有依据，但 production 优化方向还没有被证明。replay readiness / materialization 审计说明旧 observational candidates 不能直接当 exact treatment；随后新增的 `mt20_greedy_apollo_01` real capture/replay 证明，在完整 source log / signatures / arc option ids / start times / RMP pool / true dual / cut snapshot 被捕获后，确实可以发现有局部 RMP impact 的 returned batch。impact dataset 进一步把该 high-impact context 和 duplicate no-op context 统一成 candidate/treatment rows。新增 capture 扩展尝试则显示，同类 capture 触发并不稳定。全局 scan 与 candidate-to-capture gap 进一步说明：已有 `40` 个 replay target 候选，但 clean exact-context replay calibration 仍需要按 target 转成完整 treatment payload。本轮新增的 capture targets 把这一步落实为 `3` 个 exact-context 抓取目标；target002 pt0.3 复核后，coverage 已更新为 `capture_event_count = 114`、`target_with_exact_capture_count = 3`、`uncovered_target_count = 0`。`tranq20_01` target 的离线 replay 显示 `26` 个 high-impact candidates、full batch `4/4` 改善、best delta `-70.009099`；`target001/002` sweep 的离线 replay显示 `66` 个 ready cases、`117` 个 high-impact candidates、`59` 个 no-op candidates、best delta `-267.639664`；target002 pt0.3 又新增 `73` 个 impact candidate rows。这里把根因进一步收紧为：20 规模确实存在多个有局部 RMP impact 的 returned batches，但同一 replay universe 里 high-impact 和 no-op candidate 并存，仍缺少能在加入前、低开销、跨 context 泛化地区分 high-impact 与 no-op/replacement 的 selector。即使 target002 已 exact covered，5/10 no-regression 与 20 wall-time speedup 仍未同时证明，所以仍不能作为 production selector 或求解路径修改。

## Evidence Ledger 校验

为避免最终根因判断只停留在文字报告层，本轮新增只读 verifier：

```text
BPC_future/scripts/verify_root_cause_evidence.py
```

当前工作树复核：

```text
2026-06-13 当前复核已重新运行 evidence ledger verifier，结果 all_checks_pass=true。
新增 optimization_direction_readiness section，结论为 check_root_cause_known_but_optimization_direction_unproven=true，production_direction_proven=false。
新增 counterfactual_replay_global_capture_scan section，结论为 clean replay sample scarce：global ready 20 context count = 1。
新增 counterfactual_replay_candidate_to_capture_gap section，结论为推荐 replay targets 尚未转成足够 clean exact-context capture：recommended candidate count = 3，ready 20 context count = 1。
新增 counterfactual_capture_targets section，结论为 3 个 exact-context targets 已定义且全部要求 diagnostic-only / no-certificate-effect / complete payload，但当前仍不是 replay-ready case。
新增 counterfactual_capture_target_coverage section，早期复核为 `2/3` 个 targets exact covered；后续 target002 pt0.3 复核已经更新为 target_with_exact_capture_count = 3、uncovered_target_count = 0、capture_event_count = 114。
新增 counterfactual_target_tranq20_replay section，结论为 `capture_target_003 / tranq20_01` 的 nonempty exact capture 有明确 local RMP impact，但仍不是 full BPC speedup proof。
新增 counterfactual_target_001_002_replay section，结论为 target001/002 相关 capture 有明确 local RMP impact，同时存在 no-op candidates；target002 pt0.3 后已 exact covered，但这只扩展 calibration 数据，不是 production selector 证明。
同一轮复核还运行完整 BPCFutureTests：Ran 502 tests in 1.440s, OK (skipped=1)。
同时运行 py_compile 与 git diff --check，均通过。
```

复查命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/verify_root_cause_evidence.py \
--output-dir BPC_future/results/root_cause_evidence_ledger_20260613
```

输出：

```text
BPC_future/results/root_cause_evidence_ledger_20260613/summary.json
```

本轮校验结果：

```text
all_checks_pass = true
small_scale_overhead:
  triggered_rows = 220
  triggered_worse_count = 220
  triggered_better_count = 0
  nontriggered_rows = 325
  nontriggered_official_changed = 0
current_small_summary_scan:
  rows = 1187
  summary_dirs = 63
  triggered_rows = 341
  triggered_worsened = 310
  triggered_improved = 0
  task10_triggered_worsened = 133
  task10_triggered_official_changed = 61
  triggered_official_changed = 61
  nontriggered_rows = 830
  nontriggered_worsened = 0
  nontriggered_official_changed = 0
phase7o_worker_roi:
  rows = 24
  all_time_limit = true
  all_incomplete_limit = true
  worker_events = 14
  legacy_final_judge_calls = 48
  completion_bound_retry_count = 0
phase8q_worker_add_columns:
  rows = 35
  all_time_limit = true
  pulse_worker_returned_journeys = 10
  pulse_worker_added_journeys = 10
  pulse_worker_added_new_task_set_count = 8
  pulse_worker_added_support_changing_count = 2
candidate_batch_selector:
  candidate_rows = 2096
  twenty_strict_candidate_rows = 848
  single_threshold tp/fn = 3 / 550
  two_feature tp/fp = 427 / 154
  two_feature_other_dataset_tp = 0
  leave_one_instance_single tp/fn = 56 / 497
  leave_one_instance_two_feature tp/fp/fn = 213 / 149 / 340
candidate_selector_models:
  leave_one_dataset linear_mean_diff precision/recall = 0.6633165829145728 / 0.7160940325497287
  leave_one_dataset linear_mean_diff tp/fp = 396 / 201
  leave_one_instance linear_mean_diff precision/recall = 0.7230769230769231 / 0.8499095840867993
  leave_one_instance linear_mean_diff tp/fp = 470 / 180
  strict_selector_gate passing_models = []
selector_failure_anatomy:
  rows = 848
  top_positive_dataset = sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613
  top_positive_dataset positive_share = 0.8698010849909584
  robust_single_feature_candidates = []
  mixed_dataset_direction_feature_count = 10
  mixed_instance_direction_feature_count = 10
hindsight_oracle_gap:
  top_hindsight_feature = incumbent_within2
  top_hindsight_auc = 0.7848223863671192
  top_addition_before_feature = batch_pair_overlap
  top_addition_before_auc = 0.6995310632298403
  leave_one_dataset hindsight precision/recall = 0.7880658436213992 / 0.6925858951175407
  leave_one_dataset addition-before precision/recall = 0.676056338028169 / 0.7811934900542495
  leave_one_instance hindsight recall = 0.7160940325497287
  leave_one_instance addition-before recall = 0.38698010849909587
candidate_label_granularity:
  stage_rows = 288
  candidate_rows = 848
  batch_label_counts improved/worsened = 136 / 152
  candidate_label_counts improved/worsened = 553 / 295
  positive_rate_shift_candidate_minus_batch = 0.1799004192872118
  improved_vs_worsened_avg_candidate_expansion_ratio = 2.0951146560319045
  label_mixed_candidate_batches = 0
batch_level_selector:
  rows = 288
  top_pre_batch_feature = returned_union_size
  top_pre_batch_auc = 0.6897977941176471
  leave_one_dataset pre_batch precision/recall = 0.4392156862745098 / 0.8235294117647058
  leave_one_dataset pre_batch fp = 143
  leave_one_instance pre_batch precision/recall = 0.46619217081850534 / 0.9632352941176471
  leave_one_instance pre_batch fp = 150
  leave_one_dataset hindsight precision/recall = 0.6821705426356589 / 0.6470588235294118
trajectory_signal_ladder:
  pre_batch top_feature = returned_union_size
  pre_batch leave_one_dataset precision = 0.4392156862745098
  immediate_addition top_feature = addition_new_count
  immediate_addition leave_one_dataset precision = 0.4855769230769231
  next_rmp_movement top_feature = next_rmp_objective_delta
  next_rmp_movement leave_one_dataset precision = 0.4794007490636704
  hindsight_trajectory top_feature = incumbent_within2
  hindsight_trajectory leave_one_dataset precision = 0.6821705426356589
batch_gate_stability:
  positive trigger aggregate rule = returned_union_size >= 11.0
  positive trigger aggregate precision/recall = 0.8695652173913043 / 0.14705882352941177
  positive trigger leave_one_dataset tp/fp = 0 / 3
  positive trigger leave_one_instance precision/recall = 0.2 / 0.022058823529411766
  negative no-op aggregate rule = returned_union_size <= 2.0
  negative no-op aggregate precision/recall = 0.8125 / 0.17105263157894737
  negative no-op leave_one_dataset precision/recall = 0.41025641025641024 / 0.10526315789473684
  negative no-op leave_one_instance recall = 0.03289473684210526
context_stratification:
  dataset improved-rate range = 0.7272727272727273
  instance improved-rate range = 0.32667047401484867
  profile improved-rate range = 0.8372093023255814
  returned_union_size direction mixed by dataset = true
  returned_union_size direction mixed by instance = true
  returned_union_size direction mixed by profile = true
context_only_baseline:
  holdout dataset best precision/recall = 0.5679012345679012 / 0.3382352941176471
  holdout instance best precision/recall = 0.635593220338983 / 0.5514705882352942
  holdout profile best precision/recall = 0.6796116504854369 / 0.5147058823529411
  all best context-only precision < 0.75
matched_context_audit:
  strict keys = instance + profile
  strict mixed_group_count = 8
  strict mixed_rows = 94
  strict mixed_row_share = 0.3263888888888889
  strict top_direction_counts positive/negative/flat = 3 / 4 / 1
  strict top_feature_counts = best_rc:4, returned_avg_start_time:1, returned_low_risk_arc_frac:1, returned_pair_jaccard:1, returned_union_size:1
matched_context_pairwise:
  strict keys = instance + profile
  mixed_group_count = 8
  mixed_rows = 94
  pair_count = 244
  passing_strict_pairwise_gate = []
  top_feature = returned_union_size
  top_feature best_orientation_auc = 0.5450819672131147
  top_feature non_tie_share = 0.13114754098360656
  top_feature group_consistency = 0.5
exact_context_label_conflicts:
  exact_context keys = instance + cg_iter + pricing_kind + active_hash_before + rmp_objective_before
  exact_context conflict_group_count = 12
  exact_context conflict_rows = 120
  exact_context conflict_row_share = 0.4166666666666667
  full_feature keys include best_rc + returned_task_sets + returned_sequences + returned_arc_families
  full_feature conflict_group_count = 14
  full_feature conflict_rows = 65
  full_feature conflict_row_share = 0.22569444444444445
  largest full_feature conflict labels improved/worsened = 4 / 11
counterfactual_replay_coverage:
  mixed_context_count = 12
  mixed_context_rows = 120
  descriptor totals pure_improved/pure_worsened/mixed = 12 / 21 / 14
  pure_descriptor_pair_count = 40
  replay_candidate_context_count = 6
  mixed_descriptor_context_count = 10
  interpretation = replay candidates exist, but observational replay remains candidate-only
counterfactual_replay_candidates:
  candidate_count = 40
  low_context_noise_candidate_count = 3
  mixed_descriptor_context_candidate_count = 37
  recommended_candidate_ids = replay_candidate_001, replay_candidate_003, replay_candidate_004
  recommended scope = 2 low-context-noise candidates + 1 mixed-context stress candidate
counterfactual_replay_candidate_to_capture_gap:
  recommended_candidate_count = 3
  global_ready_20_context_count = 1
  recommended_candidate_minus_ready_20_context_count = 2
  interpretation = replay targets exist, but they have not yet been converted into enough clean exact-context capture samples
counterfactual_capture_targets:
  target_count = 3
  exact_context_count = 3
  candidate_ids = replay_candidate_001, replay_candidate_003, replay_candidate_004
  interpretation = concrete no-certificate-effect capture targets exist, but they are not replay-ready treatments
counterfactual_capture_target_coverage:
  target_count = 3
  capture_event_count = 114
  target_with_near_match_count = 3
  target_with_exact_capture_count = 3
  uncovered_target_count = 0
  interpretation = target002 pt0.3 recovered exact coverage; all planned targets now have exact capture, but this remains calibration data rather than production speedup proof
counterfactual_target_tranq20_replay:
  manifest_ready_case_count = 4
  impact_high_impact_candidate_count = 26
  impact_best_objective_delta = -70.009099
  interpretation = tranq20 target replay has local RMP impact, but is not a production speedup proof
counterfactual_target_001_002_replay:
  manifest_ready_case_count = 66
  impact_high_impact_candidate_count = 117
  impact_noop_candidate_count = 59
  impact_best_objective_delta = -267.639664
  interpretation = target001/002 sweep expands local RMP impact calibration; target002 is now exact-covered after pt0.3, but no-op candidates persist
counterfactual_replay_readiness:
  recommended_candidate_count = 3
  descriptor_count = 6
  ready_candidate_count = 0
  descriptors_with_truncated_sampling = 1
  descriptors_with_candidate_row_start_times = 6
  descriptors_with_ambiguous_candidate_row_start_times = 0
  interpretation = selected replay contexts are useful, but current descriptors are not exact replay payloads
counterfactual_replay_materialization:
  recommended_candidate_count = 3
  descriptor_count = 6
  entry_count = 27
  materialized_entry_count = 27
  observed_descriptors_materialized = 6
  complete_descriptors_materialized = 5
  interpretation = observed descriptor entries can materialize as TimedTrips, but exact replay still needs full JourneyColumn/RMP/dual/cut snapshots
counterfactual_replay_capture_skeleton:
  config = journey_counterfactual_replay_capture_enabled
  default = disabled
  event = journey_counterfactual_replay_capture
  side_effect = diagnostic_only, replay_no_certificate_effect, official_bound_effect=false
  captures = full returned JourneyColumn batch when max_journeys=0, per-trip arc_option_ids/start/end/cost/occupancy, true RC, context hashes, active task sets, pool signature snapshot, true dual vector, cut payloads
  validation = 3 focused tests + driver smoke + capture audit + py_compile
  smoke_log = BPC_future/results/root_cause_counterfactual_replay_capture_smoke_20260613/logs/very_small_driver_capture.jsonl
  smoke_audit_summary = BPC_future/results/root_cause_counterfactual_replay_capture_smoke_20260613/audit/summary.json
  smoke_replay_manifest_summary = BPC_future/results/root_cause_counterfactual_replay_capture_smoke_20260613/replay_manifest/summary.json
  smoke_event_count = 1
  smoke_complete_event_count = 1
  smoke_returned_journey_count = 1
  smoke_captured_journey_count = 1
  smoke_pool_journey_payload_count = 4
  smoke_ready_replay_case_count = 1
  smoke_treatment_count = 3
  smoke_candidate_class = duplicate_signature / weak_replacement_or_duplicate
  smoke_all_checks_pass = true
  interpretation = capture plus manifest makes future controlled replay inputs concrete, but the smoke case is not itself an optimization direction or ROI proof
counterfactual_replay_feasible_smoke:
  capture_log = BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/logs/very_small_duplicate_noop_capture.jsonl
  replay_manifest = BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_manifest/replay_cases.json
  replay_result = BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_result/summary.json
  control_status = OPTIMAL
  control_objective = 232.270984
  returned_candidate_class = duplicate_signature / weak_replacement_or_duplicate
  changed_treatment_count = 0
  improving_treatment_count = 0
  best_objective_delta = 0.0
  interpretation = a true-RC negative duplicate can be a local RMP no-op; negative RC alone is not enough evidence for a useful 20-scale optimization direction
counterfactual_replay_real_capture_mt20_apollo:
  capture_log = BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/logs/mt20_greedy_apollo_01__strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority__capture_t10_v2.jsonl
  audit_summary = BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/audit_v2/summary.json
  replay_manifest = BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2/replay_cases.json
  replay_result = BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2/summary.json
  capture_event_count = 1
  returned_journey_count = 4
  pool_journey_payload_count = 164
  vehicle_count = 17
  candidate_class = 4 new task sets, 0 duplicate signatures, 0 active-support-changing at capture time
  control_status = OPTIMAL
  control_objective = 1061.554044
  full_returned_batch_objective = 924.43786
  full_returned_batch_delta = -137.116184
  best_single_delta = -137.116184
  best_single_candidate = task_set [4,5,8], sequence [8,5,4], true_rc -137.15071
  changed_treatment_count = 7
  improving_treatment_count = 7
  interpretation = exact-context replay now proves that at least one real 20-task captured returned batch has immediate local RMP impact; this is stronger than observational correlation, but still not a full BPC wall-time / optimality speedup proof
counterfactual_replay_impact_dataset:
  real_capture_mt20_apollo:
    candidate_row_count = 4
    high_impact_candidate_count = 4
    noop_candidate_count = 0
    full_batch_improved_count = 1
    best_objective_delta = -137.116184
  duplicate_noop_smoke:
    candidate_row_count = 1
    high_impact_candidate_count = 0
    noop_candidate_count = 1
    full_batch_improved_count = 0
    best_objective_delta = 0.0
  combined:
    dataset_count = 2
    candidate_row_count = 5
    candidate_impact_class_counts = improved:4, noop:1
    treatment_impact_class_counts = improved:7, noop:4
    best_objective_delta = -137.116184
  interpretation = exact-context replay impact rows now separate one high-impact 20-task captured context from one duplicate/no-op smoke in the same calibration format; sample size is still far too small for a production selector
counterfactual_replay_capture_expansion:
  mt20_greedy_tranq_01:
    status = TIME_LIMIT
    pricing_state = INCOMPLETE_LIMIT
    official_best_rc = 15.7995965
    worker_events = 0
    capture_event_count = 0
    profile_dp_tail_class = profile_dp_state_cap_tail
  tranq20_01:
    status = TIME_LIMIT
    pricing_state = INCOMPLETE_LIMIT
    official_best_rc = 26.8389145
    worker_events = 0
    capture_event_count = 0
    profile_dp_tail_class = profile_dp_state_cap_tail
  interpretation = same-profile 20-task capture expansion did not produce additional ready replay cases; the bottleneck is now stable no-certificate-effect returned-batch capture, not replay tooling
counterfactual_replay_gap_phase8q:
  source_logs = BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613/logs
  summary = BPC_future/results/root_cause_counterfactual_replay_gap_20260613/summary.json
  files_scanned = 35
  addition_event_count = 136
  replay_candidate_addition_count = 136
  replay_candidate_added_journey_total = 143
  replay_candidate_with_capture_count = 0
  missing_capture_replay_candidate_count = 136
  active_changed_task_set_total = 2
  new_task_set_total = 131
  replacement_task_set_total = 12
  interpretation = existing real worker/addition logs contain many candidate additions, but none has exact-context replay capture; they support the root-cause hypothesis but cannot by themselves prove a treatment-level optimization direction
```

这个 verifier 不运行 solver，只读取当前已有 reports / summary.csv / summary.json。它同时保留原 21 个 small/guard result-set 报告口径，并补充扫描当前 `BPC_future/results` 下所有带 `improvement_class` 的 5/10 summary rows。它验证的是“根因解释的证据是否仍可复查”，不是证明优化已经成功。

## 下一步的正确边界

下一步不应继续：

- 扩大 Pulse worker budget；
- 打开 worker default；
- 打开 official certificate gate；
- 简单提高 profile-DP cap / pricing time；
- 默认 return8 / return12；
- 只按 rough RC / rank / best RC 重排；
- 只按全样本 `true_reduced_cost` 阈值筛选；
- 只按简单二特征 AND/OR gate 筛选；
- 直接上线当前 nearest-centroid / shallow-tree 简单模型；
- 继续 target-specific 手工 priority。

下一步如果继续，应只做 calibration-only returned-batch selector modeling：

1. 继续扩展 per-candidate / per-batch dataset，而不是直接接 production path；
2. 只使用 addition 前可见字段：
   - task-set；
   - sequence；
   - signature / start-time / timing；
   - arc option family；
   - rough RC / true RC；
   - relation to current active top samples；
   - batch union / overlap / diversity；
   - new / replacement / support-changing class；
3. 标签使用后验 outcome / next-RMP objective delta / incumbent update，但这些标签不能在线使用；
4. 先解释 exact replay selector gate 中 true-RC / 二特征 pair / 简单模型在部分切分强、dataset holdout 失败的反例；
5. 再解释 Apollo20 `[4,14,18]` vs `[5,10,18]` 这类反例；
6. 再解释 Tranq return8 worsened / return12 improved 这类反例；
7. 只有当 selector 在 5/10 no-op gate 和 20 hard repeat 上都稳定，才允许做 opt-in A/B。

## 当前决策

当前不要宣称优化成功，也不要继续把 Sharded Pulse worker / proof route 作为主线扩大。

当前主线应转为：

> returned-column quality 与 RMP trajectory 的直接因果诊断，目标是找到 addition 前可见的 batch selector；在 selector 被证明前，所有求解路径修改都应保持 opt-in / diagnostic-only。
