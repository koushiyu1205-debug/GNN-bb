# P0V5 Multi-Resolution Frontier GAT V9R1

## 1. 研究问题

V9R0 证明256-label局部图能提高scale50的QD1排序可辨识性，但19/19个
scale50 context均达到256-label cap，样本通常只覆盖完整frontier的约4%–35%。
V9R1检验：在不增加label pop、不运行辅助prefix的条件下，同时使用完整
64-cell frontier mass graph和256-label局部图，能否达到安全选择所需的
benefit/adverse/rank门。

本链仍为`diagnostic_only`，使用已经暴露的历史development标签，只回答
representation问题，不授权性能、runtime或deployment。

## 2. 两个严格绑定的视图

两个视图都来自同一个literal-Q0请求的第4096次pop：

- **完整mass视图**：固定8×8 depth/RC cells，共64节点，聚合整个frontier的
  label count、terminal比例、RC、深度、creation age、last-task entropy和
  parent transition；空cell也保留。
- **局部结构视图**：最多256个确定性抽样label nodes，加scale个task nodes，
  保留label-state、Q0/QD1 rank、parent、dominance surface、last-task和
  task/dual/branch/cut结构。

绑定审计要求38/38 context的context ID、instance、scale、ratio、benefit、
adverse和28维context vector完全一致。64-cell graph的三次QPF0 graph hash必须
一致。

禁止输入endpoint trajectory、counter deltas、full-run winner、final wall、
objective或certificate。新链产生的arm outcome数量固定为0。

## 3. Multi-resolution Interaction-GAT

两个视图各使用独立的两层edge-aware attention：hidden 16、2 heads、
residual、LayerNorm、ReLU、dropout 0.1。

- label与task nodes分别做mean/max/attention pooling；
- cell nodes做mean/max/attention pooling；
- 两个视图的edge分别做mean/max pooling；
- 两个视图投影到32维后，拼接`label`、`cell`、绝对差、逐元素乘积和16维
  context embedding；
- 输出`p_benefit/positive_gain/p_adverse`；
- 每模型参数少于30k。

独立训练`gat/mlp/linear/no_message/shuffled_topology`。所有模型获得相同数值、
fold、instance weights和seeds；topology controls拥有独立训练结果。

训练保持5-fold instance-grouped OOF，seeds为
`61635/91267/170141`，每实例总权重为1。normalization、class weights和early
stopping只使用当前fold train instances。

## 4. 冻结gate

只有全部满足才进入单请求Native fresh pilot：

- scale50 instance benefit BA `>=0.70`；
- scale50 instance adverse BA `>=0.70`；
- scale50 instance rank accuracy `>=0.65`；
- benefit BA不低于最佳MLP/Linear超过`0.02`；
- benefit BA不低于no-message和shuffled-topology；
- rank不低于两个topology controls；
- benefit BA或rank至少有一个topology control下降`>=0.02`；
- tensorization+三seed ensemble warm p99 `<=10ms`；
- 将两个历史graph-build wall保守相加后的总p99 `<=15ms`；
- 每个context的保守总准备成本/QPF0 wall `<=2%`。

相似数值签名的相反标签比例继续报告，但不作为gate，因为该统计只使用
mean/min/max，不能观察本链新增的cell topology；安全性由严格OOF分类、排序和
topology-control门判断。

失败写：

```text
FAIL / MULTIRES_FRONTIER_NOT_IDENTIFIABLE
```

并授权下一研究阶段为`MULTI_TIMEPOINT_LATE_SWITCH_ORACLE`，不得在V9R1调参。

## 5. 通过后的边界

通过diagnostic也不构成加速证据。下一阶段必须在同一个正式exact request内
同时构造两视图并进行portable Native forward，然后重新运行：

1. fresh pilot；
2. calibration与一次性heldout；
3.完整BPC Development-E2E；
4. formal full100。

scale30采用高激活QD1门，scale50采用高置信选择性门。任何阶段都不允许加入
QB1、QGR1或辅助prefix。
