from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class IncidentAiAnalysis(Base):
    __tablename__ = "analisis_ia_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    transcribed_audio: Mapped[str | None] = mapped_column("audio_transcrito", Text)
    generated_summary: Mapped[str | None] = mapped_column("resumen_generado", Text)
    predicted_incident_type_id: Mapped[int | None] = mapped_column(
        "tipo_incidente_predicho_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.tipos_incidente.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    predicted_priority_level: Mapped[str | None] = mapped_column(
        "nivel_prioridad_predicho", String(20)
    )
    suggested_specialty_id: Mapped[int | None] = mapped_column(
        "especialidad_sugerida_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.especialidades.id", onupdate="CASCADE", ondelete="SET NULL"),
    )
    visible_damage_detected: Mapped[str | None] = mapped_column("danio_visible_detectado", Text)
    predicted_requires_tow: Mapped[bool | None] = mapped_column(
        "requiere_remolque_predicho", Boolean
    )
    confidence_score: Mapped[float | None] = mapped_column("puntaje_confianza", Numeric(5, 2))
    raw_response_json: Mapped[str | None] = mapped_column("respuesta_cruda_json", Text)
    created_at: Mapped[str] = mapped_column(
        "fecha_creacion", DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        "fecha_actualizacion", DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    incident = relationship("Incident", back_populates="ai_analysis")
    predicted_incident_type = relationship("IncidentType")
    suggested_specialty = relationship("Specialty")
