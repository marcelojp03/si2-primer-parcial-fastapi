import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.incident_evidence import IncidentEvidence
from app.schemas.ai_analysis import AiAnalysisRead
from app.services.assignment_service import AssignmentService
from app.services.ai_service import AiService
from app.utils.s3_client import build_evidence_key, upload_file

router = APIRouter(prefix="/ai-analysis", tags=["ai-analysis"])
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/vnd.wave",
    "audio/ogg",
    "audio/x-m4a",
    "application/octet-stream",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB (Whisper limit)


def _safe_filename(filename: str | None, fallback: str) -> str:
    name = Path(filename or fallback).name.strip()
    return name or fallback


async def _persist_evidence_files(
    incident_id: int,
    session: DbSession,
    *,
    audio_file: tuple[bytes, str, str] | None,
    image_files: list[tuple[bytes, str, str]],
) -> None:
    """
    Store AI input files as incident evidence.

    Evidence persistence is best-effort: AI analysis must still work if S3 is
    temporarily unavailable or credentials are missing in local development.
    """
    try:
        if audio_file:
            audio_bytes, audio_content_type, audio_filename = audio_file
            audio_key = build_evidence_key(incident_id, audio_filename)
            await upload_file(
                audio_bytes,
                audio_key,
                content_type=audio_content_type,
                metadata={
                    "incident_id": str(incident_id),
                    "evidence_type": "AUDIO",
                },
            )
            session.add(
                IncidentEvidence(
                    incident_id=incident_id,
                    evidence_type="AUDIO",
                    file_key=audio_key,
                    file_url=f"s3://{settings.AWS_S3_BUCKET}/{audio_key}",
                    mime_type=audio_content_type,
                    file_name=audio_filename,
                    file_size=len(audio_bytes),
                )
            )

        for image_bytes, image_content_type, image_filename in image_files:
            image_key = build_evidence_key(incident_id, image_filename)
            await upload_file(
                image_bytes,
                image_key,
                content_type=image_content_type,
                metadata={
                    "incident_id": str(incident_id),
                    "evidence_type": "IMAGEN",
                },
            )
            session.add(
                IncidentEvidence(
                    incident_id=incident_id,
                    evidence_type="IMAGEN",
                    file_key=image_key,
                    file_url=f"s3://{settings.AWS_S3_BUCKET}/{image_key}",
                    mime_type=image_content_type,
                    file_name=image_filename,
                    file_size=len(image_bytes),
                )
            )

        if audio_file or image_files:
            await session.commit()
            logger.info(
                "run_ai_analysis: persisted evidence incident=%d audio=%s images=%d",
                incident_id,
                bool(audio_file),
                len(image_files),
            )
    except Exception:
        await session.rollback()
        logger.warning(
            "run_ai_analysis: evidence persistence failed incident=%d",
            incident_id,
            exc_info=True,
        )


@router.post("/{incident_id}", response_model=AiAnalysisRead)
async def run_ai_analysis(
    incident_id: int,
    session: DbSession,
    _current_user: CurrentUser,
    audio: Annotated[
        UploadFile | None, File(description="Audio file (webm, mp3, wav, ogg, m4a)")
    ] = None,
    images: Annotated[
        list[UploadFile] | None, File(description="Vehicle damage photos (jpg, png, webp)")
    ] = None,
):
    """
    Run the full AI analysis pipeline for an incident.

    Accepts optional audio and image files via multipart/form-data.
    If no files are sent, the analysis uses only the incident's text description.
    """
    # Validate & read audio
    audio_bytes = None
    audio_filename = None
    audio_content_type = None
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
        audio_filename = _safe_filename(audio.filename, "audio.wav")
        audio_content_type = audio.content_type or "application/octet-stream"

    # Validate & read images
    image_data_list: list[tuple[bytes, str]] = []
    image_evidence_files: list[tuple[bytes, str, str]] = []
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
            image_content_type = img.content_type or "application/octet-stream"
            image_filename = _safe_filename(img.filename, "imagen.jpg")
            image_data_list.append((img_bytes, image_content_type))
            image_evidence_files.append((img_bytes, image_content_type, image_filename))

    logger.info(
        "run_ai_analysis: incident=%d audio=%s images=%d",
        incident_id,
        bool(audio_bytes),
        len(image_data_list),
    )

    await _persist_evidence_files(
        incident_id,
        session,
        audio_file=(
            (audio_bytes, audio_content_type, audio_filename)
            if audio_bytes and audio_content_type and audio_filename
            else None
        ),
        image_files=image_evidence_files,
    )

    import asyncio

    service = AiService(session)
    analysis = await service.run_analysis(
        incident_id=incident_id,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        image_data_list=image_data_list or None,
    )

    # Reintentar generación de candidatos hasta 3 veces con backoff
    candidates = None
    assignment_svc = AssignmentService(session)
    for attempt in range(1, 4):
        try:
            candidates = await assignment_svc.generate_candidates_if_missing(incident_id)
            if candidates:
                break
        except Exception as e:
            logger.warning(
                "Candidate generation attempt %d/3 failed for incident %d: %s",
                attempt,
                incident_id,
                e,
            )
            if attempt == 3:
                raise
            await asyncio.sleep(attempt * 2)

    if candidates:
        logger.info(
            "run_ai_analysis: auto candidates incident=%d count=%d",
            incident_id,
            len(candidates),
        )
    else:
        logger.warning(
            "run_ai_analysis: no candidates found for incident=%d "
            "(no workshops nearby or all filtered out)",
            incident_id,
        )

    return analysis


@router.get("/{incident_id}", response_model=AiAnalysisRead)
async def get_ai_analysis(incident_id: int, session: DbSession, _current_user: CurrentUser):
    """Get the existing AI analysis for an incident."""
    from sqlalchemy import select

    from app.core.exceptions import NotFoundError
    from app.models.incident_ai_analysis import IncidentAiAnalysis

    stmt = select(IncidentAiAnalysis).where(IncidentAiAnalysis.incident_id == incident_id)
    result = await session.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise NotFoundError("AI analysis not found for this incident")
    return analysis
