# Selector Context Scalar Candidate 审计

日期：2026-06-13

## 目标

检查 addition-before 可见的 context scalar 是否能替代 exact context_hash。
本审计只读 replay candidate rows，不运行求解器。

## 结论

all_checks_pass = true
row_count = 280
label_counts = {'noop': 71, 'improved': 209}

关键结果：

- base_mixed_group_count = 5
- base_instance_cg_pricing_mixed_group_count = 3
- control_objective_exact_mixed_group_count = 0
- control_objective_bin_100_mixed_group_count = 0
- context_hash_mixed_group_count = 0
- control_objective_bin_100_group_count = 107
- context_hash_group_count = 137

解释：`instance + cg_iter + pricing_kind/state` 仍然无法消除 mixed labels；
`control_objective` 精确值和 100-bin 都能在当前样本中消除 mixed labels；
它比 exact context_hash 更粗，因此是一个值得继续 holdout 的 context scalar 候选。

但这不是 production selector 证明。`control_objective` 可能只是当前 replay 样本的
context surrogate；必须先通过 context / instance / dataset holdout，再进入 full BPC A/B。

## Feature Sets

| Feature Set | Groups | Mixed Groups | Mixed Rows |
|---|---:|---:|---:|
| base | 94 | 5 | 30 |
| base_instance_cg_pricing | 107 | 3 | 18 |
| base_control_objective_exact | 115 | 0 | 0 |
| base_control_objective_bin_100 | 107 | 0 | 0 |
| base_context_hash | 137 | 0 | 0 |

## 下一步含义

下一步应优先做 calibration-only selector holdout，把 `control_objective` /
`rmp_objective_before` 与列局部特征、context family 特征组合起来测试。
在 holdout 和 full BPC A/B 之前，不应把它接成生产 selector。
