# BPC_future 根因补充：counterfactual replay impact dataset

日期：2026-06-13

## 目标

把 exact-context counterfactual replay 的结果转成可累计的数据表，后续用于校准 returned-batch selector。

这一步仍然是 diagnostic-only：

- 不运行 solver；
- 不运行 pricing；
- 不加列；
- 不改变 certificate；
- 不更新 official lower bound；
- 不证明 production selector。

## 新增脚本

```text
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py
```

输入：

- `replay_cases.json` 或 manifest 目录；
- `replay_results.json` 或 replay result 目录。

输出：

- `summary.json`
- `candidate_impact_rows.csv`
- `treatment_impact_rows.csv`

核心字段：

- candidate descriptor：
  - task set；
  - sequence；
  - true reduced cost；
  - new / duplicate / replacement / active-support-changing class；
- local RMP treatment outcome：
  - single-candidate objective delta；
  - full-batch objective delta；
  - dual L1 delta；
  - no-op / improved / worsened impact class。

## 已跑数据集

### 1. real_capture_mt20_apollo

输入：

```text
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2/replay_cases.json
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2/replay_results.json
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo/summary.json
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo/candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo/treatment_impact_rows.csv
```

结果：

- `all_checks_pass=true`
- `case_count=1`
- `candidate_row_count=4`
- `single_candidate_with_replay_count=4`
- `high_impact_candidate_count=4`
- `noop_candidate_count=0`
- `full_batch_improved_count=1`
- `best_objective_delta=-137.116184`

解释：

- 该 real 20-task context 中，4 条 captured returned candidates 的 single-treatment replay 全部是 local RMP high-impact；
- full returned batch 也改善局部 RMP；
- 这证明 high-impact returned batch 真实存在。

### 2. duplicate_noop_smoke

输入：

```text
BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_manifest/replay_cases.json
BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_result/replay_results.json
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/summary.json
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/treatment_impact_rows.csv
```

结果：

- `all_checks_pass=true`
- `case_count=1`
- `candidate_row_count=1`
- `single_candidate_with_replay_count=1`
- `high_impact_candidate_count=0`
- `noop_candidate_count=1`
- `full_batch_improved_count=0`
- `best_objective_delta=0.0`

解释：

- 该 candidate 是 true-RC negative，但 duplicate / weak replacement；
- replay 中它对局部 RMP 是 no-op；
- 这证明 negative RC 本身不能作为 useful-column selector。

### 3. combined

新增聚合脚本：

```text
BPC_future/scripts/summarize_counterfactual_replay_impact_datasets.py
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/summary.json
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_treatment_impact_rows.csv
```

结果：

- `all_checks_pass=true`
- `dataset_count=2`
- `candidate_row_count=5`
- `high_impact_candidate_count=4`
- `noop_candidate_count=1`
- `candidate_impact_class_counts={improved: 4, noop: 1}`
- `treatment_impact_class_counts={improved: 7, noop: 4}`
- `best_objective_delta=-137.116184`

解释：

- 现在已有一个统一的 replay impact calibration table；
- 但它只有 5 条 candidate rows，其中 4 条来自同一个 real Apollo20 context；
- 因此它能证明数据链路和两端现象，但不能训练或上线 selector。

## 对根因判断的影响

这一步把两端事实放进同一种数据格式：

1. real 20-task 中存在 high-impact returned candidates；
2. true-RC negative duplicate 也可能完全 no-op。

因此当前根因不是：

- 找不到负列；
- 所有 worker negative 都没用；
- 只要 negative 就应该加；
- 只要加更多列就会优化。

更准确的根因仍然是：

> 缺少 addition-before、context-aware、可泛化、低开销的 returned-batch selector。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_manifest_v2/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_apollo_20260613/replay_result_v2/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_manifest/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/replay_result/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/summarize_counterfactual_replay_impact_datasets.py \
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo \
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke \
--output-dir BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined
```

Focused test：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_counterfactual_replay_impact_dataset_classifies_candidate_rows \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_counterfactual_replay_impact_dataset_summary_combines_examples
```

Evidence ledger：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/verify_root_cause_evidence.py \
--output-dir BPC_future/results/root_cause_evidence_ledger_20260613
```

新增 verifier check：

```text
counterfactual_replay_impact_dataset.check_impact_dataset_separates_high_impact_and_noop = true
```

## 当前边界

- 目前只有一个 real 20-task high-impact context；
- duplicate no-op 是 very_small smoke，不代表 20-task duplicate 分布；
- 该 dataset 只能用于 calibration，不是 production selector；
- 后续必须累计更多 exact-context replay cases，才能判断 selector 是否可泛化。
