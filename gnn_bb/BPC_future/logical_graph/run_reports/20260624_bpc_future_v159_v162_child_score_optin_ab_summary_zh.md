# BPC_future V159-V162 Child-Score Opt-in A/B 总结

日期：2026-06-24

## 目的

验证 `journey_child_priority_mode=child_score` 是否能在已知正例链路中安全命中，并观察它是否能降低 proof cost。该批次只读/复用 canonical random-TW 20 的 `greedy-anchor seed61001` 单实例结果，不是 20-scale 全量性能结论。

## 输入

```text
V131 baseline:
  BPC_future/results/20260624_v131_v118_context_gate_score_tailaction_depth1_signals_greedy_seed61001_140.csv

V159 child-score map:
  BPC_future/results/journey_child_score_map_v159_v114_positive_chain_20260624/journey_child_score_map.json

V160 opt-in:
  BPC_future/results/20260624_v160_v131_plus_v159_child_score_seed61001_140.csv

V161 branch-impact audit:
  BPC_future/results/journey_branch_impact_audit_v161_v160_child_score_seed61001_20260624

V162 A/B audit:
  BPC_future/results/journey_branch_score_ab_audit_v162_v160_vs_v131_child_score_20260624
```

## 结果

```text
V131: OPTIMAL, solving_time=86.296993, node_count=5, pricing_calls=41, exact_pricing_calls=18
V160: OPTIMAL, solving_time=87.754026, node_count=5, pricing_calls=41, exact_pricing_calls=18
```

日志确认 `child_score` 命中：

- root `[2,6]`：仍按 `same_vehicle` 再 `separate_vehicle` 处理。
- depth1 `[8,12]`：child-score 把顺序改成 `separate_vehicle` 再 `same_vehicle`。

V161 显示这次仍是 completion-bound tail 主导：`child_probe_row_count=4`、`total_child_completion_bound_retries=9`、`max_child_corrected_bound_gain=5.109067`。V162 显示 `selected_pair_changed_count=0`、`node_count_delta_sum=0`、`exact_pricing_calls_delta_sum=0`、`wall_improved_count=0`。

## 结论

`child_score` 运行路径是 exact-safe 的：它只改变同一 Ryan-Foster branch 下两个 child 的入队顺序，不改变 branch constraint、lower bound、剪枝、certificate 或 official bound。

但 V160 没有带来加速；它没有减少节点数、pricing 次数、exact-pricing 次数或 completion-bound tail。当前不能把 V159/V160 升级为默认策略。下一步应继续用 limited strong branching / fixed-expansion probe 采集 mixed child proof-cost 标签，再把 `child_score` 作为 shadow/opt-in 调度接口做更大范围 A/B。
