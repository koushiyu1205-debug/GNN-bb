# B2：Pricing-Tail Optimization Layer

## 1. 目标

B2 在 B1 root-only true-dual BPC baseline 上增加 pricing-tail 优化。

它解决的问题是：

```text
true-dual final judge 找到了 negative columns，
但这些 candidates 可能 duplicate、forbidden、branch-infeasible、cut-inconsistent、dominance-filtered，
或者无法真正进入当前 RMP，导致 tail 反复消耗时间而不推进 master。
```

B2 仍然不做：

```text
branch tree
live cuts
GAT guidance
route-order branch
support-aware selector 默认启用
complex tail scheduler 默认启用
```

---

## 2. B2 相对 B1 新增

```text
Addability-aware harvesting
Hidden-negative audit
DUPLICATE_ONLY audit
Pruning / dominance profiling counters
Completion-bound ordering / audit-only structure
Candidate addability metrics
```

B2 的核心不是“多找负列”，而是：

```text
把 true-RC negative 转化成真正能进入 master 的 useful columns。
```

---

## 3. 必须实现的模块

建议路径：

```text
src/lunar_ice_bpc/exact/bpc/pricing/harvest.py
src/lunar_ice_bpc/exact/bpc/pricing/hidden_negative_audit.py
src/lunar_ice_bpc/exact/bpc/pricing/duplicate_only_audit.py
src/lunar_ice_bpc/exact/bpc/pricing/profiling.py
src/lunar_ice_bpc/exact/bpc/pricing/completion_bounds.py
src/lunar_ice_bpc/exact/bpc/pricing/worker_seed_catalog.py
```

可复用 B1 中的：

```text
ColumnPool
MasterColumnView
ReducedCostContext
ColumnSemanticSignature
ProofDebtQueue
```

---

## 4. Harvesting 正式流程

任何 candidate 进入 harvest 选择前，必须经过：

```text
candidate journey
  -> true reduced-cost filter
  -> branch feasibility filter
  -> cut coefficient / cut feasibility filter
  -> forbidden signature filter
  -> exact duplicate signature check
  -> ColumnPool.addability_check
  -> MasterColumnView membership check
  -> would_enter_master == true
  -> harvest selector
```

`harvest_selected_count` 只允许统计：

```text
would_enter_master == true
```

的 columns。

---

## 5. MVP Harvest Selector

第一版 selector 必须保持简单：

```text
1. true_rc < -eps
2. unique full ColumnSemanticSignature
3. would_enter_master == true
4. prefer new task set
5. then strongest true reduced cost
6. cap per batch
7. log diversity metrics
```

`active_support_difference` 在 B2 中只能 log，不作为默认选择条件。

GAT priority 在 B2 中不存在；GAT 相关字段只能保留空接口。

---

## 6. AddabilityReport

`ColumnPool.addability_check()` 至少返回：

```text
is_new_signature
is_forbidden_signature
is_allowed_by_branch
is_allowed_by_cut_context
cut_coefficients
branch_signature
dominance_key
would_replace_existing
would_change_active_support
would_enter_master
reject_reason
current_master_contains_signature
pool_contains_signature
```

如果 `would_enter_master=false`，必须有 `reject_reason`。

---

## 7. DUPLICATE_ONLY 审计

`DUPLICATE_ONLY` 不能静默通过。

如果 final judge 只返回 duplicate / replacement candidates，必须触发：

```text
RMP membership audit
manual reduced-cost audit
pricing reduced-cost audit
signature coefficient audit
branch/cut coefficient mapping audit
```

分类：

```text
DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC:
    existing master column manual RC also < -eps; RMP dual binding inconsistent.

DUPLICATE_IN_POOL_NOT_IN_MASTER:
    pool has column, current node RMP does not; MasterColumnView / addability issue.

DUPLICATE_SIGNATURE_COEFFICIENT_MISMATCH:
    same signature maps to different task / branch / cut coefficients.

DUPLICATE_REPLACEMENT_ONLY:
    candidate is replacement or dominated; not proof progress.
```

`DUPLICATE_ONLY` 不得关闭 node。

---

## 8. Hidden-Negative Audit

触发条件：

```text
fast worker returned LOCAL_NO_COLUMN_UNCERTIFIED
true-dual final judge later returned FOUND_NEGATIVE
```

记录：

```text
node_id
cg_iter
worker_kind
hidden_task_set
hidden_sequence
hidden_path_signature
hidden_true_rc
hidden_column_signature
miss_reason_guess
worker_candidate_budget
worker_generated_count
final_judge_generated_count
```

可能原因：

```text
task set not generated
path profile not generated
resource precheck too aggressive
dominance too aggressive
duplicate filter conflict
branch filter mismatch
cut reduced-cost mismatch
worker budget too small
```

Hidden-negative audit 只反哺 worker seed，不改变 certificate 语义。

---

## 9. ProfilingCounter

B2 必须引入统一 profiling 对象：

```text
PruningCounter:
    labels_generated
    labels_extended
    labels_pruned_by_resource
    labels_pruned_by_time_window
    labels_pruned_by_dominance
    labels_pruned_by_completion_bound
    labels_pruned_by_branch
    labels_pruned_by_cut
    check_time_by_filter
    dominance_time
    bound_time
    queue_time
    candidate_addability_time
    candidate_duplicate_count
    candidate_addable_count
```

没有 profiling 的 optimization 只能 diagnostic，不能默认启用。

---

## 10. Completion Bound 在 B2 的边界

B2 可以实现 completion-bound 结构，但默认只允许：

```text
ordering
audit
profiling
```

不默认 pruning。

Pruning opt-in 条件：

```text
1. Direct-DP/BPC alignment 仍通过。
2. bound-on/off consistency 通过。
3. profiling shows net positive benefit。
4. no-regression smoke 通过。
```

branch context 或 cut context 非空时，completion-bound pruning 默认 fail-closed。

---

## 11. B2 消融实验

对比：

```text
B2 = B1 + pricing-tail optimization
vs
B1 = root-only BPC
```

消融开关：

```text
harvesting_off / harvesting_on
hidden_negative_audit_off / on
duplicate_only_audit_off / on
completion_bound_ordering_off / on
completion_bound_pruning_off / opt_in
```

---

## 12. B2 验收指标

必须报告：

```text
objective_diff_vs_B1
certificate_scope_diff_vs_B1
rmp_iteration_count
pricing_round_count
final_judge_call_count
found_negative_count
harvest_candidate_negative_count
harvest_addable_candidate_count
harvest_selected_count
harvest_duplicate_signature_count
harvest_forbidden_signature_count
harvest_dominance_filtered_count
duplicate_only_count
hidden_negative_count
replacement_only_round_count
```

成功不是只看 wall time，而是看：

```text
1. certificate scope 与 B1 完全一致。
2. objective 与 B1 完全一致。
3. addable selected columns 占比上升。
4. duplicate-only 不再静默。
5. RMP iterations / final-judge calls 不增加，最好下降。
6. replacement-only rounds 下降。
```

---

## 13. B2 通过标准

进入 B3 前，必须满足：

```text
1. harvesting 只选择 would_enter_master=true columns。
2. DUPLICATE_ONLY 会触发 audit。
3. Hidden-negative audit 能定位 worker miss。
4. completion-bound pruning 默认关闭或 opt-in。
5. 所有 pruning / dominance / bound 都有 profiling counters。
6. B1 和 B2 的 objective / certificate scope 一致。
7. B2 没有引入新的 BPC_INCOMPLETE。
```

---

## 14. B2 失败标准

任一情况失败：

```text
1. harvest_selected_count 包含不可进入 master 的 columns。
2. duplicate-only negative 被当作 harmless。
3. completion-bound pruning 默认开启但没有 consistency + profiling。
4. B2 改变 B1 的 objective 或 certificate scope。
5. hidden-negative 被用于 certificate。
6. worker local no-column 被升级为 no-negative proof。
```

---

## 15. Codex 禁止事项

B2 不准实现：

```text
branch tree
gat guidance
live cuts
route-order branch
support-aware selector 默认启用
complex tail scheduler 默认启用
```

先证明：

```text
true-RC negative candidates 能被正确筛成 master-addable columns。
```
