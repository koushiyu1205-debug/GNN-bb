# Journey Branch Child-Probe Proxy Ranking

日期：2026-06-28

## 目的

把同一 parent context 下的 child-probe proof-cost proxy 转成相对排序，用于采样导航和模型诊断。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
raw_child_probe_row_count = 272
raw_proxy_branch_row_count = 34
proxy_branch_row_count = 16
filtered_out_proxy_branch_row_count = 18
proxy_context_count = 5
proxy_ranking_pair_count = 28
right_censored_proxy_ranking_pair_count = 28
min_proxy_score_gap = 0.05
min_started_child_count = 1
context_counts = {'all_right_censored_context': 3, 'single_pair_context': 2}
min_promotion_proxy_score = 0.0
min_promotion_fathom_count = None
min_promotion_corrected_bound_gain = None
max_promotion_completion_bound_retry_count = None
max_promotion_negative_pricing_event_count = None
require_promotion_complete_label = False
promotion_ready_branch_count = 0
promotion_blocked_branch_count = 16
promotion_blocked_reason_counts = {'proxy_score_below_promotion_threshold': 16}
sampling_navigation_ready = True
ranking_training_ready = False
production_ready = False
certificate_effect = False
official_bound_effect = False
```

## 关键 Context

- node=0 depth=0 alts=1 spread=0.0 best=[16, 17] score=-20.885806267 promote=False worst=[16, 17] score=-20.885806267
- node=1 depth=1 alts=4 spread=9.617900208 best=[1, 10] score=-8.652006892 promote=False worst=[1, 3] score=-18.2699071
- node=3 depth=2 alts=3 spread=17.091070335 best=[1, 13] score=-8.294076248 promote=False worst=[1, 10] score=-25.385146583
- node=4 depth=2 alts=7 spread=15.878820763 best=[5, 8] score=-5.470638633 promote=False worst=[1, 13] score=-21.349459396
- node=10 depth=3 alts=1 spread=0.0 best=[5, 8] score=-16.762501825 promote=False worst=[5, 8] score=-16.762501825

## Top Proxy Ranking Pairs

- node=3 depth=2 better=[1, 13] worse=[1, 10] gap=17.091070335 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[5, 8] worse=[1, 13] gap=15.878820763 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=3 depth=2 better=[1, 3] worse=[1, 10] gap=15.4426493 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[13, 19] worse=[1, 13] gap=13.501659321 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[1, 3] worse=[1, 13] gap=12.690999963 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[1, 2] worse=[1, 13] gap=12.674093188 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[1, 19] worse=[1, 13] gap=12.576385029 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[1, 9] worse=[1, 13] gap=11.933039613 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[1, 10] worse=[1, 3] gap=9.617900208 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[1, 6] worse=[1, 3] gap=9.569413992 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=1 depth=1 better=[3, 10] worse=[1, 3] gap=9.054703542 reason=child_probe_proxy_score right_censored=True better_promote=False
- node=4 depth=2 better=[5, 8] worse=[1, 9] gap=3.94578115 reason=corrected_gain_then_proxy_score right_censored=True better_promote=False

## 使用边界

这些 rows 是 right-censored proxy，不是 full replay / timeout-resolved 标签；只能用于决定下一批 longer probe / replay 优先级。
它们不能作为剪枝依据、no-negative certificate、official bound、exact pricing 替代品，也不应直接接入生产 branch score map。
