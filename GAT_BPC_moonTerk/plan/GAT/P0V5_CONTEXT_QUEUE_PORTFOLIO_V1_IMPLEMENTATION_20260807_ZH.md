# P0V5 Context Queue Portfolio V1 实施说明

## 1. 实施状态与研究边界

本链是在 `P0V4 + V5 Bidirectional Exact` 之上新增的独立 development-only 研究链。它没有修改 `no_cut` production default、历史 baseline registry、Q0 comparator 或证书语义，也不会自动进行 production promotion。

旧 `QG2TinyGAT` 的 `TERMINATED_NEGATIVE` 结论保持不变。新动作名为 `QGR1`，其算法表面、监督 schema、runtime policy、checkpoint 和 run root 均与 QG2 分离。

实现完成的工程范围包括：

- Native/Python `QGR1` policy 贯通；
- Q0-only previous-proof pressure features；
- GAT/MLP/Linear 输入同构的 context selector；
- manifest/hash/schema/OOD/NaN/Inf fail-closed runtime；
- scale5/10/20 pre-manifest、pre-Torch literal-Q0 bypass；
- immutable split/corpus/execution/training/acceptance freeze；
- arm admission、QGR1 force-on、portfolio oracle、heldout、development E2E 和 formal full100 gate；
- 独立 Native build：`build/native-spprc-context-queue-portfolio-v1`。

长时间 fresh-process matrix、训练、heldout、E2E 和 full100 尚需按状态机依次执行；任何后阶段脚本都不能授权跳过前置 gate。

## 2. QGR1 的精确安全实现

Native enum 为 `QGR1DepthResidualGAT`，Python policy ID 为 `QGR1`。实验队列的总序为：

```text
terminal-capable first
-> visited_count deeper first
-> floor(partial_rc / 1e-4) smaller first
-> label-state GAT score
-> exact partial_rc
-> creation_sequence_id
```

`1e-4` 是代码和 freeze 中的唯一合法 QGR1 bucket。GAT 只在 terminal class、depth 和 bucket 均相同的 label 之间生效。它不改变 label generation、dominance、completion bound、reduced cost、negative threshold、legal route universe、停止条件或 certificate。

`State` 没有新增 embedding，Native test 继续约束 `sizeof(State)==176`。现有 generic guidance telemetry 同时覆盖 QGR1：scored/nonzero labels、ordering decisions、reordered-label hash count、covered buckets 和 estimated scoring wall。

QGR1 zero-score comparator 的可观测搜索计数与 QD1 相同；正式 runtime 对 zero/nonfinite potential 不创建 QGR1 request，直接返回原始 Q0 对象。

## 3. Pre-action feature 与反馈泄漏防护

`BackendPricingRequest` 新增：

- `proof_tail_previous_queue_policy_id`；
- `proof_tail_previous_dominance_candidate_checks`；
- `proof_tail_previous_dominance_wall_sec`；
- `proof_tail_previous_max_visited_bucket_size`。

它们由 final-judge proof telemetry 进入下一轮 live context。只有上一轮确实执行 literal Q0 proof 时，previous wall、processed labels 和三项 dominance pressure 才进入 portfolio feature；上一轮是 QD1/QB1/QGR1 或 policy identity 缺失时，这些值在 tensorization 前全部变成 missing，并带 presence mask。

## 4. Runtime 决策顺序

入口为 `prepare_context_queue_portfolio_request_from_environment`。调用顺序冻结为：

```text
scale not in {30,50}                 -> same request object / Q0
not exact or not official            -> same request / Q0
not V5 fallback                      -> same request / Q0
incoming action not literal Q0       -> same request / Q0
preexisting guidance or DSSR         -> same request / Q0
manifest/authority/binding failure   -> same request / Q0
schema/hash/OOD/NaN/Inf failure      -> same request / Q0
all arms rejected or vetoed          -> same request / Q0
otherwise                            -> exactly one arm
```

scale check 位于 manifest 环境变量读取、manifest 文件访问、portfolio tensor module import 和 Torch import 之前。QGR1 ranker 只在 selector 已选择 QGR1 后加载；QGR1 被 veto 时 manifest 不要求也不会打开 ranker 文件。

runtime 记录 Torch first-import、checkpoint load、tensorization、inference 和 total preparation wall。GAT/MLP/Linear 参数上限为 50k，Torch 固定单线程。

启用 development candidate 的环境变量为：

```bash
export LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_MANIFEST=/absolute/path/research_candidate.manifest.json
export LUNAR_ICE_P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_EVALUATION_MODE=1
```

manifest 内仍必须有 `development_e2e_authorized=true`。`deployment_authorized` 和 `production_switch_authorized` 默认为 false。

## 5. 两层模型

QGR1 label ranker 复用两层 32-dim、2-head edge-aware attention，输出 node potential、arc potential 和 15 维 state coefficients。新监督构造器只保留真正落在 QGR1 action surface 上的 pair，并对 admitted ancestor、existing dominator、incoming dominator 三类赋予相同总权重。50,000 pair cap 前后均检查每条 admitted route 至少保留一个 actionable pair。

Context selector 的三个非 Q0 head 分别输出：

- benefit probability；
- conditional positive gain；
- adverse probability。

GAT、MLP 和 Linear 使用相同 node/edge/context 输入。GAT 唯一额外能力是 message passing；简单模型不会被削减 feature。训练损失实现为：

```text
benefit BCE
+ 0.5 * positive-gain Huber
+ adverse BCE
+ 0.25 * arm-vs-Q0 / arm-vs-arm pairwise logistic rank
```

训练脚本以 instance 为外层求平均，context 为实例内层求平均，repeat 已在数据集生成前折叠成 context median。

## 6. 冻结链与文件

静态配置：

```text
configs/experiments/p0v5_context_queue_portfolio_v1.json
```

初始化命令：

```bash
PYTHONPATH=src python scripts/initialize_p0v5_context_queue_portfolio_v1.py
```

默认生成：

```text
runs/p0v5_context_queue_portfolio_v1_20260807_r1/
  config.freeze.json
  source.freeze.json
  instance_split.freeze.json
  execution.freeze.json
  acceptance.freeze.json
  freeze.registry.json
  state.initial.json
  state.json
```

拆分按每个规模的 instance content hash 和固定 seed `61635` 决定，数量严格为 10/4/3/3。正式 scale5/10/20/30/50 各前 20 个实例的 content hash 写入 blacklist；任何 development/formal overlap 立即 terminal failure。

所有 source、Native binary、selected exact config、runner、analyzer、trainer 和 acceptance code SHA-256 都进入 registry。freeze 后任一漂移使后续脚本 fail closed。

## 7. Context corpus 与 matched matrix

先用本链的 Native build 采集 current-engine root context。旧 real-map snapshot 的
engine hash 与本链不一致，只保留为 diagnostic，不允许直接 replay：

```bash
PYTHONPATH=src python scripts/collect_p0v5_context_queue_portfolio_contexts.py root
```

若 root coverage 未达预冻结最低门槛，该命令返回 2，并明确要求一次固定的 tree
supplement。supplement 的 scale 只由 root coverage 决定，不读取 arm outcome：

```bash
PYTHONPATH=src python scripts/collect_p0v5_context_queue_portfolio_contexts.py tree
```

在 root collection 和必要的固定 tree supplement 完成后，用下列命令冻结 context，不可按 outcome 补选：

```bash
PYTHONPATH=src python scripts/freeze_p0v5_context_queue_portfolio_corpus.py \
  --snapshot-index runs/p0v5_context_queue_portfolio_v1_20260807_r1/context_snapshot_index.current.json
```

选择器按 root/tree、plain/branch_cut、round band、previous-Q0 pressure 做 outcome-blind round-robin；每个实例最多三个 context。生成的 `matched_qd1_qb1_execution.freeze.json` 对每个 train/calibration context 冻结三次 fresh-process block，每个 block 重新包含 Q0，arm 顺序由 state hash 轮转。

runner 输出的 canonical row 至少包含：

```json
{
  "context_id": "...",
  "instance_hash": "...",
  "scale": 30,
  "partition": "train",
  "arm": "QD1",
  "repeat": 0,
  "status": "COMPLETED",
  "wall_sec": 12.3,
  "milestone_reached": true,
  "correctness_redlines": []
}
```

每个 context/arm 必须恰好三行。双删失为 undetermined；Q0 complete 而 arm timeout/memory-limit 为 adverse；Q0 censored 而 arm complete 用 cap 作保守分母。

先冻结 Q0 target milestone，再执行 QD1/QB1 matched matrix；runner 始终只启动一个
fresh subprocess，不会并行 Native process：

```bash
PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_matrix.py milestone

PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_matrix.py matrix
```

## 8. 状态机命令

阶段决策统一使用：

```bash
PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  arm_admission --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/matched_matrix_rows.json

PYTHONPATH=src python scripts/train_p0v5_qgr1_label_gat.py \
  --trace-corpus runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_q0_trace_corpus.freeze.json \
  --output-dir runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_training

PYTHONPATH=src python scripts/freeze_p0v5_qgr1_execution.py force_on

PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_matrix.py matrix \
  --schedule runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_force_on_execution.freeze.json \
  --potential-index runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_force_on_potential_index.freeze.json \
  --output runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_force_on_rows.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  qgr1_force_on --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_force_on_rows.json

# 仅当 force-on admitted 时执行：
PYTHONPATH=src python scripts/freeze_p0v5_qgr1_execution.py supplement

PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_matrix.py matrix \
  --schedule runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_supplement_execution.freeze.json \
  --potential-index runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_supplement_potential_index.freeze.json \
  --output runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_supplement_rows.json

PYTHONPATH=src python scripts/merge_p0v5_context_queue_portfolio_rows.py \
  --primary runs/p0v5_context_queue_portfolio_v1_20260807_r1/matched_matrix_rows.json \
  --additional runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_force_on_rows.json \
               runs/p0v5_context_queue_portfolio_v1_20260807_r1/qgr1_supplement_rows.json \
  --output runs/p0v5_context_queue_portfolio_v1_20260807_r1/complete_admitted_arm_matrix.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  portfolio_oracle --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/complete_admitted_arm_matrix.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  heldout --input heldout_fresh_rows.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  development_e2e --input development_e2e_rows.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  formal_full100 --input formal_full100_rows.json
```

Performance failure can veto QD1/QB1/QGR1 by arm-scale；correctness redline terminates the whole chain。scale30 或 scale50 oracle headroom 未通过也直接 terminal，不允许跨规模平均掩盖。

## 9. Selector dataset、训练与冻结

完整 admitted-arm matrix 先转换成 context-level dataset：

```bash
PYTHONPATH=src python scripts/build_p0v5_context_queue_portfolio_training_dataset.py \
  --outcomes complete_admitted_arm_matrix.json
```

然后训练 3 models × 3 seeds：

```bash
PYTHONPATH=src python scripts/train_p0v5_context_queue_portfolio_selector.py \
  --dataset runs/p0v5_context_queue_portfolio_v1_20260807_r1/portfolio_training_dataset.freeze.json \
  --qgr1-ranker /absolute/path/qgr1_ranker.pt
```

训练脚本执行 train-only normalization/envelope、calibration-only Platt calibration 和固定 threshold grid。候选首先要求 calibration harmful activation 为零；然后严格按 worst-scale GM、combined instance-weighted GM、harmful Wilson upper、preparation p99、parameter count 排序。无零伤害 threshold 时冻结 no-op 并 terminal；不允许将 heldout 用于重选模型或 threshold。

唯一候选输出：

```text
selector_candidate.pt
selector_training/*.pt
selector_training/*.curve.json
selector_selection.decision.json
research_candidate.manifest.json
```

若 MLP/Linear 胜出，`claim_boundary` 明确限制为 queue-policy selector speedup，不声称 GAT graph advantage。

## 10. 一次性 heldout fresh

唯一模型冻结后，为每个 heldout context 启动一个全新的 selector process，先冻结一次
action；action freeze 不读取任何 heldout wall。若选择 Q0，candidate 侧写为
`Q0_SELECTED`，仍把 tensorization/import/load/inference preparation tax 加入 candidate
wall：

```bash
PYTHONPATH=src python scripts/freeze_p0v5_context_queue_portfolio_heldout.py

PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_matrix.py matrix \
  --schedule runs/p0v5_context_queue_portfolio_v1_20260807_r1/heldout_execution.freeze.json \
  --potential-index runs/p0v5_context_queue_portfolio_v1_20260807_r1/heldout_potential_index.freeze.json \
  --output runs/p0v5_context_queue_portfolio_v1_20260807_r1/heldout_fresh_rows.json

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  heldout --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/heldout_fresh_rows.json
```

`heldout_fresh_rows.json` 同时带各规模 preparation p99；heldout failure 直接 terminal，
没有 second-best model fallback，也不会重选 threshold。

heldout 通过后，完整 BPC controller 以单 Native process 串行执行预留的 3+3
development instances，每个 side 三重复；通过 gate 后写
`research_candidate.freeze.json`，再允许正式 full100 单次 paired run：

```bash
PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_full_bpc.py development_e2e

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  development_e2e \
  --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/development_e2e_rows.json

PYTHONPATH=src python scripts/run_p0v5_context_queue_portfolio_full_bpc.py formal_full100

PYTHONPATH=src python scripts/finalize_p0v5_context_queue_portfolio_stage.py \
  formal_full100 \
  --input runs/p0v5_context_queue_portfolio_v1_20260807_r1/formal_full100_rows.json
```

full100 schedule 在任何正式 outcome 前冻结 100 个 instance pair 及 hash-based arm
order；small-scale model/selector/ranker call counter 必须全为零。formal analyzer 同时
生成 scale30/50 的 instance-bootstrap GM 95% CI，只有两个规模均 strong speedup 且
CI upper `<1.0` 时，`promotion_review_metric_gate` 才为 true；依然不会自动切换 production。

## 11. 测试与当前验证

专项 Python test 覆盖：

- scale20 pre-manifest/pre-Torch identity bypass；
- 三个 selector 输入/输出 parity 和 `<50k` 参数；
- 非 Q0 previous trajectory missingness；
- QD1 单臂安装；
- QGR1 ranker contract 和 guidance binding；
- zero QGR1 potential literal Q0；
- manifest implementation hash drift literal Q0；
- QGR1 actionable supervision、三类 equal mass 和 admitted-route retention。

Native test 覆盖 QGR1 zero-score/QD1 等价、非零 exact route/RC 一致，以及 500 组 Q0/QGR1 exhaustive differential。正式实验仍需报告 objective、legal universe、global minimum、RC reconstruction、certificate 和 label-drop redline；test pass 不能替代 fresh wall evidence。
