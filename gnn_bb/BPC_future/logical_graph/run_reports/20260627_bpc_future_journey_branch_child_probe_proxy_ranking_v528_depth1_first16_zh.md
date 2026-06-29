# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-27

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 72
raw_proxy_branch_row_count = 15
proxy_branch_row_count = 8
filtered_out_proxy_branch_row_count = 7
proxy_context_count = 2
proxy_ranking_pair_count = 11
right_censored_proxy_ranking_pair_count = 11
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
promotion_blocked_branch_count = 8
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 8}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=1 spread=0.0 best=[1, 2] score=-20.92126255 promote=False worst=[1, 2] score=-20.92126255
- node=1 depth=1 alts=7 spread=6.040173342 best=[5, 11] score=-9.092470008 promote=False worst=[1, 10] score=-15.13264335

## Top Proxy Ranking Pairs

- node=1 depth=1 better=[5, 11] worse=[1, 10] gap=6.040173342 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[10, 18] worse=[1, 10] gap=5.947171508 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 20] worse=[1, 10] gap=5.946774475 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 10] worse=[1, 10] gap=5.940872617 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[2, 10] worse=[1, 10] gap=5.939830425 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[15, 16] worse=[1, 10] gap=5.938707725 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 11] worse=[15, 16] gap=0.101465617 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 11] worse=[2, 10] gap=0.100342917 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 11] worse=[5, 10] gap=0.099300725 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 11] worse=[5, 20] gap=0.093398867 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[5, 11] worse=[10, 18] gap=0.093001834 reason=child_probe_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
