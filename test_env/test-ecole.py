# test_ecole_env.py
import sys
import traceback


def describe_observation(obs):
    """打印 NodeBipartite observation 的基本形状。"""
    if obs is None:
        return "None"

    parts = []
    for name in ("row_features", "variable_features", "edge_features"):
        value = getattr(obs, name, None)
        if value is not None:
            parts.append(f"{name}.shape={getattr(value, 'shape', type(value).__name__)}")

    return ", ".join(parts) if parts else type(obs).__name__


def main():
    import ecole

    print("Python:", sys.version.split()[0])
    print("Ecole:", getattr(ecole, "__version__", "unknown"))

    # 1. 生成一个小型 set cover MILP 实例
    gen = ecole.instance.SetCoverGenerator(
        n_rows=100,
        n_cols=200,
        density=0.05,
    )
    gen.seed(123)
    instance = next(gen)
    print("Instance generated:", type(instance))

    # 2. 创建 Branching 环境
    # NodeBipartite: 测试图特征 observation
    # LpIterations: 测试 reward function
    env = ecole.environment.Branching(
        observation_function=ecole.observation.NodeBipartite(),
        reward_function=ecole.reward.LpIterations(),
        scip_params={"display/verblevel": 0},  # 关闭 SCIP 大量输出
    )
    env.seed(123)

    # 3. reset 环境
    observation, action_set, reward_offset, done, info = env.reset(instance)

    print("\nreset OK")
    print("  done:", done)
    print("  reward_offset:", reward_offset)
    print("  action_set size:", 0 if action_set is None else len(action_set))
    print("  observation:", describe_observation(observation))
    print("  info type:", type(info).__name__)

    # 4. 随便选第一个合法 branching action，跑几步
    total_reward = float(reward_offset) if reward_offset is not None else 0.0
    max_steps = 20
    steps = 0

    while not done and steps < max_steps:
        if action_set is None or len(action_set) == 0:
            raise RuntimeError("Environment is not done, but action_set is empty.")

        action = int(action_set[0])

        observation, action_set, reward, done, info = env.step(action)

        steps += 1
        total_reward += float(reward) if reward is not None else 0.0

        print(
            f"step {steps:02d}: "
            f"reward={reward}, "
            f"done={done}, "
            f"next_action_set_size={0 if action_set is None else len(action_set)}"
        )

    print("\nsteps run:", steps)
    print("total_reward:", total_reward)

    if done:
        print("✅ Ecole 环境测试通过：episode 已正常结束。")
    else:
        print("✅ Ecole 环境测试通过：已成功 reset/step，达到 max_steps 后停止。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("❌ Ecole 环境测试失败:", repr(exc), file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)