# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 24
raw_proxy_branch_row_count = 11
proxy_branch_row_count = 4
filtered_out_proxy_branch_row_count = 7
proxy_context_count = 1
proxy_ranking_pair_count = 5
right_censored_proxy_ranking_pair_count = 5
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

- node=0 depth=0 alts=4 spread=2.649503037 best=[10, 19] score=-6.667612505 worst=[3, 19] score=-9.317115542

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[10, 19] worse=[3, 19] gap=2.649503037 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[10, 19] worse=[3, 17] gap=2.646417862 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 5] worse=[3, 19] gap=1.621905592 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[1, 5] worse=[3, 17] gap=1.618820417 reason=corrected_gain_then_proxy_score right_censored=True
- node=0 depth=0 better=[10, 19] worse=[1, 5] gap=1.027597445 reason=corrected_gain_then_proxy_score right_censored=True

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
