import numpy as np
from gymnasium import Env, spaces


class ConstructionSchedulerEnv(Env):
    metadata = {"render_modes": []}

    def __init__(self) -> None:
        super().__init__()
        self.observation_space = spaces.Box(low=0, high=1, shape=(10,), dtype=np.float32)
        self.action_space = spaces.Discrete(10)
        self.steps = 0
        self.max_steps = 50

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.steps = 0
        obs = np.random.rand(10).astype(np.float32)
        return obs, {}

    def step(self, action):
        self.steps += 1
        reward = float(np.random.uniform(-1, 1))
        terminated = self.steps >= self.max_steps
        truncated = False
        obs = np.random.rand(10).astype(np.float32)
        info = {"action": int(action)}
        return obs, reward, terminated, truncated, info
