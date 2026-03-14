import logging
from app.modules.workforce_scheduler.schemas import WorkforceAllocation, WorkforceRequest, WorkforceResponse
from app.services.rl.workforce_rl import load_rl_model

logger = logging.getLogger(__name__)


def _greedy(payload: WorkforceRequest) -> WorkforceResponse:
    schedule: list[WorkforceAllocation] = []
    idle_total = 0
    available_total = 0

    for group in payload.groups:
        allocated = min(group.required, group.available)
        utilization = 0.0 if group.available == 0 else allocated / group.available
        schedule.append(WorkforceAllocation(role=group.role, allocated=allocated, utilization=round(utilization, 3)))
        idle_total += max(group.available - allocated, 0)
        available_total += group.available

    idle_rate = 0.0 if available_total == 0 else idle_total / available_total
    return WorkforceResponse(schedule=schedule, idle_rate=round(idle_rate, 3), optimization_method="greedy")


def optimize_workforce(payload: WorkforceRequest) -> WorkforceResponse:
    try:
        model = load_rl_model()
        if model is None:
            return _greedy(payload)

        # Lightweight RL inference path for MVP: derive allocation mix from model action.
        obs = [0.5] * 10
        action, _state = model.predict(obs, deterministic=True)
        schedule: list[WorkforceAllocation] = []
        idle_total = 0
        available_total = 0

        for idx, group in enumerate(payload.groups):
            base = min(group.required, group.available)
            boost = 1 if idx == int(action) % max(1, len(payload.groups)) else 0
            allocated = min(group.available, base + boost)
            utilization = 0.0 if group.available == 0 else allocated / group.available
            schedule.append(WorkforceAllocation(role=group.role, allocated=allocated, utilization=round(utilization, 3)))
            idle_total += max(group.available - allocated, 0)
            available_total += group.available

        idle_rate = 0.0 if available_total == 0 else idle_total / available_total
        return WorkforceResponse(schedule=schedule, idle_rate=round(idle_rate, 3), optimization_method="rl_ppo")
    except Exception as e:
        logger.error(f"RL optimization failed in workforce_scheduler: {e}")
        return _greedy(payload)

