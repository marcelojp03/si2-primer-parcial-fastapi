import base64
import json
import logging
import re

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.incident_ai_analysis import IncidentAiAnalysis
from app.models.incident_type import IncidentType
from app.models.specialty import Specialty
from app.repositories.incident_repository import IncidentRepository

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ── Prompts ──────────────────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """
Eres un asistente experto en auxilio mecánico vehicular.
Recibirás información de un incidente: descripción textual del conductor, transcripción de un audio
(si existe) y análisis de fotos del vehículo (si existen).

A partir de TODA la información disponible, determina:

1. "incident_type": Clasifica en uno de estos tipos exactos:
   BATERIA | LLANTA | CHOQUE | MOTOR | LLAVE | INCIERTO

2. "priority_level": Prioridad del incidente:
   BAJA | MEDIA | ALTA | CRITICA

3. "specialty": Especialidad recomendada:
   BATERIA | LLANTAS | MOTOR | SUSPENSION | CERRAJERIA_VEHICULAR | REMOLQUE

4. "requires_tow": true si el vehículo no puede moverse por sí solo, false si puede.

5. "visible_damage": Descripción breve del daño visible (si hay fotos). Si no hay fotos, null.

6. "summary": Resumen ejecutivo del incidente en 2-3 oraciones para el taller.

7. "confidence_score": Tu confianza de 0.00 a 1.00 en esta clasificación.

Devuelve SOLO JSON válido con este formato exacto:
{
  "incident_type": "...",
  "priority_level": "...",
  "specialty": "...",
  "requires_tow": true|false,
  "visible_damage": "..." | null,
  "summary": "...",
  "confidence_score": 0.00
}
"""

IMAGE_ANALYSIS_PROMPT = """
Eres un perito experto en daños vehiculares.
Analiza esta(s) imagen(es) del vehículo y describe:
1. Tipo de daño visible (abolladuras, rayones, rotura de vidrios, llanta ponchada, humo, etc.)
2. Gravedad estimada (leve, moderado, severo)
3. Si el vehículo parece poder moverse por sí solo

Responde en español, en máximo 3 oraciones concisas.
"""

# ── Maps ─────────────────────────────────────────────────────────────────

INCIDENT_TYPE_MAP = {
    "BATERIA": "BATERIA",
    "LLANTA": "LLANTA",
    "CHOQUE": "CHOQUE",
    "MOTOR": "MOTOR",
    "LLAVE": "LLAVE",
    "INCIERTO": "INCIERTO",
}

SPECIALTY_MAP = {
    "BATERIA": "BATERIA",
    "LLANTAS": "LLANTAS",
    "MOTOR": "MOTOR",
    "SUSPENSION": "SUSPENSION",
    "CERRAJERIA_VEHICULAR": "CERRAJERIA_VEHICULAR",
    "REMOLQUE": "REMOLQUE",
}


def _extract_json(text: str) -> dict:
    """Extract JSON from an LLM response that may contain markdown fences."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return json.loads(cleaned[start : end + 1])


# ── Service ──────────────────────────────────────────────────────────────


class AiService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)

    # ── 1. Transcribe audio via Whisper ──────────────────────────────────

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """Send audio bytes to OpenAI Whisper and return the transcribed text."""
        logger.info("transcribe_audio: sending %d bytes to Whisper", len(audio_bytes))
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes),
            language="es",
        )
        text = transcript.text.strip()
        logger.info("transcribe_audio: got %d chars", len(text))
        return text

    # ── 2. Analyze images via GPT-5.4-mini Vision ──────────────────────────────

    async def analyze_images(self, image_data_list: list[tuple[bytes, str]]) -> str:
        """
        Send one or more images to GPT-5.4-mini Vision.
        image_data_list: list of (image_bytes, mime_type) tuples.
        Returns a textual description of the visible damage.
        """
        if not image_data_list:
            return ""

        content: list[dict] = [{"type": "text", "text": IMAGE_ANALYSIS_PROMPT}]
        for img_bytes, mime_type in image_data_list:
            b64 = base64.b64encode(img_bytes).decode()
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64}", "detail": "low"},
                }
            )

        logger.info(
            "analyze_images: sending %d image(s) to GPT-5.4-mini Vision", len(image_data_list)
        )
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=300,
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()
        logger.info("analyze_images: got %d chars", len(result))
        return result

    # ── 3. Full classification from all evidence ─────────────────────────

    async def classify_incident(
        self,
        description: str,
        audio_transcription: str | None = None,
        image_analysis: str | None = None,
    ) -> dict:
        """
        Build a unified prompt with all available info and ask GPT-5.4-mini to classify.
        Returns parsed JSON dict with classification fields.
        """
        user_parts = [f"Descripción del conductor: {description}"]
        if audio_transcription:
            user_parts.append(f"Transcripción de audio del conductor: {audio_transcription}")
        if image_analysis:
            user_parts.append(f"Análisis de fotos del vehículo: {image_analysis}")

        user_message = "\n\n".join(user_parts)

        logger.info("classify_incident: prompt length=%d", len(user_message))
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": CLASSIFICATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content
        logger.info("classify_incident: raw response len=%d", len(raw or ""))
        return _extract_json(raw)

    # ── 4. Orchestrator: run full pipeline for an incident ───────────────

    async def run_analysis(
        self,
        incident_id: int,
        audio_bytes: bytes | None = None,
        audio_filename: str | None = None,
        image_data_list: list[tuple[bytes, str]] | None = None,
    ) -> IncidentAiAnalysis:
        """
        Full AI pipeline:
        1. Transcribe audio (if provided)
        2. Analyze images (if provided)
        3. Classify & generate summary
        4. Save IncidentAiAnalysis to DB
        """
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident not found")

        # Step 1: Audio transcription
        audio_text = None
        if audio_bytes:
            audio_text = await self.transcribe_audio(audio_bytes, audio_filename or "audio.webm")

        # Step 2: Image analysis
        image_desc = None
        if image_data_list:
            image_desc = await self.analyze_images(image_data_list)

        # Step 3: Classification
        description = incident.description_text or incident.title
        classification = await self.classify_incident(
            description=description,
            audio_transcription=audio_text,
            image_analysis=image_desc,
        )

        # Step 4: Map to DB fields — resolve FKs
        predicted_type_id = None
        inc_type_name = INCIDENT_TYPE_MAP.get(classification.get("incident_type"))
        if inc_type_name:
            stmt = select(IncidentType).where(IncidentType.name == inc_type_name)
            result = await self.session.execute(stmt)
            inc_type = result.scalar_one_or_none()
            if inc_type:
                predicted_type_id = inc_type.id

        suggested_specialty_id = None
        spec_name = SPECIALTY_MAP.get(classification.get("specialty"))
        if spec_name:
            stmt = select(Specialty).where(Specialty.name == spec_name)
            result = await self.session.execute(stmt)
            spec = result.scalar_one_or_none()
            if spec:
                suggested_specialty_id = spec.id

        # Upsert analysis row
        existing_stmt = select(IncidentAiAnalysis).where(
            IncidentAiAnalysis.incident_id == incident_id
        )
        existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()

        analysis_data = {
            "incident_id": incident_id,
            "transcribed_audio": audio_text,
            "generated_summary": classification.get("summary"),
            "predicted_incident_type_id": predicted_type_id,
            "predicted_priority_level": classification.get("priority_level"),
            "suggested_specialty_id": suggested_specialty_id,
            "visible_damage_detected": classification.get("visible_damage"),
            "predicted_requires_tow": classification.get("requires_tow", False),
            "confidence_score": classification.get("confidence_score", 0),
            "raw_response_json": json.dumps(classification, ensure_ascii=False),
        }

        if predicted_type_id is not None:
            incident.incident_type_id = predicted_type_id
        incident.priority_level = classification.get("priority_level")
        incident.requires_tow = classification.get("requires_tow", False)

        if existing:
            for key, value in analysis_data.items():
                if key != "incident_id":
                    setattr(existing, key, value)
            ai_analysis = existing
        else:
            ai_analysis = IncidentAiAnalysis(**analysis_data)
            self.session.add(ai_analysis)

        await self.session.commit()
        await self.session.refresh(ai_analysis)

        logger.info(
            "run_analysis: incident=%d type=%s priority=%s specialty=%s tow=%s conf=%.2f",
            incident_id,
            classification.get("incident_type"),
            classification.get("priority_level"),
            classification.get("specialty"),
            classification.get("requires_tow"),
            classification.get("confidence_score", 0),
        )
        return ai_analysis
