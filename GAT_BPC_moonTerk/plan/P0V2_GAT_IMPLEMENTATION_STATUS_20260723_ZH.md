# P0 V2 跨规模 GAT 优化：实施与实测状态

更新时间：2026-07-24  
P0 V2 实验 control：`FROZEN_NATIVE_LIVE_SRI_P0_OPTIMIZED_BASELINE_V2`  
binding V2 同代码 B0：`P0V2_BINDING_V2_SAME_CODE_B0_CONTROL_20260723`  
split manifest：
`c05be9fea1828b64690050f51003d9879685db6af2d78ae7c4e343774b5b5c5f`  
production 默认：`no_cut`  
GAT 实验 cut policy：root-only `P0`

## 1. 最终结论

评审后的首轮计划已经实施到它所规定的 fail-closed 边界：

- 非 ML 基础设施已实现并通过回归；
- 5/10/20/30 每规模 60 个新 accepted 实例已经生成；
- 240 个实例完成 binding V2 下的 clean B0；
- 240 个实例完成 instrumented P0 snapshot/harvest 采集；
- development、calibration、protected final test 已按 content hash 冻结；
- linear 和两层 MLP 已完成五折训练、pricing replay、harvest replay；
- OOD calibration 与模型选择严格分离；
- full80 和现有 scale50/100 没有参与训练、归一化、校准或选择；
- 在线 H/HA、GAT、proof queue、branch 均未被离线信号解锁。

当前结论不是“GAT 已经优化 P0”，而是：

> linear/MLP 在五折 task/arc replay 上明显低于 P0，harvest 数据又不能完整复现
> v1 selector；按照最小模型阶梯和阶段门槛，停止在离线 discovery，禁止用更复杂
> GAT 或后续 Q/branch 模块掩盖失败。

因此：

- 没有在线 eligible checkpoint；
- 没有运行 H 或 HA 端到端实验；
- 没有训练任何 GAT rung；
- 没有生成 scale50/100 新开发数据；
- 没有运行 full80 或现有 scale50/100 的性能评估；
- production 仍为 `no_cut`，P0 V2 仍只作为实验 control。

离线门槛的机器可读结论位于：

```text
runs/p0v2_gat_offline_discovery_v3/offline_discovery_gate.json
```

其中：

```text
passed                       = false
online_h_authorized          = false
online_ha_authorized         = false
gat_training_authorized      = false
proof_queue_online_authorized = false
branch_online_authorized     = false
```

## 2. 已完成的基础设施

### 2.1 深度不可变与 content-addressed cache

`LunarIceData` 构造时递归冻结：

- `tasks`；
- `arcs` 和内部 path-option mapping；
- `reference_solution` 中的 dict/list。

新增可 pickle 的 `FrozenMap`。实例构造时固定
`instance_content_hash`，Native static payload、GAT static tensor sidecar 和
snapshot replay 都以该 hash 为身份：

- 运行时 mutation 抛出 `TypeError`；
- pickle/unpickle 后 content hash 不变；
- 同内容不同对象可共享缓存；
- 相同 instance ID 但内容不同不能命中旧缓存；
- sidecar 内容或 hash 不一致时 fail closed。

### 2.2 CanonicalSolveBindingV2

唯一工厂是：

```python
CanonicalSolveBindingV2.from_backend_request(request)
```

它从 exact request 绑定：

- instance、config、exact engine；
- objective mode、Phase、RMP iteration；
- mathematical dual hash；
- raw IEEE dual diagnostic hash；
- branch context；
- full cut context；
- projected pricing-cut context；
- cut lineage、live-cut policy、separator policy；
- feature、normalization、checkpoint、OOD policy版本。

数学 dual hash 把 `+0.0/-0.0` 统一成 `0.0`；raw IEEE hash 保留 bit-level
差异用于传输诊断。旧 P0 V2 freeze 没有被重写，新实验使用 binding V2 下 fresh
运行的同代码 B0。

Exact backend、guidance、Native payload 和 replay snapshot 共享 canonical
serializer。Guidance 只复制并验证 binding，不建立平行 hash。

### 2.3 legal universe 与 no-filter telemetry

排序前后记录：

```text
legal_action_universe_hash_before_sort
legal_arc_universe_hash_before_sort
legal_branch_shortlist_hash_before_sort
guidance_filter_count
guidance_arc_drop_count
guidance_label_drop_count
guidance_branch_pair_drop_count
```

允许排序改变 label 创建轨迹、retained frontier、harvest columns 和 task-set
representatives；不允许 guidance 主动过滤合法工作。NaN/Inf、binding mismatch、
OOD 或 checkpoint/schema mismatch 会整包回退 P0。

### 2.4 完整 guidance 生命周期成本

已接入：

```text
guidance_import_sec
guidance_checkpoint_load_sec
guidance_tensorize_sec
guidance_forward_total_sec
guidance_call_count
guidance_binding_validation_sec
guidance_native_install_sec
guidance_total_wall_sec
guidance_total_wall_ratio
```

未通过部署门槛的规模在入口返回：

```text
CHECKPOINT_AVAILABLE_BUT_GUIDANCE_BYPASSED
```

该路径不会导入 Torch、读取 checkpoint 或构图。

### 2.5 Snapshot replay

Pricing snapshot 已绑定：

- canonical solve binding；
- static graph/content hash；
- true dual 和可用 RMP primal；
- branch/full-cut/projected-cut context；
- pricing mode、budget 和 queue policy；
- P0 ordering；
- exact 或 censored result；
- legal action universe hash。

Replay 不需要重跑完整 B&B，可以比较 deterministic、linear、MLP/GAT ordering，
并检查相同合法宇宙、RC 与 certificate semantics。Replay 本身不产生 certificate。

## 3. 新开发数据与 B0

### 3.1 数据生成

已生成 240 个新 accepted 实例：

| 规模 | accepted |
|---:|---:|
| 5 | 60 |
| 10 | 60 |
| 20 | 60 |
| 30 | 60 |

实例与生成 manifest 位于：

```text
data/gat_p0v2/development_instances/
data/gat_p0v2/development_instances_manifest.json
```

### 3.2 binding V2 clean B0

240/240 完成同代码 B0：

| 规模 | BPC_OPTIMAL | BPC_INCOMPLETE_PRICING | BPC_GAP_AVAILABLE |
|---:|---:|---:|---:|
| 5 | 60 | 0 | 0 |
| 10 | 60 | 0 | 0 |
| 20 | 60 | 0 | 0 |
| 30 | 31 | 22 | 7 |

语义 redline 为 0。Clean B0 保留了 6 个 raw diagnostic flags：

- 5 个来自 timeout 路径的 RC 默认诊断值；
- 1 个来自“配置存在但该 run 未观察到 worker tail”的默认字段。

这些字段没有进入 certificate scope，语义审计仍为通过；原始值被保留，没有被
抹掉。scale30 的 index 10、11 通过独立 repair run 补齐，最终每个规模内部只有
一个 config hash：

```text
scale5  14afd8235b032f9b
scale10 4dd4b0d920101fb1
scale20 b18732982dd77da7
scale30 84518dd570f44ed3
```

P0 difficulty 统计只使用 exact rows；incomplete/gap 以 censored 形式保存，不加
固定罚项。scale30 有 31 个 exact、29 个 censored。

### 3.3 冻结 split

冻结结果：

| partition | scale5 | scale10 | scale20 | scale30 | scale50 | scale100 | 总数 |
|---|---:|---:|---:|---:|---:|---:|---:|
| development | 48 | 48 | 48 | 48 | 0 | 0 | 192 |
| calibration | 12 | 12 | 12 | 12 | 0 | 0 | 48 |
| protected final test | 20 | 20 | 20 | 20 | 20 | 20 | 120 |

development 五折大小为 `39/38/38/38/39`，分层最大 fold imbalance 为 1。
审计结果：

```text
zero_content_hash_overlap                     = true
protected_full120_training_or_calibration_count = 0
protected_full120_not_used                    = true
```

split 按 content hash 固定，并按 time-window、task mode、hotspot、fleet ratio 和
P0 difficulty 分层。normalization 只在每折 training 部分拟合。

## 4. Instrumented P0 与训练材料

240 个实例完成 instrumented P0 collection：

| 规模 | optimal | legal incomplete/gap |
|---:|---:|---:|
| 5 | 60 | 0 |
| 10 | 60 | 0 |
| 20 | 60 | 0 |
| 30 | 31 | 29 |

本轮 instrumented collection 的语义和 raw redline 均为 0。

采集产物：

```text
immutable pricing snapshots     2,179
raw training-row files         11,440
collection directory size       4.8 GiB
```

为避免 scale20/30 重复静态图导致磁盘和内存膨胀，materializer 把静态图拆成
content-addressed sidecar：

| 产物 | contexts / entries | 大小 |
|---|---:|---:|
| development compact JSONL | 10,589 | 202 MiB |
| calibration compact JSONL | 446 | 7.9 MiB |
| static tensor sidecar | 240 | 27 MiB |

development 中有 192 个 static entries，calibration 中有 48 个。未探索候选从未
作为负样本。

观测到的 label 事实：

```text
exact-pricing grade 0     272,220
exact-pricing grade 3     287,824
masked unexplored      11,231,266
harvest grade 3             1,293
harvest grade 4           233,927
```

本批数据没有真实 `duplicate_negative`，因此没有伪造 grade 1。

## 5. Harvest 契约修正

离线审计发现原始 v1 harvest row 有一个不能带入部署的语义问题：

- v1 `harvest_context[2]` 记录 `would_enter_master`；
- 在线同一位置传入 `is_new_task_set`。

代码已升级采集契约为
`lunar_ice_bpc.gat_harvest_training_row.v2`，统一为：

```text
true_reduced_cost
would_change_active_support
is_new_task_set
task_fraction
```

同时发现当前 grade 4 定义与 `would_change_active_support` 在 235,220 个候选上
100% 等价。若模型直接读取该字段，会产生目标泄漏，并重复 P0 已知的 selector
规则。

为此新增 composite feature v3：

```text
lunar_ice_bpc.gat_features.v3
lunar_ice_bpc.gat_harvest_model_context.v2_without_selector_facts
```

送入模型前强制把以下两个 selector facts 置零：

```text
would_change_active_support
is_new_task_set
```

原值仍保留在 exact telemetry 和 replay 中，由 P0 的
new-task-set-before-replacement 逻辑使用。训练、replay、runtime 和 deployment
freezer 共享同一 sanitizer；旧 checkpoint 因缺少 schema 无法部署。

## 6. 最小模型阶梯实测

### 6.1 训练

只训练了计划要求的前两级：

| 模型 | 参数量 | 五折单 run wall time |
|---|---:|---:|
| linear | 232 | 4.86–5.31 s |
| MLP 2×32 | 13,061 | 9.11–9.26 s |

每个 instance/head/phase 最多保留 8 个 context；原始 10,589 个 context 压缩为
2,773 个 bounded contexts。每 epoch 按

```text
head -> scale -> instance -> node phase -> RMP context -> candidates
```

确定性轮换一个 context。没有 calibration/protected rows 参与训练或
normalization。10 个 checkpoint 均为 shadow，`online_eligible=false`。

### 6.2 Pricing task/arc 五折 replay

五折合计 1,733 个 validation contexts。结果：

| ranker | first observed-negative rank p50（五折） | weighted top-5 recall | mean inference/context |
|---|---|---:|---:|
| P0 | 1 / 1 / 1 / 1 / 1 | 0.08432 | 0 |
| linear v3 | 20 / 8 / 1 / 1 / 32 | 0.03473 | 7.34 ms |
| MLP v3 | 1 / 1 / 40 / 45 / 15 | 0.03836 | 7.64 ms |

两种学习模型都低于 P0，并在多个 fold 上严重拉低首个 observed-negative
candidate 的 rank。所有 replay 的 legal universe 均保持一致。

这个指标是 task/arc membership ordering，不等同于 Stage B 的在线
first-addable-negative wall time；它只能作为离线 discovery gate。其结论已足够
否决继续训练更复杂模型。

### 6.3 Route-level harvest replay

五折合计 4,460 个 validation contexts，其中 396 个同时含 grade 3/4、具备排序
辨识度：

| ranker | informative first-useful mean rank | weighted NDCG@5 | mean inference/context |
|---|---:|---:|---:|
| P0 | 1.28535 | 0.99612 | 0 |
| linear v3 | 1.26515 | 0.99375 | 0.357 ms |
| MLP v3 | 1.14646 | 0.99581 | 0.759 ms |

MLP 在 first-useful rank 上有局部改善，但 NDCG@5 仍没有超过 P0。更关键的是，
现有 4,460 个 rows 全是旧 v1，缺少可精确恢复 active-task-set membership 的字段，
所以这里只能精确 replay selector 之前的候选 ordering，不能作为在线 H promotion
证据。

### 6.4 OOD calibration

10 个 v3 shadow checkpoint 都在独立的 48 个 calibration instances、446 个
contexts 上完成 OOD threshold calibration：

- checkpoint weights 未改变；
- development 未用于校准；
- protected final test 未使用；
- model selection 没有被重新打开；
- 输出仍为 `online_eligible=false`。

scale30 的 max-abs-z threshold 明显高于 5/10/20，这一事实被保留为 scale-specific
fallback gate，不通过一个全局阈值掩盖跨规模分布差异。

## 7. 为什么没有继续 GAT、H/HA、Q 和 branch

离线 gate 对 linear 和 MLP 都给出三个共同 blocker：

```text
legacy_v1_harvest_selector_context
task_arc_top5_recall_not_better_than_p0
task_arc_first_rank_regressed
```

在 composite feature v3 中，目标泄漏已被消除，不再是 blocker；但真实排序信号
仍然不够。

模型阶梯合同要求：

> 只有更小模型在相同 folds 和预算下显示有效信号后，才允许训练更复杂模型。

因此：

- 不训练 `gat1x32x1`、`gat2x32x2`、`gat3x64x4`；
- 不创建 online deployment manifest；
- 不运行 H 或 HA 端到端；
- 不实现 Native Q1–Q4 在线 queue；
- branch/proof head 继续只做 shadow；
- 不生成 scale50/100 新开发数据；
- 不触碰最终 full120 性能评估。

这正是评审意见中“失败时回退 P0，不用后续复杂模块掩盖前一阶段失败”的执行结果。

## 8. Proof queue 与 branch 的代码边界

### 8.1 Proof queue

Q0–Q4 使用显式字典序 tuple；非数学优先级统一使用 `heuristic_*` 命名。跨策略
replay 用 canonical state/path signature 对齐，`creation_sequence_id` 只保证同一
策略内部确定性。

这些实现仅用于 shadow/differential test，没有接入 Native exact queue。Exact
proof 仍使用原 Q0。

### 8.2 Branch

branch shadow 已实现：

- 只重排当前 P0 shortlist；
- 排序前后 shortlist universe hash 相同；
- pair input 对交换对称：
  `sum / abs-difference / product / global / context`；
- missing score 回原 deterministic 顺序；
- same/different 两个 child 都保留；
- U0/U1 all-pairs 仅为离线 control。

`branch_cost` 越小越好。Incomplete probe 保存 lower bound、time/memory censoring 和
child status，不使用固定罚项。没有 branch online ordering 变化。

## 9. 测试与资源

最终验证：

```text
foundation tests                    38 passed
Native/exact targeted regression   407 passed + 22 subtests
full repository pytest             453 passed + 22 subtests
Native CTest                         2 / 2 passed
```

此外：

- compact static cache hash、stale rejection 和 epoch rotation 有专门测试；
- raw-vs-learned harvest leakage 有专门测试；
- route replay universe permutation 有专门测试；
- pre-import bypass、signed-zero、binding、pickle、mutation、queue/branch symmetry、
  timeout/memory incomplete 和 split isolation 均有覆盖。

长任务使用单训练进程或最多 5 路 replay，每进程 2 个 Torch/BLAS threads。完成时：

```text
available memory 约 12 GiB
swap used        约 118 MiB
disk available  约 809 GiB
```

没有出现 runaway memory 或 disk use。

## 10. 下一次合法研究动作

当前计划已经在 discovery gate 处正常终止。若以后重新开启这一方向，顺序应是：

1. 先重新定义不由当前输入直接给出的 harvest 下游 target，例如加入列后的实际
   bound gain、后续 duplicate pressure 或 matched-budget trajectory；
2. 新采集 v2 harvest rows，确保 offline/online `is_new_task_set` 完全一致；
3. 改善 exact-pricing 的监督单元，使目标与“P0 已经 rank=1”的候选 membership
   指标区分开；
4. 先只重训 linear 五折；
5. linear 有可靠 signal 后才训练 MLP；
6. MLP 相对 linear 有显著增益且开销过门槛后，才允许训练第一个小 GAT；
7. 只有新的 offline gate 通过，才进入在线 H，再到 HA；
8. HA 独立通过后，才能解锁 proof queue、branch 和 scale50/100 development。

在此之前，任何 full80 或现有 scale50/100 运行都不会提供合法的研发选择证据。
