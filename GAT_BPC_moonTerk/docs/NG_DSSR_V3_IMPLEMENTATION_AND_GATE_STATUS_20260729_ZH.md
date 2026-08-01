# ng-DSSR V3 实施与否决门槛报告

日期：2026-07-29

## 结论

ng-DSSR V3 已作为独立、默认关闭的候选完成实现、安全测试和冻结
scale20/011 尾部 dual 的 matched replay。结果不支持继续：

- `k=6/10/14` 三个具有真实 ng-route 松弛的候选均未在门槛预算内
  exact closed；
- 三者都在第一次 ng relaxation 内超时，尚未进入任何
  counterexample refinement；
- `k=20` 能 exact closed，但它包含全部 `20×20=400` 个 memory
  relation，等价于 full-elementary 结构对照，不再是有效松弛；
- 因此 `promotion_allowed=false`，不运行 scale30 sentinel，不运行
  六规模验证，不建立 freeze，也不改变 P0 V3。

机器可读结论：

```text
runs/ng_dssr_v3_development_20260729/scale20_011_summary.json
```

最终 replay 的 request binding 全部匹配，汇总时绑定的当前 engine
hash 为：

```text
native_rcspp_host              4946976f382cf9a8
native_rcspp_ng_dssr_v3_host   fe11e6e58721fa40
```

## 实现边界

新 policy：

```text
multi_sortie_ng_memory_counterexample_refinement_v3
```

新 backend：

```text
native_rcspp_ng_dssr_v3_inprocess
native_rcspp_ng_dssr_v3_host
```

实现保持以下 exact-safe 边界：

1. 仅允许 exact-proof pricing 使用；
2. 所有公开负列必须通过全 journey task sequence 的 elementarity
   审计；
3. non-elementary 路线只产生局部 memory relation，不公开为列；
4. 只有本轮搜索 exhaustive、frontier empty、zero label drop 且没有
   负路线时，才允许 DSSR relaxation certificate；
5. timeout、memory limit 和 refinement stall 全部 fail closed；
6. 强制 Q0，关闭 guidance、completion bound、subset dominance 和
   proof-potential trace；
7. branch task 的完整 visited bits 仍进入 dominance key，cut state
   必须相同才允许 dominance；
8. 不改变合法路线宇宙、reduced cost、bound、pruning 或 certificate
   语义。

## ng memory 与局部细化

每个 task `i` 有一个局部 memory set `N_i`。状态沿路径扩展到 task
`j` 时按以下关系更新：

```text
Π(P + j) = (Π(P) ∩ N_j) ∪ {j}
```

若下一 task 已存在于当前 `Π(P)`，则该扩展被禁止。初始 `N_i` 使用
确定性的 symmetric travel-time 最近邻：

```text
score(i,j) = min(time(i,j), time(j,i))
tie break = task ID
```

审计发现重复 task `v` 的 cycle 后，把 `v` 加入 cycle 上各中间
host task 的 memory set。这样只增加阻断该反例所需的局部关系，而
不是像 DSSR V1/V2 一样把 task 提升为所有状态都记录的 global
critical task。

这一实现对应 ng-route relaxation 与 decremental state-space
relaxation 的标准组合思路。算法依据见：

```text
Pecin et al., Improved branch-cut-and-price for capacitated vehicle
routing, technical report:
https://bib-di.inf.puc-rio.br/ftp/pub/docs/techreports/13_11_pecin.pdf
```

## P0 状态大小保护

V3 没有扩大 P0 的 Native label state。实现复用一个互斥辅助区：

```text
P0:
  positive_task_dual_reward + last_model_arc_index

ng-DSSR V3:
  ng memory bitset
```

V3 强制关闭会读取 P0 辅助字段的 completion/trace/guidance 路径。
编译期和运行测试均固定：

```text
label_state_bytes = 200
```

此外 V3 现在是默认关闭的编译期插件：

```text
LUNAR_SPPRC_ENABLE_NG_DSSR_V3=OFF  # P0/正式 build 默认值
LUNAR_SPPRC_ENABLE_NG_DSSR_V3=ON   # 仅隔离 development build
```

默认 `OFF` 时，`ng_dssr_active()` 是编译期常量 false，P0 热路径中的
ng repeat、memory update、cut-state 额外比较和 trace 分支会被编译器
直接消除。build info 明确返回：

```text
ng_dssr_v3_compiled = false
ng_dssr_v3_policy = disabled
```

因此正式 P0 不增加 per-label memory，也不承担失败候选的运行时分支。

## Binding 与 telemetry

以下字段进入 request、engine/config hash 和
`CanonicalSolveBindingV2`：

```text
ng_dssr_initial_neighborhood_size
dssr_policy_version
dssr_negative_batch_target
```

新增 telemetry：

```text
ng_dssr_enabled
ng_dssr_initial_neighborhood_size
ng_dssr_initial_relation_count
ng_dssr_final_relation_count
ng_dssr_relation_add_count
ng_dssr_forbidden_cycle_count
ng_dssr_full_elementary_fallback_count
```

iteration trace 还记录每轮 relation count、relation add 和 forbidden
cycle count。host IPC、replay 和正式 labeling facade 使用同一字段。

## 测试

隔离 build：

```text
build/native-spprc-ng-dssr-v3       # V3=ON
build/native-spprc-p0-no-ng-v3      # V3=OFF
```

最终结果：

```text
CTest: 2/2 passed
Pytest: 109 passed, 24 subtests passed
```

V3 新增覆盖：

- elementary negative batch；
- non-elementary cycle 的局部 relation refinement；
- relaxed no-negative certificate；
- full-memory 与 P0 的 exact result 对照；
- branch + SRI cut context；
- host IPC 和 canonical binding；
- timeout/memory fail-closed、zero certificate leak；
- 正式 labeling facade 接线；
- Q0/禁用 completion/subset dominance 的运行约束；
- `label_state_bytes == 200`。

## 冻结 sentinel 实验

来源：

```text
instance:
  lunar_ice_sp50_020_011_seed829011
content hash:
  99fe0d93672e1dc9
probe:
  runs/p0v3_six_scale_full120_baseline_20260727/slots/
  scale_020/instance_011/attempt_01/scale_020/pools/
  scale_020/instance_011/stage_001/probe.json
```

方法：

- 同一 source、同一真实 P0 tail dual、同一 branch/cut context；
- matched host execution；
- memory limit 8 GiB；
- 每组重新跑同代码 P0；
- `k=6/10/14` 使用统一的 60 秒确定性否决预算；
- `k=20` 是 full-elementary structural control；
- 候选必须 exact closed、zero drop、binding match 且
  `wall <= 1.10×P0`；
- full-memory control 不属于有效 relaxation candidate。

结果：

| k | 角色 | P0 wall | V3 wall | 比率或删失下界 | 状态 | max bucket | dominance checks |
|---:|---|---:|---:|---:|---|---:|---:|
| 6 | ng candidate | 17.195s | 60.166s | >3.499× | TIMEOUT | 35,445 | 3,259,882,242 |
| 10 | ng candidate | 17.139s | 60.217s | >3.514× | TIMEOUT | 33,798 | 3,097,480,996 |
| 14 | ng candidate | 17.285s | 60.327s | >3.490× | TIMEOUT | 20,229 | 3,647,688,130 |
| 20 | full-elementary control | 17.568s | 18.442s | 1.0498× | COMPLETE | 5,853 | 1,307,268,464 |

所有行：

```text
request_bindings_match = true
labels_dropped = false
```

但 `k=6/10/14` 均为：

```text
dssr_iteration_count = 1
dssr_refinement_count = 0
ng_dssr_relation_add_count = 0
```

这说明失败发生在任何可训练或可改进的 refinement 决策之前。真实
瓶颈是 relaxed dominance key 把大量不同 full visited histories
合并进很大的 ng-memory bucket，导致 quadratic-like candidate
comparisons。它不是错误的 critical-task 选择，也不是需要 GAT 学习
cycle relation 的问题。

## 最终处置

```text
P0 V3:
  unchanged

DSSR V1:
  failed historical candidate

DSSR V2:
  failed development candidate

ng-DSSR V3:
  exact-safe implementation retained, default off,
  terminated before scale30

production no_cut:
  unchanged
```

不能把 `k=20` 的结果解释成 ng-DSSR 成功：它没有放松 elementarity，
并且比 P0 慢约 5%。继续把 `k` 调到 18/19 只会在“几乎 P0”附近为
该单个 development sentinel 调参，既没有可归因的松弛收益，也会
扩大过拟合风险。

## P0 编译隔离差分

第一次把 V3 运行时分支直接编入同一个 binary 后，3 次交替测量显示
P0 native wall 从旧 build 的 15.927 秒均值增加到 16.324 秒，约
`1.025×`。虽然 exact 工作量完全相同，这仍不满足基准零侵入要求。

加入默认 `OFF` 的编译 gate 后，再做 3 组严格交替测量：

| build | host wall mean | native wall mean |
|---|---:|---:|
| 旧 DSSR V2 build | 16.520811s | 15.726904s |
| 当前 V3=OFF P0 build | 16.485019s | 15.664868s |

对应：

```text
host mean ratio   = 0.997834
native mean ratio = 0.996055
exact semantics match = true
processed/extended labels match = true
P0 compile gate = PASS
```

证据：

```text
runs/ng_dssr_v3_development_20260729/
  p0_compile_gate_final_differential/
```

本结果同时给出一个重要的 GAT 边界：GAT 不应放在首次 ng-route
relaxation 的逐 label 操作或 memory-relation 选择上。这里连第一轮
都无法以可接受成本完成，任何 per-label/高频模型调用只会进一步增加
开销。后续若继续 GAT，只应回到低频、已有合法候选上的一次性排序
动作，并在训练前先通过 matched exact oracle 的净收益下界。
