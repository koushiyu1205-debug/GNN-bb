# Selector Context Disambiguation 审计

日期：2026-06-13

## 目标

检查哪些 context 维度能消除 replay candidate impact 的 mixed labels。
本审计只读现有 exact-context replay candidate rows，不运行求解器。

## 结论

all_checks_pass = true
row_count = 280
label_counts = {'noop': 71, 'improved': 209}

关键结果：

- local_sequence_mixed_group_count = 5
- local_sequence_online_instance_mixed_group_count = 5
- local_sequence_online_dataset_mixed_group_count = 1
- local_sequence_online_context_hash_mixed_group_count = 0
- local_sequence_group_count = 94
- context_hash_group_count = 137

解释：task-set / sequence / online flags / instance 都不足以消除 mixed labels；
dataset 维度能减少但不能消除；只有 exact context_hash 在当前样本中消除了 mixed labels。
这支持 RMP trajectory / context coupling 根因，但 context_hash 本身太具体，
不能直接作为 production addition-before selector。

## Ladder

| Ladder | Groups | Mixed Groups | Mixed Rows |
|---|---:|---:|---:|
| local_task_set | 88 | 6 | 41 |
| local_sequence | 94 | 5 | 30 |
| local_sequence_online_flags | 94 | 5 | 30 |
| local_sequence_online_instance | 94 | 5 | 30 |
| local_sequence_online_pricing | 95 | 5 | 30 |
| local_sequence_online_cg_iter | 106 | 3 | 18 |
| local_sequence_online_dataset | 108 | 1 | 6 |
| local_sequence_online_context_hash | 137 | 0 | 0 |

## 下一步含义

当前不应把 context_hash 当作 selector。正确下一步是继续 no-certificate-effect
exact-context capture / replay，并寻找可泛化、addition-before 可见、且通过
context / instance / dataset holdout 的 context/RMP trajectory 特征。
