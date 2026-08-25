# P0V5 Counterfactual-Prefix Interaction-GAT QD1 Selector V8 实施说明

## 1. 证据边界

V8 是独立证据链。V7R3 保持 `FAIL / SCALE50_BENEFIT_HARM_NOT_SEPARABLE`，其 38 个 context 和 228 个 matched task 只能用于 representation development；不能授权 V8 性能、threshold 或部署。正式候选仍为 development-only。

V8 的唯一动作是 `CONTINUE_Q0 / SWITCH_QD1_AT_4096`。QB1、QGR1 和 label ranker 不属于接口。辅助 prefix 结果必须同时满足 `truncated_diagnostic=true`、`exact=false`、`routes=[]`、`certificate=null`，不能进入 RMP 或签发 closure。

## 2. Native 实现

`SolveParams.counterfactual_prefix` 提供 `disabled/counterfactual_q0_prefix/counterfactual_qd1_prefix`。prefix 在 literal-Q0 完成 4096 次 pop 后保存相同 base graph，并在同一请求中保存 `+128/+512/+2048` 三个 endpoint。QD1 prefix 使用既有 QD1 comparator 原位迁移；迁移前后 label 数、creation ID 集合及 rolling hash 必须一致。

frontier 抽样最多 256 个 label，顺序固定为 terminal、Q0 top、QD1 top、deepest、depth-RC cell coverage、state/creation-ID bottom-k。图还包含 canonical task nodes、parent/last-task/dominance-surface/task-interaction edges。`State` 未改动，ABI 仍为 176 bytes。

训练端为三视图共享权重的两层 edge-aware GAT。每个视图输出 mean/max/attention node pooling、mean/max edge pooling和 context encoding；head 同时读取 base、Q0 endpoint、QD1 endpoint、QD1-Q0、绝对差和 24 个 counter delta。生产推理由 C++ portable forward 执行，不在 pricing 中导入 Torch。

## 3. Fail-closed runtime

Python 先做 scale、lifecycle、exact/official、V5 fallback 和 incoming-Q0 检查。未通过时返回同一个 request，且不读取 manifest。通过后才验证 manifest/bundle，运行两个 telemetry-only prefix，验证 base hash，再调用 Native portable ensemble。任何 prefix、schema、OOD、数值或 disagreement 错误均创建新的 literal-Q0 exact request。只有正式 exact request可以返回路线或 certificate。

## 4. 冻结与停止

Bootstrap freeze 绑定 Native/source/schema/V7R3 import 和 representation schedule。Representation gate 选择满足所有门槛的最小预算；三个预算均失败时写 `COUNTERFACTUAL_PREFIX_NOT_IDENTIFIABLE`，后续 candidate census、pilot、heldout、E2E 和 formal writers 均被 terminal guard 拒绝。

后续 pilot/performance freeze 只能在前一 gate 通过后创建。所有性能矩阵使用单 Native process，scale30/50 cap 分别为 300/600 秒，完整 BPC 为 3600 秒；辅助请求及模型准备 wall 全部计入 candidate 净 wall。
