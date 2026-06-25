# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 402
raw_proxy_branch_row_count = 122
proxy_branch_row_count = 75
filtered_out_proxy_branch_row_count = 47
proxy_context_count = 4
proxy_ranking_pair_count = 770
right_censored_proxy_ranking_pair_count = 770
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 4}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 75
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 75}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=24 spread=4.936627208 best=[4, 13] score=-4.4494776 promote=False worst=[18, 20] score=-9.386104808
- node=0 depth=0 alts=24 spread=2.838798967 best=[12, 20] score=-5.94631295 promote=False worst=[2, 5] score=-8.785111917
- node=0 depth=0 alts=3 spread=1.107087717 best=[14, 17] score=-8.371379933 promote=False worst=[1, 4] score=-9.47846765
- node=0 depth=0 alts=24 spread=6.609261217 best=[8, 15] score=-2.91104205 promote=False worst=[10, 20] score=-9.520303267

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[8, 15] worse=[10, 20] gap=6.609261217 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[5, 12] gap=6.406725883 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[3, 11] gap=6.078765275 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[9, 10] gap=6.037430233 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[11, 20] gap=6.0220025 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[10, 13] gap=5.961232608 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[2, 20] gap=5.951901825 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[3, 10] gap=5.925611125 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[12, 14] gap=5.742627467 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[14, 18] gap=5.658035498 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[11, 12] gap=5.631050808 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[14, 15] gap=5.569404425 reason=child_fathom_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
