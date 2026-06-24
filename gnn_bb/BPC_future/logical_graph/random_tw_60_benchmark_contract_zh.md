# BPC_future 主 benchmark 口径：分层 random-TW 60-instance

日期：2026-06-23

## 结论

后续实验、测试、加速效果、no-regression 结论和最终达标声明，都必须在分层 random-TW 60-instance 集合上给出证据。

旧 `moon_trek_60`、旧 `tranq10_01`、旧 `apollo20_physical_*` 等实例可以继续用于机制诊断、日志解剖和历史问题复现，但不能作为主效果结论。

20 规模的日常运行预算可以放宽到 600s，用来观察 proof tail、late negative、branch 行为和失败原因；但最终目标不变：canonical `tasks_020` 的 60 个实例都必须在 200s 内返回 `OPTIMAL`，600s 结果不能替代 200s 达标声明。

## Canonical 目录

主 benchmark logical graph 目录：

```text
BPC_future/logical_graph/tasks_005
BPC_future/logical_graph/tasks_010
BPC_future/logical_graph/tasks_020
BPC_future/logical_graph/tasks_030
BPC_future/logical_graph/tasks_050
BPC_future/logical_graph/tasks_100
```

每个规模 60 个实例。

## 分层结构

每个规模均为：

```text
2 个地形 × 3 个时间窗模式 × 10 个 seed = 60 个实例
```

地形：

```text
apollo15_20km
tranquillitatis_balmer_like_20km
```

时间窗模式：

```text
greedy-anchor
random-wave
sector-wave
```

这里的 random-TW 指“时间窗由带随机 seed / jitter / 可行密度筛选的生成器产生”，不是没有分类的无结构随机抽样。它是分层 benchmark：先按地形和时间窗模式分类，再在每类中保留 10 个 accepted seed。

## 效果声明规则

允许作为主效果证据：

- `BPC_future/logical_graph/tasks_005/...`
- `BPC_future/logical_graph/tasks_010/...`
- `BPC_future/logical_graph/tasks_020/...`
- `BPC_future/logical_graph/tasks_030/...`
- `BPC_future/logical_graph/tasks_050/...`
- `BPC_future/logical_graph/tasks_100/...`

不允许作为主效果证据，只能标注为诊断：

- `BPC_future/data/generated/moon_trek_60/...`
- `BPC_future/data/generated/moon_trek_balanced_60_20260609/...`
- `BPC_future/configs/apollo20_physical_*` 默认实例
- 单个旧 hard-case 的 historical probe

报告中如果使用非 canonical 实例，必须明确写：

```text
用途 = 诊断，不计入主 benchmark 效果结论
```

## 当前已验证结果

5/10 规模 600s no-regression 当前结果（V3 corrected-bound guarded fathom 合入后，默认配置）：

- 5 规模：60/60 OPTIMAL，当前 avg `0.338764s`，上一份 current avg `0.347385s`，旧基线 avg `0.321070s`。
- 10 规模：60/60 OPTIMAL，当前 avg `4.750018s`，上一份 current avg `5.479933s`，旧基线 avg `5.030619s`。

结果文件：

```text
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks5.csv
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks10.csv
```

20 规模当前阻塞代表：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
```

这是 canonical `tasks_020` 60-instance 集合内的实例，不是旧 hard-set。

20 规模 V3 诊断补充：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

在 V3 corrected-bound opt-in + 600s 下仍为 `EXTERNAL_TIME_LIMIT`，且没有 `journey_corrected_node_bound_fathom`。这不能作为 20 规模加速达标证据。

20 规模时间口径：

- 诊断/采样/尾部观察：允许 per-instance `600s`。
- 正式达标 gate：必须 per-instance `200s`，且 `60/60 OPTIMAL`。

## 2026-06-24 20规模当前水平

canonical `tasks_020` 60-instance 已按 600s 单实例预算、4 并行完成一次全量测试：

```text
csv = BPC_future/results/20260624_full600_randomtw60_tasks20_parallel4.csv
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_full600_randomtw60_tasks20_parallel4_zh.md
OPTIMAL = 26/60
OPTIMAL <= 200s = 20/60
OPTIMAL > 200s = 6/60
EXTERNAL_TIME_LIMIT = 30/60
TIME_LIMIT = 4/60
```

结论：当前版本没有达到 20 规模目标；即使把诊断预算放宽到 600s，也只有 26/60 证明最优。后续任何“20 规模已加速/已达标”声明都必须覆盖这 60 个 canonical 实例，并且最终以 200s gate 为准。

2026-06-24 补充：V141 曾尝试把 V131 的 no-column D 类 early branch 全局打开到 `tasks_020`，但前 4 个 `greedy-anchor/apollo15_20km` 都在 600s 外部超时后中断，不能作为 full600 改善证据。V142 随后给 no-column early branch 增加 context require gate，只保留已验证的 `tasks020_01_seed61001 / greedy-anchor / tranquillitatis_balmer_like_20km` 正例；该单实例从默认 full600 `327.745824s` 降到 `89.245413s`，但最多只把当前 `<=200s OPTIMAL` 从 `20/60` 推到 `21/60`，仍不是 20-scale 达标。

## 20规模诊断日志最低口径

下一轮 20 规模 600s 诊断/采样至少应保留以下只读诊断信号：

- `journey_tail_action_audit_enabled=true`：写出 `journey_corrected_node_bound_audit`，用于 Tail Action Controller A/B/C/D 分类、水位和 productivity 统计。
- `journey_branch_candidate_log_top_n=100`：写出 `journey_branch_candidates` top-N 特征，用于 branch-impact / child-proof-cost / coverage-gap replay 采样。
- late-negative audit 输入所需的 `journey_pricing`、`journey_column_addition`、weak filtered 字段必须保留，用于区分 active-support-changing、inactive-only 和 weak/profile filtered tail。

这些字段只用于诊断和训练数据构造，不能当 official bound、certificate 或剪枝依据。行为开关仍需单独 opt-in，例如 corrected-bound fathom、tail-action early branch、branch-score/horizon candidate priority。

V109/V110 新增的 `journey_tail_action_no_column_early_branch_before_final_probe_enabled` 和 `journey_tail_action_no_column_early_branch_allow_incomplete_limit_before_final_probe` 也是行为开关，不是诊断字段。canonical `moon_trek_20_smoke.yaml` 当前显式设为 `False`；只有 opt-in A/B 才能打开。打开后若 D 类 no-column 节点满足 guard，会在 completion-bound final probe 前 early branch，并继承已有节点下界；它不产生 official bound 或 certificate。`allow_incomplete_limit_before_final_probe` 只允许 final-probe 前 `INCOMPLETE_LIMIT` + no-column 的 weak/profile filtered tail 走 early branch，不能被解释成 incomplete pricing 可剪枝。

V110/V112 诊断结果：

```text
V110 random-wave/tranquillitatis seed61001 tail-action only:
120s = EXTERNAL_TIME_LIMIT, trigger=5
220s = EXTERNAL_TIME_LIMIT, trigger=7

V112 greedy-anchor/tranquillitatis seed61001 branch-score + V110:
csv = BPC_future/results/20260624_v112_branch_score_plus_tail_action_greedy_seed61001_140.csv
status = OPTIMAL
wall = 89.431052s
root selected pair = [2,6]
```

解释：Tail Action Controller 的行为入口已经能触发，但单独打开不能保证 20 规模加速；它需要和 branch pair / child ordering 一起使用。V112 是单实例 in-context 正例，不是 canonical `tasks_020` 60/60 的达标证据。

已用 canonical `tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/...seed61001` 做 140s 字段验证：

```text
results = BPC_future/results/20260624_diag_top100_tail_action_seed61001_140.csv
tail_action_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_controller_audit_diag_top100_seed61001_140_zh.md
late_negative_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_late_negative_tail_audit_diag_top100_seed61001_140_zh.md
branch_impact_report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_branch_impact_diag_top100_seed61001_140_zh.md
```

该验证确认 `journey_corrected_node_bound_audit`、late-negative 输入和 `journey_branch_candidates` top100 均会落日志；但 140s branch-impact 行全部右删失，不能作为稳定训练标签。后续 branch-impact / child-proof-cost 样本必须来自受控 replay、child probe 或完成/timeout-resolved 的 paired run。

2026-06-24 补充：V147 已把 `build_journey_branch_candidate_replay_runbook.py` 增加为双模式工具。默认 `full_replay` 仍生成完整 forced-pair replay 命令；显式 `--probe-mode child_probe` 时，命令会注入小 `max_nodes/journey_max_nodes`、可选 `max_cg_iterations/journey_max_cg_iterations`、corrected-bound/tail-action 诊断日志，并显式关闭 corrected-bound fathom 和 tail-action early branch 行为。V147 生成了 `BPC_future/results/journey_branch_candidate_child_probe_runbook_v147_v141_apollo_depth01_20260624`，`entry_count=16`、`time_limit=60`、`probe_max_cg_iterations=8`。该 runbook 只用于采 `child_probe_rows.jsonl` proof-cost 标签，不是 20-scale 性能结果。

2026-06-24 追加：V148 证明 `probe_max_cg_iterations=8` 太紧，16 条都停在 root CG，没有产生 branch/child 标签。V149 去掉 CG cap 后能产生 `branch_count=10`、`child_probe_row_count=20`，但全部 right-censored。V151 给 runbook 生成器增加 `--max-source-event-time`，排除预算内到不了源分支的晚事件；V152 在 seed61103/seed61000 的 6 条 root child-probe 上得到 `child_probe_row_count=28`、`forced_pair_matched_branch_count=6`、`max_child_corrected_bound_gain=3.321616`、`total_child_fathom_events=1`。V153 把这些行转成 diagnostic-only proxy score map，但默认 right-censored 惩罚下所有候选仍是负分，`[2,9]` 只是最高的负分。V155 进一步把同父节点 child-probe proxy 转成 started-child-only 相对排序：`proxy_branch_row_count=6`、`proxy_context_count=2`、`proxy_ranking_pair_count=6`，但 `right_censored_proxy_ranking_pair_count=6`、`ranking_training_ready=false`。这些是 branch pair / child ordering 的删失 proxy 标签，只能用于诊断、采样导航或后续训练特征，不能接 solver opt-in，也不能声明为 20-scale 加速效果。

2026-06-24 追加验证：V156 对 V155 的 top proxy pair 做了 600s full replay，`seed61000 [2,9]` 和 `seed61103 [10,18]` 均为 `EXTERNAL_TIME_LIMIT`。V157 审计确认 `forced_pair_matched_count=2`，但 `right_censored_branch_count=19`、`usable_branch_impact_training_count=0`。因此 V155 proxy top pair 不能升级为强正例或生产 score map；它只证明这些候选有局部 proof-cost 信号，不证明能解决 20-scale timeout。

2026-06-24 追加：V158 新增 `journey_child_priority_mode=child_score` 和 `BPC_future/scripts/build_journey_child_score_map.py`。它把 V152 的 started child-probe rows 转成 same/separate child-direction score map，并在 `journey_child_queued` 记录 `child_priority_score` / `child_priority_score_key`。该入口只改变同一 branch 下两个 child 的处理顺序，不改变 lower bound、剪枝、certificate 或 official bound；V158 输出仍是 diagnostic-only / production_ready=false，不是 canonical 20-scale 性能证据。

2026-06-24 追加：V159-V162 对 `child_score` 做了单实例 in-context opt-in 验证。V159 从 V114 positive-chain child-probe 行生成 `BPC_future/results/journey_child_score_map_v159_v114_positive_chain_20260624/journey_child_score_map.json`；V160 在 canonical `tasks_020/greedy-anchor/...seed61001` 上同时打开 V118 branch-score 和 V159 child-score，仍为 `OPTIMAL`，但相对 V131 baseline 没有减少节点数、pricing 次数或 exact-pricing 次数：二者均为 `node_count=5`、`pricing_calls=41`、`exact_pricing_calls=18`，`solving_time` 从 `86.296993s` 变为 `87.754026s`。V161/V162 审计确认 child-score 命中并改变了 depth1 `[8,12]` 的 same/separate child 顺序，但没有形成加速证据。因此 `child_score` 目前只能作为 shadow/标签入口，不能作为 random-TW 60-instance benchmark 的默认配置或通过阈值依据。

2026-06-24 追加：V163 在 `profile_exhausted_no_column` completion-bound final probe 前补齐 Tail Action Controller no-column gate 调用。该补丁仍是默认关闭行为，canonical benchmark 不打开 `journey_tail_action_no_column_early_branch_enabled` 或 `journey_tail_action_no_column_early_branch_before_final_probe_enabled`；因此它不是性能结果，也不是通过阈值依据。它的作用是让 opt-in A/B 中这条 final-probe 入口也能记录 gate audit 或 exact-safe early branch，避免 D 类节点绕过统一 controller。

2026-06-24 追加：V164 对 full600 20-scale 现有日志做只读统计，`journey_exact_pricing_completion_bound_retry` 的主触发是 `profile_exhausted_no_column=799`，远高于 `no_retry_budget=109`。因此 future canonical 20-scale 600s 诊断必须能在该主 funnel 上看到 Tail Action Controller 审计。V164 修改为：即使 before-final-probe 行为门关闭，只要 `journey_tail_action_audit_enabled=True`，也会记录 `journey_tail_action_no_column_early_branch_gate(gate_reason=before_final_probe_disabled)`。这仍不改变求解、不 early branch、不产生 bound/certificate；它只是保证默认 benchmark 的诊断日志能统计 A/B/C/D 分类和 D 类被行为门拦下的规模。

2026-06-24 追加：V165 在 canonical random-TW 20 中选 3 个高 retry 拖尾实例做 220s 并行 audit-only 探针，输出为 `BPC_future/results/20260624_v165_tail_action_gate_audit_probe3_220.csv` 和 `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624`。三例均为 `EXTERNAL_TIME_LIMIT`，不是性能改善证据。审计中 `tail_action` 总行数 `148`，其中 D 类 `EARLY_BRANCH=99`；final-probe 前 no-column gate row `56`，全部被 `before_final_probe_disabled` 挡住，其中 `49` 行是 D 类建议、`7` 行是 B 类 broad plateau。该结果只证明主 final-probe funnel 中 D 类机会密集；它不证明打开开关一定会加速，因为 disabled audit 不运行 depth、min_tasks、fractional branch、pool width 等行为 guard。后续 opt-in 必须继续限定在 canonical random-TW 20+ 规模，并保留 exact-safe inherited lower bound 和日志审计。

2026-06-24 追加：V166 在同一 3 个实例上打开 before-final-probe D 类 no-column early branch opt-in，并限定 `min_tasks=20`、`min_depth=1`、`max_depth=4`、`max_pool_child_width=180`、`max_pool_total_child_width=360`、`max_pool_balance_gap=180`。输出为 `BPC_future/results/20260624_v166_tail_action_before_final_probe_optin_probe3_220.csv` 和 `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624`。三例仍均为 `EXTERNAL_TIME_LIMIT`。审计显示该路径真实触发 `20` 次，全部在 `sector-wave seed61718`；该实例 completion-bound retry 从 V165 的 `22` 降到 `8`，但 exact pricing rows 从 `33` 增到 `46`，仍未求完。两个 random-wave 实例没有触发，主要被 pool child width cap 挡住。结论：该 opt-in 能减少局部 retry，但单独使用会把成本转移到 child subtree proof，不能扩大为 60-instance 默认，也不是 20-scale 200s 通过证据。

2026-06-24 追加：V167/V168 针对 V166 sector-wave node1 生成并运行两个 before-final-probe 替代 pair 反事实：`[1,10]` 和 `[4,11]`。runbook 为 `BPC_future/results/journey_branch_tail_positive_runbook_v167_v166_before_final_probe_alt_pairs_20260624`，审计为 `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624`。两条仍均为 `EXTERNAL_TIME_LIMIT`。`[1,10]` 能把源 node1 局部 child subtree 从 `pricing=59 / negative=31 / retry=14 / no_column_chain=9` 降到 `pricing=17 / negative=10 / retry=6 / no_column_chain=0`，但同一 run 后续 node2 变成 `pricing=92 / negative=37 / retry=56`。因此 V168 是“局部改善但全局 proof cost 仍失败”的 hard-negative，不是 branch-score 正例，也不是 20-scale 性能改善证据。

2026-06-24 追加：V169 用 `BPC_future/scripts/audit_journey_tail_action_counterfactual_delta.py` 对 V167/V168 做离线反事实 delta 审计，输出为 `BPC_future/results/journey_tail_action_counterfactual_delta_v169_v168_node1_alt_pairs_20260624` 和 `BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_counterfactual_delta_v169_node1_alt_pairs_zh.md`。结果为 `matched_counterfactual_count=2`、`local_tail_improved_count=2`、`whole_run_improved_count=0`、`local_improved_but_whole_run_not_count=2`、`right_censored_counterfactual_count=2`。因此 V169 只把 V168 固化成 local-only hard-negative 标签；它不运行 solver、不产生 official bound/certificate、不证明 20-scale 加速，也不能作为 whole-run branch-score 正例。

2026-06-24 追加：V170 把 V169 的 counterfactual delta 接入统一 tail-impact training rows v4，输出为 `BPC_future/results/journey_tail_impact_training_rows_v170_v166_plus_v169_counterfactual_20260624` 和 `BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v170_v166_plus_v169_counterfactual_zh.md`。该数据集 `training_row_count=22`，其中 `tail_action_proof_cost=20`、`tail_action_counterfactual_delta=2`，标签为 `y_local_tail_improved=2`、`y_whole_run_improved=0`、`y_local_improved_but_whole_run_not=2`。V170 只是训练数据契约修正：`y_useful_tail_reduction` 只跟 whole-run improvement 对齐，防止 local-only improvement 误进 GAT 正例；它不是 solver 性能结果，也不是 benchmark 通过证据。

2026-06-24 追加：V171/V172 补跑 V167 runbook 中已运行的 11 条 replay，综合报告为 `BPC_future/logical_graph/run_reports/20260624_bpc_future_v171_v172_v167_full_replay_negative_zh.md`。11 条全部 `EXTERNAL_TIME_LIMIT`；tail-action 审计有 `early_branch_triggers=28`、`no_column_gate_D_rows=220`，但 counterfactual delta 只有 `matched_counterfactual_count=5`、`whole_run_improved_count=0`、`local_improved_but_whole_run_not_count=5`。V172 统一训练行 `training_row_count=33`，其中 `tail_action_counterfactual_delta=5`，全部是 local-only hard-negative。该结果进一步说明 V167 sector-wave context 不能作为 branch-score/GAT useful-tail-reduction 正例，也不是 20-scale 加速证据。

2026-06-24 追加的 V106/V107 root coverage-gap replay 覆盖 canonical `tasks_020` 中两个新的 random-wave 实例：

```text
runbook = BPC_future/results/journey_branch_candidate_replay_runbook_v106_v105_coverage_gap_20260624
branch_impact = BPC_future/results/journey_branch_impact_audit_v106_root_gap4_20260624
delta = BPC_future/results/journey_branch_counterfactual_delta_v107_v106_root_gap4_20260624
ranking = BPC_future/results/journey_branch_counterfactual_ranking_v108_v107_root_gap4_20260624
forced_pairs = [2,10], [10,18], [5,7], [5,18]
status_pairs = EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT, 4/4
timeout_resolved_count = 0
ranking_pair_count = 0
```

该批次只证明这些 root coverage-gap 候选未解决 220s timeout，不能作为 branch-score 正向训练样本，也不能作为 20 规模加速证据。
