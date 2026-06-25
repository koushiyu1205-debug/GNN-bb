# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 84
raw_proxy_branch_row_count = 17
proxy_branch_row_count = 6
filtered_out_proxy_branch_row_count = 11
proxy_context_count = 2
proxy_ranking_pair_count = 10
right_censored_proxy_ranking_pair_count = 10
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 1, 'single_pair_context': 1}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 6
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 6}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=1 spread=0.0 best=[1, 3] score=-1.428750608 promote=False worst=[1, 3] score=-1.428750608
- node=2 depth=1 alts=5 spread=10.665966383 best=[1, 8] score=-3.41025165 promote=False worst=[1, 2] score=-14.076218033

## Top Proxy Ranking Pairs

- node=2 depth=1 better=[1, 8] worse=[1, 2] gap=10.665966383 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[8, 10] worse=[1, 2] gap=8.331990391 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 8] worse=[1, 13] gap=5.924190175 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 10] worse=[1, 2] gap=5.854384766 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 8] worse=[1, 10] gap=4.811581617 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 13] worse=[1, 2] gap=4.741776208 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[8, 10] worse=[1, 13] gap=3.590214183 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[8, 10] worse=[1, 10] gap=2.477605625 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 8] worse=[8, 10] gap=2.333975992 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=2 depth=1 better=[1, 10] worse=[1, 13] gap=1.112608558 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
