from pathlib import Path

from stable_baselines3 import PPO

from app.services.rl.workforce_env import ConstructionSchedulerEnv


MODEL_PATH = Path("artifacts/models/workforce_scheduler_ppo.zip")


def load_rl_model() -> PPO | None:
    if MODEL_PATH.exists():
        return PPO.load(str(MODEL_PATH))
    return None


def train_rl_model(total_timesteps: int = 2000) -> str:
    env = ConstructionSchedulerEnv()
    model = PPO("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=total_timesteps)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    return str(MODEL_PATH)
