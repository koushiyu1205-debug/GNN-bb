# 03_B2_Pricing_Tail_Optimization_Layer.md

## 0. 本轮定位

B2 不是 GAT、不是 cuts、不是 full branch tree。B2 是在 B0/B1 proof-safe core 之上，把 root-level pricing / column-generation / certificate-tail 做成一个可用、可消融、可解释的优化层。

B2 的核心矛盾已经很清楚：

```text
B0 direct-DP 在 20-scale 仍然可以快速得到 fixed-graph exact optimum；
B1/B2 的 root BPC proof-tail 在 10/20 上仍然 timeout；
B2A full-universe RC audit 已经显示 full universe 已知时可以非常快；
B2B seeded-tail-CG 目前没有在 10/20 上展示真实改进。
```

因此，本轮 B2 不能继续只做 addability / duplicate / hidden-negative 的 logging。它必须升级为一个 **usable exact solver layer**：在 5/10/20 上能稳定给出 fixed-graph exact optimal solution，同时清楚标注 certificate scope；并且单独评估 BPC root-pricing 路线相对 B1 是否真的更优。

---

## 1. B2 优化目标

### 1.1 产品级目标：5/10/20 可求得 fixed-graph exact optimum

我同意“B2 至少应该成为一个可求 5/10/20 最优解的可行求解器”这个目标，但必须精确定义证书范围：

```text
B2_PRODUCT_EXACT_SOLVER:
    对 5/10/20 输出 fixed-graph exact optimal solution；
    optimal 可以来自 DIRECT_DP_FIXED_GRAPH_OPTIMAL，也可以来自 BPC_NODE_LP_CERTIFIED + integral_root；
    不能把 direct-DP optimal 冒充 BPC_TREE_OPTIMAL；
    不能把 diagnostic RMP bound 冒充 official bound。
```

也就是说，B2 的产品级 solver 可以合法使用：

```text
1. B0 direct-DP oracle；
2. B2A full-universe RC audit fast path；
3. B2B seeded root-CG；
4. fail-closed BPC diagnostic when no exact proof is available.
```

但所有输出必须带 certificate scope：

```text
DIRECT_DP_FIXED_GRAPH_OPTIMAL
BPC_NODE_LP_CERTIFIED
DIAGNOSTIC_RMP_BOUND
DIAGNOSTIC_PRICING_FRONTIER
FEASIBLE_INCUMBENT_ONLY
```

如果 20-scale 由 direct-DP 求得最优，那是成果，但它不是 BPC proof 成果。B2 报告必须分开统计：

```text
exact_solution_count_by_any_valid_scope
bpc_node_lp_certified_count
bpc_tree_optimal_count
```

### 1.2 BPC 级目标：让 root pricing-tail 真的变好

B2 的算法优化目标不是重复证明 direct-DP 已经强，而是让 BPC root pricing 更接近可扩展：

```text
B2A:
    full universe 已经完整时，避免重复 final-judge 枚举；
    用 membership + manual RC audit 快速闭合 root LP。

B2B:
    seed pool 不完整时，降低 pricing-tail 成本；
    让 true-RC negative 更快进入 master；
    避免 duplicate-only / replacement-only / hidden-negative tail；
    在 10-scale 上至少出现真实 BPC improvement。
```

B2B 要晋级，不能只靠 5-scale no regression。它至少要在 10-scale 或 selected 20-scale 上展示：

```text
wall time 降低；
final judge calls 降低；
pricing rounds 降低；
time-to-first-negative 降低；
candidate generation / label generation 明显下降；
或 timeout 变成 BPC_NODE_LP_CERTIFIED。
```

---

## 2. B2 与 B1/B0 的关系

### 2.1 B0 direct-DP oracle

B0 是 fixed-graph finite-universe exact oracle。它可以给 5/10/20 的 exact optimal solution，但不是 BPC certificate。

B2 必须保留 B0 作为：

```text
objective oracle；
small/medium scale exact fallback；
BPC alignment reference；
20-scale product exact solver fallback。
```

### 2.2 B1A / B2A

```text
B1A_full_universe_root_audit:
    full universe 预装进 root RMP；
    仍可能重复调用 final judge；
    主要验证 proof boundary。

B2A_full_universe_rc_audit_fast_path:
    full universe 完整且已在 current master view；
    直接对完整 universe 做 manual RC audit；
    不重复 label-pricing final judge；
    只有 full-universe completeness + all columns in master + min RC >= -eps + dual fingerprint 绑定时才可给 BPC_NODE_LP_CERTIFIED。
```

B2A 是 B1A 的优化版。它可以作为 accepted full-universe audit fast path。

### 2.3 B1B / B2B

```text
B1B_seeded_root_CG:
    从 B0 incumbent + singleton/canonical seed pool 出发；
    final judge 找 negative；
    add columns；
    re-solve RMP；
    尝试 closure。

B2B_seeded_tail_CG:
    同样从 seed pool 出发；
    增加 addability-aware harvesting、duplicate-only audit、hidden-negative audit、profiling、negative-search/proof-mode 分离；
    目标是让 B1B 的 root pricing tail 真实变快。
```

B2B 是最终 BPC root-CG 路线的候选；但如果它没有优于 B1B，就不能晋级。

---

## 3. B2 核心算法改造

## 3.1 把 pricing 分成 Negative-Search Mode 与 Proof Mode

这是 B2 下一轮最关键的优化。

经典 column generation / branch-and-price 的常见做法是：

```text
在普通 CG 轮次中，pricing 只需要找到若干 true-RC negative columns；
只有当准备证明 node no-negative 时，才需要完整 exact pricing closure。
```

当前 B1/B2 的 10/20 timeout 很可能来自：每轮都倾向于做重型 exhaustive final judge，而不是先快速找可加入的 negative columns。

因此 B2B 应拆成两种 pricing mode：

```text
NEGATIVE_SEARCH_MODE:
    目标：尽快找到一批 addable true-RC negative columns。
    可在找到 enough_addable_negatives 后停止。
    输出状态只能是 FOUND_NEGATIVE 或 INCOMPLETE_LIMIT。
    不能输出 CERTIFIED_NO_NEGATIVE。

PROOF_MODE:
    目标：完整搜索 fixed pricing universe，证明 no negative。
    只有它能输出 CERTIFIED_NO_NEGATIVE。
```

硬规则：

```text
NEGATIVE_SEARCH_MODE 的 no-column 永远是 LOCAL_NO_COLUMN_UNCERTIFIED 或 INCOMPLETE_LIMIT；
不能关闭 node；
不能生成 official lower bound；
不能让 root_lp_bound_official=true。
```

B2B loop 应改成：

```text
solve RMP
  -> NEGATIVE_SEARCH_MODE pricing
  -> if addable true-RC negatives found:
         harvest batch, add, continue
  -> if no addable negatives found or search budget exhausted:
         PROOF_MODE final judge
  -> if proof mode no-negative:
         BPC_NODE_LP_CERTIFIED
  -> else:
         fail-closed diagnostic
```

为什么这能优化：

```text
B1/B2 当前在 10/20 上很可能还没到 harvest 阶段就被 full final judge enumeration 卡住。
negative-search/proof-mode 分离可以把大部分轮次从“证明无负列”改成“找几条有用负列”，减少不必要的 exhaustive scan。
```

---

## 3.2 B2A：full-universe RC audit fast path 正式化

B2A 已经表现出价值，但需要把 gate 写硬。

B2A 只有在以下条件全部满足时才能 certificate：

```text
full_universe_complete = true
all full-universe column signatures are in MasterColumnView
no forbidden signature
no active unsupported branch/cut context
RMP status = OPTIMAL
ReducedCostContext dual_fingerprint bound to RMP
manual RC audited for every full-universe column
min_manual_rc >= -eps
ProofDebtQueue empty
```

如果任何条件失败：

```text
B2A becomes DIAGNOSTIC_RMP_BOUND or DIAGNOSTIC_PRICING_FRONTIER;
不能 official；
不能 BPC_NODE_LP_CERTIFIED。
```

B2A 报告必须统计：

```text
full_universe_column_count
master_column_count
all_columns_in_master
manual_rc_audited_count
manual_rc_min
manual_rc_audit_time
rmp_solve_time
total_wall
```

目标：

```text
5-scale full: 20/20 no regression, faster than B1A
10-scale selected/full: B2A substantially faster than B1A
20-scale selected: if full-universe enumeration is feasible, B2A may be used as diagnostic fast path; if not, fail-closed cleanly
```

---

## 3.3 B2B：addability-aware harvesting 保留，但不再作为唯一优化点

B2B 当前已经能记录：

```text
candidate_negative_count
addable_negative_count
duplicate_in_current_master_count
in_pool_not_master_count
selected_count
added_to_master_count
duplicate_only_count
hidden_negative_count
```

但第一轮结果显示：5-scale negative candidates 基本全 addable，duplicate-only 和 hidden-negative 都不是当前 bottleneck。

因此下一轮 B2B 的重点应从“只做 addability audit”转为：

```text
1. negative-search/proof-mode 分离；
2. time-to-first-negative profiling；
3. label/sequence/template generation profiling；
4. exact-first-step bound / ordering；
5. worker seed catalog 对 negative search 的帮助；
6. final proof only at termination。
```

Harvesting MVP 仍然保留：

```text
true_rc < -eps
unique full signature
would_enter_master == true
prefer new task set
then strongest reduced cost
cap per batch
log diversity metrics
active_support_difference log-only
```

---

## 3.4 B2C：limited pricing diagnostic，不给证书

为了定位 10/20 timeout，B2 应新增一个 diagnostic pricing probe：

```text
B2C_LIMITED_PRICING_DIAGNOSTIC
```

它的目标不是闭合 root，而是回答：

```text
10/20 是完全找不到 negative？
还是 negative 很多但 enumeration 太慢？
还是 seed pool 太弱导致 dual 很坏？
还是 completion-bound / dominance / ordering 没有发挥作用？
```

B2C 可使用 budget：

```text
max_seconds
max_sortie_labels
max_journey_labels
max_task_sequences
max_path_option_assignments
max_negative_candidates
```

输出：

```text
time_to_first_negative
first_negative_true_rc
first_addable_negative_time
labels_generated_before_first_negative
labels_generated_total
sortie_labels_generated
journey_labels_generated
candidate_negative_count
addable_negative_count
best_true_rc
top_task_sets
top_path_signatures
stop_reason
```

证书规则：

```text
B2C can never return CERTIFIED_NO_NEGATIVE;
B2C can never set root_lp_bound_official=true;
B2C can only output FOUND_NEGATIVE or INCOMPLETE_LIMIT / LOCAL_NO_COLUMN_UNCERTIFIED.
```

---

## 3.5 B2D：proof-tail kernel optimization candidates

B2D 是 B2 的 proof-tail kernel 优化集合。每个优化必须可单独开关并消融。

候选包括：

### A. DirectPricingCache across CG rounds

```text
cache sortie feasibility, route template expansions, path-option signatures, task-mask labels
keyed by instance_id + task_set + path_option_policy + resource constraints
must not cache reduced-cost values across dual changes unless dual fingerprint included
```

目标：减少重复枚举。

### B. Exact-first-step lower bound / ordering

吸收 BPC_future 的经验：第一步 transition 用真实 travel time / energy / shadow / service cost，suffix 使用 optimistic lower bound。

第一版用途：

```text
ordering / diagnostic first
pruning opt-in only after consistency audit
```

### C. Positive-cover-dual ordering

```text
prioritize partial labels that can collect high positive cover duals early
```

只能改变 search order，不能 certificate。

### D. Addable-negative early stop in negative-search mode

```text
stop NEGATIVE_SEARCH_MODE once selected_count >= min_batch_size or max_batch_size;
return FOUND_NEGATIVE, not CERTIFIED_NO_NEGATIVE.
```

### E. Path-option dominance audit reuse

Only if path-option dominance policy is part of certificate scope.

### F. Label profiling counters

Every pricing run must emit:

```text
labels_generated
labels_extended
labels_pruned_by_resource
labels_pruned_by_time_window
labels_pruned_by_dominance
labels_pruned_by_completion_bound
labels_pruned_by_branch
bound_check_time
dominance_time
queue_time
cache_hit_count
cache_miss_count
```

Without profiling, no optimization can become default.

---

## 4. B2 solver modes

B2 should expose a single product-level runner with explicit modes.

```text
B2_PRODUCT_EXACT_SOLVER
B2A_FULL_UNIVERSE_RC_AUDIT
B2B_SEEDED_TAIL_CG
B2C_LIMITED_PRICING_DIAGNOSTIC
B2D_KERNEL_ABLATION
```

### 4.1 B2_PRODUCT_EXACT_SOLVER

Decision order:

```text
1. Try B0 direct-DP if task_count <= direct_dp_product_max_tasks.
   If success: return DIRECT_DP_FIXED_GRAPH_OPTIMAL.

2. If BPC root proof requested:
   a. If full universe is available and complete, run B2A.
   b. Else run B2B.

3. If BPC root LP certificate exists and integral_root=true:
   return exact optimal with BPC_NODE_LP_CERTIFIED + integral_root observation.

4. If BPC root LP certificate exists but root fractional:
   return BPC_GAP_AVAILABLE / needs B3 branch tree.
   Do not claim BPC_TREE_OPTIMAL.

5. If no proof:
   return FEASIBLE_INCUMBENT_ONLY or DIAGNOSTIC_PRICING_FRONTIER fail-closed.
```

Product acceptance for 5/10/20:

```text
5/10/20 exact_solution_count_by_valid_scope = 100%
no certificate leakage
certificate scope distribution reported
```

This product acceptance is separate from B2B acceptance.

---

## 5. Required ablation design

B2 must compare against the current best accepted baseline, not automatically chain from failed modes.

### 5.1 Matrix

Run real instances at 5/10/20/30:

```text
5-scale full:
    B0
    B1A
    B1B
    B2A
    B2B
    B2_PRODUCT_EXACT_SOLVER

10-scale full or selected5->full:
    B0
    B1A
    B1B
    B2A
    B2B
    B2_PRODUCT_EXACT_SOLVER

20-scale:
    fail-closed guard with max_direct_tasks < 20
    selected direct20 probe with B0/B1A/B1B/B2A/B2B/B2_PRODUCT_EXACT_SOLVER
    full direct-DP product run if budget permits

30-scale:
    fail-closed diagnostic
    limited-pricing diagnostic if useful
```

### 5.2 Mandatory row fields

```text
scale
instance_id
mode
baseline_name
candidate_name
certificate_scope
algorithm_status
pricing_state
uses_true_dual_bpc_certificate
exact_solution_by_valid_scope
B0_direct_objective
root_lp_bound
root_lp_bound_official
root_bound_le_B0_objective
integral_root
pricing_round_count
final_judge_call_count
negative_search_call_count
proof_mode_call_count
time_to_first_negative
candidate_negative_count
addable_negative_count
selected_count
added_to_master_count
duplicate_only_count
hidden_negative_count
labels_generated
labels_extended
labels_pruned_by_resource
labels_pruned_by_time_window
labels_pruned_by_dominance
labels_pruned_by_completion_bound
cache_hit_count
cache_miss_count
manual_rc_audit_pass
pricing_rc_audit_pass
proof_debt_unreleased_count
wall_time
fail_closed_reason
```

### 5.3 Summary metrics

```text
exact_solution_count_by_valid_scope
DIRECT_DP_FIXED_GRAPH_OPTIMAL_count
BPC_NODE_LP_CERTIFIED_count
BPC_TREE_OPTIMAL_count
fail_closed_count
timeout_count
mean_wall
p90_wall
mean_pricing_rounds
mean_final_judge_calls
mean_time_to_first_negative
mean_labels_generated
candidate_negative_count
addable_negative_count
selected_count
added_to_master_count
duplicate_only_count
hidden_negative_count
root_bound_gt_B0_violation_count
manual_rc_fail_count
pricing_rc_fail_count
direct_root_official_leak_count
proof_debt_unreleased_certified_count
```

---

## 6. Acceptance criteria

### 6.1 Redlines

B2 cannot be accepted if any of these are nonzero:

```text
root_bound_gt_B0_violation_count
direct_root_official_leak_count
manual_rc_fail_count
pricing_rc_fail_count
certificate_scope_regression_count
objective_mismatch_count
b1_5scale_regression_count
proof_debt_unreleased_certified_count
```

### 6.2 Product solver acceptance

B2_PRODUCT_EXACT_SOLVER accepted if:

```text
5-scale exact_solution_by_valid_scope = 20/20
10-scale exact_solution_by_valid_scope = 20/20 or selected5/5 before full
20-scale exact_solution_by_valid_scope = 20/20 or selected direct20 all solved before full
all scopes reported correctly
no BPC certificate leakage
```

Valid exact scopes:

```text
DIRECT_DP_FIXED_GRAPH_OPTIMAL
BPC_NODE_LP_CERTIFIED with integral_root=true
future BPC_TREE_OPTIMAL
```

If 20-scale is solved only by direct-DP, that is accepted for product exactness but not for BPC proof progress.

### 6.3 B2A acceptance

B2A accepted if:

```text
5-scale no regression vs B1A
10-scale selected/full significantly faster than B1A
root LP bound identical to B1A when both certified
certificate scope identical
full-universe RC audit gates pass
```

### 6.4 B2B acceptance

B2B accepted only if:

```text
5-scale no regression vs B1B
and at least one 10-scale or selected 20-scale improvement exists:
    timeout -> BPC_NODE_LP_CERTIFIED
    or wall time lower
    or final_judge_call_count lower
    or pricing_round_count lower
    or labels_generated lower
    or time_to_first_negative lower
without any redline violation.
```

If B2B only matches B1B on 5-scale and still times out on 10/20, it remains diagnostic.

### 6.5 Entry to B3

B3 can start only under one of these conditions:

```text
Condition A:
    B2B accepted as seeded-CG baseline.

Condition B:
    B2_PRODUCT_EXACT_SOLVER accepted for 5/10/20 exact solution,
    and B3 explicitly uses current best accepted BPC baseline rather than B2B.
```

If B2B is not accepted, B3 cannot inherit B2B as baseline.

---

## 7. Implementation tasks for Codex

### Task 1: Update B2 solver mode separation

Implement or verify:

```text
B2A_FULL_UNIVERSE_RC_AUDIT
B2B_SEEDED_TAIL_CG
B2C_LIMITED_PRICING_DIAGNOSTIC
B2_PRODUCT_EXACT_SOLVER
```

### Task 2: Split pricing into negative-search and proof-mode

Add interfaces:

```text
run_negative_search_pricing(...)
run_proof_mode_final_judge(...)
```

Guarantee:

```text
negative-search cannot certify no-negative.
```

### Task 3: Add full pricing profiling

Emit counters for every pricing call.

### Task 4: Add B2 product solver

It must return best valid exact scope among direct-DP and BPC proof.

### Task 5: Expand ablation runner

Include 5/10/20/30 real instances and all B2 modes.

### Task 6: Generate report

Report must clearly answer:

```text
Did B2 produce a usable 5/10/20 exact solver?
How many results are direct-DP exact vs BPC certified?
Did B2A improve full-universe audit cost?
Did B2B improve seeded-CG on 10/20?
What is the main remaining bottleneck?
Can we enter B3, and under which condition?
```

---

## 8. Why this plan is better than current B2

Current B2 first round successfully established proof-safe diagnostics and showed B2A is useful, but it also showed:

```text
addability is not the current bottleneck on solved rows;
B2B does not improve 10/20;
B1/B2 timeout before harvesting can matter;
full final-judge enumeration cost is the real next target.
```

This optimized B2 plan therefore changes the focus from “log better harvesting” to:

```text
usable exact product solver for 5/10/20;
negative-search/proof-mode separation;
final-judge enumeration cost profiling and reduction;
exact-safe full-universe audit fast path;
clear B2A vs B2B acceptance;
clean handoff to B3 only when justified.
```
