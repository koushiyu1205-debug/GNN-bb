# V690 RouteOpt/BKF Dynamic-K Diverse Pool：seed61311 hard20 验证

## 结论

V690 没有在 180 秒内闭环，但它比“无效测试”更有价值：

- status：`TIME_LIMIT`
- wall：`179.889301s`
- best primal：`570.891015`
- best dual：`547.186422`
- gap：`0.041522`
- nodes：`11`
- columns：`474`

这个 best primal / gap 与 V635/V636 中 forced root `[16,17]` 的 600 秒结果一致，但 V690 在 180 秒内已经达到。说明 RouteOpt/BKF phased testing 能更早找到改善 incumbent/gap 的路径；但它仍没有解决 best dual 不动的问题。

## 对比 V635/V636

V635/V636 full replay 中：

| root pair | status | wall | gap | best primal | best dual | branch | CB retry | fathom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `[17,20]` selected | EXTERNAL_TIME_LIMIT | `600.016897` | `0.045761` | `573.426825` | `547.186422` | 35 | 38 | 0 |
| `[16,20]` alt | EXTERNAL_TIME_LIMIT | `600.016970` | `0.044568` | `572.711053` | `547.186422` | 36 | 38 | 0 |
| `[16,17]` alt | EXTERNAL_TIME_LIMIT | `600.015880` | `0.041522` | `570.891015` | `547.186422` | 28 | 39 | 9 |

V690 在 180 秒内达到：

| selected policy | status | wall | gap | best primal | best dual | nodes | fathom |
|---|---:|---:|---:|---:|---:|---:|---:|
| routeopt dynamic-K diverse | TIME_LIMIT | `179.889301` | `0.041522` | `570.891015` | `547.186422` | 11 | 4 |

所以 V690 不是 strict full-solve positive，但可以作为 `weak_gap_incumbent_positive`：

- 更早达到 V636 的 best incumbent；
- gap 与 forced `[16,17]` 一致；
- branch 数和 fathom 结构已有改善；
- best dual 没动，说明不是 proof bound 解决。

## 分支轨迹

V690 分支事件：

| depth | node | selected pair | baseline pair | selected changed | Phase 1 min gain | Phase 1 product | width balance | Phase 2 neg child |
|---:|---:|---|---|---:|---:|---:|---:|---:|
| 0 | 0 | `[8,16]` | `[1,10]` | true | `5.913583` | `161.659846144` | 56 | 0 |
| 1 | 1 | `[13,19]` | `[4,9]` | true | `3.9892665` | `66.511530417` | 57 | 0 |
| 1 | 2 | `[5,14]` | `[1,3]` | true | `14.6270631` | `431.071412105` | 58 | 0 |
| 2 | 5 | `[5,13]` | `[1,10]` | true | `3.5905825` | `17.711727688` | 52 | 0 |
| 2 | 6 | `[16,17]` | `[1,10]` | true | `2.406741227` | `12.735372834` | 58 | 0 |
| 3 | 10 | `[13,19]` | `[1,10]` | true | `5.7392135` | `43.472536407` | 91 | 0 |

root 处 `[16,17]` 也被测试了，但 `[8,16]` 的 Phase 1 gain product 更高：

| root pair | Phase 1 min gain | Phase 1 product | width balance | Phase 2 neg child |
|---|---:|---:|---:|---:|
| `[8,16]` | `5.913583` | `161.659846144` | 56 | 0 |
| `[16,17]` | `5.913583` | `143.703521911` | 45 | 0 |

这说明 phased testing 不是简单复现之前 forced replay 的 root pair，而是在当前 state 下选择了另一个双侧 LP gain 更强的 pair，并在 depth 2 继续选到 `[16,17]`。

## Retry / proof-tail 统计

事件统计：

- `journey_exact_pricing_completion_bound_retry`：9
- `journey_exact_pricing_retry`：1
- `journey_exact_pricing_retry_skipped`：4
- fathom：
  - `bound`：2
  - `inherited_bound`：2

Phase testing 统计：

- Phase 1：`ok=66`，`dynamic_k_excluded=138`
- Phase 2：`ok=49`，`dynamic_k_excluded=155`

V690 的 retry 数量远低于 V635/V636 的 38-39 次，但这部分不能直接同口径比较，因为 V690 只有 180 秒预算。后续 full600 才能判断 retry gate / phased testing 是否真正节省 total proof CPU。

## 当前解释

seed61311 的结果说明：

1. `routeopt_bkf_staged + diverse dynamic-K` 能改变 branch tree，并更快拿到更好 incumbent/gap。
2. 这个 hard case 的 root/branch 调整仍不足以闭环，因为 best dual 仍停在 `547.186422`。
3. 对这类实例，branch score 只能减少搜索浪费；要真正闭环，还需要 cuts/formulation 或更强 incumbent。

## 对主线的影响

V689 是 strict positive，V690 是 weak positive。两者合起来支持把 RouteOpt/BKF controller 继续推进，但也说明下一步不能只做 branch：

- solver 内 phased testing：继续；
- branch 标签：加入双 child gain product、gap/fathom/retry；
- full60：需要验证平均收益；
- cuts/formulation：必须并行启动，否则 best dual 不动的实例仍会 timeout。
