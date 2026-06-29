# V717-V720 RouteOpt/BKF 分阶段分支采样校准报告

日期：2026-06-28

## 背景

RouteOpt 对当前 BPC_future 的主要启发不是“直接换 solver”，而是把分支决策拆成可审计的分阶段测试：

1. 先用便宜特征快速筛选候选 Ryan-Foster pair。
2. 再对少量候选做 partial testing / child probe。
3. 根据双 child 的下界抬升、宽度风险、负列风险和证明成本动态决定是否值得进入更贵的 full replay。
4. 所有学习结果只影响排序和调度，不提供 official bound、certificate 或剪枝依据。

这正对应我们当前的问题：20 规模不是单纯“找不到负列”，而是 proof tail 中 branch pair、child order、completion-bound retry 和 exact pricing closure 的组合成本没有被学到。

参考来源：

- RouteOpt 2.0 README：强调 improved branching module、modular architecture、solver adapter 和可扩展模块。
- RouteOpt 1.0 README：明确包含 two-stage learning-to-branch，并提醒 pricing 极难实例需要按建议调整参数。
- Operations Research 2026 two-stage learning-to-branch 摘要：第二阶段用 partial testing 降低 heuristic testing 负担，并用动态公式调整进入第二阶段的候选数。
- RouteOpt modular solver 摘要：模块化 branching、cutting plane、variable reduction，以及 node restoration 支持并行 B&B。

## 已落地改动

### 1. V716 runbook 增加分阶段采样字段

文件：

- `BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py`
- `BPC_future/tests/test_journey_branch_candidate_replay_runbook.py`

主要变化：

- runbook 开始读取 node-level phased controller summary 和 candidate-level phase1/phase2 字段。
- RouteOpt/BKF staged score 同时考虑：
  - `phase1_min_child_lp_gain`
  - `phase1_child_lp_gain_product`
  - `phase1_child_width_balance`
  - `phase2_negative_child_count`
  - `phase2_negative_journey_count`
  - `phase2_worst_negative_severity`
  - child width / total width / balance gap
- 对 phased testing 出现 official-bound/certificate effect 的上下文 fail-closed，不把这种样本混入纯调度学习。

### 2. V717 用 V711/V712 phased snapshot 做 paired child-probe

输入上下文：

- 实例：`apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716`
- source selected baseline pair：`[15,19]`
- 采样出的 alternative pairs：`[10,19]`、`[15,17]`、`[4,6]`

runbook 摘要：

- `entry_count = 4`
- `paired_group_count = 1`
- `paired_baseline_entry_count = 1`
- `paired_alternative_entry_count = 3`
- `branch_impact_priority_context_count = 1`
- `phased_testing_exact_effect_skip_count = 0`

说明：这批 source log 主要有 candidate-level phase 字段，node-level phased summary 没有覆盖，所以 `phased_testing_priority_context_count = 0`。采样本身仍然用到了候选级 phase1/phase2 字段。

### 3. V718 审计 paired child-probe

审计摘要：

- `branch_count = 5`
- `forced_pair_branch_count = 4`
- `forced_pair_matched_branch_count = 4`
- `complete_label_branch_count = 4`
- `usable_branch_impact_training_count = 4`
- `run_status_counts = {"OPTIMAL": 5}`
- `tail_class_counts = {"completion_bound_tail": 4, "unprocessed_children": 1}`
- `total_child_completion_bound_retries = 29`
- `total_child_exact_pricing_events = 40`
- `total_child_negative_pricing_events = 42`
- `total_child_fathom_events = 9`
- `official_bound_effect = false`
- `certificate_effect = false`

这说明当前数据可以用于排序/调度学习和 proof-cost 诊断，但不能作为 official certificate 数据。

### 4. V719 paired summary 和 V720 delta rows 保留 BKF/phase 字段

文件：

- `BPC_future/scripts/summarize_journey_paired_probe_runbook.py`
- `BPC_future/scripts/build_journey_paired_probe_delta_rows.py`
- `BPC_future/tests/test_journey_paired_probe_summary.py`
- `BPC_future/tests/test_journey_paired_probe_delta_rows.py`

补齐字段：

- `source_alt_routeopt_bkf_score`
- `source_alt_routeopt_bkf_reason`
- `source_alt_routeopt_bkf_stage`
- `phase1_min_child_lp_gain`
- `phase1_child_lp_gain_product`
- `phase1_child_width_balance`
- `phase2_negative_child_count`
- `phase2_negative_journey_count`
- `phase2_worst_negative_severity`

V720 输出：

- `output_row_count = 3`
- `output_counterfactual_label_counts = {"paired_probe_neutral_proxy": 3}`
- `production_ready = false`

## V717 实测结果

| pair | role | status | wall_time | gain vs baseline | child_proof_cpu | CB retry | negative pricing events | BKF score | phase1 min gain | phase1 product | phase2 neg child |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `[15,19]` | selected baseline | OPTIMAL | 159.353445 | 0.000000 | 82.286951 | 6 | 12 | - | - | - | - |
| `[10,19]` | alternative | OPTIMAL | 161.920060 | -2.566615 | 176.099765 | 6 | 9 | 24.462299605 | 3.400417303 | 49.695215619 | 0 |
| `[15,17]` | alternative | OPTIMAL | 176.207406 | -16.853961 | 99.393235 | 11 | 11 | 24.128475909 | 3.530037902 | 43.356238509 | 0 |
| `[4,6]` | alternative | OPTIMAL | 149.480225 | +9.873220 | 61.262008 | 6 | 10 | 23.792996315 | 3.684208667 | 59.005534427 | 1 |

## 关键观察

### 观察 1：RouteOpt/BKF staged 思路是对的

这批数据证明，分支 pair 的差异会真实影响完整求解时间。即使同一个实例、同一个 forced root pair replay，`[4,6]` 相对 selected baseline `[15,19]` 快了约 `9.87s`，并且 child proof CPU 明显更低。

这说明我们不能只让 GAT 学“这个 pair 看起来 fractional 好不好”，而要让它学：

- 两个 child 是否都能抬高安全下界；
- child proof CPU 是否下降；
- CB retry 是否减少；
- 负列链是否会变短；
- child 是否更快拿到 certificate。

### 观察 2：当前 BKF 权重需要校准

当前 BKF 排序为：

1. `[10,19]`：score `24.462`
2. `[15,17]`：score `24.128`
3. `[4,6]`：score `23.793`

但实测最快的是 `[4,6]`。

原因很可能是当前分数对 `phase2_negative_child_count=1` 和 `phase2_worst_negative_severity=0.574961` 惩罚偏重，而对 `phase1_child_lp_gain_product=59.006`、`child_proof_cpu` 降低、generated/evaluated 规模下降的奖励不足。

这不是坏事，反而是我们想要的 calibration signal：RouteOpt 的 two-stage testing 本质上就是用便宜测试发现“原始打分公式哪里不准”，然后动态修正候选测试预算和排序。

### 观察 3：这批还不能当 strict positive

V719/V720 只有 `neutral_proxy`：

- 最大 wall-time gain 是 `[4,6]` 的 `+9.873s`。
- 小于当前 `>=30s` 弱正例阈值。
- 没有 TIME_LIMIT -> OPTIMAL。

因此它不能作为 production-ready 正例，只能作为校准样本和辅助标签。后续需要在更多 hard contexts 上重复这个流程，寻找大于 30s 或 100s 的 gain，以及 TIME_LIMIT -> OPTIMAL 的 full replay。

## 对我们后续优化的启发

### 1. 主线应从“模型直接决策”改成“模型提出候选 + 分阶段测试”

RouteOpt 的启发是：不要相信单个 GAT score 直接决定分支。正确流程应是：

```text
candidate pool
  -> cheap structural filters
  -> GAT / BKF score shortlist
  -> phase1 LP child gain probe
  -> phase2 short pricing/proof-risk probe
  -> paired child-probe / full replay
  -> score calibration / score-gated early branch
```

这比裸开 branch score 或 early branch 更稳，因为每一步都有 fail-closed 边界。

### 2. 分支标签要从单 child 或单指标改成双 child 平衡收益

当前 proof tail 的关键不是某个 child 好，而是两个 child 都不能太差。后续训练标签至少要包含：

- `min(child_lp_gain)`
- `child_lp_gain_product`
- `child_width_balance`
- `max(child_proof_cpu)`
- `sum(child_cb_retry)`
- `worst_child_negative_chain`

这和 RouteOpt 的 branch testing 思想一致：branching quality 不是单边收益，而是整棵子树闭环成本。

### 3. `phase2 negative` 不应被简单视为坏信号

本次 `[4,6]` 有一个 phase2 negative child，却最快。说明：

- 少量负列不一定代表坏；
- 关键是负列是否 active-support-changing，是否拖成长链，是否引起大量 CB retry；
- phase2 负列风险要和 child proof CPU、exact pricing 次数、generated/evaluated 规模一起解释。

### 4. 需要状态作用域，而不是全局 pair 好坏

同一个 pair 在不同 node/depth/branch-prefix 下意义不同。RouteOpt 的 staged testing 是围绕当前节点上下文做的，这和我们前面 state-key / context gate 的方向一致。

后续 score map 不应只按 `(instance, pair)` 粗粒度应用，而应至少包含：

- instance / family / scale
- node depth
- branch prefix hash
- candidate rank / fractionality
- child pool width/balance
- tail class
- retry taxonomy
- phased testing summary

### 5. cuts/formulation 仍是另一条线，不能被 branch learning 取代

RouteOpt 的模块化 solver 明确把 branching、cutting plane、variable reduction 分开。对我们也是一样：

- 当 `z_RMP < UB` 时，pricing proof 无法直接 fathom；
- branch learning 只能让子树更快闭环；
- 如果大量节点 LP bound 本身不够，需要 pricing-compatible cuts、更强 master/formulation 或更好的 incumbent。

所以 branch score 是 proof-tail 加速线，不是全局下界强化线。

## 下一步建议

1. 在 4-8 个 hard contexts 上继续跑 V716/V717 这种 paired phased probe，优先选择 completion-bound tail 和 retry 高的节点。
2. 调整 BKF 分数：降低单次 phase2 negative child 惩罚，提高 phase1 product、min child gain 和 proof CPU 改善权重。
3. 把 neutral calibration rows 加入辅助训练头，不作为 strict positive。
4. 对出现 `>30s gain` 或 TIME_LIMIT -> OPTIMAL 的样本再做 full replay，形成 production-ready branch wall-time 标签。
5. solver 内部继续保留 score-gated early branch，不裸开；无 score、低置信度、child width 超限、phase exact effect 不干净时全部回退。

## 验证

已运行：

```bash
python -m py_compile \
  BPC_future/scripts/build_journey_paired_probe_delta_rows.py \
  BPC_future/tests/test_journey_paired_probe_delta_rows.py \
  BPC_future/scripts/summarize_journey_paired_probe_runbook.py \
  BPC_future/tests/test_journey_paired_probe_summary.py \
  BPC_future/scripts/build_journey_branch_candidate_replay_runbook.py \
  BPC_future/tests/test_journey_branch_candidate_replay_runbook.py

python -m unittest \
  BPC_future.tests.test_journey_paired_probe_delta_rows \
  BPC_future.tests.test_journey_paired_probe_summary \
  BPC_future.tests.test_journey_branch_candidate_replay_runbook
```

结果：

```text
Ran 24 tests in 0.123s
OK
```

