# B0：Direct-DP Fixed-Graph Frozen Oracle

## 1. 角色定位

B0 不是新的 BPC 实现部分，而是整个 `Lunar-GAT-BPC-Exact` 的冻结对照组。

它代表当前 `GAT_BPC_moonTerk` 中已经能跑通的：

```text
fixed logical graph
fixed path-option universe
fixed lunar instance payload
exhaustive direct-DP / set-partition exact baseline
```

B0 的作用不是证明 Branch-Price-and-Cut 已经完成，而是作为后续 BPC 模块的 **oracle、校验器和消融基线**。

Codex 在实现后续模块时，必须把 B0 当成固定事实，不得改写它的目标、字段语义或证书含义。

---

## 2. B0 的 exact claim

B0 可以声明：

```text
DIRECT_DP_FIXED_GRAPH_OPTIMAL
```

其含义是：

```text
在 instance manifest 声明的固定 resource-map payload、固定 directed logical graph、固定 path-option set、固定 objective 和固定 feasibility constraints 内，direct-DP 已经完整求解 finite universe 的整数最优解。
```

它不能声明：

```text
BPC_NODE_LP_CERTIFIED
BPC_TREE_OPTIMAL
true-dual BPC certificate
```

除非后续 BPC 层真的完成 RMP dual binding、true-dual pricing closure 和 tree closure。

---

## 3. B0 的固定宇宙

B0 exact universe 必须绑定到 instance manifest，而不是绑定到口头参数：

```text
fixed depot
fixed task set
fixed resource-map payload declared by manifest
fixed directed logical graph declared by instance
fixed path-option set per ordered pair
fixed vehicle/resource parameters
fixed time windows
fixed objective function
fixed path-option dominance policy
```

当前 sp50 benchmark 可以是：

```text
50 x 50 km resource map
100 m grid
three path options per ordered pair:
    low_time
    low_energy
    low_risk
```

但算法文档中应写成：

```text
exact over the fixed resource-map payload declared by the instance manifest
```

这样未来换真实 LOLA / Diviner / M3 / LEND 数据时，不需要重写算法 exact claim，只需要 manifest 记录新的 fixed universe。

---

## 4. B0 与 BPC 的关系

B0 是后续 BPC 的 oracle，但不是 BPC 本身。

后续 BPC 版本必须与 B0 对齐：

```text
same instance payload
same depot/task set
same fleet rule
same path-option dominance policy
same objective
same earliest-service assumption
same resource constraints
same journey cost
same time-window interpretation
same max_tasks_per_trip / Q_ice / B_use / shadow limit
```

如果 BPC 与 B0 objective 不一致，Codex 必须分类原因：

```text
missing column
pricing reduced-cost bug
objective mismatch
dominance bug
path-option filtering mismatch
start-time universe mismatch
fleet/journey interpretation mismatch
```

不得通过调参掩盖不一致。

---

## 5. B0 应输出的对照指标

每个 B0 run 必须保留：

```text
instance_id
scale
status
exact_status
certificate_scope
objective
journey_count
sortie_count
route_template_count
pareto_label_count
set_partition_state_count
wall_time_sec
path_option_dominance_policy
path_option_dominance_filtered_count
infeasibility_scope_if_any
```

其中：

```text
status = DIRECT_DP_BASELINE_OPTIMAL 或 DIRECT_DP_NO_COVER 或 DIRECT_DP_TIME_LIMIT
certificate_scope = DIRECT_DP_FIXED_GRAPH_OPTIMAL 或 DIRECT_DP_NO_COVER 或 FEASIBLE_INCUMBENT_ONLY
```

---

## 6. B0 冻结规则

Codex 不得在后续模块中修改 B0 的语义。

允许：

```text
增加审计字段
增加 manifest hash
增加 path-option universe fingerprint
增加 direct-DP/BPC alignment tests
```

禁止：

```text
把 B0 的 exact_status 改写成 BPC_OPTIMAL
把 direct-DP lower bound 伪装成 BPC node bound
把 restricted RMP diagnostic bound 当 official bound
把 GAT 或 BPC 逻辑混入 direct baseline
```

---

## 7. B0 到 B1 的进入条件

进入 B1 前，Codex 必须确认：

```text
1. B0 可以稳定输出 DIRECT_DP_FIXED_GRAPH_OPTIMAL / DIRECT_DP_NO_COVER / diagnostic 状态。
2. certificate_scope 不再使用裸字符串，而应能映射到 enum。
3. B0 objective components 可被 BPC alignment tests 调用。
4. B0 column / sortie / journey cost 能作为后续 BPC oracle。
5. Task id 全程保持 string，bit mask 只能通过 TaskIndexMap。
```

---

## 8. 消融意义

B0 是所有后续版本的共同对照：

```text
B1 vs B0:
    BPC 数学宇宙和 direct-DP 是否一致。

B2 vs B0:
    tail optimization 是否仍保持 objective / certificate scope 不变。

B3 vs B0:
    branch tree closed 后的 integer incumbent 是否对齐 direct-DP integer optimum。

B4 vs B0:
    cuts 是否只改善 proof workload，而不改变 finite-universe optimum。

B5 vs B0:
    GAT 是否只减少 search workload，而不改变 exact result。
```

---

## 9. Codex 禁止事项

Codex 不得：

```text
1. 把 DIRECT_DP_FIXED_GRAPH_OPTIMAL 写成 BPC_TREE_OPTIMAL。
2. 用 B0 结果替代 BPC true-dual no-negative certificate。
3. 在 B0 里加入 GAT、branch、cut、pricing closure 逻辑。
4. 改变 B0 objective 来迎合 BPC 结果。
5. 删除 B0 / BPC alignment 所需的成本分解字段。
```

---

## 10. B0 完成定义

B0 完成的标志不是“写新代码”，而是：

```text
B0 被冻结为正式 oracle；
其 certificate scope、objective、path universe、task id、journey cost 和 manifest fingerprint 都可被后续 BPC tests 调用；
任何后续模块都不能重新解释 B0 的 optimal claim。
```
