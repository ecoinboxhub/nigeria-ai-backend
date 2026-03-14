import logging
from app.modules.progress_visualizer.schemas import ProgressInput, ProgressOutput
from app.services.cv.progress_vision import progress_vision_service

logger = logging.getLogger(__name__)


def analyze_progress(payload: ProgressInput) -> ProgressOutput:
    if payload.image_base64:
        try:
            cv_result = progress_vision_service.analyze(
                image_base64=payload.image_base64,
                planned_completion_pct=payload.planned_completion_pct,
            )
            return ProgressOutput(
                deviation_pct=cv_result["deviation_pct"],
                exceeds_threshold=cv_result["exceeds_threshold"],
                detected_objects=cv_result["detected_objects"],
                ppe_compliance_score=cv_result["ppe_compliance_score"],
                detected_completion_pct=cv_result["detected_completion_pct"],
            )
        except Exception as e:
            logger.error(f"Computer Vision analysis failed in progress_visualizer: {e}")
            # Fallback to manual input path if CV fails

    detected = payload.detected_completion_pct or 0.0
    deviation = abs(payload.planned_completion_pct - detected)
    return ProgressOutput(
        deviation_pct=round(deviation, 2),
        exceeds_threshold=deviation > 15,
        detected_completion_pct=detected,
    )

