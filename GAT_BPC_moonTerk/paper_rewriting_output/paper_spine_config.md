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
| Confirmed motivation | 面向月表水冰探测的车辆路径规划；论文主线采用定价主导、分支辅助的学习引导精确 Branch-Price-and-Cut。学习层主要引导定价，并有限度地排序分支候选；不使用学习引导割。正式下界、无负列证明、分支完备性、剪枝和最优性证明仍由 exact path 产生。后续学习效果实验由用户补充，不预设或虚构性能结论。 |
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
12. 第三阶段正文写作已于 2026-07-23 获准开始；当前先起草第三节，后续章节按用户指令逐节推进。

## Normalization Note

The submitted `draft_path` pointed to the project directory. Because the
selected workflow is `build_from_materials`, it has been normalized to an empty
draft path; the project directory remains the authoritative `materials_dir`.
