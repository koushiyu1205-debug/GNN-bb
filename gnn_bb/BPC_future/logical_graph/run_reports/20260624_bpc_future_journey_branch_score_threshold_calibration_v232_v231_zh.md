# Journey Branch Score Threshold Calibration

日期：2026-06-24

## 目的

用已完成 branch-score A/B 审计校准 score-horizon admission 阈值。该脚本只读结果，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
raw_ab_row_count = 4
target_wall = 200.0
recommended_min_score = 1.5
official_bound_effect = false
certificate_effect = false
```

## Thresholds

- threshold>0.0: admitted=4, improved=3, regressed=1, crossed_200=3, wall_delta_sum=-321.351138
- threshold>0.25: admitted=3, improved=3, regressed=0, crossed_200=3, wall_delta_sum=-344.570842
- threshold>0.5: admitted=3, improved=3, regressed=0, crossed_200=3, wall_delta_sum=-344.570842
- threshold>1.0: admitted=3, improved=3, regressed=0, crossed_200=3, wall_delta_sum=-344.570842
- threshold>1.5: admitted=3, improved=3, regressed=0, crossed_200=3, wall_delta_sum=-344.570842
- threshold>2.0: admitted=2, improved=2, regressed=0, crossed_200=2, wall_delta_sum=-310.13427
- threshold>2.5: admitted=2, improved=2, regressed=0, crossed_200=2, wall_delta_sum=-310.13427
- threshold>3.0: admitted=1, improved=1, regressed=0, crossed_200=1, wall_delta_sum=-88.249791

## 边界

推荐阈值只用于 score-horizon 调度 admission；它不改变 exact pricing、official bound 或 node certificate。样本量仍小，不能作为 production GAT 泛化门槛。
