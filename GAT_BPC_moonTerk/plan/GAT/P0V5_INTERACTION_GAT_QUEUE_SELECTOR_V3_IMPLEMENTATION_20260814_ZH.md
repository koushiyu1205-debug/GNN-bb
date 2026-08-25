# P0V5 Interaction-GAT Queue Selector V3 实施说明

## 1. 状态与边界

V3 使用独立 run root：

```text
runs/p0v5_interaction_gat_queue_selector_v3_20260814/
```

V2 的 `FAIL / INSUFFICIENT_ROOT_GAT_COVERAGE` terminal 保持只读。V3 不修改 Native、exact engine、Q0 comparator、QGR1 `1e-4` bucket 或 production default。所有候选均为 development-only，不能部署或切换生产。

唯一候选是执行两层 edge-aware message passing 的 Interaction-GAT。`MLP`、`Linear`、`no_message` 和 `shuffled_topology` 各自独立训练、独立校准和独立 checkpoint，只能作为 controls。若 GAT 不具备安全收益和 message-passing 贡献，研究链必须 terminal negative。

## 2. V3 已实现的关键修正

### 2.1 Outcome-blind corpus

初始化器只读取 V2 已冻结的：

- `r1_preaction_import.freeze.json`；
- `root_screen_snapshot_index.current.json`；
- V2 terminal、source freeze、formal blacklist 和 candidate-generation provenance。

按 `(instance_content_hash, state_hash)` 去重，并逐条复验 snapshot SHA256、state、instance、engine、config、exact action policy 和 root lifecycle。冻结目标必须严格为：

| scale | instances | contexts | multiplicity |
|---|---:|---:|---|
| 30 | 25 | 39 | 12×1、12×2、1×3 |
| 50 | 25 | 61 | 1×1、12×2、12×3 |

`arm_outcomes_imported=0`、`tree_snapshots_imported=0`、`new_candidates_generated=0`。任何 formal hash overlap 均停止。

注意：V2 的 `candidate_protected_blacklist` 是“新候选生成期”黑名单，其中包含 V3 明确要求导入的历史 development instances。当前实证中，指定的 r1/V2 corpus 与该生成期列表存在预期 provenance overlap，而与 formal blacklist 为零 overlap。V3 将前者显式记录为 `legacy_candidate_generation_protected_overlap_*`，但只允许来自两个指定 source artifacts，不允许据此引入新实例。

### 2.2 Instance-first split 与统计

初始化器按照 multiplicity 硬配额执行 deterministic categorical min-cost assignment；代价同时平衡 source cohort、median round band、previous-Q0 pressure 和 active-column density，tie-break 使用 `SHA256(seed:scale:partition:instance_hash)`。

所有 train/calibration/heldout 实例使用全部自然 contexts；E2E contexts 不进入 replay、normalization、OOD、模型或 threshold。每个实例总权重恒为 1，context 权重为 `1 / instance context count`。

所有性能统计固定为：

1. context 内三重复 matched median；
2. context 内选择 action 或 oracle winner；
3. instance 内 context ratio 取 GM；
4. scale 内实例等权取 GM。

### 2.3 Interaction-GAT 与 controls

V3 保持 feature schema v2 和 graph schema v1，新增 runtime/manifest/checkpoint/dataset/corpus 版本。唯一候选网络为：

- hidden 16、2 heads、2 layers；
- edge-aware attention；
- residual、LayerNorm、ReLU、dropout 0.1；
- node mean/max、edge mean/max、attention pooling 和 context encoder；
- 参数严格少于 20k；
- Torch 单线程。

`shuffled_topology` 依据 state hash 使用固定非零 cyclic target shift，保持 source endpoints、node/edge/context values 和 edge count 不变。`no_message` 在训练和推理均关闭 message passing。两个 topology controls 不能复用 full-GAT checkpoint。

训练采用冻结的 5-fold instance-grouped CV。每 fold 同时包含两个规模，同一实例所有 contexts 不跨 fold。每个 seed/model 的 refit epoch 为五个 fold best epoch 的中位数，然后只在全部 train instances 上训练精确 epoch 数。Benefit/adverse calibration 和 gain scaling只读取 train OOF predictions；若某 arm-scale 的 benefit 或 adverse OOF label 为单类，该 arm-scale hard-veto。

### 2.4 Runtime fail-closed

V3 runtime 在任何 manifest、graph 或 Torch/model import 前执行：

```text
scale not in {30,50} -> identical Q0 object
lifecycle != root_cg -> identical Q0 object
```

通过 cheap guards 后仍需验证 runtime/manifest/checkpoint schema、model kind、message-passing authority、checkpoint/source/corpus/split/fold/normalization/OOD hashes、engine/config/action-policy binding、threshold、NaN/Inf 和 OOD。任一失败返回原始 Q0 request 对象。QGR1 scale veto 时不会打开 ranker。

## 3. 冻结状态机与命令

### Stage A：初始化冻结

所有 V3 source、test 和本说明完成后运行：

```bash
PYTHONPATH=src python scripts/initialize_p0v5_interaction_gat_queue_selector_v3.py
```

初始化会写 immutable registry、combined corpus、14/4/4/3 split、5-fold binding、QGR1 primary contexts、Q0 milestone schedule、QD1/QB1 matrix schedule 和 QGR1 force-on schedule。冻结后修改任一被登记源码会触发 `FREEZE_HASH_DRIFT`。

### Stage B/C：Base arms 与 headroom

```bash
python scripts/run_p0v5_interaction_gat_matrix_v3.py milestone \
  --run-root runs/p0v5_interaction_gat_queue_selector_v3_20260814

python scripts/run_p0v5_interaction_gat_matrix_v3.py matrix \
  --run-root runs/p0v5_interaction_gat_queue_selector_v3_20260814

python scripts/finalize_p0v5_interaction_gat_stage_v3.py arm_admission
python scripts/finalize_p0v5_interaction_gat_stage_v3.py base_oracle
```

该矩阵包含 71 个 train+calibration contexts、每 context `Q0/QD1/QB1 × 3`，合计 639 fresh processes；单 Native process 顺序执行。任一规模 oracle headroom 失败即 terminal，不训练 GAT。

### Stage D：可选 QGR1

base oracle 两规模均通过后，使用 Q0 trace corpus 训练 14 outer-train instances/scale、11/3 inner split 的 conservative residual ranker：

```bash
python scripts/train_p0v5_qgr1_residual_gat_v3.py \
  --trace-corpus runs/.../qgr1_q0_trace_corpus.freeze.json \
  --output-dir runs/.../qgr1_training \
  --run-root runs/p0v5_interaction_gat_queue_selector_v3_20260814
```

随后先生成每个 primary state 的 potential index，再用冻结的 `qgr1_force_on_execution.freeze.json` 执行 Q0/QGR1 三重复，并按 scale 独立 finalization。Surrogate 或 force-on 性能失败只 hard-veto 对应 QGR1 authority；correctness failure 终止整链。

```bash
python scripts/export_p0v5_qgr1_potentials_v3.py \
  --checkpoint runs/.../qgr1_training/qgr1_residual_label_gat_v2.pt \
  --output-dir runs/.../qgr1_force_potentials
python scripts/run_p0v5_interaction_gat_matrix_v3.py matrix \
  --schedule runs/.../qgr1_force_on_execution.freeze.json \
  --potential-index runs/.../qgr1_force_potentials/potential_index.json \
  --output runs/.../qgr1_force_on_rows.json
python scripts/finalize_p0v5_interaction_gat_stage_v3.py qgr1_force_on \
  --matrix runs/.../qgr1_force_on_rows.json
```

通过 force-on 的 scale 还必须运行全 train+calibration supplement；primary force-on outcome 不进入训练矩阵：

```bash
python scripts/freeze_p0v5_qgr1_supplement_v3.py
python scripts/export_p0v5_qgr1_potentials_v3.py \
  --checkpoint runs/.../qgr1_training/qgr1_residual_label_gat_v2.pt \
  --schedule runs/.../matched_qgr1_supplement_execution.freeze.json \
  --output-dir runs/.../qgr1_supplement_potentials
python scripts/run_p0v5_interaction_gat_matrix_v3.py matrix \
  --schedule runs/.../matched_qgr1_supplement_execution.freeze.json \
  --potential-index runs/.../qgr1_supplement_potentials/potential_index.json \
  --output runs/.../matched_qgr1_supplement_rows.json
```

### Stage E/F：Dataset、grouped-CV 与 calibration

将 admitted fresh arms 合并后构图：

```bash
python scripts/merge_p0v5_interaction_gat_outcomes_v3.py INPUT... --output runs/.../all_train_calibration_outcomes.json
python scripts/build_p0v5_interaction_gat_training_dataset_v3.py \
  --outcomes runs/.../all_train_calibration_outcomes.json
python scripts/train_p0v5_interaction_gat_selector_v3.py \
  --dataset runs/.../interaction_gat_training_dataset.freeze.json
```

训练器会为 5 model kinds × 3 seeds 生成独立 grouped-CV、OOF calibrator、refit checkpoint 和 curves。只有满足 zero harm、两规模 activation/GM 和 topology contribution gates 的 GAT 能冻结为 candidate。

### Stage G：One-shot heldout

```bash
python scripts/predict_p0v5_interaction_gat_actions_v3.py
python scripts/run_p0v5_interaction_gat_heldout_replays_v3.py
python scripts/analyze_p0v5_interaction_gat_heldout_v3.py
```

五个模型在 outcome 前选择 action，runner 只执行 `Q0 + distinct selected actions` 的三重复并共享 outcome。Analyzer 给每个模型加入自己的 preparation/load wall，按实例折叠并一次性应用 GAT-vs-simple/topology gates。失败不允许重选 seed/threshold/envelope。

### Stage H：Development-E2E 与 formal

```bash
python scripts/run_p0v5_interaction_gat_full_bpc_v3.py development_e2e
python scripts/run_p0v5_interaction_gat_full_bpc_v3.py formal_full100
```

V3 bootstrap 只替换现有可选 Python guidance dispatch，不修改 exact source。小规模与 tree 在 runtime cheap guard 返回 literal Q0。Development 通过后 research candidate hash 冻结；formal 后只写 terminal PASS/FAIL，不再训练或调整 candidate。

## 4. 审计与测试

专项测试覆盖：

- combined import count/hash/dedup；
- 25+25 split 与所有 multiplicity quotas；
- instance/context partition 和 E2E 隔离；
- instance total weight、context order invariance；
- grouped-CV instance isolation 和双规模 fold；
- independent controls、参数上限、deterministic shuffled topology；
- small-scale/tree pre-manifest identity bypass；
- instance-first admission/oracle/selected-action gates；
- V2 terminal 保持原始失败。

Native/exact differential、QGR1 comparator surface、certificate、label-drop 和 `sizeof(State)==176` 继续由未修改的既有 exact/native test suites 约束；V3 不复制或放松这些测试。

## 5. 当前实施状态

代码与冻结控制器已实现，但 Stage B 的 639 个 fresh processes 以及后续昂贵实验不会被伪装为已经完成。初始化前必须先完成专项测试；初始化成功仅表示 `READY_FOR_Q0_MILESTONE_FREEZE`，不是性能 PASS，也不构成 production authorization。
