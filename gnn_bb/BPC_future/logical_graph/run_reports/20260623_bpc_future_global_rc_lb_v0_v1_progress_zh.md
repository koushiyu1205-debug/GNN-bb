# BPC_future global remaining RC LB / corrected bound V0-V3 进展

日期：2026-06-23

## 背景

本轮对齐了：

- `BPC_future/logical_graph/计划.md`
- `BPC_future/logical_graph/bpc_future_expert_analysis.md`
- `BPC_future/logical_graph/bpc_future_global_rc_lb_and_branch_probe_design.md`
- 主报告 `20260623_bpc_future_stage4_gat_on_20scale_speed_status_zh.md`
- 当前 v154 / Stage 3 / Stage 4 / 5000 样本相关报告
- `gat_bpc_future_target_mode_optimization_plan_zh.md`

结论仍是：20 规模 proof tail 的核心阻塞不是 v154 分类精度，而是节点 bound 只能等 full pricing closure 后才成为官方 lower bound。GAT 继续保留为列发现、admission/order/mode hint，但不能提供证书或官方剪枝。

## 已完成改动

### 1. Pricing result proof schema

在 `JourneyPricingResult` 增加：

- `global_remaining_rc_lb`
- `global_remaining_rc_lb_valid`
- `global_remaining_rc_lb_coverage_complete`
- `frontier_region_count`
- `frontier_unsupported_region_count`
- `pending_complete_min_rc`
- `pricing_proof_kind`

新增 proof kind：

- `NONE`
- `EXHAUSTIVE_NO_NEGATIVE`
- `FRONTIER_BOUND_NO_NEGATIVE`
- `FRONTIER_BOUND_INCOMPLETE`

旧的 direct-label full no-negative certificate 现在会写出 `EXHAUSTIVE_NO_NEGATIVE` 和 `global_remaining_rc_lb=0.0`。

### 2. Frontier ledger / direct-label frontier coverage V1-V2

新增 `FrontierBoundLedger` / `FrontierBoundToken`，支持：

- active token 最小 lower bound
- parent -> children 原子替换
- pending complete candidate 最小 RC
- unsupported region fail-closed 计数

新增 `_direct_open_label_frontier_lower_bound()`，能从 direct-label active heap 扫描 OPEN labels，并用 completion-bound optimistic objective 给未扩展区域计算 reduced-cost lower bound。

当前 V1 的安全边界：

- full exhaustive no-negative 仍输出 `EXHAUSTIVE_NO_NEGATIVE`，可作为旧证书。
- incomplete/tail 状态只输出 `FRONTIER_BOUND_INCOMPLETE` 审计字段。
- 如果存在 lazy/profile/resume/cache/beam/restricted universe/dirty frontier/filtered weak 或 duplicate 影响覆盖，`global_remaining_rc_lb_valid=false`，fail-closed。
- V2 已接入 direct-label 主循环的 token 生命周期：root label 初始化 frontier token；完整展开一个 label 后用 child tokens 原子替换 parent；如果 time-limit 发生在 label expansion 中途，parent token 保持 active，因此不会再因为 popped-but-not-replaced 区域丢失而自动 fail-closed。
- V3 已新增默认关闭的 guarded fathom：`journey_corrected_node_bound_fathom_enabled=true` 时，只有 valid corrected LB 足以达到 incumbent，才允许用 corrected bound fathom 当前节点。

### 3. Corrected node bound 审计

新增 `_journey_pricing_corrected_node_bound()`：

```text
safe_rc_lb = global_remaining_rc_lb - rc_bound_safety_eps
delta = max(0, -safe_rc_lb)
R_N = min(rmp_fleet_limit_used, |T|)
corrected_node_lb = z_RMP - R_N * delta - node_bound_safety_eps
```

fail-closed 条件：

- pricing 不是 global-certificate capable
- 返回了 negative journey
- global RC LB invalid
- coverage incomplete
- unsupported region > 0
- `rmp_fleet_limit_used` 缺失或非法

新增默认关闭的日志：

```yaml
journey_corrected_node_bound_audit_enabled: true
```

打开后输出 `journey_corrected_node_bound_audit`，包含 RMP objective、R_N、global RC LB、dual repair delta、corrected node LB、proof kind、coverage 字段、dual/cut/branch hash。

本轮已把 audit 接到：

- root-only journey solve 主 exact / exact retry / completion-bound retry
- branch-price node 主 exact / exact retry / duplicate completion-bound retry / final completion-bound retry / escalation retry

默认配置下这些日志不改变求解行为，不提前剪枝。V3 opt-in 只在 corrected bound 已经足以剪枝时改变节点状态。

### 4. Corrected-bound guarded fathom V3

新增默认关闭配置：

```text
journey_corrected_node_bound_fathom_enabled
```

触发条件：

```text
corrected.valid = true
corrected_node_lb >= incumbent - integer_tol
```

触发后记录：

```text
journey_corrected_node_bound_fathom
bound_kind = PRICING_CORRECTED_DUAL_BOUND 或 FULL_LP_CERTIFICATE
exact_safe = true
```

边界：

- 不把 corrected bound 当成 full LP closure；
- corrected LB 不足以剪枝时仍走原 retry / certificate / incomplete 逻辑；
- GAT、weak-negative classifier、heuristic 仍不能作为 bound 或 certificate。

### 5. RMP fleet RHS 元数据

`JourneyRMPSolution` 现在携带 `active_fleet_limit`，作为产生当前 dual 的那次 RMP solve 实际 fleet RHS。后续 corrected bound 不再需要从 driver 状态事后猜测 R_N。

## 验证结果

Focused tests：

```text
Ran 6 tests in 0.041s
OK

Ran 3 tests in 0.042s
OK

V2:
Ran 6 tests in 0.019s
OK

V3 guarded fathom:
Ran 10 tests in 0.007s
OK
```

覆盖：

- frontier ledger 原子替换
- interrupted expansion 期间 parent frontier 保持 active，直到 replace
- frontier no-negative 非 exhausted certificate
- coverage incomplete fail-closed
- direct open-label frontier lower-bound 扫描
- restricted beam mode 下 frontier bound fail-closed
- corrected bound 公式和 `R_N=min(fleet_rhs, |T|)`
- unsupported frontier fail-closed
- corrected bound audit 日志
- corrected bound opt-in fathom 日志
- corrected bound fathom 默认关闭
- ledger config 映射
- direct-label old certificate proof kind
- NG certificate 旧路径不退化
- replacement repair no-column 仍不是 global certificate

编译：

```text
python -m compileall -q BPC_future/pricing/journey_pricing.py BPC_future/solver/journey_driver.py BPC_future/master/journey_rmp.py BPC_future/tests/test_bpc_future.py
```

通过。

5-task smoke：

```text
moon_trek_5_journey.yaml --time-limit 30
--set journey_pricing_direct_journey_label_frontier_bound_ledger_enabled=true
--set journey_corrected_node_bound_audit_enabled=true
--set journey_pricing_direct_journey_label_global_certificate_enabled=true

V1:
apollo15_20km_tasks05_01_seed6000: OPTIMAL, time=2.831999s
tranquillitatis_balmer_like_20km_tasks05_01_seed6000: OPTIMAL, time=1.596065s

V2:
apollo15_20km_tasks05_01_seed6000: OPTIMAL, time=2.457707s
tranquillitatis_balmer_like_20km_tasks05_01_seed6000: OPTIMAL, time=1.618255s
```

最新日志确认：

- 主 exact：`journey_corrected_node_bound_audit.valid=false`，原因 `pricing_not_global_certificate_capable`，符合 fail-closed。
- completion-bound retry：`valid=true`，`bound_kind=FULL_LP_CERTIFICATE`，`pricing_proof_kind=EXHAUSTIVE_NO_NEGATIVE`，`global_remaining_rc_lb=0.0`，`corrected_node_lb=RMP objective`。

V3 单实例集成 smoke：

```text
instance:
BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json

config:
journey_pricing_direct_journey_label_frontier_bound_ledger_enabled=true
journey_pricing_direct_journey_label_global_certificate_enabled=true
journey_corrected_node_bound_audit_enabled=true
journey_corrected_node_bound_fathom_enabled=true

result:
OPTIMAL
solver solving_time = 0.789679s
node_count = 1
pricing_calls = 4
exact_pricing_calls = 3
```

JSONL 里出现：

```text
journey_corrected_node_bound_audit.valid = true
bound_kind = FULL_LP_CERTIFICATE
pricing_proof_kind = EXHAUSTIVE_NO_NEGATIVE
journey_corrected_node_bound_fathom
```

这个 smoke 只证明 V3 opt-in 实跑链路可用；它不是 5/10 full no-regression，也还不是 20 规模非 exhaustive corrected-bound 加速证据。

## 追加：V3 后 canonical random-TW 5/10 no-regression

默认配置复跑：

```text
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks5.csv
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks10.csv
```

结果：

```text
5 规模：60/60 OPTIMAL，avg 0.338764s，median 0.283343s，p90 0.409191s，p95 0.850825s，max 0.908696s
10 规模：60/60 OPTIMAL，avg 4.750018s，median 1.638110s，p90 8.986406s，p95 23.789413s，max 50.060277s
```

上一份 current full600 对照：

```text
5 规模：60/60 OPTIMAL，avg 0.347385s，median 0.314546s，p90 0.432270s，p95 0.469372s，max 1.005447s
10 规模：60/60 OPTIMAL，avg 5.479933s，median 1.876931s，p90 10.031230s，p95 28.400749s，max 56.850713s
```

结论：V3 合入后默认配置未破坏 5/10 canonical random-TW no-regression。5 规模 p95 有波动但绝对值仍小于 1s；10 规模主要分位均改善。

## 追加：20 规模 V3 opt-in 600s 诊断

运行：

```text
BPC_future/results/20260623_v3_corrected_bound_600_randomtw20_seed61000.csv
```

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

结果：

```text
status = EXTERNAL_TIME_LIMIT
return_code = 124
wall_time = 600.022094s
journey_corrected_node_bound_fathom = 0
```

日志摘要：

```text
journey_pricing = 84
journey_rmp = 45
journey_corrected_node_bound_audit = 31
journey_exact_pricing_completion_bound_retry = 9
branch_count = 4
max_node = 8
max_depth = 3
```

corrected-bound audit：

```text
negative_journey_requires_column_addition = 12
pricing_not_global_certificate_capable = 13
ok = 6
valid corrected audits = 6
corrected fathoms = 0
```

关键发现：

- V3 入口在真实 20 规模日志中能产生 valid corrected-bound artifact；
- 4 条 valid 是 full certificate，不能代表非 exhaustive 加速；
- 2 条 `PRICING_CORRECTED_DUAL_BOUND` 来自 `FRONTIER_BOUND_INCOMPLETE`，但 `global_remaining_rc_lb` 约 `-424`，导致 corrected LB 约 `-6600`，完全无法剪枝；
- 该实例仍被 late true-negative、weak-negative filtered、NG DSSR time limit 和 completion-bound retry 交替拖住。

结论：20 规模 seed61000 仍未达成 600s，更不用说 200s。下一步应收紧 frontier LB 并减少 late true-negative discovery，而不是继续只打开 V3 fathom。

10-task smoke：

```text
moon_trek_10_journey.yaml --time-limit 60
--set journey_pricing_direct_journey_label_frontier_bound_ledger_enabled=true
--set journey_corrected_node_bound_audit_enabled=true
--set journey_pricing_direct_journey_label_global_certificate_enabled=true

V1:
apollo15_20km_tasks10_01_seed11000: OPTIMAL, time=6.744654s
tranquillitatis_balmer_like_20km_tasks10_01_seed11000: TIME_LIMIT, time=58.521509s

V2:
apollo15_20km_tasks10_01_seed11000: OPTIMAL, time=5.806320s
tranquillitatis_balmer_like_20km_tasks10_01_seed11000: TIME_LIMIT, time=58.082117s
```

10-task audit 证据：

- apollo10 cg=2 的 completion-bound retry：`valid=true`，`FULL_LP_CERTIFICATE`，`global_remaining_rc_lb=0.0`。
- tranq10 cg=11 的 completion-bound retry：`pricing_proof_kind=FRONTIER_BOUND_INCOMPLETE`，但 `valid=false`、`global_remaining_rc_lb_valid=false`、`frontier_unsupported_region_count=3`，`pricing_reason=time_limit`。
- V2 后 tranq10 没有进入 completion-bound retry；最后停在 cg=13 的 `weak_negative_journeys_filtered`，`exact_retry` 也因同样原因 incomplete，说明该实例这次的主要阻塞变成 late negative / weak-negative tail，而不是 frontier coverage fail-closed。

额外对照：

```text
tranq10 only, --set journey_skip_ordinary_retry_after_weak_negative_filtered=true
TIME_LIMIT, time=59.240903s
```

该开关没有改善这次实例，因为后段仍持续发现真实负列，未进入稳定 no-column proof tail。

这不是完整 10-task no-regression 证明；只能说明本轮默认关闭改动没有造成直接崩溃。V1 暴露出的 popped-but-not-replaced frontier 缺口已经由 V2 修补；V2 又暴露出另一个现实问题：部分实例在 60 秒内仍不断发现 late negative columns，尚未到达可证明的 no-column tail。

## 当前状态判断

本轮完成的是 proof contract 的 V0/V1 接口、direct open-label frontier LB helper、V2 token 生命周期、fail-closed 审计层，以及 V3 最小 guarded fathom 入口。它还没有完成真正的 20 规模加速，因为尚未在 canonical random-TW 20 规模上证明 corrected LB 能频繁且足够强地剪枝。

要让 20 规模接近 200 秒内最优，下一步必须把 direct-label completion-bound retry 的未探索空间真正接入 `FrontierBoundLedger`，让 incomplete/tail 状态也能给出有效的 `global_remaining_rc_lb`：

- OPEN direct labels
- lazy next-sortie/profile generation
- pending complete candidates
- resume heap / physical catalog
- worker shard root
- unsupported region fail-closed

只有当 `global_remaining_rc_lb_valid=true` 且 `coverage_complete=true` 能在 incomplete/tail 状态下出现，corrected node bound 才会开始减少 branch proof tail。

同时，tranq10 V2 说明仅有 corrected-bound 还不够：如果后段持续发现真实负列，节点还不能 fathom。下一条主线要减少 late negative column discovery 的 CG 轮数，让 solver 更早进入 certificate candidate / no-column proof tail。

## 下一步

已完成 `direct-label frontier coverage V2` 的第一步：

1. 在 direct-label heap 初始化时注册 root frontier token。
2. 每次 label expansion 用原子替换维护 child tokens，而不是只在结束时扫 heap；pop 后 parent token 必须保持 active，直到 complete children 全部入 ledger。
3. 对 pending complete candidate 记录 `pending_complete_min_rc`。
4. 对 label-resume heap / physical catalog / lazy next-sortie 生成补齐 coverage 语义；无法补齐的区域计入 unsupported，禁止 bound。
5. 在 5-task exhaustive audit 中验证 reported LB 永远不超过真实 remaining RC。
6. 通过后在 20 规模打开 corrected-bound audit，观察是否能在 proof tail 未 full closure 时产生有效 node LB。
7. corrected-bound gate 已接入默认关闭的 guarded fathom；下一步必须先做 5/10 no-regression 和 20 规模 canonical 诊断，确认它不是只在 toy/focused test 中生效。

新的下一步：

1. 在 20 规模之前先做 tranq10 late-negative tail 诊断：统计 cg>=8 的 negative task-set 是否重复、是否只替换已有 task-set、是否由 weak threshold 或 GAT admission 延迟导致。
2. 针对 late negative columns，优先把 GAT/admission 用在“后段真实负列提前批量加入”，而不是 branch fathom。
3. 当一轮 exact pricing 只剩 weak negatives 或 completion-bound frontier valid 时，在 600s 诊断预算中打开 corrected-bound fathom opt-in，观察 canonical 20 规模是否出现有效剪枝。
4. 正式 5/10 no-regression 后，再跑 20 规模 200s gate。

在这之前，不应默认打开 corrected-bound fathom，也不应训练新的 branch GAT。

## 追加：learning true-RC support-aware filter opt-in

### 改动

新增默认关闭配置：

```text
journey_learning_true_rc_support_aware_filter_enabled
journey_learning_true_rc_support_overlap_threshold
```

作用位置：

- 只作用于 learning-smoothed heuristic 的 true-RC filter；
- 只改变 cap 内候选排序；
- 不改变 exact pricing；
- 不改变 completion certificate；
- 不永久丢弃 true-RC negative，后续 exact pricing 仍是兜底。

排序优先级：

```text
active-support-changing
new task-set
replacement
其他 true-RC negative
```

其中 active-support-changing 由当前 active task-set 与候选 task-set 的 overlap 以及 pool 中已有 task-set raw cost 判断。日志新增：

```text
support_aware_filter_enabled
support_overlap_threshold
active_support_task_set_count
known_task_set_count
support_aware_candidate_active_support_changing_journeys
support_aware_selected_active_support_changing_journeys
support_aware_candidate_new_task_set_journeys
support_aware_selected_new_task_set_journeys
support_aware_candidate_replacement_journeys
support_aware_selected_replacement_journeys
```

### 验证

Focused tests：

```text
test_journey_learning_true_rc_filter_fills_strong_cap_with_weak_true_negatives
test_journey_learning_true_rc_filter_certificate_context_rejects_weak_fill
test_journey_learning_true_rc_filter_support_aware_is_opt_in

Ran 3 tests
OK
```

Proof / frontier focused tests：

```text
test_frontier_bound_ledger_replaces_parent_atomically
test_frontier_bound_ledger_keeps_parent_for_interrupted_expansion
test_direct_open_label_frontier_lower_bound_scans_active_heap
test_direct_label_frontier_bound_fails_closed_on_restricted_beam_mode
test_corrected_node_bound_uses_fleet_rhs_and_task_count
test_corrected_node_bound_audit_logs_proof_artifact

Ran 6 tests
OK
```

编译通过：

```text
compileall:
BPC_future/solver/journey_driver.py
BPC_future/pricing/journey_pricing.py
BPC_future/master/journey_rmp.py
BPC_future/tests/test_bpc_future.py
```

5-task default-off smoke：

```text
results = BPC_future/results/20260623_support_aware_default_off_5task_smoke.csv

apollo5: OPTIMAL, time=2.923285s
tranq5:  OPTIMAL, time=1.591690s
```

5-task opt-in smoke：

```text
results = BPC_future/results/20260623_support_aware_optin_5task_smoke.csv

apollo5: OPTIMAL, time=2.381230s
tranq5:  OPTIMAL, time=1.593241s
```

10-task opt-in, overlap=1.0：

```text
results = BPC_future/results/20260623_support_aware_optin_10task_probe.csv

apollo10: OPTIMAL, time=5.805125s
tranq10:  TIME_LIMIT, time=59.184352s, columns=447, cg=16
```

10-task tranq-only opt-in, overlap=0.5：

```text
results = BPC_future/results/20260623_support_aware_overlap05_tranq10_probe.csv

tranq10: TIME_LIMIT, time=54.386273s, columns=439, cg=13
```

结构化日志摘要：

```text
cg=1:
  candidate_journeys=16
  true_negative_journeys=13
  kept_journeys=4
  support_aware_candidate_active_support_changing_journeys=4
  support_aware_selected_active_support_changing_journeys=4

cg=2:
  candidate_journeys=7
  true_negative_journeys=4
  kept_journeys=2
  support_aware_candidate_active_support_changing_journeys=4
  support_aware_selected_active_support_changing_journeys=2
```

### 结论

该 opt-in 不是最终解，但有可用信号：

- overlap=1.0 太窄，几乎没有 active-support-changing 候选。
- overlap=0.5 能让 early learning batch 选择 active-support-overlap 的 true-RC negative，并改变 tranq10 早期 RMP 轨迹。
- tranq10 仍然 TIME_LIMIT，最后停在 `weak_negative_journeys_filtered`，说明 support-aware admission 只能减少一部分 late-negative 轮数，不能替代 frontier corrected-bound / proof-tail closure。

下一步应把这条线作为 Phase 2 的一个 opt-in 杠杆保留，同时继续主攻：

1. weak-negative tail 后的 completion-bound / corrected-bound 接入；
2. direct-label frontier coverage 的 unsupported region 消除；
3. 20 规模上 paired A/B 验证是否减少 exact pricing calls 和 CB retry。

## 追加：weak-negative final probe opt-in 与 tranq10 尾部探针

### 改动

新增默认关闭配置：

```text
journey_certificate_completion_bound_weak_negative_final_probe_enabled
journey_certificate_completion_bound_weak_negative_min_time
```

语义：

- 当 exact pricing 没有返回可加入列，但 `weak_negative_journeys_filtered > 0` 时，可以直接跳过普通 retry，把剩余窗口交给 completion-bound final judge。
- 该路径不产生任何新的剪枝证书；final judge 必须自己找到 true-negative column 或返回 incomplete。
- 默认关闭时行为不变。

同时，`_journey_completion_bound_probe_budget_is_viable()` 增加 `pricing` 参数。只有在 weak-negative final probe opt-in 且当前 pricing 符合 weak-tail 条件时，才使用 `journey_certificate_completion_bound_weak_negative_min_time` 作为较低的最小探测时间；普通 after-retry final judge 仍使用原来的 `journey_certificate_completion_bound_after_retry_min_time`。

### 验证

Focused tests：

```text
test_weak_negative_filtered_retry_skip_is_opt_in_and_column_free
test_retry_budget_completion_reserve_is_opt_in_and_bounded
test_journey_learning_true_rc_filter_support_aware_is_opt_in
test_frontier_bound_ledger_replaces_parent_atomically
test_frontier_bound_ledger_keeps_parent_for_interrupted_expansion
test_direct_open_label_frontier_lower_bound_scans_active_heap
test_direct_label_frontier_bound_fails_closed_on_restricted_beam_mode
test_corrected_node_bound_uses_fleet_rhs_and_task_count
test_corrected_node_bound_audit_logs_proof_artifact

Ran 9 tests
OK
```

编译通过：

```text
compileall:
BPC_future/solver/journey_driver.py
BPC_future/pricing/journey_pricing.py
BPC_future/master/journey_rmp.py
BPC_future/tests/test_bpc_future.py
```

5-task default-off smoke：

```text
results = BPC_future/results/20260623_weak_final_probe_default_off_5task_smoke.csv

apollo5: OPTIMAL, time=2.376873s
tranq5:  OPTIMAL, time=1.600399s
```

### tranq10 探针 1：support-aware + weak final probe

```text
results = BPC_future/results/20260623_weak_final_probe_overlap05_tranq10_probe.csv

tranq10: TIME_LIMIT, time=58.063417s, columns=433, cg=16
```

关键日志：

```text
cg=16 exact:
  pricing_state=INCOMPLETE_LIMIT
  reason=weak_negative_journeys_filtered
  negative_journeys=0
  weak_negative_journeys_filtered=1

cg=16 exact_completion_bound_retry:
  pricing_time_limit=1.008343
  reason=time_limit
  pricing_proof_kind=FRONTIER_BOUND_INCOMPLETE
  global_remaining_rc_lb_valid=true
  coverage_complete=true
  frontier_region_count=1
  global_remaining_rc_lb=-2980.049904
  corrected_node_lb=-5757.401110
```

结论：

- weak-negative 后跳过普通 retry 已生效。
- 但 final judge 启动太晚，只剩约 1 秒。
- 更关键的是 frontier LB 太松，虽然 coverage complete，但 `global_remaining_rc_lb=-2980` 不能产生有用 corrected bound。

### tranq10 探针 2：pre-exact handoff

```text
results = BPC_future/results/20260623_pre_exact_handoff_overlap05_tranq10_probe.csv

tranq10: TIME_LIMIT, time=59.216602s, columns=427
```

关键日志：

```text
cg=14 exact_completion_bound_pre_exact_handoff:
  new_time_limit=8.672381
  reason=time_limit
  negative_journeys=4
  best_reduced_cost=-1.156187
```

结论：

- pre-exact handoff 可以更早进入 completion-bound judge。
- 但它花了 8.7 秒只返回 4 个 true-negative columns，没有闭合证明。
- 这说明单纯提前进入 judge 不够，还需要更强 frontier lower bound 或更高效的 negative-column batch return。

### tranq10 探针 3：pre-exact handoff + harvest soft-return

```text
results = BPC_future/results/20260623_pre_exact_softreturn_overlap05_tranq10_probe.csv

tranq10: TIME_LIMIT, time=58.353717s, columns=439
```

关键现象：

```text
cg=13 exact_completion_bound_pre_exact_handoff:
  reason=time_limit
  negative_journeys=0
  best_reduced_cost=-0.0
```

结论：

- 早返回参数没有解决该尾部。
- 这轮尾部不是“已经找到负列但迟迟不返回”，而是 final judge 需要证明或给出强 lower bound。

### 当前判断

本轮修掉的是一个调度缺口：weak-negative tail 现在可以直接交给 completion-bound final judge，不再必须浪费一次普通 retry。

但 tranq10 仍未闭合，主因已经变成：

1. final judge 在最后窗口启动时预算不足；
2. 即使 coverage complete，`global_remaining_rc_lb` 仍极松；
3. late true-negative columns 还会持续出现，节点尚未稳定进入 no-column proof tail。

因此下一步不应继续只调 weak-negative 阈值。更高优先级是：

1. 强化 direct-label frontier token 的 admissible lower bound，尤其是 root/open-label 的 suffix bound；
2. 让 completion-bound judge 在找到一批 true-negative columns 时更高效返回，但不能牺牲 final proof；
3. 在 20 规模前继续用 tranq10 作为快速尾部探针，只有 tranq10 不再卡在 weak/proof tail 后，再跑 20 秒级 gate。

## 追加：frontier LB 分解诊断与 two-cycle 小预算门控

### 新增诊断字段

为解释 `global_remaining_rc_lb` 为什么过松，`JourneyPricingResult` 与 `journey_pricing` 日志新增：

```text
frontier_min_active_lb
frontier_min_active_label_objective
frontier_min_active_suffix_lb
frontier_min_active_future_cut_reward
frontier_min_active_suffix_winner
```

这些字段只解释 active frontier 中最小 token 的组成，不参与剪枝、证书或 bound 计算。

### 诊断结果

tranq10 pre-exact handoff 诊断：

```text
results = BPC_future/results/20260623_frontier_lb_diag_preexact20_tranq10_probe.csv

tranq10: TIME_LIMIT, time=58.845022s
```

关键日志：

```text
cg=13 exact_completion_bound_pre_exact_handoff:
  pricing_time_limit=6.0
  reason=time_limit
  negative_journeys=0
  global_remaining_rc_lb=-163.236570727
  frontier_min_active_label_objective=50.0
  frontier_min_active_suffix_lb=-213.236570727
  frontier_min_active_future_cut_reward=0.0
  frontier_min_active_suffix_winner=unique_route
  two_cycle_table_complete=true
  two_cycle_state_count=83853
```

解释：

- final judge 的最小 frontier token 仍是 root label，`label_objective=50.0`。
- `global_remaining_rc_lb` 主要来自 suffix bound，future cut reward 不是本次主因。
- 6 秒窗口里大量时间花在 completion-bound/two-cycle 构造和准备，frontier 没有推进到可证明收口。

### two-cycle 小预算门控

新增默认关闭配置：

```text
journey_certificate_completion_bound_two_cycle_budget_gate_enabled
journey_certificate_completion_bound_two_cycle_min_time_limit
```

语义：

- 只在 `_journey_config_with_call_deadline()` 拿到本次 final judge 实际 `time_limit` 后判断；
- 只有 completion-bound final judge 且 two-cycle 已启用时生效；
- 若本次预算小于阈值，则关闭本次调用的 two-cycle 构表；
- exact-safe：这只会削弱 pruning / bound，不会产生伪证书。找不到证书仍然 incomplete。

Focused tests：

```text
test_final_judge_config_with_call_deadline_sets_absolute_deadline
test_final_judge_call_budget_can_gate_two_cycle_opt_in
test_weak_negative_filtered_retry_skip_is_opt_in_and_column_free
test_retry_budget_completion_reserve_is_opt_in_and_bounded
test_direct_label_frontier_bound_fails_closed_on_restricted_beam_mode
test_corrected_node_bound_uses_fleet_rhs_and_task_count

Ran 6 tests
OK
```

5-task default-off smoke：

```text
results = BPC_future/results/20260623_budgetgate_default_off_5task_smoke.csv

apollo5: OPTIMAL, time=2.412562s
tranq5:  OPTIMAL, time=1.603315s
```

apollo10 default-off smoke：

```text
results = BPC_future/results/20260623_budgetgate_default_off_apollo10_smoke.csv

apollo10: OPTIMAL, time=5.834479s
```

tranq10 two-cycle budget gate 探针：

```text
results = BPC_future/results/20260623_frontier_lb_diag_preexact20_budgetgate10_tranq10_probe.csv

tranq10: TIME_LIMIT, time=59.234500s
```

关键日志：

```text
cg=13 exact_completion_bound_pre_exact_handoff:
  pricing_time_limit=6.174533
  two_cycle_enabled=false
  two_cycle_state_count=0
  negative_journeys=1
  best_reduced_cost=-0.306982
```

结论：

- 小预算门控按预期生效，避免了 two-cycle 构表，并让 final judge 在同一窗口内至少推进到一个 true-negative column。
- 但 tranq10 仍然 TIME_LIMIT，说明该门控只是避免浪费预算，不是 proof-tail 的根本解。
- 下一步应继续收紧 root/open-label suffix LB，或让 final judge 的 negative harvesting 在小预算下能更早、更批量地返回 true-negative columns。
