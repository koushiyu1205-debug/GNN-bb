# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 20
raw_proxy_branch_row_count = 10
proxy_branch_row_count = 4
filtered_out_proxy_branch_row_count = 6
proxy_context_count = 1
proxy_ranking_pair_count = 6
right_censored_proxy_ranking_pair_count = 6
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 1}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=4 spread=2.31257415 best=[5, 13] score=-6.8222623 worst=[9, 13] score=-9.13483645

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[5, 13] worse=[9, 13] gap=2.31257415 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[2, 5] worse=[9, 13] gap=2.11789062 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[5, 13] worse=[3, 16] gap=1.702274393 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[2, 5] worse=[3, 16] gap=1.507590863 reason=child_fathom_then_proxy_score right_censored=True
- node=0 depth=0 better=[3, 16] worse=[9, 13] gap=0.610299757 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[5, 13] worse=[2, 5] gap=0.19468353 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
