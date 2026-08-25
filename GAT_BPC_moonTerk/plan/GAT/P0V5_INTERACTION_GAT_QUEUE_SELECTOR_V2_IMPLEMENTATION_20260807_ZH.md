# P0V5 Interaction-GAT Queue Selector V2 实施说明

## 1. 当前实施状态

本研究链与 `p0v5_context_queue_portfolio_v1_20260807_r1` 完全分离。旧链的
`FAIL / INSUFFICIENT_CONTEXT_COVERAGE` 是只读输入，不会被续写、覆盖或重新解释。

V2 当前完成的是可执行研究基础设施和所有 fail-closed 契约；尚未运行昂贵的
root screen、三重复 arm matrix、训练、heldout、E2E 或 formal full100。因此，
当前没有新的 wall-time speedup 结论，也没有 research candidate。

生产默认仍是：

```text
no_cut + P0V4/P0V5 Exact + literal Q0
```

V2 始终冻结：

```json
{
  "development_only": true,
  "deployment_authorized": false,
  "production_switch_authorized": false
}
```

## 2. 核心实现

### 2.1 稀疏 Interaction Graph

实现文件：

```text
src/lunar_ice_bpc/guidance/interaction_gat_queue_v2.py
```

接口版本：

```text
feature: lunar_ice_bpc.p0v5_interaction_gat_queue_features.v2
graph:   lunar_ice_bpc.p0v5_root_interaction_graph.v1
```

构图只使用 action 前可见的实例、true dual、active task sets、branch/cut context
和 literal-Q0 previous-proof telemetry。完整任务图不再直接承担 message topology。

每个 task 的邻居为：

- active-route 共现 top-4；
- 最小旅行时间 top-4；
- active Ryan–Foster/cut 的全部强制 pair；
- self-loop。

所有关系双向化并去重，tie-break 固定为 canonical task ID。节点增加 active-column
incidence、route cardinality、branch/cut incidence；边携带共现、条件共现、三 path
option 的 time/energy/risk 摘要、时间窗兼容度以及 branch/cut flags。

graph builder 不接收 outcome 参数，也不读取 selected arm、winner 或 post-action
telemetry。非 Q0 previous policy 会把所有 previous-proof trajectory 输入清空为
missing + presence mask 0。

### 2.2 GAT-only runtime

实现文件：

```text
src/lunar_ice_bpc/guidance/interaction_gat_queue_runtime_v2.py
```

runtime policy：

```text
P0V5_ROOT_INTERACTION_GAT_SELECTOR_V2
```

调用顺序严格为：

```text
scale bypass
-> root-only lifecycle bypass
-> exact/official/V5/Q0 checks
-> manifest and immutable binding
-> graph build
-> Torch import/tensorization/checkpoint/inference
-> at most one exact-safe arm
```

因此 scale5/10/20 和 scale30/50 tree request 都会在 manifest、graph 和 Torch 前返回
同一个 Q0 request 对象。任何 schema/hash/OOD/NaN/Inf/threshold/authority 失败也返回
同一个对象。

runtime 只接受：

```json
{
  "model_kind": "gat",
  "message_passing_required": true,
  "controls_candidate_authorized": false
}
```

MLP、Linear checkpoint 无法通过 runtime manifest/checkpoint gate。

完整 BPC 不修改 frozen exact 模块，而由：

```text
scripts/run_lunar_ice_interaction_gat_acceptance_v2.py
scripts/run_p0v5_interaction_gat_full_bpc_v2.py
```

在每个 candidate fresh process 启动时，把现有 optional portfolio dispatch callable
绑定到 V2 runtime，然后原样进入标准 acceptance runner。这个 adapter 不改变 Native
binary、exact source、queue comparator 或 engine hash；Q0 side 仍直接运行标准入口。
runtime telemetry 显式记录 manifest read、graph build、model call、ranker call、Torch
first import 和 tree model call，formal small-scale 零调用不依赖间接推断。

### 2.3 Context GAT 与 controls

Context GAT 为两层 edge-aware attention，hidden 32、2 heads；每层具有 residual、
LayerNorm 和 ReLU。pooling 包含 node mean/max、learned attention pool、edge mean/max
和 context MLP。参数必须严格少于 50k，Torch 固定单线程。

MLP、Linear 获得完全相同的 node/edge/context 数值，但失去 endpoint/message
passing。它们只作为 calibration/heldout controls，不能成为 candidate。

训练脚本：

```text
scripts/train_p0v5_interaction_gat_selector_v2.py
```

脚本固定三个 GAT seeds，训练并冻结 GAT、MLP、Linear 以及 no-message、
shuffled-topology 控制。只有 GAT 可以进入 candidate manifest。GAT 若没有安全
calibration threshold，或不满足 topology contribution gate，会直接写 terminal
negative；不会回退到 MLP/Linear。

### 2.4 QGR1 conservative residual ranker

实现文件：

```text
src/lunar_ice_bpc/guidance/qgr1_residual_supervision_v2.py
scripts/train_p0v5_qgr1_residual_gat_v2.py
```

Native `QGR1DepthResidualGAT`、`1e-4` bucket 和 `sizeof(State)==176` 均未修改。
V2 supervision 在同 terminal/depth/RC-bucket action surface 内构造：

- 75% supervised mass：admitted ancestor、existing dominator、incoming dominator；
- 25% neutral mass：无已知偏好的同 action-surface pairs；
- supervised pressure weight：`sqrt(1 + group_size)`，截断为 8；
- loss：pairwise logistic + `0.1 * neutral Huber-to-zero` + `1e-5 * potential L1`。

每规模 outer-train 为 12 instances，inner split 固定 10/2。node/arc/state 三组
potential 的 ranker-inner-train absolute magnitude 75% quantile 在 wall outcome 前写入
checkpoint metadata。runtime 会硬零化低于阈值的 potential；zero/nonfinite 输出退回
literal Q0。QGR1 veto 时 runtime 不打开 ranker 文件。

pair count 也保持至少 3:1 的 supervised/neutral 比例；trace 中 supervised pair 不足时
不会用 neutral pair 填满剩余 50,000 cap。三类 supervised family 先 instance/context
等权，再施加 action-surface pressure weight。

## 3. 数据和冻结链

初始化命令：

```bash
PYTHONPATH=src:build/native-spprc-context-queue-portfolio-v1 \
python scripts/initialize_p0v5_interaction_gat_queue_selector_v2.py
```

初始化器执行：

- 验证 r1 terminal decision 和全部 r1 freeze；
- 验证 Native engine 仍为 `0480c284f7a248d6`；
- 只导入 r1 root-CG Q0 pre-action snapshots；
- 拒绝 r1 tree、任何 outcome-bearing field 和 formal hash overlap；
- 冻结 formal 001--020 以及 P0V2/P0V4/QG2-oracle/DSSR 历史 development
  content-hash blacklist；新生成 candidate 与其中任一 hash 重叠都会停止；
- 冻结 source/config/execution/acceptance/graph/formal blacklist；
- 生成现有 20+20 instances 的缺失 root-screen schedule。

root census 的执行顺序：

```bash
python scripts/run_p0v5_interaction_gat_root_screen_v2.py existing
python scripts/run_p0v5_interaction_gat_root_screen_v2.py index
python scripts/manage_p0v5_interaction_gat_census_v2.py evaluate
```

若不足，`evaluate` 会按固定 seed 和每批 5 个的规则写下一批 generation request；随后：

```bash
python scripts/run_p0v5_interaction_gat_root_screen_v2.py generate --per-scale-target 5
python scripts/run_p0v5_interaction_gat_root_screen_v2.py candidates
python scripts/manage_p0v5_interaction_gat_census_v2.py evaluate
```

`--per-scale-target` 是累计 target，最多 30。达到每规模 23 eligible instances 后：

```bash
python scripts/manage_p0v5_interaction_gat_census_v2.py finalize
```

finalize 在任何 arm outcome 前冻结：

- 每规模 12 train / 4 calibration / 4 selector-heldout / 3 development-E2E；
- train/calibration/heldout 每实例恰好两个 root contexts；
- Q0 proof milestone schedule；
- Q0/QD1/QB1 三重复 blocked schedule。

若 30 个新候选用尽仍不足，写
`FAIL / INSUFFICIENT_ROOT_GAT_COVERAGE`，且 terminal 后所有后续 writer 拒绝运行。

## 4. 阶段执行

Q0 milestone 和 fresh matched matrix 复用已经审计的单进程 replay runner：

```bash
python scripts/run_p0v5_interaction_gat_matrix_v2.py milestone \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807

python scripts/run_p0v5_interaction_gat_matrix_v2.py matrix \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807
```

QD1/QB1 admission 后，QGR1 使用独立 V2 hard-zero potential exporter 和 execution
freeze。force-on 通过后再采完整 train/calibration Q0-vs-QGR1 matrix；各 arm 使用自己的
fresh Q0 control，最后在 collapse 后合并，不把不同 block 的 Q0 wall 混作同一个 control：

```bash
python scripts/freeze_p0v5_qgr1_execution_v2.py force_on --run-root ...
python scripts/run_p0v5_interaction_gat_matrix_v2.py matrix \
  --run-root ... \
  --schedule .../qgr1_force_on_execution.freeze.json \
  --potential-index .../qgr1_force_on_potential_index.freeze.json \
  --output .../qgr1_force_on_rows.json
python scripts/finalize_p0v5_interaction_gat_stage_v2.py qgr1_force_on \
  --run-root ... --input .../qgr1_force_on_rows.json

python scripts/freeze_p0v5_qgr1_execution_v2.py full_matrix --run-root ...
python scripts/run_p0v5_interaction_gat_matrix_v2.py matrix \
  --run-root ... \
  --schedule .../qgr1_full_matrix_execution.freeze.json \
  --potential-index .../qgr1_full_matrix_potential_index.freeze.json \
  --output .../qgr1_full_matrix_rows.json
python scripts/merge_p0v5_interaction_gat_outcomes_v2.py \
  --run-root ... --base .../matched_matrix_rows.json \
  --qgr1 .../qgr1_full_matrix_rows.json
```

V2 stage finalizer：

```bash
python scripts/finalize_p0v5_interaction_gat_stage_v2.py arm_admission --input ...
python scripts/finalize_p0v5_interaction_gat_stage_v2.py qgr1_force_on --input ...
python scripts/finalize_p0v5_interaction_gat_stage_v2.py portfolio_oracle --input ...
python scripts/finalize_p0v5_interaction_gat_stage_v2.py heldout --input ...
python scripts/finalize_p0v5_interaction_gat_stage_v2.py development_e2e --input ...
python scripts/finalize_p0v5_interaction_gat_stage_v2.py formal_full100 --input ...
```

finalizer 已实现 V2 的更严格 arm gate、QGR1 reorder/scoring gate、每规模 oracle
headroom、GAT calibration topology gate、heldout GAT-vs-controls gate、development E2E
和 formal small-scale zero-call gate。

唯一 GAT、MLP/Linear controls 与 topology controls 冻结后，heldout 的执行链为：

```bash
python scripts/freeze_p0v5_interaction_gat_heldout_v2.py \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807

python scripts/run_p0v5_interaction_gat_heldout_replays_v2.py \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807

python scripts/analyze_p0v5_interaction_gat_heldout_v2.py \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807 \
  --rows runs/p0v5_interaction_gat_queue_selector_v2_20260807/heldout_distinct_action_rows.json

python scripts/finalize_p0v5_interaction_gat_stage_v2.py heldout \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807 \
  --input runs/p0v5_interaction_gat_queue_selector_v2_20260807/heldout_analysis.json
```

每个 context 的五个模型各在独立 fresh process 中作一次决定；Native 只对它们实际
选择到的 distinct actions 做三重复。analyzer 再把模型自己的 preparation tax 加回
对应 action wall，避免重复执行相同 arm，也不会把 controls 的 action 当成 candidate。

heldout 通过后，完整 BPC 命令为：

```bash
python scripts/run_p0v5_interaction_gat_full_bpc_v2.py development_e2e \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807
python scripts/finalize_p0v5_interaction_gat_stage_v2.py development_e2e \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807 \
  --input runs/p0v5_interaction_gat_queue_selector_v2_20260807/development_e2e_rows.json

python scripts/run_p0v5_interaction_gat_full_bpc_v2.py formal_full100 \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807
python scripts/finalize_p0v5_interaction_gat_stage_v2.py formal_full100 \
  --run-root runs/p0v5_interaction_gat_queue_selector_v2_20260807 \
  --input runs/p0v5_interaction_gat_queue_selector_v2_20260807/formal_full100_rows.json
```

## 5. Exact-safe 边界

V2 没有修改任何 Native/exact execution source。GAT 只能：

- 在 Q0/QD1/QB1/QGR1 中选择一个 queue action；
- 若选择 QGR1，只在同 terminal/depth/RC bucket 内改变 label 次序。

GAT 不能筛除 label、改变 dominance/bound/reduced cost、选择 cuts/branch、提前停止、
声明 global minimum 或签发 certificate。任何 incomplete/censor 仍是性能失败而不是
exact closure。

## 6. 测试

专项测试文件：

```text
tests/test_p0v5_interaction_gat_queue_selector_v2.py
```

覆盖：graph determinism、稀疏 top-k、双向/self-loop、共现 differential、强制
branch/cut edges、trajectory missing、parameter cap、permutation invariance、small/tree
pre-import bypass、GAT-only manifest、QGR1 veto no-open、V2 gates、75/25 residual pairs
、fresh-process dispatch adapter、small/tree explicit zero-call counters 以及 r1 terminal
immutability。

原有 V1/Native exact differential、QGR1 ordering surface 和 `State==176` 测试继续保留，
没有被复制成新的、较弱的正确性标准。
