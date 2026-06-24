# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-24

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 28
raw_proxy_branch_row_count = 11
proxy_branch_row_count = 6
filtered_out_proxy_branch_row_count = 5
proxy_context_count = 2
proxy_ranking_pair_count = 6
right_censored_proxy_ranking_pair_count = 6
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

- node=0 depth=0 alts=3 spread=1.70866985 best=[2, 9] score=-8.110030433 worst=[4, 5] score=-9.818700283
- node=0 depth=0 alts=3 spread=0.479780508 best=[10, 18] score=-8.895945175 worst=[1, 20] score=-9.375725683

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[2, 9] worse=[4, 5] gap=1.70866985 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[2, 9] worse=[9, 10] gap=1.26924785 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[10, 18] worse=[1, 20] gap=0.479780508 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[9, 10] worse=[4, 5] gap=0.439422 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 10] worse=[1, 20] gap=0.394212966 reason=child_probe_proxy_score right_censored=True
- node=0 depth=0 better=[10, 18] worse=[1, 10] gap=0.085567542 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
