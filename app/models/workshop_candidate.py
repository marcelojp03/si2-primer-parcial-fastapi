from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SCHEMA = "auxilio_mecanico"


class WorkshopCandidate(Base):
    __tablename__ = "candidatos_taller_incidente"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        "incidente_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.incidentes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    workshop_id: Mapped[int] = mapped_column(
        "taller_id",
        BigInteger,
        ForeignKey(f"{SCHEMA}.talleres.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    score: Mapped[float | None] = mapped_column("puntaje", Numeric(10, 2))
    distance_km: Mapped[float | None] = mapped_column("distancia_km", Numeric(10, 2))
    estimated_arrival_minutes: Mapped[int | None] = mapped_column(
        "tiempo_estimado_llegada_min", Integer
    )
    notified: Mapped[bool] = mapped_column(
        "fue_notificado", Boolean, nullable=False, server_default="false"
    )
    notified_at: Mapped[str | None] = mapped_column("fecha_notificacion", DateTime)
    invitation_deadline: Mapped[str | None] = mapped_column("fecha_limite_respuesta", DateTime)
    response_status: Mapped[str] = mapped_column(
        "estado_respuesta", String(30), nullable=False, server_default="PENDIENTE"
    )
    responded_at: Mapped[str | None] = mapped_column("fecha_respuesta", DateTime)
    response_time_seconds: Mapped[int | None] = mapped_column(
        "tiempo_respuesta_segundos", Integer
    )
    response_note: Mapped[str | None] = mapped_column("observacion_respuesta", String(255))
    quotation_estimated_cost: Mapped[float | None] = mapped_column("costo_cotizacion", Numeric(10, 2))
    quotation_completion_minutes: Mapped[int | None] = mapped_column("tiempo_cotizacion_min", Integer)
    quotation_description: Mapped[str | None] = mapped_column("descripcion_cotizacion", String(500))

    # Relationships
    incident = relationship("Incident", back_populates="workshop_candidates")
    workshop = relationship("Workshop")
