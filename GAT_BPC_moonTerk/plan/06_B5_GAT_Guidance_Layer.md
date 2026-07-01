<!--
Lunar-GAT-BPC-Exact 可消融 baseline 递增路线文档。
原则：每一层都是一个可运行 candidate baseline；只有在真实 5/10/20/30 规模消融中优于当前 best accepted baseline，才可晋级。
-->
# 06_B5_GAT_Guidance_Layer

## 0. 定位

B5 是独立的 guidance 候选层：

```text
B5 = best_accepted_exact_baseline + GAT guidance
```

B5 cannot be used to repair a broken exact baseline. If B2/B3/B4 were not accepted, B5 compares against the current best accepted exact baseline.

GAT's role:

```text
ordering
priority
finite delay advice
shadow diagnostics
probe-budget allocation
```

GAT never provides:

```text
official lower bound
certificate
fathom
prune
permanent rejection of true-RC negative
```

---

## 1. B5 core objective

B5 must show real workload improvement while preserving exact behavior:

```text
same objective
same certificate scope
same proof debt clearance
same true-dual no-negative semantics
less work or faster closure
```

B5 must not change:

```text
mathematical model
pricing universe
cut validity
branch feasibility
certificate ledger
node bound semantics
```

---

## 2. B5 rollout modes

### 2.1 B5A_shadow_only

Default first mode.

```text
GAT computes scores
scores are logged
solver ignores scores
objective/certificate identical by construction
```

Purpose:

```text
collect labels
measure top-K recall
measure false-safe risk
audit OOD / uncertainty
```

### 2.2 B5B_pricing_ordering_opt_in

GAT can reorder pricing candidates or worker seeds.

Hard rules:

```text
no candidate true-RC negative can be permanently dropped
delayed negative enters ProofDebtQueue
final judge still runs before certificate
```

### 2.3 B5C_branch_ordering_opt_in

GAT can reorder branch pair candidates.

Hard rules:

```text
branch candidate must be feasible under branch context
NO_FRACTIONAL_RF_PAIR is still not integrality proof
GAT cannot skip branch fallback
```

### 2.4 B5D_harvest_ordering_opt_in

GAT can reorder already true-RC negative candidates after addability check.

Hard rules:

```text
would_enter_master == true first
GAT priority tie-breaker only in MVP
proof debt blocks certificate if delayed
```

### 2.5 B5E_all_guidance_opt_in

Only after B5B/B5C/B5D individually pass do-no-harm.

---

## 3. Context compatibility

GuidanceHint must include:

```text
candidate_id
candidate_signature
priority
uncertainty
source
diagnostic_only
finite_delay_budget
branch_context_signature
cut_context_signature
path_option_universe_signature
reduced_cost_context_fingerprint
model_id
feature_schema_version
```

Hard rule:

```text
If branch/cut/path universe/reduced-cost context mismatches training or shadow validation scope,
GAT must fall back to shadow-only.
```

---

## 4. ProofDebtQueue integration

Whenever GAT delays a true-RC negative candidate:

```text
ProofDebtQueue.add(candidate)
```

Before any certificate:

```text
ProofDebtQueue.release_all_before_certificate()
or reprice all delayed candidates
or block certificate
```

Required counters:

```text
delayed_negative_count
released_before_certificate_count
rechecked_before_certificate_count
certificate_blocked_by_delayed_negative
delay_budget_exhausted_count
delayed_negative_caused_extra_cg_round_count
```

---

## 5. GAT labels

Shadow data must include:

```text
observed true-RC negative found by final judge
hidden-negative miss
harvest selected / not selected
candidate addability accepted / rejected
reject reason
delayed negative became proof debt
delayed negative released / repriced
active support changed
child proof CPU
branch pair win/loss under same context
pricing pressure
certificate time
no-harvest CPU
```

Splits:

```text
split by instance
split by scale
split by seed family
random-row split cannot be main claim
```

---

## 6. B5 消融实验设计

B5 must compare to current best accepted exact baseline.

### 6.1 5-scale full

Run all 20:

```text
previous_best_exact_baseline
B5A_shadow_only
B5B_pricing_ordering_opt_in
B5C_branch_ordering_opt_in if branch tree exists
B5D_harvest_ordering_opt_in if harvest baseline exists
```

Required:

```text
objective identical
certificate_scope identical
proof_debt_empty
no additional incomplete rows
```

### 6.2 10-scale selected then full

Selected 5 first, full if stable.

Metrics:

```text
wall time
pricing calls
final judge calls
RMP iterations
generated labels
added columns
node count
certificate time
top-K recall
proof debt counters
```

B5 should improve workload without changing exact result.

### 6.3 20-scale

Run:

```text
20 fail-closed guard
20 selected direct20/proof-tail probe
```

Purpose:

```text
show whether GAT reduces pricing/branch/harvest workload on hard rows
without creating certificate leakage
```

If previous baseline cannot close 20, B5 cannot claim optimal improvement. It may claim diagnostic workload improvement only if exact-safe.

### 6.4 30-scale

Diagnostic / gap workload only unless previous exact baseline can run.

Required:

```text
no certificate leak
guidance fallback if context incompatible
shadow metrics present
```

---

## 7. Required output fields

```text
scale
instance_id
mode
previous_baseline_mode
gat_mode
model_id
feature_schema_version
guidance_context_compatible
algorithm_status
certificate_scope
previous_certificate_scope
objective
previous_objective
objective_identical
certificate_scope_identical
uses_true_dual_bpc_certificate
pricing_state
proof_debt_unreleased_count
delayed_negative_count
released_before_certificate_count
delay_budget_exhausted_count
pricing_call_count
final_judge_call_count
RMP_iteration_count
generated_label_count
added_column_count
node_count
certificate_time
wall_time
wall_time_delta
topK_recall_for_final_judge_negatives
false_safe_count
permanent_drop_count
do_no_harm_pass
fallback_reason
```

---

## 8. Do-no-harm gate

B5 cannot be accepted unless:

```text
objective_mismatch_count = 0
certificate_scope_regression_count = 0
permanent_drop_count = 0
proof_debt_unreleased_count = 0 for certified rows
additional_incomplete_count = 0
false_certificate_count = 0
```

Then performance can be evaluated.

---

## 9. Improvement requirement

B5 is accepted only if it improves over previous accepted exact baseline on real 5/10/20/30 ablation:

```text
wall time decreases
or pricing calls decrease
or final judge calls decrease
or generated labels decrease
or RMP iterations decrease
or node count decreases
or certificate time decreases
```

without do-no-harm failure.

If B5 only logs shadow data:

```text
B5A may be accepted as data-collection mode,
but B5 guidance layer is not accepted as optimization.
```

---

## 10. Report requirements

Produce:

```text
runs/b5_gat_guidance_ablation/b5_gat_rows.csv
runs/b5_gat_guidance_ablation/b5_gat_summary.json
runs/b5_gat_guidance_ablation/b5_gat_report_zh.md
```

Markdown sections:

```text
1. Previous accepted exact baseline
2. GAT modes
3. Do-no-harm redlines
4. 5/10/20/30 matrix
5. Workload deltas
6. Proof debt audit
7. Top-K recall / false-safe audit
8. Context compatibility / fallback audit
9. B5 accepted? yes/no
10. If no, model/data/feature/schema repair target
```

---

## 11. Exit statement

B5 is not accepted because GAT was run. B5 is accepted only if:

```text
GAT preserves exact proof semantics
and measurably reduces search workload over the previous accepted exact baseline
on real 5/10/20/30 ablation.
```
