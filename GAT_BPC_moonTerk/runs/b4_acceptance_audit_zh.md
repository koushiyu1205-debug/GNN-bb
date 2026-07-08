# B4 Cut/Formulation 接受审计

## 结论

- B4A cut diagnostic 已实现并通过安全红线：accepted as diagnostic only。
- B4B root-live subset-row 未被接受：当前没有通过形成有效 live cut 收益。
- B4E pricing-formulation candidate 已被接受：接受点是 30-scale compact pricing proof-tail 的可测改善。
- 30-scale 仍不是 `BPC_TREE_OPTIMAL` 闭合；所有 30-scale B4D/B4E 结果仍属于 `DIAGNOSTIC_PRICING_FRONTIER`。

## 固定前提

- Official objective: `normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion`。
- `makespan` 只作为 metric，不进入 pricing objective。
- 5/10/20 B3B 保持 accepted exact baseline。
- 30 B3B/B4D 是 staged frontier diagnostic，不是 exact tree certificate。

## B4A/B4B Cut 线

- Artifact: `runs/b4_cut_formulation_ablation/b4_cut_report_zh.md`。
- B4A diagnostic safe: `True`。
- B4B live subset-row accepted: `False`。
- B4E cut candidate accepted: `False`。
- 5-scale B4A: 20/20 tree optimal，无证书回归。
- 10-scale B4A: 20/20 tree optimal，观测到 33 个 subset-row violation，但只作为 diagnostic signal。
- 20/30 restricted-pool diagnostic 不允许升级 `BPC_TREE_OPTIMAL`。
- redline 全部为 0，包括 objective mismatch、certificate regression、manual/pricing RC audit、cut dual sign、dominance compatibility、restricted pricing certificate leak。

## B4C/B4D Pricing Formulation 线

- Artifact: `runs/b4_pricing_formulation_diagnostic/b4_pricing_report_zh.md`。
- Full variant matrix complete: `True`。
- Tested variants: V0/V1/V2/V3/V4/V5。
- B4E pricing-formulation accepted: `True`。
- No-negative certified rows: `0`。
- 因为所有 relevant rows 仍发现负列或没有非负 dual-bound certificate，B4E 不声称 30-scale exact closure。

## 30-scale plus57 Formal Matrix 关键结果

| variant | conclusion |
| --- | --- |
| V0 current compact pricing | baseline；mean wall 534.420204s；best dual bound -0.008003885 |
| V1 endpoint+pair | 更慢且 dual bound 更松；不是接受方向 |
| V2 latest-start slot bound | 最干净收益点；mean wall 349.240056s；dual bound 与 V0 相同 |
| V3 time-window pruning | 单独使用拖尾；negative-feasibility timeout，proof 约 760s |
| V4 combined | 有同源同轮次改善；best dual bound -0.007881834；mean wall 428.457137s |
| V5 subset-row diagnostic | active-pool diagnostic only；不加 live row，不证明 no-negative |

## Accepted B4E 的精确定义

B4E 当前接受的是：

```text
latest-start slot bound / combined compact-pricing formulation strengthening
```

它改善的是 30-scale staged frontier 的 compact pricing proof-tail：

- 能减少变量/slot 或约束规模。
- 能降低同源同轮次 proof wall time。
- V4 在 same source / same round 下改善 dual bound。

它不意味着：

- 30-scale 已经得到 `BPC_TREE_OPTIMAL`。
- negative-feasibility 可以证明 no-negative。
- restricted active-pool cut/probe 可以代替 unrestricted exact pricing proof。
- subset-row cut 已经可以安全 live 化到整棵树。

## 后续进入 B5/B4.1 前置条件

- 将 V2 latest-start slot bound 作为默认轻量 strengthening candidate。
- 将 V4 combined 作为较强但更重的 diagnostic candidate。
- 不继续在 V1 endpoint+pair 单独方向耗时。
- 不把 V5 subset-row diagnostic 升级为 live cut，除非后续通过 RMP coefficient、pricing coefficient、manual RC、pricing RC、dual sign、ledger validation、completion-bound fail-closed 全链审计。
