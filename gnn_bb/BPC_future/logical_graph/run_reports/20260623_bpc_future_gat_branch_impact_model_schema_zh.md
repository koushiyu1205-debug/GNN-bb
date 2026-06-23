# BPC_future GAT Branch-Impact 模型结构与审计数据报告

日期：2026-06-23

## 目的

把当前 “GAT 找到真负列但没有减少 root/branch tail” 的问题，转成可训练的
branch-impact 监督信号。该步骤只做 offline / audit-only 模型结构和数据 schema，
不接 solver，不改变 branch decision，不运行 BPC / pricing / RMP，不产生
certificate 或 official bound。

## 新增产物

- `BPC_future/learning/branch_impact_model.py`
- `BPC_future/tests/test_gat_branch_impact_model.py`
- `BPC_future/results/journey_branch_impact_audit_20260623/branch_training_rows.jsonl`
- `BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_audit_zh.md`

## 模型结构

新增 `GATBranchImpactModel`：

- 复用 `HierarchicalOptionGAT` 编码 logical graph / task embeddings；
- 输入 Ryan-Foster pair：`branch_pair_indices = [task_i, task_j]`；
- 输入 branch candidate 特征：fractionality、same mass、support count、pool split width 等；
- 输入 RMP / branch context 特征；
- 输出 branch-impact heads：
  - `branch_priority`
  - `tail_improved`
  - `completion_bound_tail`
  - `early_branch_continues`
  - `negative_chain_continues`
  - `active_touch`
  - `inactive_only`
  - `predicted_child_negative_pricing_events`
  - `predicted_child_completion_bound_retries`
  - `predicted_child_early_branch_triggers`

该模型目标不是替代 branching rule，而是为后续 audit-only / shadow branch scoring
提供结构：学习哪个 RF pair 更可能减少后续 negative chain / CB tail，而不是只看
当前 pool width 或 fractionality。

## Exactness Boundary

```text
production_ready = false
pricing_oracle = false
branching_oracle = false
certificate_source = false
official_bound_effect = false
can_prune_branch_candidates = false
can_permanently_discard_true_rc_negative = false
default_solver_effect = false
```

因此：

- 不改变 official pricing universe；
- 不改变 `_choose_journey_branch`；
- 不改变 reduced-cost 公式；
- 不产生 lower bound；
- 不参与 no-negative certificate；
- 不允许剪掉 branch candidate；
- 后续若进入 solver，也只能先 shadow / opt-in，并且所有子节点仍必须由 exact pricing closure 证明。

## Branch-Impact 训练行

`audit_journey_branch_impact.py` 现在除原始审计外，还输出：

```text
branch_training_row_count = 11
branch_training_rows =
  BPC_future/results/journey_branch_impact_audit_20260623/branch_training_rows.jsonl
```

特征 schema：

```text
depth
candidate_count
eligible_count
has_candidate_log
branch_rank_in_top
branch_rank_in_priority_top
same_mass
fractionality
support_count
incumbent_relation_known
incumbent_relation_same
incumbent_disagreement
pool_same_allowed
pool_separate_allowed
pool_max_child_width
pool_total_child_width
pool_balance_gap
```

标签 schema：

```text
y_tail_improved
y_completion_bound_tail
y_early_branch_continues
y_negative_chain_continues
y_active_touch
y_inactive_only
y_child_negative_pricing_events
y_child_completion_bound_retries
y_child_early_branch_triggers
```

当前 11 条样本来自 4 个 root56/width/depth 探针，聚合仍显示：

```text
tail_class_counts = {'completion_bound_tail': 3, 'early_branch_continues': 7, 'negative_chain_continues': 1}
active_touch_branch_count = 5
inactive_only_branch_count = 6
total_child_negative_pricing_events = 63
total_child_completion_bound_retries = 5
total_child_early_branch_triggers = 7
```

这说明当前样本主要是失败/拖尾监督信号，还不足以训练 production model；下一步需要
继续采集能显著缩短 tail 的正 branch-impact 对照，或在 shadow 中记录未选候选的
counterfactual-like 特征。

## 当前结论

这一步让 GAT 的作用从“列 priority”扩展到“branch-impact 学习接口”，但还没有形成
20 规模加速。它解决的是可学习信号缺口，不是 solver 性能本身。

下一步应优先：

1. 用新字段重新跑 root56/depth 探针，确保 `selected` / `priority_top` 绑定实际选择；
2. 继续积累 branch outcome 样本，尤其是能减少 negative chain / CB retry 的正例；
3. 再训练/审计 branch-impact head；
4. 只在 shadow 中比较 GAT branch score 与当前 fractionality / pool_split / width 策略；
5. 若 shadow 证明能减少 tail，再考虑 default-off opt-in branch priority。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/learning/branch_impact_model.py BPC_future/tests/test_gat_branch_impact_model.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_gat_branch_impact_model
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile BPC_future/scripts/audit_journey_branch_impact.py BPC_future/tests/test_journey_branch_impact_audit.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest BPC_future.tests.test_journey_branch_impact_audit BPC_future.tests.test_gat_branch_impact_model
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/audit_journey_branch_impact.py ... --output-dir BPC_future/results/journey_branch_impact_audit_20260623 --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_branch_impact_audit_zh.md
```
