# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 152
raw_proxy_branch_row_count = 43
proxy_branch_row_count = 28
filtered_out_proxy_branch_row_count = 15
proxy_context_count = 2
proxy_ranking_pair_count = 261
right_censored_proxy_ranking_pair_count = 261
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 2}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 28
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 28}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=24 spread=5.045828992 best=[2, 3] score=-3.2641109 promote=False worst=[8, 18] score=-8.309939892
- node=0 depth=0 alts=4 spread=0.834210117 best=[1, 14] score=-3.234282108 promote=False worst=[3, 6] score=-4.068492225

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[2, 3] worse=[8, 18] gap=5.045828992 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[10, 14] gap=4.959430781 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[10, 20] gap=4.950103647 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[4, 6] gap=4.944722785 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[4, 20] gap=4.94043934 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[7, 14] gap=4.926729072 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 3] worse=[4, 14] gap=4.920309476 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[6, 14] worse=[8, 18] gap=4.863177134 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 6] worse=[8, 18] gap=4.855991667 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[6, 14] worse=[10, 14] gap=4.776778923 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[5, 6] worse=[10, 14] gap=4.769593456 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[6, 14] worse=[10, 20] gap=4.767451789 reason=child_fathom_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
