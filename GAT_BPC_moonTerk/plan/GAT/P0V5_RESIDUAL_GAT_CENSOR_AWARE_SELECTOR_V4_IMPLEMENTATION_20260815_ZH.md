# P0V5 Residual-GAT Censor-Aware Queue Selector V4 实施说明

## 1. 冻结边界

V4 使用独立 run root：

```text
runs/p0v5_residual_gat_censor_aware_selector_v4_20260815/
```

V3 的 `FAIL / RESOURCE_CENSOR_UNDETERMINED` 只作为诊断假设来源。V4 不导入
V3 snapshot、arm outcome、normalization、threshold 或授权。QB1 在 config、模型
输出维度和 runtime manifest 三层永久 veto。生产默认仍为
`no_cut + P0V4/P0V5 Exact + Q0`。

V4 只允许 root-CG 的 scale30/50 request 进入 manifest。scale5/10/20 与所有
tree request 在 manifest、interaction graph 和 Torch 之前返回同一个 Q0 request
对象。候选始终为 development-only。

## 2. Native telemetry-only 引擎

冻结前运行 `scripts/audit_p0v5_native_telemetry_differential_v4.py`，分别在旧
portfolio Native build 与 V4 telemetry-only build 的独立 Python 进程中执行
500 组 literal-Q0 exact-proof 请求。status、frontier、label-drop、最小 RC、
certificate blockers 与带 reduced-cost 的 canonical route universe 必须 500/500
一致；审计报告及两个 binary hash 进入 `source.freeze.json`。

新增 `qgr1_stratified_reservoir_v1`，只在 literal-Q0 training trace 开启：

- existing/incoming dominator 各保留 12,500 个 bottom-k preference pairs；
- action surface 最多 3,125 个，每个 surface 最多 8 个 labels；
- 最多 512 条 admitted witness routes 和 25,000 个去重 ancestors；
- 最终 label-state union 上限 100,000；
- seed 默认取 `SHA256(state_hash)` 前 64 bit；
- bottom-k priority 由无状态 `mix64` 生成，不依赖 unordered container 遍历顺序。

mandatory witness、pair endpoint 或 parent chain 无法完整保存时设置
`proof_queue_label_trace_incomplete=true`。该 context 不进入 QGR1 training。
performance wall replay 始终关闭 trace。

采样器不读取或修改 comparator、dominance、bound、route generation、negative
threshold 或 certificate。500 组 randomized differential 同时比较 trace-off Q0、
trace-on Q0、QG2 和 QGR1 的 status、exhaustiveness、frontier、route count 和完整
reduced-cost multiset。`sizeof(State)==176` 继续由 Native test 固定。

## 3. Fresh corpus 与执行顺序

内容角色固定为：

- train：V3 train 的 14+14 instance contents，V4 新引擎重跑；
- calibration：V3 selector-heldout 的 4+4 contents，未暴露 arm outcomes；
- heldout：seed base `260815000` 新生成的 4+4 contents；
- development-E2E：V3 E2E 的 3+3 contents，未暴露 arm outcomes。

若固定内容在新引擎没有自然 root context，才按冻结 seed 顺序使用新 candidate
替换；每规模最多 30 个。正式 001--020 content hashes 全部在 blacklist。每个实例
最多保存 3 个自然 root contexts，同一实例所有 contexts 同 partition且总权重为 1。

执行严格分两步：

1. 对 train+calibration context 先做一次 trace-off literal-Q0 milestone screen；
2. 只对 screen 通过的 train context 冻结并运行独立的 telemetry-only stratified
   trace schedule，该 wall 不具有 performance authority；
3. 只有 `milestone_reached=true`、非 TIMEOUT/MEMORY_LIMIT、无 label drop 的
   context 才进入预冻结 `Q0/QD1 × 3` schedule，matched wall 全部 trace-off。

未达到 milestone 的 context 写 `REPLAY_INELIGIBLE`，不会创建任何非 Q0 task。

## 4. Censor-aware 折叠

每个 matched block 使用以下固定规则：

- Q0/arm 都完成：`arm_wall / q0_wall`；
- Q0 完成、arm 删失：`cap / q0_wall`，同时 adverse；
- Q0 删失、arm 完成：`arm_wall / cap`，为保守收益；
- 双删失：relative ratio missing，但 resource-censor label 为正。

至少 2/3 blocks 可比较才形成 context median ratio。单个双删失 context 不会终止
链；最终 determined context/instance coverage 不足时才写
`INSUFFICIENT_DETERMINED_COVERAGE`。任何 objective、route universe、global minimum、
true RC、certificate 或 exhaustive-with-label-drop redline 仍立即终止全链。

## 5. 两层 GAT

QGR1 label GAT 只从 trace-complete literal-Q0 future traces 训练，保持 75% 三类
supervised pairs、25% neutral、pairwise logistic、0.1 neutral Huber、1e-5 L1、
75% magnitude hard-zero 和固定 `1e-4` bucket。QGR1 只可在同 terminal、depth、
RC bucket 内改变顺序。

Context Interaction-GAT 的 action universe 是 `Q0/QGR1/QD1`。两层 edge-aware
attention 使用 hidden 16、2 heads、residual、LayerNorm、ReLU、dropout 0.1，参数
少于 20k。每个非 Q0 arm 输出：

```text
p_benefit
conditional_positive_gain
p_adverse
p_resource_censor
```

risk score 固定为：

```text
p_benefit * positive_gain
- lambda_adverse * p_adverse
- lambda_resource * p_resource_censor
```

MLP、Linear、independent no-message、independent shuffled-topology 使用相同输入和
独立 checkpoint，只能作为 controls。simple control 获胜或 message passing 无贡献
时写 negative，不能替换 GAT 候选。

## 6. 当前实施入口

```text
configs/experiments/p0v5_residual_gat_censor_aware_selector_v4.json
scripts/initialize_p0v5_residual_gat_censor_aware_selector_v4.py
scripts/collect_p0v5_residual_gat_root_contexts_v4.py
scripts/run_p0v5_residual_gat_matrix_v4.py
scripts/finalize_p0v5_residual_gat_stage_v4.py
scripts/train_p0v5_qgr1_residual_gat_v4.py
scripts/run_p0v5_qgr1_force_on_v4.py
scripts/finalize_p0v5_residual_portfolio_v4.py
scripts/build_p0v5_residual_gat_training_dataset_v4.py
scripts/train_p0v5_residual_interaction_gat_selector_v4.py
scripts/run_p0v5_residual_gat_heldout_v4.py
scripts/run_p0v5_residual_gat_full_bpc_v4.py
```

所有 immutable artifact 使用 write-once 语义；source/config/native binary 漂移会
fail closed。terminal 后所有 collector、replay、trainer 和 finalizer writer 必须拒绝
继续生成 artifact。
