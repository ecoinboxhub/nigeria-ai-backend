import mlflow
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.rl.workforce_rl import train_rl_model


def main() -> None:
    model_path = train_rl_model(total_timesteps=3000)
    mlflow.set_experiment("workforce_scheduler")
    with mlflow.start_run(run_name="ppo_training"):
        mlflow.log_param("algorithm", "PPO")
        mlflow.log_param("model_path", model_path)
        mlflow.log_metric("timesteps", 3000)
    print(f"Saved PPO model: {model_path}")


if __name__ == "__main__":
    main()
