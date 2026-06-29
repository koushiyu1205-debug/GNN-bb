# V693-V694 RouteOpt/BKF Diverse Smoke8 与 Score-Protected Hybrid 诊断

## 结论

V692/V693 合计覆盖 random-TW canonical 20-scale 前 8 个 Apollo greedy-anchor 实例：

| version | rows | OPTIMAL | TIME_LIMIT | EXTERNAL_TIME_LIMIT | capped mean | <=200s OPTIMAL |
|---|---:|---:|---:|---:|---:|---:|
| V692/V693 RouteOpt full-open | 8 | 4 | 1 | 3 | `451.145286s` | 1 |

它给出两类信号：

1. 正信号：RouteOpt/BKF staged testing 能把部分 hard case 推到 OPTIMAL。
   - seed61103：V545 `EXTERNAL_TIME_LIMIT` → V692 `422.843567s OPTIMAL`
   - seed61716：V545 `245.683781s OPTIMAL` → V693 `144.396446s OPTIMAL`
   - seed61000：V545 `342.221005s OPTIMAL` → V692 `310.997477s OPTIMAL`

2. 负信号：full-open RouteOpt/BKF 会破坏 V545 已验证的好路径。
   - seed61614：V545 `344.379775s OPTIMAL` → V693 `589.554913s OPTIMAL`

因此不能直接把 RouteOpt/BKF full-open 作为 full60 默认策略。正确方向是 hybrid：

- 高置信 state-scoped score 命中时，保护 V545 score winner；
- score 缺失或低置信时，再启用 RouteOpt/BKF phased testing；
- 对已经 OPTIMAL 且有 score-covered path 的实例，要避免 depth1/depth2 被 RouteOpt 无条件改写。

## V693 Rows 5-8 结果

| instance | V693 status | wall | gap | V545 status | V545 wall | 说明 |
|---|---:|---:|---:|---:|---:|---|
| seed61410 | EXTERNAL_TIME_LIMIT | `600.020374` | `0.066532` | EXTERNAL_TIME_LIMIT | `600.020553` | 未闭环，gap 可用 |
| seed61512 | EXTERNAL_TIME_LIMIT | `600.021474` | `0.078552` | EXTERNAL_TIME_LIMIT | `600.020286` | 未闭环，gap 可用 |
| seed61614 | OPTIMAL | `589.554913` | `0.0` | OPTIMAL | `344.379775` | 明显回归 |
| seed61716 | OPTIMAL | `144.396446` | `0.0` | OPTIMAL | `245.683781` | 明显加速 |

## Rows 1-8 对比

| instance | V692/V693 | wall | V545 | V545 wall | old baseline |
|---|---:|---:|---:|---:|---:|
| seed61000 | OPTIMAL | `310.997477` | OPTIMAL | `342.221005` | EXTERNAL_TIME_LIMIT |
| seed61103 | OPTIMAL | `422.843567` | EXTERNAL_TIME_LIMIT | `600.021953` | EXTERNAL_TIME_LIMIT |
| seed61205 | TIME_LIMIT | `341.369882` | TIME_LIMIT | `340.774743` | TIME_LIMIT |
| seed61308 | EXTERNAL_TIME_LIMIT | `600.029541` | EXTERNAL_TIME_LIMIT | `600.033104` | EXTERNAL_TIME_LIMIT |
| seed61410 | EXTERNAL_TIME_LIMIT | `600.020374` | EXTERNAL_TIME_LIMIT | `600.020553` | EXTERNAL_TIME_LIMIT |
| seed61512 | EXTERNAL_TIME_LIMIT | `600.021474` | EXTERNAL_TIME_LIMIT | `600.020286` | EXTERNAL_TIME_LIMIT |
| seed61614 | OPTIMAL | `589.554913` | OPTIMAL | `344.379775` | EXTERNAL_TIME_LIMIT |
| seed61716 | OPTIMAL | `144.396446` | OPTIMAL | `245.683781` | OPTIMAL |

## V693 Branch Diagnostics

### seed61410

- status：`EXTERNAL_TIME_LIMIT`
- branch count：7
- completion-bound retry：12
- fathom：`bound=1`
- best primal：`534.597743`
- best dual：`499.030007`
- gap：`0.066532`

selected path 前缀：

| depth | pair | Phase 1 gain product |
|---:|---|---:|
| 0 | `[15,16]` | `104.290110201` |
| 1 | `[1,4]` | `270.235804998` |
| 1 | `[1,9]` | `302.702439381` |
| 2 | `[1,17]` | `356.248069487` |
| 2 | `[1,19]` | `515.837434466` |

### seed61512

- status：`EXTERNAL_TIME_LIMIT`
- branch count：8
- completion-bound retry：11
- fathom：0
- best primal：`557.840356`
- best dual：`514.020685`
- gap：`0.078552`

selected path 前缀：

| depth | pair | Phase 1 gain product |
|---:|---|---:|
| 0 | `[12,19]` | `184.124179208` |
| 1 | `[15,19]` | `78.396689456` |
| 1 | `[12,15]` | `164.601345931` |
| 2 | `[12,16]` | `73.628214864` |
| 2 | `[1,4]` | `709.250492829` |

### seed61614

V693 full-open RouteOpt：

- status：`OPTIMAL`
- wall：`589.554913s`
- branch count：7
- completion-bound retry：11
- fathom：`bound=4`, `inherited_bound=4`

V545：

- status：`OPTIMAL`
- wall：`344.379775s`
- branch count：3
- completion-bound retry：7
- fathom：`bound=4`

路径差异：

| version | branch path prefix |
|---|---|
| V545 | `[4,19] -> [1,2] -> [1,4]` |
| V693 full-open RouteOpt | `[6,18] -> [4,13] / [4,19] -> ...` |

V693 选了 Phase 1 gain product 更大的 root `[6,18]`，但完整证明更慢。这说明短预算 child LP/heuristic probe 仍不能完全代表完整 proof cost。

### seed61716

- status：`OPTIMAL`
- wall：`144.396446s`
- branch count：1
- completion-bound retry：3
- fathom：`bound=2`

selected root：

| pair | Phase 1 gain product |
|---|---:|
| `[2,16]` | `4.213998488` |

该实例说明 RouteOpt/BKF 可以显著减少 proof-tail。

## V694 Score-Protected RouteOpt

针对 seed61614 新增 opt-in：

```text
journey_branch_candidate_phased_testing_preserve_score_gate_winner_enabled=true
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon
journey_branch_candidate_score_path=V543 score rows
journey_branch_candidate_score_selection_gate_enabled=true
journey_branch_candidate_score_selection_gate_min_score=0.67
journey_branch_candidate_score_selection_gate_require_score_source=true
journey_branch_candidate_score_require_state_key=true
```

结果：

| version | status | wall | branch path prefix |
|---|---:|---:|---|
| V545 | OPTIMAL | `344.379775` | `[4,19] -> [1,2] -> [1,4]` |
| V693 full-open RouteOpt | OPTIMAL | `589.554913` | `[6,18] -> ...` |
| V694 score-protected RouteOpt | OPTIMAL | `409.229598` | `[4,19] -> [6,18] -> [4,10]` |

V694 证明：

- root score preserve 生效：root 选 `[4,19]`，score `0.74`，`preserved=true`；
- 保护 root 后确实避免了 V693 的大部分回归；
- 但 depth1/depth2 score 缺失时 RouteOpt 仍改写了 V545 的 fallback path，所以仍慢于 V545。

## 实现更新

新增 opt-in 配置：

```text
journey_branch_candidate_phased_testing_preserve_score_gate_winner_enabled
```

语义：

- 仅在 `routeopt_bkf_staged` 下生效；
- 仅当 base priority 的第一候选通过 `branch_score_selection_gate` 时生效；
- 生效时直接保留 base score winner，不执行 Phase 1/2 覆盖；
- score 缺失、低于阈值、无 source、超 width cap 时仍进入 RouteOpt/BKF phased testing。

日志新增：

- `phased_testing_preserve_score_gate_winner_enabled`
- `phased_testing_preserve_score_gate_winner_preserved`
- `phased_testing_preserve_score_gate_winner_reason`

exact-safe 边界：

- 该门只决定是否保留 branch ordering；
- 不提供 bound；
- 不提供 certificate；
- 不剪枝；
- child 仍靠 exact pricing closure。

## 当前判断

RouteOpt/BKF 不能 full-open，但仍应保留为主线组件：

1. 对 score-missing hard context，RouteOpt/BKF 能产生 `EXTERNAL_TIME_LIMIT -> OPTIMAL`。
2. 对 score-covered context，V545 state-scoped replay 仍更稳，应优先保护。
3. 对 score-missing 但已能较快 OPTIMAL 的 context，RouteOpt/BKF 可能造成回归，需要更强 gating。

下一步不应直接跑 full60 full-open。更合理的是：

1. 跑 hybrid protected smoke8/12：
   - V543 score path；
   - score gate preserve；
   - RouteOpt 只处理 score gate miss。
2. 对 seed61614 继续做 depth1 path 保护：
   - 若 base priority fallback 是 fractionality 且该节点属于 V545 已解轨迹，可考虑不强制 RouteOpt；
   - 或加入 `routeopt_only_when_tail_risk_high` gate。
3. 对 seed61410/61512 这种仍 timeout 且 gap 高的实例，转向 cuts/formulation 和 retry proof-cost。
