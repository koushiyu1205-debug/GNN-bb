# SCIP 路径生成版 CVRPTW 模型

这个版本把原来的“弧变量 + 时间/载重/能量递推 Big-M 约束”改成了路径生成模型。

整体流程是：

1. 生成可复现实例，包括地形点、地形边、任务点和车辆参数。
2. 在底层地形图上计算基地与任务点之间的最短路闭包。
3. 枚举一批可行 sortie 路径；每条路径在生成时已经满足时间窗、载重、电池和回基地约束。
4. 用 SCIP 求解路径选择 MILP，在车辆-架次槽位中选择路径并覆盖所有任务。
5. 校验任务覆盖、车辆工作时长、路径载重和路径能量。

因为路径可行性已经在生成阶段处理，主 MILP 不再需要原来的时间、载重、能量 Big-M 递推约束，模型会更容易理解，也更方便继续扩展成列生成。

## 目录结构

```text
main.py                    主入口：串联实例、路径生成、建模、求解和输出
src/instance_data.py       生成 very_small 和 medium 测试实例
src/terrain.py             构建地形图并计算最短路闭包
src/route_generation.py    枚举可行 sortie 路径
src/path_milp.py           构建路径选择 MILP
src/solve.py               设置 SCIP 参数、求解并提取解
src/validation.py          校验求解结果
src/io_utils.py            JSON、路径、日志等通用工具
```

## 运行

```bash
cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance very_small --time-limit 30
python3.12 main.py --instance medium --time-limit 60
```

输出默认写到 `outputs/`：

- `instance_<name>.json`：实例数据
- `routes_<name>.json`：生成出的可行路径池
- `solution_<name>.json`：SCIP 求解结果和校验结果

## 常用参数

控制路径池大小：

```bash
python3.12 main.py --instance medium --max-route-tasks 4 --successor-limit 6 --max-routes 10000
```

静默 SCIP 日志：

```bash
python3.12 main.py --instance medium --time-limit 60 --quiet
```

## 说明

- 当前路径池是“生成出的路径集合”上的精确 MILP，不等价于枚举所有可行路径后的完整路径模型。
- `successor-limit` 和 `max-routes` 越小，路径池越小，求解越快，但模型越偏启发式。
- 单任务路径会始终优先生成，所以每个单独可行的任务都有兜底路径。
- 默认 medium 参数大约生成 1.3k 条路径；在 5 辆车、每辆 4 个架次下，大约对应 2.6 万个路径-车辆-架次二进制变量。

