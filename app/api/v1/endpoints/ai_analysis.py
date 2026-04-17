import logging
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession
from app.schemas.ai_analysis import AiAnalysisRead
from app.services.ai_service import AiService

router = APIRouter(prefix="/ai-analysis", tags=["ai-analysis"])
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/ogg",
    "audio/x-m4a",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB (Whisper limit)


@router.post("/{incident_id}", response_model=AiAnalysisRead)
async def run_ai_analysis(
    incident_id: int,
    session: DbSession,
    _current_user: CurrentUser,
    audio: Annotated[UploadFile | None, File(description="Audio file (webm, mp3, wav, ogg, m4a)")] = None,
    images: Annotated[list[UploadFile] | None, File(description="Vehicle damage photos (jpg, png, webp)")] = None,
):
    """
    Run the full AI analysis pipeline for an incident.

    Accepts optional audio and image files via multipart/form-data.
    If no files are sent, the analysis uses only the incident's text description.
    """
    # Validate & read audio
    audio_bytes = None
    audio_filename = None
    if audio and audio.filename:
        if audio.content_type not in ALLOWED_AUDIO_TYPES:
            from app.core.exceptions import BadRequestError
            raise BadRequestError(
                f"Audio type '{audio.content_type}' not allowed. Use: {', '.join(ALLOWED_AUDIO_TYPES)}"
            )
        audio_bytes = await audio.read()
        if len(audio_bytes) > MAX_AUDIO_SIZE:
            from app.core.exceptions import BadRequestError
            raise BadRequestError("Audio file exceeds 25 MB limit")
        audio_filename = audio.filename

    # Validate & read images
    image_data_list: list[tuple[bytes, str]] = []
    if images:
        for img in images:
            if not img.filename:
                continue
            if img.content_type not in ALLOWED_IMAGE_TYPES:
                from app.core.exceptions import BadRequestError
                raise BadRequestError(
                    f"Image type '{img.content_type}' not allowed. Use: {', '.join(ALLOWED_IMAGE_TYPES)}"
                )
            img_bytes = await img.read()
            if len(img_bytes) > MAX_IMAGE_SIZE:
                from app.core.exceptions import BadRequestError
                raise BadRequestError(f"Image '{img.filename}' exceeds 10 MB limit")
            image_data_list.append((img_bytes, img.content_type))

    logger.info(
        "run_ai_analysis: incident=%d audio=%s images=%d",
        incident_id,
        bool(audio_bytes),
        len(image_data_list),
    )

    service = AiService(session)
    analysis = await service.run_analysis(
        incident_id=incident_id,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        image_data_list=image_data_list or None,
    )
    return analysis


@router.get("/{incident_id}", response_model=AiAnalysisRead)
async def get_ai_analysis(incident_id: int, session: DbSession, _current_user: CurrentUser):
    """Get the existing AI analysis for an incident."""
    from sqlalchemy import select
    from app.models.incident_ai_analysis import IncidentAiAnalysis
    from app.core.exceptions import NotFoundError

    stmt = select(IncidentAiAnalysis).where(IncidentAiAnalysis.incident_id == incident_id)
    result = await session.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise NotFoundError("AI analysis not found for this incident")
    return analysis
