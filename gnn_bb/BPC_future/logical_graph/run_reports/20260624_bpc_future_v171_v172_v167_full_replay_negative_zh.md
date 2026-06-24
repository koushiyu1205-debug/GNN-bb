# V171/V172 V167 Full Replay Negative Summary

## 背景

V167 runbook 共有 12 条 before-final-probe tail-action 反事实命令。此前 V168 只跑了 node1 的两个替代 pair，并由 V169/V170 证明它们是 local-only improvement hard-negative。

本轮补跑 V167 剩余 9 条命令，使已运行条目达到 11 条：

```text
runbook = BPC_future/results/journey_branch_tail_positive_runbook_v167_v166_before_final_probe_alt_pairs_20260624
ran_entries = 02-12
time_limit = 220s
instance = BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json
```

entry1 源 child-order 命令仍未补跑；它不是 alt-pair counterfactual 正例来源。

## 运行结果

11 条已跑 replay 全部为：

```text
status = EXTERNAL_TIME_LIMIT
return_code = 124
wall ~= 220s
```

没有任何 timeout-resolved、OPTIMAL 或 200s 内求优结果。

## V171 审计

```text
audit = BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_controller_audit_v171_v167_full_replay11_zh.md
log_file_count = 11
row_count = 615
EARLY_BRANCH = 447
CONTINUE_COLUMN_GENERATION = 152
BROAD_PLATEAU_FALLBACK = 16
early_branch_triggers = 28
no_column gate rows = 228
no_column gate D rows = 220
```

这说明 before-final-probe no-column early branch 在这些 replay 中非常活跃，但仍没有带来整轮完成。

## Counterfactual Delta

```text
delta = BPC_future/results/journey_tail_action_counterfactual_delta_v171_v167_full_replay11_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_action_counterfactual_delta_v171_v167_full_replay11_zh.md
matched_counterfactual_count = 5
local_tail_improved_count = 5
whole_run_improved_count = 0
local_improved_but_whole_run_not_count = 5
right_censored_counterfactual_count = 5
```

匹配到的 5 条都是 local-only hard-negative：

```text
[4,7]  -> [1,10], local_delta=-42.35, status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
[4,7]  -> [4,11], local_delta=-32.95, status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
[1,10] -> [1,15], local_delta=-17.85, status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
[1,10] -> [2,15], local_delta=-19.95, status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
[4,11] -> [1,10], local_delta=-3.25,  status EXTERNAL_TIME_LIMIT -> EXTERNAL_TIME_LIMIT
```

剩余 alt pair 没有形成可对齐的 tail-action proof-cost delta，不能当作正例或有效排序样本。

## V172 Training Rows

```text
output = BPC_future/results/journey_tail_impact_training_rows_v172_v171_full_replay11_counterfactual_20260624
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_tail_impact_training_rows_v172_v171_full_replay11_counterfactual_zh.md
training_row_count = 33
tail_action_proof_cost = 28
tail_action_counterfactual_delta = 5
y_local_tail_improved = 5
y_whole_run_improved = 0
y_local_improved_but_whole_run_not = 5
tail_label_training_ready = false
```

## 判断

V171/V172 没有产生 whole-run positive。它进一步确认：在这个 sector-wave seed61718 context 中，换局部分支 pair 可以缩短某个节点的 proof tail，但不能解决整轮 timeout。

这批数据只能作为 hard-negative catalog 和采样导航，不能作为 branch-score/GAT 的 useful-tail-reduction 正例，也不是 20-scale 加速证据。下一步应停止在同一 V167 context 上继续深挖局部 pair，转向新的 canonical 20 contexts 或更强的 whole-run intervention：root/early strong-bound pair、incumbent/cuts/formulation、或能同时降低 sibling/deeper subtree proof cost 的 child ordering。
