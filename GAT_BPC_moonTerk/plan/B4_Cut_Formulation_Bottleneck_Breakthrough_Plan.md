# B4 Cut/Formulation Bottleneck Breakthrough Plan

## 0. 当前定位

当前不要把 B4 理解成“继续给已经闭合的 5/10/20 加几条 cut”。

当前已接受主线是：

```text
Objective v1:
    normalized_operating_cost
  + normalized_risk
  + 0.4 * normalized_weighted_completion_time

makespan:
    metric only
    not in pricing objective
```

当前已知结果：

```text
5-scale:  B3B = 20/20 BPC_TREE_OPTIMAL
10-scale: B3B = 20/20 BPC_TREE_OPTIMAL
20-scale: B3B = 20/20 BPC_TREE_OPTIMAL
30-scale: no exact certificate; feasible incumbents and pricing/frontier diagnostics only
```

因此 B4 的真正任务不是提高 5/10/20 的 optimal count，而是：

```text
1. 保持 5/10/20 B3B exact certificate 不回归；
2. 诊断哪些 valid cuts / formulation rows 对 lower bound、node count、certificate time 有真实贡献；
3. 针对 30-scale 的核心瓶颈：compact pricing / final-judge no-negative proof gap；
4. 将 B4 切成可消融的 diagnostic -> live-opt-in 路线，而不是默认开启 cut。
```

---

## 1. 当前 B4 要突破的瓶颈

### 1.1 不是缺可行解

30-scale 当前已经有 reference feasible incumbent / compact product incumbent。报告显示 30-scale 当前不是缺上界，而是缺 exact lower bound / BPC certificate。

### 1.2 不是简单 row timeout 黑盒

当前 telemetry 已经把 30-scale 失败定位到：

```text
complete-universe RC audit / true-dual pricing tail / compact pricing proof bound gap
```

代表性信号：

```text
- direct-DP 在 sortie_candidate_generation 阶段爆炸；
- B1B / BPC root 能用 reference seed 启动；
- final judge 可以持续发现真实 negative reduced-cost columns；
- compact pricing batch 能显著减少外层 RMP rounds；
- staged resume 能累积 active columns；
- 但 unrestricted no-negative proof 仍然无法闭合；
- 多次 replay 显示 proof-tail dual 下仍可能隐藏真实 negative column。
```

所以 B4 的突破方向应当是：

```text
A. master-side cut diagnostics: 是否能抬 root/node LP bound；
B. pricing-side formulation strengthening: 是否能改善 compact pricing proof bound；
C. staged frontier integration: 是否能把新 formulation 的收益体现在 BPC root/node closure 上。
```

---

## 2. B4 总原则

### 2.1 B4 不能改变的东西

B4 不允许改变：

```text
- objective function;
- certificate taxonomy;
- direct-DP / BPC certificate boundary;
- worker no-column semantics;
- final judge as only no-negative certificate source;
- B3B accepted result for 5/10/20;
- makespan metric-only status.
```

### 2.2 B4 不允许默认做的事情

第一轮 B4 禁止默认启用：

```text
- fleet lower-bound live cut;
- route-order branch;
- GAT guidance;
- completion-bound pruning under active cut;
- task-set dominance under route/resource/time-sensitive cut;
- any cut that lacks RMP/pricing/manual reduced-cost consistency audit.
```

### 2.3 B4 成功不能只看 cut 数量

以下不算 B4 成功：

```text
cut_candidate_count > 0
cut_added_count > 0
cut_dual_nonzero_count > 0
```

B4 只有在真实消融中改善以下至少一项，才算有效：

```text
- root_lp_bound increases;
- global lower bound improves;
- root / tree gap decreases;
- node count decreases;
- certificate time decreases;
- compact pricing proof bound improves;
- final judge hidden-negative discovery becomes more efficient;
- 30-scale proof-tail fail reason becomes materially more precise.
```

---

## 3. B4 推荐分层

```text
B4A: cut diagnostic only
B4B: subset-row live opt-in, root/node certificate gated
B4C: pricing formulation strengthening diagnostic
B4D: 30-scale staged frontier + formulation probe
B4E: accepted B4 candidate only if measurable improvement exists
```

每个子层都必须能单独开关，能和 B3B / current 30-scale diagnostic baseline 做 A/B。

---

## 4. B4A：Cut Diagnostic Only

### 4.1 目标

只回答：

```text
当前实例/节点中，是否存在有潜力的 valid cut signal？
```

B4A 不改变 solver 行为：

```text
- 不加 RMP rows；
- 不改变 pricing；
- 不改变 certificate；
- 不改变 lower bound；
- 不改变 branch tree。
```

### 4.2 需要实现 / 完善

模块：

```text
exact/bpc/cuts/subset_row.py
exact/bpc/cuts/cut_context.py
exact/bpc/cuts/cut_audit.py
exact/bpc/cuts/coefficient_audit.py
exact/bpc/cuts/dominance_compatibility.py
runners/b4_cut_formulation_ablation.py
```

已有 `exact/core/cuts.py` 和 `exact/bpc/cuts/cut_audit.py` 可以复用，但要确认 report 字段完整。

### 4.3 必须记录字段

```text
cut_candidate_count
cut_violated_count
max_violation
mean_violation
violated_subset_size_histogram
cut_kind
cut_key
rhs
sense
coefficient_dependency
coefficient_vector_hash
pricing_supported
completion_bound_supported
dominance_compatible
would_bind_on_current_rmp
would_change_dual_support
affected_column_count
active_support_overlap
```

### 4.4 实验矩阵

```text
5-scale full 20:
    B3B baseline
    B4A diagnostic

10-scale full 20:
    B3B baseline
    B4A diagnostic

20-scale full 20:
    B3B baseline
    B4A diagnostic

30-scale selected:
    reference incumbent / B1B staged frontier / compact pricing state
    B4A diagnostic
```

### 4.5 B4A 通过标准

```text
- no certificate scope regression;
- no objective mismatch;
- no direct-DP certificate leak;
- all cut coefficient vectors reproducible;
- fleet lower-bound live disabled;
- completion-bound pruning under cut context disabled;
- report identifies whether subset-row has real violation signal.
```

B4A 可以通过诊断，但不能被称为 accepted optimization baseline。

---

## 5. B4B：Subset-Row Live Opt-In

### 5.1 进入条件

只有当 B4A 找到明确 subset-row signal 时，才允许 B4B：

```text
cut_violated_count > 0
max_violation > eps
cut coefficient is task-set based
pricing coefficient supported
manual RC audit supported
completion-bound pruning fail-closed
```

### 5.2 允许的 live cut

第一轮只允许：

```text
subset-row cut
```

严禁 live：

```text
fleet lower-bound cut
route/resource/time/order-sensitive cut
```

### 5.3 证书要求

B4B 如果启用 live cut，必须通过：

```text
integer validity proof
RMP coefficient audit
pricing coefficient audit
manual RC == pricing RC
cut dual sign audit
CutContextVersion
CutCoefficientVector
CutDominanceCompatibilityReport
completion-bound fail-closed under active cuts
```

任何一项失败：

```text
certificate_scope = DIAGNOSTIC_PRICING_FRONTIER
or FEASIBLE_INCUMBENT_ONLY
```

不能输出：

```text
BPC_NODE_LP_CERTIFIED
BPC_TREE_OPTIMAL
```

### 5.4 第一轮 B4B 的范围

不要直接做全树 cut-enhanced BPC。第一轮只做：

```text
B4B-root-live-subset-row
```

用途：

```text
- 验证 cut reduced cost 语义；
- 观察 root bound movement；
- 检查 cut dual sign；
- 检查 final judge with cut context 是否正确。
```

只有 root live 安全并且有 measurable improvement 后，才考虑：

```text
B4B-node-live-subset-row
```

### 5.5 B4B 成功标准

B4B 必须相比 B3B / no-cut root 有真实收益：

```text
root_lp_bound_delta > eps
or root_gap_delta < -eps
or node_count_delta < 0
or certificate_time_delta < 0
or proof-tail fail reason becomes stricter / more informative
```

如果：

```text
cut_added_count > 0
but bound unchanged
and node count unchanged
and certificate time worse
```

则 B4B 不接受。

---

## 6. B4C：Pricing Formulation Strengthening Diagnostic

### 6.1 为什么 B4C 比 master cut 更关键

当前 30-scale 的主要瓶颈不是 5/10/20 的 tree closure，而是：

```text
unrestricted compact pricing proof bound gap
```

因此 B4 不应只盯 master subset-row。必须有 pricing-side formulation strengthening。

### 6.2 目标

在不改变 certificate 语义的前提下，测试哪些 compact pricing formulation rows 能改善：

```text
- compact pricing dual bound;
- root LP proof gap;
- negative-feasibility search speed;
- optimization-proof no-negative proof speed;
- hidden negative replay efficiency.
```

### 6.3 候选 formulation diagnostics

优先级：

```text
1. endpoint-order cuts already shown useful: continue measuring;
2. pair-adjacency cuts already shown useful: continue measuring;
3. latest-service-start slot bound;
4. time-window arc pruning;
5. route/resource feasibility rows;
6. task visit lower bound rows;
7. outgoing/start future-tail lower bound rows;
8. subset-row-derived pricing cuts if coefficient can be represented safely.
```

### 6.4 每个 formulation row 必须报告

```text
formulation_kind
row_count_added
var_count_before / after
constraint_count_before / after
arc_options_removed
slot_count_before / after
compact_pricing_best_rc
compact_pricing_dual_bound
compact_pricing_gap
mip_nodes
simplex_iterations
wall_time
negative_found
negative_rc
can_certify_no_negative
certificate_scope
```

### 6.5 B4C 禁止事项

```text
- formulation diagnostic cannot certify unless unrestricted exact pricing proof passes;
- negative-feasibility subproblem can find columns but cannot prove no-negative;
- restricted/no-good search cannot become official proof;
- positive incumbent RC cannot be interpreted as no-negative if dual bound remains negative.
```

---

## 7. B4D：30-scale staged frontier integration

### 7.1 当前 30-scale 状态

30-scale 首实例已经能通过 staged resume 积累 active columns，但仍没有 no-negative proof。B4D 需要把 cut/formulation diagnostics 接入 staged frontier，而不是每次从头跑。

### 7.2 B4D 目标

```text
从当前 staged active column pool 出发，比较不同 formulation strengthening 对下一阶段的边际贡献。
```

### 7.3 推荐实验

对 30-scale 首实例：

```text
baseline staged state:
    latest active column pool
    latest dual / RMP state

run variants:
    V0: current compact pricing proof
    V1: endpoint-order + pair-adjacency
    V2: latest-service-start slot bound
    V3: time-window arc pruning
    V4: V1 + V2 + V3 combined
    V5: subset-row master diagnostic only
```

每个 variant 跑：

```text
negative-feasibility 600s
optimization-proof 900s
optional staged continuation 900s
```

记录：

```text
new negative columns found
best negative RC
proof dual bound
proof gap
columns added
active columns after merge
whether no-negative certified
```

### 7.4 B4D 判定

B4D 成功不是必须 closure，而是要给出清楚选择：

```text
哪个 formulation family 最能改善 proof bound / 找列效率？
哪个 formulation family 只是加约束但没有帮助？
当前 30-scale 是仍在加列阶段，还是接近 proof-tail 阶段？
```

---

## 8. B4E：Accepted B4 Candidate

B4E 只有在以下条件满足时才能成为 accepted baseline：

```text
1. redlines all zero;
2. 5/10/20 no regression;
3. at least one real improvement over B3B or current 30 diagnostic baseline;
4. live cut, if any, passes full RC/pricing/cut/dominance audit;
5. no fleet lower-bound live cut unless explicit proof exists;
6. completion-bound pruning remains fail-closed under active cuts unless separately proved.
```

B4E 可以有两种接受方式：

```text
B4E-master-cut-accepted:
    subset-row live cut improves B3B workload or bound.

B4E-pricing-formulation-accepted:
    compact pricing formulation strengthening improves 30-scale proof-tail metrics.
```

B4E 不要求 30-scale BPC_TREE_OPTIMAL，但必须提供 measurable progress。

---

## 9. Redlines

以下必须为 0：

```text
objective_mismatch_count
certificate_scope_regression_count
direct_dp_certificate_leak_count
manual_rc_with_cuts_fail_count
pricing_rc_with_cuts_fail_count
cut_coefficient_audit_fail_count
cut_dual_sign_audit_fail_count
cut_dominance_compatibility_fail_count
fleet_lower_bound_live_enabled_without_proof_count
completion_bound_unsafe_with_cuts_count
restricted_pricing_claimed_no_negative_count
positive_incumbent_rc_claimed_certificate_count
```

如果任何 redline > 0：

```text
B4 remains diagnostic only.
```

---

## 10. Required tests

### 10.1 Cut coefficient tests

```text
test_subset_row_coefficient_overlap_floor_divisor
test_subset_row_rhs_floor_size_divisor
test_cut_coefficients_for_journey_stable_order
test_cut_coefficient_vector_hash_changes_when_cut_active
```

### 10.2 Reduced cost tests

```text
test_manual_rc_with_subset_row_cut_matches_pricing_rc
test_cut_dual_sign_for_subset_row_is_nonpositive
test_cut_context_empty_does_not_change_rc
test_live_cut_fails_closed_when_pricing_audit_missing
```

### 10.3 Dominance / signature tests

```text
test_cut_aware_signature_includes_cut_hash
test_task_set_dominance_not_enabled_under_active_resource_sensitive_cut
test_completion_bound_pruning_disabled_under_active_cut
```

### 10.4 Safety tests

```text
test_fleet_lower_bound_cut_diagnostic_only
test_restricted_negative_feasibility_cannot_certify_no_negative
test_positive_best_rc_with_negative_dual_bound_is_not_certificate
test_b4_diagnostic_does_not_change_certificate_scope
```

### 10.5 Regression tests

```text
test_5_scale_b3b_objective_unchanged_with_b4a
test_10_scale_b3b_objective_unchanged_with_b4a
test_20_scale_b3b_objective_unchanged_with_b4a
test_b4b_live_subset_row_no_regression_on_smoke
```

---

## 11. B4 experiment matrix

### 11.1 Smoke

```text
5-scale instance 001:
    B3B
    B4A diagnostic
    B4B live subset-row if violated
```

### 11.2 Full exact scales

```text
5-scale full 20:
    B3B
    B4A
    B4B only if B4A finds signal

10-scale full 20:
    B3B
    B4A
    B4B only if signal

20-scale full 20:
    B3B
    B4A
    B4B selected signal instances only
```

### 11.3 30-scale diagnostic

```text
30-scale selected first instance:
    current staged state
    B4C formulation variants
    B4D staged continuation

30-scale selected 5:
    only after first instance shows useful signal
```

---

## 12. Report outputs

B4 must produce:

```text
runs/b4_cut_formulation_ablation/b4_cut_rows.csv
runs/b4_cut_formulation_ablation/b4_cut_summary.json
runs/b4_cut_formulation_ablation/b4_cut_report_zh.md
```

B4C/B4D 30-scale formulation diagnostics should additionally produce:

```text
runs/b4_pricing_formulation_diagnostic/b4_pricing_rows.csv
runs/b4_pricing_formulation_diagnostic/b4_pricing_summary.json
runs/b4_pricing_formulation_diagnostic/b4_pricing_report_zh.md
```

Markdown report must answer:

```text
1. What is the previous accepted baseline?
2. Which cut/formulation modes were tested?
3. Did any cut violate and bind?
4. Did any live cut pass RC/pricing/dominance audits?
5. Did root/tree bound move?
6. Did node count or certificate time improve?
7. Did compact pricing proof bound improve on 30-scale?
8. Did any diagnostic accidentally claim certificate?
9. Is B4 accepted? If yes, which sublayer?
10. If not accepted, what is the next most promising cut/formulation target?
```

---

## 13. Codex execution order

Codex should follow this order exactly:

```text
Step 1: Read current B3/B4 reports and normalized objective audit.
Step 2: Freeze objective v1 and B3B as previous accepted baseline.
Step 3: Implement/repair B4A diagnostic runner and report fields.
Step 4: Run B4A on 5/10/20 full and 30 selected diagnostic.
Step 5: Only if B4A finds subset-row signal, implement B4B root live opt-in smoke.
Step 6: Implement B4C pricing formulation diagnostics for 30-scale compact proof gap.
Step 7: Add B4D staged frontier integration for 30-scale first instance.
Step 8: Decide whether B4E exists based on measured improvement.
```

Do not proceed to GAT/B5 during this work.

---

## 14. Final success statement

B4 is successful only if it can honestly say one of the following:

```text
B4-master-cut result:
    A mathematically valid live subset-row cut improves bound/tree/certificate workload without certificate regression.

B4-pricing-formulation result:
    A pricing formulation strengthening measurably improves 30-scale compact pricing proof gap or negative discovery efficiency.
```

If neither is true, B4 remains diagnostic and the project should not claim B4 optimization.
