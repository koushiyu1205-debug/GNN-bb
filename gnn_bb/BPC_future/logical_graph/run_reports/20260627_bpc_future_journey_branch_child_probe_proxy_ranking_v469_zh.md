# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-27

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 592
raw_proxy_branch_row_count = 224
proxy_branch_row_count = 120
filtered_out_proxy_branch_row_count = 104
proxy_context_count = 15
proxy_ranking_pair_count = 336
right_censored_proxy_ranking_pair_count = 336
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 15}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 120
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 120}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=8 spread=0.610496266 best=[2, 10] score=-8.767171392 promote=False worst=[18, 20] score=-9.377667658
- node=0 depth=0 alts=8 spread=4.853142173 best=[2, 16] score=-4.179975525 promote=False worst=[16, 17] score=-9.033117698
- node=0 depth=0 alts=8 spread=4.590693908 best=[8, 16] score=-4.19918355 promote=False worst=[3, 17] score=-8.789877458
- node=0 depth=0 alts=8 spread=3.694578741 best=[10, 18] score=-4.965127342 promote=False worst=[7, 15] score=-8.659706083
- node=0 depth=0 alts=8 spread=1.376223092 best=[9, 10] score=-7.1379989 promote=False worst=[10, 19] score=-8.514221992
- node=0 depth=0 alts=8 spread=5.820154692 best=[8, 15] score=-3.195011475 promote=False worst=[2, 10] score=-9.015166167
- node=0 depth=0 alts=8 spread=1.035556292 best=[16, 18] score=-8.37312095 promote=False worst=[8, 15] score=-9.408677242
- node=0 depth=0 alts=8 spread=1.637568909 best=[5, 7] score=-7.124868233 promote=False worst=[17, 18] score=-8.762437142
- node=0 depth=0 alts=8 spread=2.67268392 best=[10, 19] score=-6.249560797 promote=False worst=[3, 19] score=-8.922244717
- node=0 depth=0 alts=8 spread=1.33985943 best=[2, 5] score=-7.335323158 promote=False worst=[17, 20] score=-8.675182588
- node=0 depth=0 alts=8 spread=0.047251308 best=[7, 9] score=-9.295666167 promote=False worst=[5, 11] score=-9.342917475
- node=0 depth=0 alts=8 spread=1.957846975 best=[5, 8] score=-6.96891255 promote=False worst=[2, 9] score=-8.926759525

## Top Proxy Ranking Pairs

- node=0 depth=0 better=[8, 15] worse=[2, 10] gap=5.820154692 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[10, 20] gap=5.8187406 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[5, 18] gap=5.700474725 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[2, 13] gap=5.610255025 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[16, 17] gap=4.853142173 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 15] worse=[10, 17] gap=4.802539558 reason=child_fathom_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 16] worse=[3, 17] gap=4.590693908 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[12, 20] gap=4.535185595 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 16] worse=[2, 11] gap=4.442720402 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[8, 16] worse=[7, 13] gap=4.436179667 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[7, 8] gap=4.35580574 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=0 depth=0 better=[2, 16] worse=[13, 19] gap=3.961104715 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
