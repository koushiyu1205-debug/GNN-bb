# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 36
raw_proxy_branch_row_count = 13
proxy_branch_row_count = 9
filtered_out_proxy_branch_row_count = 4
proxy_context_count = 2
proxy_ranking_pair_count = 15
right_censored_proxy_ranking_pair_count = 15
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 2}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=5 spread=0.833285092 best=[1, 14] score=-3.23451645 worst=[3, 14] score=-4.067801542
- node=2 depth=1 alts=4 spread=5.926432284 best=[1, 8] score=-3.408432283 worst=[1, 13] score=-9.334864567

## Top Proxy Ranking Pairs

- node=2 depth=1 better=[1, 8] worse=[1, 13] gap=5.926432284 reason=child_fathom_then_proxy_score right_censored=True
- node=2 depth=1 better=[1, 8] worse=[1, 10] gap=4.8142147 reason=child_fathom_then_proxy_score right_censored=True
- node=2 depth=1 better=[8, 10] worse=[1, 13] gap=3.591856342 reason=child_fathom_then_proxy_score right_censored=True
- node=2 depth=1 better=[8, 10] worse=[1, 10] gap=2.479638758 reason=child_fathom_then_proxy_score right_censored=True
- node=2 depth=1 better=[1, 8] worse=[8, 10] gap=2.334575942 reason=corrected_gain_then_proxy_score right_censored=True
- node=2 depth=1 better=[1, 10] worse=[1, 13] gap=1.112217584 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[3, 14] gap=0.833285092 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[3, 6] gap=0.8329292 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 3] worse=[3, 14] gap=0.725360334 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 3] worse=[3, 6] gap=0.725004442 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 14] worse=[1, 6] gap=0.447823058 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 6] worse=[3, 14] gap=0.385462034 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
