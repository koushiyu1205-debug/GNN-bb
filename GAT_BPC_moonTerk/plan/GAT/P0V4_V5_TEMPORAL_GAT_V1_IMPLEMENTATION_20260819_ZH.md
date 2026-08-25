# P0V4+V5 Temporal-GAT V1 实现状态（2026-08-19）

## 当前结论

代码链已经实现，fresh real-map corpus 正在串行生成；尚未产生任何 queue
outcome，因而当前状态是 `CORPUS_GENERATING_DEVELOPMENT_ONLY_NOT_PROMOTED`。
production default 仍是历史 `no_cut`；实验 run root 与新 production registry
在各自合法 gate 之前都不会创建。

本实现只在 P0V5 bidirectional prepass 返回 P0V4 exact fallback 后，对
scale30/50 的 `root_cg` request 安装 reversible Temporal-GAT trial。其他
scale、tree pricing、非 official objective、非 exact request 均继续 literal Q0。

## 已实现的 exact-safe 路径

- scale30/50 分别在 4096/16384 pops 触发 Q0→QD1 migration。
- 支持 `CollectTrial`、`ForceTrialContinue`、`ForceTrialRevert`、
  `LearnedAfterTrial`，K 只允许 128/512/2048。
- QD1→Q0 先构造 staging queue，验证 size、duplicate、creation ID 和 hash，
  再原子交换；creation ID 跨双向 migration 保留。
- request 在 K 内自然结束时不调用模型；timeout、memory、label drop 和
  incomplete 仍沿用原 exact fail-closed/certificate semantics。
- Temporal-GAT v2 使用共享 32-d cell/label-task encoder、两层 4×8
  edge-aware GAT、t0/tK shared weights、128→64 trunk 和 scale-specific heads。
- Native 直接运行三 seed portable ensemble；schema/OOD/nonfinite/model 异常
  均选择当前 frontier 的 `MIGRATE_BACK_TO_Q0`。
- Temporal Native build 必须同时保留 production P0V5 的
  `bidirectional_feasibility_compiled=true` 与
  `ng_dssr_v3_compiled=true`，且 `State` 仍为 176 bytes；bootstrap 和最终
  source audit 都逐字段核对 frozen build-info，禁止因 build flag 缺失而静默
  降级成纯 P0V4。
- OOD envelope 固定为仅由相应 fold-train 拟合的逐特征 `mean ± 8σ`；不是
  live request hash allowlist。selected exact config、source freeze、Native binary
  与 bundle file hash 仍是硬绑定。
- telemetry 包含 t0/tK cell graph、label+task graph、temporal identity edges、
  counter/hash、双向 migration conservation、trial/migration/inference wall、
  OOD/disagreement 和最终 action。
- fresh corpus publication 使用 `.partial` 完整写入、重新解析/校验后再
  `os.replace`；freeze 同时绑定 driver/generator/map source hash，并在发布前后
  复核 `data/` 与 `runs/` 下所有 `*logical_graph.json` 的 protected inventory。
  当前 inventory 为 1605 个文件（其中 10 个来自 `runs/`），不再遗漏文件名前缀
  不是 `instance_` 的历史实例。
- scale50 的 outcome-blind boundary eligibility 使用 literal Q0，并显式携带
  canonical `4096/8192/16384` observation prefix；它不会借 eligibility 启动
  QD1 trial。scale30 对应 prefix 为 `4096`。
- full-BPC、formal 与 canary 统一采样 fresh subprocess tree 的 VmRSS；这样
  scale30 in-process backend 即使没有 host-only RSS 字段也有 peak-memory 证据。
  每个 canonical row 绑定 resource telemetry 的 path/hash，promotion 时再次复核。

## 冻结实验顺序

以下步骤必须按顺序执行，不得跳过或在 outcome 后修改 config/grid/gates。

```bash
python scripts/generate_p0v5_temporal_gat_production_corpus_v1.py \
  --config configs/experiments/p0v5_temporal_gat_production_v1.json
python scripts/initialize_p0v5_temporal_gat_production_v1.py \
  --config configs/experiments/p0v5_temporal_gat_production_v1.json

python scripts/audit_p0v5_temporal_gat_native_differential_v1.py \
  --source-freeze runs/p0v5_temporal_gat_production_v1_round1_20260819/source.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round1_20260819 \
  --output runs/p0v5_temporal_gat_production_v1_round1_20260819/native_differential.report.json

python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py collect \
  --config runs/p0v5_temporal_gat_production_v1_round1_20260819/config.freeze.json \
  --corpus data/p0v5_temporal_gat_production_v1_round1/corpus.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round1_20260819
python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py eligibility \
  --config runs/p0v5_temporal_gat_production_v1_round1_20260819/config.freeze.json \
  --corpus data/p0v5_temporal_gat_production_v1_round1/corpus.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round1_20260819
python scripts/collect_p0v5_temporal_gat_root_contexts_v1.py freeze \
  --config runs/p0v5_temporal_gat_production_v1_round1_20260819/config.freeze.json \
  --corpus data/p0v5_temporal_gat_production_v1_round1/corpus.freeze.json \
  --run-root runs/p0v5_temporal_gat_production_v1_round1_20260819
```

随后用 `freeze_p0v5_temporal_gat_trial_schedule_v1.py` 先冻结 train 全 K
schedule，用 `run_p0v5_temporal_gat_trial_schedule_v1.py` 串行执行三臂三次
blocked repeats，再用 `select_p0v5_temporal_gat_trial_k_v1.py` 冻结每尺度 K。
calibration replay schedule 必须传入该 K selection；development/sealed 使用
独立 full-BPC 四臂 frozen schedule，sealed final 只有在 development audit PASS
后才可启动。

`build_p0v5_temporal_gat_dataset_v1.py` 只对 CONTINUE 与 REVERT 的直接比值
造标签；两臂都 incomplete 的 row 只保留资源审计。训练入口是
`train_p0v5_temporal_gat_production_v1.py`，包含 5-fold instance-grouped CV、
三 seed ensemble、linear/MLP/no-message/shuffled-topology/deterministic controls、
calibration-only threshold selection 和 representation gate。

任何脚本写出 `terminal_decision.json` 后，同一 round 的所有后续入口都会
拒绝运行；不能删除 terminal artifact 继续拟合。新一轮必须使用新的
experiment ID、seed range、fresh calibration/development/sealed partitions 与
registry candidate ID。

## 晋升边界

- `verify_p0v5_temporal_gat_portable_v1.py`：calibration 全图 + 500 synthetic
  graph，要求 action mismatch=0、max error≤1e-9、Native inference p99≤10ms。
- `audit_p0v5_temporal_gat_source_bundle_v1.py`：source/binary/bundle/hash/176-byte
  ABI audit。
- `audit_p0v5_temporal_gat_e2e_v1.py`：development 与 sealed-final gates；任一
  FAIL 都是 terminal negative。
- formal acceptance 仍由
  `configs/experiments/p0v4_final_acceptance_v1.yaml` 控制。scale100 只能作为
  diagnostic。
- `finalize_p0v5_temporal_gat_production_v1.py candidate` 只有在 development、
  sealed、formal、portable、source/binary/bundle 五类证据全部 PASS 后才生成
  immutable candidate 和 canary schedule，并把 candidate 以
  `AWAITING_CANARY` 写入独立 registry；active policy 此时仍为 `no_cut`。
- `activate` 还要求绑定 candidate manifest 的 canary PASS；它新建独立
  production policy registry，不修改历史 baseline registry。
- `rollback` 将新 registry 的 active policy 恢复为 `no_cut`。Runtime 在新
  registry 不存在、损坏或 active policy 为 `no_cut` 时保持 literal Q0。

## 本轮已完成的代码级验证

- Native CTest：2/2 PASS。
- Temporal production contract Python tests：16/16 PASS。
- 既有 P0V5 bidirectional/V10 回归：23/23 PASS。
- 实际 P0V5 midpoint/certificate 定向回归：10/10 PASS。
- 当前 Native 相对 reference Native 的 disabled-Q0 exact differential：
  500 cases，0 mismatch。
- Native contract binary 的机器可解析 marker：
  `TEMPORAL_ACTION_RANDOMIZED_EXACT cases=500 mismatches=0`；正式 audit 会直接
  解析该 marker，不再静态填写 randomized differential 结果。
- 单组 3-seed Python/C++ portable forward：最大绝对误差
  `5.551115123125783e-17`。
- 20 个 synthetic scale50 multi-resolution graphs 的 Native 三 seed inference：
  median `2.921 ms`，observed max/p99 `3.235 ms`。

这些是实现验证，不是 fresh corpus、development、sealed final 或 formal
promotion 证据，不能用于切换 production default。
