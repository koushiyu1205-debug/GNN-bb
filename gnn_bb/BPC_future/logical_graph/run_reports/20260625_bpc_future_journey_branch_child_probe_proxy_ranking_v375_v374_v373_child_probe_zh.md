# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-25

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 646
raw_proxy_branch_row_count = 226
proxy_branch_row_count = 138
filtered_out_proxy_branch_row_count = 88
proxy_context_count = 9
proxy_ranking_pair_count = 1195
right_censored_proxy_ranking_pair_count = 1195
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 7, 'has_uncensored_pair_context': 1, 'single_pair_context': 1}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 1
promotion_blocked_branch_count = 137
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 137}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=24 spread=7.054499601 best=[6, 10] score=-2.795804892 promote=False worst=[8, 13] score=-9.850304493
- node=0 depth=0 alts=16 spread=4.692602733 best=[2, 16] score=-4.0916044 promote=False worst=[10, 18] score=-8.784207133
- node=0 depth=0 alts=24 spread=2.823152457 best=[17, 18] score=-6.537260835 promote=False worst=[11, 16] score=-9.360413292
- node=0 depth=0 alts=24 spread=1.103115859 best=[16, 18] score=-8.373189033 promote=False worst=[3, 5] score=-9.476304892
- node=0 depth=0 alts=1 spread=0.0 best=[2, 12] score=-7.272180592 promote=False worst=[2, 12] score=-7.272180592
- node=0 depth=0 alts=10 spread=17.550405867 best=[3, 10] score=8.119794042 promote=True worst=[8, 13] score=-9.430611825
- node=0 depth=0 alts=13 spread=3.0350449 best=[10, 14] score=-6.355548642 promote=False worst=[1, 14] score=-9.390593542
- node=0 depth=0 alts=24 spread=5.742145516 best=[4, 16] score=-4.306152267 promote=False worst=[6, 15] score=-10.048297783
- node=0 depth=0 alts=2 spread=0.007070542 best=[11, 17] score=-6.087787983 promote=False worst=[11, 20] score=-6.094858525

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[3, 10] worse=[8, 13] gap=17.550405867 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[9, 17] gap=16.874715575 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[8, 9] gap=16.869640434 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[16, 19] gap=16.83581455 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[6, 16] gap=16.806555575 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[12, 14] gap=16.724735984 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[9, 14] gap=16.460378484 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[2, 16] gap=14.700397109 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[3, 10] worse=[3, 7] gap=14.131010809 reason=child_fathom_then_proxy_score right_censored=True better_promote=True
- node=0 depth=0 better=[6, 10] worse=[8, 13] gap=7.054499601 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[10, 11] worse=[8, 13] gap=6.75322286 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[6, 10] worse=[12, 17] gap=6.243805075 reason=child_fathom_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
