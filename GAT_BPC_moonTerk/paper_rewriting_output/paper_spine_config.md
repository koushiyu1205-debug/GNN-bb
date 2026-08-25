# PaperSpine Configuration

| Field | Value |
|---|---|
| Workflow | `build_from_materials` |
| Scene | `journal` |
| Tier | `pro` |
| Output language | `en` |
| Target | Transportation Research Part C: Emerging Technologies |
| Materials directory | `/home/kai/work/GAT_BPC_moonTerk` |
| Draft path | Empty; this workflow builds from materials |
| Confirmed motivation | 面向月表水冰探测的车辆路径规划；精确主线更新为 P0V4+V5，学习候选更新为正在准备的 QG2 标签状态 GAT。学习只在 V5 双向中点预处理与 P0V4 穷举回退之间重排证明尾部标签，分支引导保留为后续扩展；不使用学习引导割。正式下界、无负列证明、分支完备性、剪枝和最优性证明仍由 exact path 产生。GAT 的 Oracle、训练、校准和端到端实验未完成，不预设或虚构性能结论。 |
| Official URL | <https://www.sciencedirect.com/journal/transportation-research-part-c-emerging-technologies> |
| Reference mode | `local_first` |
| Reference paths | `.` |
| Final citation target | 20 |
| Word output | `docx` |
| Chinese translation package | `zh` |
| Humanization | `light` |
| Detection profile | `general` |
| UI language | `zh` |

## Special Requirements

1. 不虚构数据、指标、引用或实验结论。
2. 所有主张必须追溯到项目材料。
3. 明确区分严格证明、精确性保证、诊断信号和启发式策略。
4. 把主线写成定价主导、分支辅助的学习引导精确分支定价切割算法，并保持学习引导与正式证明来源分离。
5. 不使用学习引导割；割的有效性、生成、选择、激活、保留和删除由确定性精确算法规则控制。
6. 学习引导分支只排序候选，不替代分支有效性检查、完备性回退或节点证明。
7. 尚未提供的学习效果实验只建立实验协议与占位标识，不生成或暗示虚构结果。
8. 全文不要用第一人称；英文正文使用 “this paper” 或 “the proposed method”，中文翻译使用“本文”。
9. 中文论文表述默认使用“证明”；英文默认使用 `proof`/`prove`。`certify`/`certified` 仅可用于有明确推导、完备搜索或正式证明链支撑且已限定精确范围的结论，不得用于学习评分、诊断信号、启发式结果或 benchmark gate；代码字段、枚举和文件路径中的原名不改。
10. 路径范围统一使用“固定逻辑路径解空间”或 `fixed logical-path solution space`；状态语境使用“状态空间”或 `state space`；不使用“宇宙”或 `universe`。
11. 算法整体统一使用“框架”或 `framework`，不使用“骨架”或 `backbone`。
12. 全文统一使用归一化“运营成本 + 风险 + `0.4×` 加权完成时间”作为目标函数。`alpha/beta/gamma/delta` 仅属于内部兼容性审计，不得进入正文、摘要、公式、图表、结果或中文翻译。
13. 第三阶段已完成。第四阶段根据最新用户指令形成完整英文论文工作稿；尚未实现的学习模型、训练和实验结果使用明确 `TBD` 占位并留空，但不得打断问题—方法—验证—讨论的整体论证结构。
14. 第四阶段的全部改动严格限制在 `/home/kai/work/GAT_BPC_moonTerk/paper_rewriting_output/`，不得修改该目录之外的代码或报告。
15. 论文割策略采用 P0V4+V5 精确候选中的根节点 SRI-3。V5 仅使用确定性的候选分组和受限主问题增益筛选是否提交割；非根节点不分离新 SRI，已加入的根节点割可以由后代节点继承；不引入其他子集大小，也不使用学习引导割。
16. 3.1 节不把缺少物理标定与敏感性证据的月表指标混合系数写成优化模型公式；可复现性绑定冻结的生成器源码、配置和存储属性。
17. 数学变量及会变化的上下标使用斜体，固定描述标签、缩写和算子使用正体，并按 Elsevier 数学排版规则维护统一符号表。
18. 在模型中显示经典流平衡和破子环条件，并明确它们是可行路径列与原生 SPPRC 基本路径状态内嵌保证的路径级条件，而不是遗漏的主问题约束。
19. 大多数小标题只使用一个覆盖范围较大的主题短语，避免反复采用 “A and B” 式并列结构；具体机制、限制和回退条件放在正文中说明。
20. 第四节有效割小标题使用 “Valid inequalities”；正文首次正式使用 SRI-3 时解释 subset-row inequality、三任务子集、列系数含义和整数有效性。
21. 月表场景叙事不得使用“先发现就归谁”“跑马圈地”、资源竞赛、所有权优先或类似领土化表达，也不把问题另行命名为“时间敏感型资源探测”。
22. `50 km × 50 km` 范围与较高车辆速度只能表述为面向未来任务形态的前瞻性 benchmark 假设，不得写成现役月球车能力或已经验证的任务性能。
23. 永久阴影区表述为重要或高优先级的水冰候选冷阱环境，不得声称月表水冰全部只存在于永久阴影区；项目风险和资源代理不得表述为地面真值。
24. 直接太阳光不是探测、采样或钻探任务的硬性执行条件；静态任务时间窗仅用于表示外生的仪器运行、通信安排和任务计划限制，不新增动态通信资源或出发时刻相关的路径属性。
25. 引言中的真实月球数据仅表述为项目已核实使用的 LOLA 派生高程、坡度、粗糙度、永久阴影区和平均太阳可见度栅格，不得声称使用缺失的 M3、LEND 或 Diviner 图层。
26. P0V4+V5 新鲜进程验收仅支持以下范围：5、10、20、30 任务各 20 个实例全部精确闭合；50 任务 20 个实例中 15 个精确闭合，5 个为未完成定价。未完成运行不得提升为最优性、不可行性或无负列证明。
27. 当前 QG2 标签状态 GAT 只在 V5 双向中点预处理未产生可用负列后、P0V4 穷举回退之前，对同一终止类别和同一约化成本桶内的标签排序；不得过滤、支配、剪枝、改变约化成本或界，也不具有证明权限。Oracle、训练、校准和端到端验收完成前，正文只能报告方法设计、实现约束和待验证实验协议。

## Normalization Note

The submitted `draft_path` pointed to the project directory. Because the
selected workflow is `build_from_materials`, it has been normalized to an empty
draft path; the project directory remains the authoritative `materials_dir`.
