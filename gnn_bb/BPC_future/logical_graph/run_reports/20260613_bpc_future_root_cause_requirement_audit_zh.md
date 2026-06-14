# BPC_future 根因目标逐项审计

日期：2026-06-13

最后复核：2026-06-14

## 目的

本报告只做目标逐项审计，不提出主线求解器修改。

用户目标要求不是“找到一个看起来合理的解释”，而是：

1. 查清为什么 5/10 规模不能不退化；
2. 查清为什么 20 规模不能稳定优化；
3. 不局限 Pulse，必须覆盖求解路径中的真实瓶颈；
4. 判断必须有证据，不能猜测；
5. 没有明确优化证据时，不能把某个方向算作根因闭环；
6. 只有在 exactness 不变、5/10 不退化、20 明显加速同时被证明后，才能说目标完成。

当前审计结论：

> 根因解释已经有强证据；生产优化方向尚未证明；目标仍未完成。

## 当前根因结论

当前最可信的根因是：

> 5/10 规模对固定开销极其敏感，任何真实 worker / probe / audit 一旦触发就容易回退；20-task hard tail 不是没有负列，而是 returned JourneyColumn batch 的 candidate/signature/timing composition 与后续 RMP active basis / dual / pricing trajectory 存在强上下文耦合。现有规则能产生 true-RC negative columns，也能在个别 exact-context replay 中显著改善局部 RMP objective，但还没有 addition-before、context-aware、可泛化、低开销的 returned-batch selector 能稳定选中高 impact batch，同时保护 5/10。

这不是 Pulse 单点结论。证据覆盖：

- Pulse hidden-negative worker；
- profile-DP cap / pricing time；
- returned count / return8 / return12；
- rough RC / rank / best RC；
- candidate-level / batch-level selector；
- active relation / RMP movement；
- exact-context counterfactual replay；
- small-scale overhead guard。

## 需求逐项状态

| 要求 | 当前证据 | 状态 |
|---|---|---|
| 查清 5-task 为什么不能不退化 | small-scale overhead 审计中，真实触发 worker/audit/probe 的小规模 rows `220/220` wall-time 变差，`triggered_better_count=0`；当前全 results scan 中 task5 nontriggered `official_changed=0`，task5 triggered `worsened=177` | 已有强证据：5-task 必须 no-op 或极严 gate |
| 查清 10-task 为什么不能不退化 | 当前全 results scan 中 task10 nontriggered `official_changed=0`，但 task10 triggered `worsened=133` 且 `official_changed=61`；Phase 7O / 后续 worker ROI 显示 worker 能安全加列但没有稳定减少 tail | 已有强证据：10-task 触发路径有 regression risk；还没有 production-safe 10-task gate |
| 查清 20-task 为什么不能稳定优化 | Phase 7O rows `24` 全部 `TIME_LIMIT / INCOMPLETE_LIMIT`，worker events `14` 但无稳定 ROI；Phase 8Q worker returned/added `10/10`，new task sets `8`，support-changing `2`，但仍 all `TIME_LIMIT` | 已有强证据：能加负列不等于能缩短 tail |
| 不局限 Pulse | verifier 同时检查 selector、profile-DP、returned boundary、counterfactual replay、small-scale overhead、RMP trajectory | 已覆盖多组件 |
| 判断不能猜测 | `verify_root_cause_evidence.py` 读取已有 summary/json/csv/report，当前 `all_checks_pass=true` | 当前根因判断可复查 |
| 尝试修改后才判断方向 | 已尝试 worker、audit、current probe、return count、profile-DP cap、selection mode、capture/replay；结果显示没有同时满足 5/10 no-regression 与 20 improvement 的方向 | 已有大量负证据；但优化方向未闭环 |
| exactness 不能牺牲 | 当前所有 Pulse / replay / capture 仍 diagnostic-only 或正常 add-column；incomplete/duplicate/no-column 不更新 official lower bound | exactness 边界目前守住 |
| 找到 20 有用列是否成立 | exact-context replay 中 `mt20_greedy_apollo_01` control objective `1061.554044`，full returned batch `924.43786`，delta `-137.116184` | 成立：有用 batch 真实存在 |
| true-RC negative 是否足以有用 | duplicate/no-op replay best objective delta `0.0`；说明 true-RC negative 也可能是局部 RMP no-op | 不足：必须看 batch impact |
| 是否已有 production selector | 推荐 selector `true_reduced_cost <= -12.430587` 在 280 条 exact replay rows 上仍有 `22` 个 false positives 和 `31` 个 false negatives；feature / model / rule-family 都没有 robust all-fold passing 证据 | 未完成 |
| 局部正信号是否能算完成 | worker 能加 20-task negative columns、exact replay 有 local RMP impact、也有 replay-calibrated selector candidate；但 `has_production_validated_selector=false` 且 `has_20_walltime_speedup_evidence=false` | 不能算完成，只能作为 calibration evidence |
| 5/10 no-op guard 是否等于生产 no-regression | task5/task10 nontriggered rows `official_changed=0`，但 task10 triggered rows `official_changed=61`，且还没有 full production-candidate BPC A/B | 不等于；当前只能说明要 no-op/gate，不能说明优化方案已通过 5/10 |
| 是否可以宣布目标完成 | 还没有证明 exactness + 5/10 no-regression + 20 大幅加速同时成立 | 不能完成 |

## 为什么“做了这么多还不行”

### 1. 小规模失败是固定开销问题

5/10 的 baseline tail 很短。worker/probe/audit 即使安全，只要真实触发，就会产生固定开销。

当前 evidence ledger 中：

```text
small_scale_overhead:
  triggered_rows = 220
  triggered_worse_count = 220
  triggered_better_count = 0
  nontriggered_rows = 325
  nontriggered_official_changed = 0
current_small_summary_scan:
  rows = 1187
  triggered_rows = 341
  nontriggered_rows = 846
  nontriggered_official_changed = 0
  task5_nontriggered_official_changed = 0
  task10_nontriggered_official_changed = 0
  task10_triggered_worsened = 133
  task10_triggered_official_changed = 61
```

含义：

- 小规模触发真实机制时，几乎只会增加时间；
- 未触发时 official result 不变；
- 10-task 尤其危险：triggered rows 中 `task10_triggered_official_changed = 61`；
- 所以 5/10 no-regression 目前只是 no-op gate 证据，不是 worker/probe 本身已经有生产收益；
- 小规模 no-regression 不能靠“让 Pulse 更聪明一点”自然获得，必须靠 no-op / scale gate / hard-tail gate。

### 2. 20 不是没有负列，而是负列价值不稳定

Phase 8Q 证明 worker 能返回并加入列：

```text
pulse_worker_returned_journeys = 10
pulse_worker_added_journeys = 10
pulse_worker_added_new_task_set_count = 8
pulse_worker_added_support_changing_count = 2
```

但同批 runs 仍然：

```text
all_time_limit = true
completion_bound_retry_count = 0
```

含义：

- add-column path 是安全的；
- 负列能进入 pool；
- 但这些列没有稳定转化成 tail 缩短或求解改善。

### 3. 单列 RC / rank / returned count 都不是稳定解释

已有 candidate / batch / selector audit 显示：

```text
candidate_batch_selector:
  twenty_strict_candidate_rows = 848
  single_threshold tp/fn = 3 / 550
  two_feature tp/fp = 427 / 154
  two_feature_other_dataset_tp = 0

candidate_selector_models:
  strict_selector_gate passing_models = []
```

含义：

- 简单阈值几乎找不到正例；
- 两特征规则表面 recall 高，但 false positive 多，并且跨 dataset 不泛化；
- 稍强的简单模型也没有达到保守 production selector 起点；
- 因此不能把 rough RC、rank、returned count、batch size、简单 diversity 当作主线优化。

当前 exact replay selector 证据进一步收紧了这个结论：

```text
exact_replay_selector_candidate_row_count = 280
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
recommended_selector_precision = 0.89
recommended_selector_recall = 0.8516746411483254
recommended_selector_false_positive_count = 22
recommended_selector_false_negative_count = 31

selector_micro_vs_fold_gate = current
robust_all_fold_passing_feature_count = 0
selector_model_micro_vs_fold_gate = current
robust_all_fold_passing_model_count = 0
selector_rule_family_search = current
rule_family_rule_count = 18887
rule_family_material_all_fold_passing_rule_count = 0
selector_rule_family_search_20only = current
rule_family_20only_rule_count = 18901
rule_family_20only_material_all_fold_passing_rule_count = 0
selector_rule_family_train_holdout = current
rule_family_train_context_material_passing_folds = 17/28
selector_rule_family_train_holdout_20only = current
rule_family_train_20only_context_material_passing_folds = 17/27
selector_context_feature_anatomy = current
context_feature_mixed_instance_group_count = 2
context_feature_mixed_dataset_group_count = 2
```

含义：

- 全样本看起来不错的 true-RC 阈值仍会漏掉 improved rows 并放入 no-op；
- 即使搜索 `18887` 个单条件/两条件 addition-before conjunction，也没有规则跨 context / instance / dataset 全部 fold 稳定通过；
- 只保留 20-task rows 后结论不变；
- 同一 instance / dataset 内也有 low-positive 与 high-positive context，说明必须解释当前 RMP/context trajectory，而不是只按实例或数据集粗分。

### 4. exact-context replay 证明“有用 batch 存在”，但也证明样本不足

真实 20-task exact-context replay：

```text
counterfactual_replay_real_capture:
  capture_event_count = 1
  captured_journey_count = 4
  best_objective_delta = -137.116184
```

impact dataset：

```text
combined:
  dataset_count = 2
  candidate_row_count = 5
  candidate_impact_class_counts = improved:4, noop:1
```

含义：

- “所有 worker negative 都没用”是错误解释；
- 至少一个真实 20-task returned batch 有明显局部 RMP impact；
- 但当前 high-impact 样本主要来自一个 Apollo20 exact context；
- 这不能推出 production selector，也不能证明 full BPC wall-time 加速。

### 5. capture 扩展失败说明 current probe 本身不稳定

同 profile 扩展到两个 20-task context：

```text
counterfactual_replay_capture_expansion:
  run_count = 2
  worker_event_count = 0
  capture_event_count = 0
  captured_journey_count = 0
  state_cap_tail_count = 2
```

含义：

- replay 工具链已经能验证 high-impact batch；
- 但稳定产生 no-certificate-effect returned-batch capture 仍是瓶颈；
- 继续简单扩大 worker/probe 预算没有证据基础。

## 已证伪或不足的解释

| 解释 | 为什么不足 |
|---|---|
| Pulse 实现不安全 | 目前 exactness guard / materialization / true-RC / no-certificate replay 都有测试和日志约束；问题不是安全接线 |
| 只要找到更多负列就能优化 | Phase 8Q 能加列但仍 TIME_LIMIT；duplicate/no-op replay delta 为 `0.0` |
| 只要扩大 worker budget | 小规模固定开销会回退；20 capture 扩展仍 worker events `0` |
| 只要提高 profile-DP cap | 旧 probe 显示 cap 提高会增加搜索/时间，不稳定减少 tail |
| 只要按更负 RC 排序 | candidate-level 对照已经证明更负 RC 可对应更差 trajectory |
| 只要 return 更多列 | return8/return12 有时改善、有时恶化；returned count 是扰动器，不是 selector |
| 只要用简单 ML selector | 当前 feature / model / rule-family 都没有通过 robust all-fold selector gate |

## 当前可行动但未证明的下一步

如果继续推进，应该做的是 calibration-only，不是主线大改：

1. 扩大 no-certificate-effect exact-context replay capture 样本；
2. 每个 capture 必须包含完整 returned batch、RMP pool、true dual、cut snapshot、context hash；
3. 用 replay impact dataset 累积 candidate / treatment rows；
4. 只使用 addition-before 可见特征训练或构造 selector；
5. 在 selector 通过跨 dataset / 跨 instance gate 前，不进入 production path；
6. 即使 selector 出现，也必须先跑 5/10 no-regression gate，再跑 selected 20 hard repeat A/B。

当前不应做：

- 不打开 Pulse worker default；
- 不打开 official certificate gate；
- 不继续堆 worker time limit；
- 不把 current probe 当 production worker；
- 不用后验 active/incumbent 字段做线上 selector；
- 不把单个 Apollo20 replay 当成 20-scale 优化证明。

## 审计结论

根因解释已经比“Pulse 不行”更具体：

> 小规模是固定开销敏感；20-task 是 returned-batch trajectory selector 缺失。负列存在，有用 batch 也存在，但当前系统不能在 addition 前稳定挑出高 impact batch。

但目标仍未完成：

> 还没有证明任何优化方向能在 exactness 不变、5/10 不退化的前提下，大幅加速 20-task 最优求解。
