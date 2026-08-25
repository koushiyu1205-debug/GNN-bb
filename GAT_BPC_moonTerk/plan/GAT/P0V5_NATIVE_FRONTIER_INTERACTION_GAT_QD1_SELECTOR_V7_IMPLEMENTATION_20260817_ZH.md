# P0V5 Native-Frontier Interaction-GAT QD1 Selector V7 实施说明

日期：2026-08-17  
状态：工程实现完成；性能证据链尚未运行，禁止声明加速成功。

## 1. 实施结论

V7 已实现为一条独立、development-only 的研究链。它不再用 pricing 前的任务图预测 QD1，而是在每个获得授权的 scale30/50 root-CG V5 fallback pricing request 中：

1. 使用历史 literal Q0 comparator 处理前 4096 次 label pop；
2. 在第 4097 次 pop 前从真实 frontier 构造固定 8×8 graph；
3. `collect_force_q0` 保持原 Q0 queue 不动，`force_qd1` 或 learned action 将同一批 label 原位迁移到 QD1 queue；
4. learned mode 在 Native 内执行三 seed portable Interaction-GAT ensemble；
5. 任一 manifest、bundle、schema、OOD、NaN/Inf、calibration 或 threshold 异常均继续当前 Q0 queue。

它只改变剩余 label 的弹出顺序。`State` 未增加字段，ABI 仍为 `sizeof(State)==176`。QB1、QGR1、label-GAT 和 ranker 不在 V7 action universe 中。

## 2. Native exact-safe 实现

Native 新增四种 probe mode：

```text
disabled
collect_force_q0   # QPF0
force_qd1          # QPD1
learned
```

`disabled` 不分配 frontier tracking 数据，保持历史 Q0 路径。probe 每个 pricing request 最多执行一次；proof 在 4096 pop 前结束或 frontier 为空时不调用模型。

迁移前后强制验证：

```text
frontier_before == drained_count == migrated_count == qd1_queue_size
creation_id_hash_before == creation_id_hash_after
duplicate_count == 0
```

任何不一致均抛出 correctness error，不能回退后继续签发 certificate。creation sequence 存在 Native 辅助映射中，不进入 `State`。

Frontier graph 固定包含 64 个 cell、16 维 node feature、10 维 edge feature和 28 维 context feature。空 cell、自环、depth/RC 邻接边均保留；可验证的 frontier parent-child transition 添加双向 typed edge。节点、边和 graph hash 对容器遍历顺序确定。

portable forward 为两层 edge-aware attention、hidden 16、2 heads、residual、LayerNorm 和 ReLU。正式 pricing 不 import Python/Torch。三 seed 输出按下式聚合：

```text
p_benefit = mean(seed p_benefit)
positive_gain = min(seed positive_gain)
p_adverse = max(seed p_adverse)
disagreement = max(seed p_benefit) - min(seed p_benefit)
```

OOF scale-specific Platt calibration 和 gain scale 已进入 portable bundle，并由 C++ 在 ensemble 聚合后、threshold 前执行，避免 Python calibration 与 Native action 不一致。

## 3. Runtime 安全边界

Python runtime 只校验 manifest 并附加 canonical portable bundle，不参与 4096-pop 决策。以下 request 在读取 manifest、构图、Torch import 和 bundle load 前返回同一 Q0 request 对象：

- scale5/10/20；
- 任意 tree lifecycle；
- 非 exact、非 official、非 V5 fallback；
- incoming policy 非 Q0；
- 已带 guidance 或 DSSR。

正式 manifest 强制 `model_kind=frontier_interaction_gat`、`message_passing_required=true`、root-only、Q0/QD1 action universe、QB1/QGR1 forced-veto 和 development-only。per-request `config_hash` 含动态 RMP/round state，不作为部署 allowlist；稳定绑定使用 selected exact config 文件 SHA256，并由 acceptance bootstrap 在启动 solver 前校验。request 内仍校验 exact engine 与 exact action-policy hash。

## 4. 数据与状态机

实现的状态顺序为：

```text
PROBE_DIAGNOSTIC
-> PILOT_CENSUS -> PILOT_MATRIX
-> MAIN_CENSUS -> MAIN_MATRIX
-> TRAINING -> HELDOUT
-> DEVELOPMENT_E2E -> FORMAL_FULL100
-> TERMINAL
```

V3–V6 instances、formal/protected contents 全部进入 blacklist。V6 只提供 outcome-blind overhead diagnostic snapshot；它的 wall/outcome/model 不进入 V7 训练或授权。

fresh pilot 与 main census 只允许两个 selection input：candidate index 和 `legal_snapshot_count>=1`。root wall、round、density 和任何 arm outcome不参与 eligibility。main split 固定为每规模 20/8/6/3；train 每实例最多两个自然 context，其余 replay partition 一个 primary context。同一实例所有 context 留在同一 partition且总权重为 1。

每个 replay context 先单独运行一次 literal-Q0 milestone，并冻结 milestone kind，之后才生成 QPF0/QPD1 task。Q0/QPF0/QPD1 使用三次 blocked fresh-process repeats、单 Native process、300/600 秒和 10.867 GiB。

## 5. 训练与公平对照

唯一候选为三 seed full GAT ensemble。以下 control 独立训练、独立 checkpoint：

```text
MLP
Linear
no_message
shuffled_topology
```

训练为 5-fold instance-grouped CV；normalization、5% OOD envelope、class weight、early stopping 和 Platt calibration 仅使用 train instances/OOF prediction。calibration 只选 scale-specific threshold，不参与 representation training。若无 safe threshold、message passing 无贡献或 simple control 更好，链必须写 negative terminal。

## 6. 已完成验证

当前工程验证包括：

- Native CTest：QPF0 graph/hash 确定、QPD1 migration invariant、Q0/QPF0/QPD1 exact differential；
- 500-case randomized Native exact differential循环；
- C++/PyTorch portable forward parity，误差门槛 `1e-5`；
- scale5/tree request identity 和 manifest drift fail-closed；
- force mode payload 不含 ranker；
- V5 frozen binary SHA256 保持 `c747bcdc674aabd7809b1b253300c033cfd37fad493f02bf3cf623136d2c42f4`。

这些是工程 correctness 证据，不是 wall-time 加速证据。probe overhead、pilot、fresh main、heldout、E2E 和 formal full100 必须按冻结状态机依次运行。

## 7. 不得作出的声明

在 formal gate 通过前不得声明：

- V7 加速 scale30/50；
- Frontier-GAT 优于 MLP/Linear/topology controls；
- production promotion 已获授权；
- QGR1 或 label-GAT 成功。

即使 V7 最终通过，也只允许声明：

```text
Native-frontier Interaction-GAT-gated QD1 queue-policy acceleration
```

