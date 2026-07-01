# B5：GAT Guidance Layer

## 1. 目标

B5 在 B4 的 proof-safe BPC baseline 上加入 GAT guidance。

GAT 的目标是：

```text
减少 search workload；
优化 pricing candidate ordering；
优化 branch pair ordering；
优化 harvest candidate ordering；
减少无效 worker / final-judge 压力；
但不改变 exact result 和 certificate semantics。
```

GAT 不是 proof component。

---

## 2. GAT 允许做什么

GAT 可以输出：

```text
candidate priority
branch pair priority
harvest priority
finite delay hint
uncertainty
OOD / confidence diagnostics
```

GAT 可以影响：

```text
pricing search order
worker seed order
branch candidate order
harvest tie-breaker
finite delay queue ordering
```

---

## 3. GAT 禁止做什么

GAT 不允许：

```text
产生 official lower bound
产生 no-negative certificate
prune / fathom node
永久 reject true-RC negative column
mutate ColumnPool / MasterColumnView / CertificateLedger
改变 reduced-cost formula
决定 cut validity
```

---

## 4. ProofDebtQueue 集成

GAT 延迟 true-RC negative 时，必须进入 proof debt：

```text
if candidate.true_rc < -eps and GAT delays:
    ProofDebtQueue.add(candidate)
```

certificate 前必须：

```text
ProofDebtQueue.release_all_before_certificate()
```

如果仍有未释放 proof debt：

```text
certificate blocked
```

记录：

```text
delayed_negative_count
released_before_certificate_count
rechecked_before_certificate_count
certificate_blocked_by_delayed_negative
delay_budget_exhausted_count
delayed_negative_caused_extra_cg_round_count
```

---

## 5. Typed GuidanceHint

exact/bpc 只能消费不可变 typed hint：

```text
GuidanceHint:
    candidate_id
    priority
    source
    finite_delay_budget
    uncertainty
    diagnostic_only
    model_version
    feature_schema_version
```

`exact/bpc/` 不得 import：

```text
torch
checkpoint loader
GAT model
OOD model
guidance policy implementation
```

测试：

```text
test_exact_bpc_has_no_torch_import
test_guidance_cannot_construct_certificate
test_guidance_cannot_mutate_exact_state
```

---

## 6. GAT 输入图

GAT 必须保留 directed logical graph 与 path options。

节点特征：

```text
depot/task flag
xy
operation_mode
science_weight
demand
service_time
service_energy
time window
shadow indicator
thermal indicator
```

有向 pair 特征：

```text
source
target
relative geometry
pair distance
sector relation
```

path option 特征：

```text
path_type
travel_time
energy
risk
shadow_exposure
distance
```

`i -> j` 和 `j -> i` 必须区分。

---

## 7. GAT 输出头

第一版三个 head：

```text
pricing_priority_head:
    task / task-set / path-option priority

branch_priority_head:
    candidate pair priority

harvest_priority_head:
    already true-RC negative candidate ordering
```

可选后续 head：

```text
proof_tail_risk_head
candidate_addability_head
delayed_negative_debt_head
phase2_pricing_pressure_head
```

---

## 8. GAT labels

第一批 shadow labels 必须服务 solver ROI，不只看分类指标。

必须记录：

```text
observed true-RC negative found by final judge
hidden-negative miss
harvest selected / not selected
candidate addability accepted / rejected
delayed negative became proof debt / released / repriced
active support changed
child proof CPU
branch pair win/loss under same context
pricing pressure
certificate time
no-harvest CPU
```

两个必须第一批就有的 label：

```text
candidate_addability_label:
    final judge found candidate; ColumnPool accepted/rejected; reject reason.

delayed_negative_debt_label:
    GAT delayed true-RC negative; later released/repriced before certificate.
```

---

## 9. Split 规则

主 split 必须按：

```text
instance
scale
seed family
```

禁止把 random-row split 作为主结论。

random-row split 只能是 debug，不是论文 claim。

---

## 10. Do-no-harm gate

GAT 进入 opt-in 行为前，必须先通过 shadow / opt-in do-no-harm gate。

要求：

```text
1. objective identical to B4 no-GAT baseline
2. certificate scope identical to B4 no-GAT baseline
3. no true-RC negative permanently dropped
4. proof_debt_queue empty before certificate
5. no additional BPC_INCOMPLETE caused by GAT delay
6. delayed true-negative release rate reported
7. false-safe rate reported
```

只有 do-no-harm 通过后，才允许讨论：

```text
wall time improvement
pricing-call reduction
final-judge-call reduction
node-count reduction
```

---

## 11. B5 消融实验

对比：

```text
B5 = B4 + GAT guidance
vs
B4 = exact BPC without GAT
```

A/B：

```text
GAT shadow only
GAT pricing ordering opt-in
GAT branch ordering opt-in
GAT harvest ordering opt-in
GAT all-guidance opt-in
```

每个 A/B 都必须独立报告：

```text
objective_diff
certificate_scope_diff
BPC_TREE_OPTIMAL count diff
BPC_INCOMPLETE count diff
wall_time_diff
pricing_call_diff
final_judge_call_diff
generated_label_diff
RMP_iteration_diff
node_count_diff
proof_debt_metrics
```

---

## 12. 成功标准

GAT 成功必须满足两层。

### Safety success

```text
objective unchanged
certificate scope unchanged
no permanent negative drop
no extra incomplete caused by delay
proof debt cleared before certificate
```

### Performance success

在 safety success 之后，再看：

```text
wall time decreases
pricing calls decrease
final judge calls decrease
generated labels decrease
RMP iterations decrease
BPC_TREE_OPTIMAL count increases or remains same with workload reduction
```

---

## 13. 失败标准

任一情况失败：

```text
1. GAT 改变 objective。
2. GAT 改变 certificate scope。
3. GAT 延迟 true-RC negative 后 certificate 前未释放。
4. GAT 造成更多 BPC_INCOMPLETE。
5. GAT 直接修改 ColumnPool / MasterColumnView / CertificateLedger。
6. exact/bpc import torch / checkpoint / model。
7. random-row split 被用作主结论。
```

---

## 14. Codex 禁止事项

Codex 不得：

```text
先写 GAT 再补 ProofDebtQueue
让 GAT reject true-RC negative
让 GAT 生成 certificate
把 GAT shadow metric 写成 exact improvement
只报告 F1 / AUC，不报告 solver ROI
在 no-GAT baseline 不稳定时训练 GAT
```

---

## 15. 为什么 GAT 放最后

GAT 学的是 solver search policy。

如果前面的：

```text
reduced cost
ColumnPool addability
harvesting semantics
branch context
cut context
certificate ledger
```

还不稳定，GAT 学到的是移动靶。

因此顺序必须是：

```text
先固定 exact solver 语义，
再让 GAT 学怎么加速它。
```
