# P0V5 Proof-Tail GAT 优化方案评审与修改建议

## 一、总体评价

当前 P0V5 Proof-Tail GAT 方案是目前几条 GAT
路线中最符合现阶段代码状态和论文目标的方案。

相比 route-level promotion、exact-pricing portfolio、branch GAT 和 label
generation GAT，Proof-tail queue ordering GAT 更匹配当前瓶颈。

核心原因：

> 当前主要问题不是找不到列，而是在 exact fallback 阶段 proof-tail
> 搜索成本过高。因此 GAT 应作用于 exact
> 搜索内部的安全排序层，而不是改变求解空间。

总体评价：

  维度               评价
  ------------------ --------
  exact安全性        9.5/10
  工程可实施性       9/10
  与P0V5瓶颈匹配度   9.5/10
  学习动作合理性     8.5/10
  论文潜力           8.5/10

------------------------------------------------------------------------

## 二、主要优势：找到正确的 GAT 控制点

Route promotion 改变 column admission，会经过：

    promotion
     ↓
    RMP
     ↓
    dual变化
     ↓
    后续pricing
     ↓
    tree

信用分配困难。

Proof-tail GAT 改变：

    queue ordering
     ↓
    negative route discovery
     ↓
    proof progress
     ↓
    pricing time

链路更直接，更适合作为第一版学习增强模块。

------------------------------------------------------------------------

## 三、必须先验证 GAT 是否必要

最大风险：

Q0 已经足够好。

因此必须先进行：

    Q0
    vs
    Perfect QG1 selector

oracle实验。

只有当 perfect oracle 存在明显收益时，才进入模型训练。

建议门槛：

-   oracle geometric mean ratio \<= 0.85；
-   正收益状态比例 \>20%。

------------------------------------------------------------------------

## 四、关键修改1：QG1目标应明确

如果 QG1 只是改变 label 顺序，但最终仍完整遍历全部状态，则收益可能有限。

优化目标应定义为：

-   first useful negative discovery time；
-   first addable column time；
-   proof completion time；
-   total wall time。

重点不是减少搜索空间，而是更早达到有效 proof progress。

------------------------------------------------------------------------

## 五、关键修改2：arc head 改为 label-state head

当前 arc-level head 与实际动作不完全匹配。

真正被调度的是 label queue，而不是 arc。

建议：

输入：

-   label状态；
-   当前节点；
-   visited摘要；
-   时间资源；
-   能量资源；
-   dual reward；
-   可行性信息。

输出：

-   label priority score；

或者采用 pairwise ranking。

------------------------------------------------------------------------

## 六、关键修改3：增加非学习baseline

必须比较：

    Q0
    Random ordering
    Handcrafted priority
    MLP
    GAT

否则无法证明收益来自GAT。

------------------------------------------------------------------------

## 七、数据规模建议

当前 fallback context 数量要求偏低。

模型学习对象是 snapshot，而不是 instance。

建议：

-   positive useful contexts \>=50。

同时检查收益集中度，避免少数状态贡献绝大部分收益导致泛化失败。

------------------------------------------------------------------------

## 八、模型结构建议

建议保留两个head：

1.  收益概率：

P(ΔT\>0)

2.  收益大小：

E(ΔT \| ΔT\>0)

最终：

score = probability × magnitude

安全约束由：

-   OOD；
-   hash binding；
-   threshold；
-   fail closed

控制，不交给模型。

------------------------------------------------------------------------

## 九、推荐实验路线

    P0V5 freeze

    ↓

    Q0 vs Oracle QG1

    ↓

    是否存在收益空间

    ↓

    Linear priority model

    ↓

    MLP

    ↓

    Tiny GAT

    ↓

    Frozen evaluation

------------------------------------------------------------------------

## 十、论文定位建议

不要写：

"GAT improves BPC"。

建议：

> Learning-guided exact proof-tail acceleration for
> branch-price-and-cut.

贡献：

1.  月表水冰探测场景 exact BPC；
2.  proof-safe exact pricing acceleration；
3.  GNN-guided search ordering while preserving exact optimality
    certification。

------------------------------------------------------------------------

## 十一、最终建议

保留：

-   Proof-tail GAT方向；
-   exact-safe ordering；
-   oracle gate。

修改：

1.  arc head → label-state head；
2.  增加random/handcrafted baseline；
3.  提高positive context要求；
4.  优先验证scale50收益；
5.  先做oracle，再训练GAT。

最终路线：

    P0V5 exact baseline

    +
    deterministic exact acceleration

    +
    proof-tail label priority GAT

    =

    learning-enhanced exact BPC
